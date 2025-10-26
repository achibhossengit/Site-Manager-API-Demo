from datetime import datetime
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from daily_records.models import DailyRecord, WorkSession, DailyRecordSnapshot
from daily_records.serializers import DailyRecordAccessSerializer, DailyRecordCreateSerializer, DailyRecordUpdatePermissionSerializer, WorkSessionSerializer, WorkSessionPermissionUpdateSerializer, WorkSessionPayOrReturnFieldUpdateSerializer, DailyRecordSnapshotSerializer
from daily_records.permissions import DailyRecordPermission, IsManagerUpdateOrConditionalReadonly, CurrentWorkSessionPermission
from api.services.get_current_worksession import get_current_worksession
from api.services.create_worksession import create_worksession
from users.models import CustomUser

class DailyRecordViewSet(ModelViewSet):    
    permission_classes = [IsAuthenticated, DailyRecordPermission]
    filterset_fields = ['site', 'employee__current_site', 'date', 'employee']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DailyRecordCreateSerializer
        elif self.request.method == 'PATCH':
            return DailyRecordUpdatePermissionSerializer
        return DailyRecordAccessSerializer

    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'employee':
            return DailyRecord.objects.filter(employee=user).order_by('date')
        elif user.user_type == 'site_manager':
            # fetch his site labours records only
            return DailyRecord.objects.filter(employee__current_site=user.current_site).order_by('date')
        elif user.user_type in ['main_manager', 'viewer']:
            return DailyRecord.objects.all().order_by('date')            
        return None
    
    def create(self, request, *args, **kwargs):
        is_many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=is_many)
        serializer.is_valid(raise_exception=True)

        site = getattr(request.user, "current_site", None)
        if not site:
            return Response({"detail": "আপনার জন্য কোনো সাইট সেট করা হয়নি।"}, status=status.HTTP_400_BAD_REQUEST)

        records = []
        for item in (serializer.validated_data if is_many else [serializer.validated_data]):
            item["site"] = site
            records.append(DailyRecord(**item))

        with transaction.atomic():
            DailyRecord.objects.bulk_create(records)

        return Response({"created": len(records)}, status=status.HTTP_201_CREATED)
    
    
class WorkSessionViewSet(ModelViewSet):
    http_method_names = ['get', 'patch']
    permission_classes = [IsAuthenticated, IsManagerUpdateOrConditionalReadonly]
    
    def get_serializer_class(self):
        if(self.request.method == 'PATCH'):
            if(self.request.user.user_type == 'site_manager'):
                return WorkSessionPermissionUpdateSerializer
            elif(self.request.user.user_type == 'main_manager'):
                return WorkSessionPayOrReturnFieldUpdateSerializer
        return WorkSessionSerializer

    def get_queryset(self):
        user = self.request.user
        employee_id = self.kwargs.get('user_pk')
        if not employee_id:
            return WorkSession.objects.none()
        employee=get_object_or_404(CustomUser,id=employee_id)
        
        if user.user_type == 'employee' and user.id != employee.id:
            raise PermissionDenied('Employee only can see his own worksessions.')
        elif user.user_type == 'site_manager' and user.current_site != employee.current_site:
            raise PermissionDenied('Site Manager only can see his his site employee worksessions.')
        return WorkSession.objects.filter(employee = employee_id)
        
    
    @action(detail=False, methods=['get'], url_path='last_session')
    def last_session(self, request, *args, **kwargs):
        last_session = self.get_queryset().order_by('end_date').last()
        
        serializer = self.get_serializer(last_session)
        return Response(serializer.data, status=status.HTTP_200_OK)

        
        
class CurrentWorkSession(APIView):
    permission_classes = [IsAuthenticated, CurrentWorkSessionPermission]
    
    def get(self, request, *args, **kwargs):
        employee_id = self.kwargs['emp_id']
        current_worksession = get_current_worksession(employee_id)

        if not current_worksession:
            return Response({})

        current_worksession.pop('last_record')
        current_worksession.pop('work_records')

        return Response(current_worksession)

    def post(self, request, *args, **kwargs):
        employee_id = self.kwargs['emp_id']
        pay_or_return = request.data.get('pay_or_return', 0)
        try:
            result = create_worksession(employee_id, pay_or_return)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_201_CREATED)
    
    
class DailyRecordSnapshotViewset(ModelViewSet):
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]
    queryset = DailyRecordSnapshot.objects.all()
    serializer_class = DailyRecordSnapshotSerializer
    filterset_fields = ['site']

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['main_manager', 'viewer']:
            return DailyRecordSnapshot.objects.filter(date=datetime.today())
        elif user.user_type == 'site_manager':
            return DailyRecordSnapshot.objects.filter(date=datetime.today(), site = user.current_site)
        elif user.user_type == 'employee':
            return DailyRecordSnapshot.objects.filter(date=datetime.today(), employee = user)
        else:
            return DailyRecordSnapshot.objects.none()
