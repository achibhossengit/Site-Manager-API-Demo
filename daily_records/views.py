from datetime import datetime
from django.db import transaction
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from daily_records.models import DailyRecord, WorkSession, DailyRecordSnapshot
from daily_records.serializers import DailyRecordAccessSerializer, DailyRecordCreateSerializer, DailyRecordUpdatePermissionSerializer, WorkSessionSerializer, WorkSessionPermissionUpdateSerializer, WorkSessionPayOrReturnFieldUpdateSerializer, DailyRecordSnapshotSerializer
from daily_records.permissions import IsAdminOrConditionalPermissionForDailyRecord, IsManagerUpdateOrConditionalReadonly, CurrentWorkSessionPermission
from api.services.get_current_worksession import get_current_worksession
from api.services.create_worksession import create_worksession


class DailyRecordViewSet(ModelViewSet):
    """
    Permissions:
        - Admins:
            → Can create, retrieve, update, and delete any daily record.
        - Main Managers:
            → Can retrieve (GET) all daily records.
            → Can update (PUT) only when permission_level == 1.
            → Can delete (DELETE) only when permission_level == 2.
            → Cannot create (POST) daily records.
        - Site Managers:
            → Can retrieve (GET) daily records for their own site.
            → Can create (POST) daily records for their employees.
            → Can partially update (PATCH) permission_level of records in their site.
        - Viewers:
            → Can only retrieve (GET) daily records.
        - Employees:
            → Can retrieve (GET) only their own daily records.
            → Cannot create, update, or delete any records.
    """
    
    permission_classes = [IsAuthenticated,  IsAdminOrConditionalPermissionForDailyRecord]
    filterset_fields = ['site', 'employee', 'date']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DailyRecordCreateSerializer
        
        if self.request.method == 'PATCH':
            return DailyRecordUpdatePermissionSerializer

        return DailyRecordAccessSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.user_type in ['main_manager', 'viewer']:
            return DailyRecord.objects.all().order_by('date')
        
        if user.user_type == 'site_manager':
            return DailyRecord.objects.filter(site=user.current_site).order_by('date')

        if user.user_type == 'employee':
            return DailyRecord.objects.filter(employee = user).order_by('date')
        
        return DailyRecord.objects.none()
    
    
    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk(self, request):
        
        records = request.data.get('records')
        record_date = request.data.get('date')
        if not isinstance(records, list) or not record_date:
            return Response(
                {"detail": "Need records and record_date both"},
                status=status.HTTP_400_BAD_REQUEST
            )

        site = request.user.current_site
        for item in records:
            item["site"] = site
            item["date"] = record_date

        serializer = self.get_serializer(data=records, many=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
class WorkSessionViewSet(ModelViewSet):
    """
    Permissions:
    1. main_manager:
        - Can view all WorkSessions.
        - Can update the `is_paid` field only if `update_permission=True`.

    2. viewer:
        - Can only view (GET) all WorkSessions.
        - Cannot perform any updates.

    3. site_manager:
        - Can view only WorkSessions created by their assigned site.
        - Can update only the `update_permission` field.

    4. employee:
        - Can view only their own WorkSessions.
        - Cannot update anything.

    Methods Allowed:
        - GET: List or retrieve WorkSessions.
        - PATCH: Partially update WorkSession (based on update_permission).
    """
    http_method_names = ['get', 'patch']
    permission_classes = [IsAuthenticated, IsManagerUpdateOrConditionalReadonly]
    filterset_fields = ['employee']
    
    def get_serializer_class(self):
        if(self.request.method == 'PATCH'):
            if(self.request.user.user_type == 'site_manager'):
                return WorkSessionPermissionUpdateSerializer
            elif(self.request.user.user_type == 'main_manager'):
                return WorkSessionPayOrReturnFieldUpdateSerializer
                
        return WorkSessionSerializer
        

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['main_manager', 'viewer']:
            return WorkSession.objects.all()
        elif user.user_type == 'site_manager':
            return WorkSession.objects.filter(site = user.current_site)
        elif user.user_type == 'employee':
            return WorkSession.objects.filter(employee = user)
        
        else: return WorkSession.objects.none()
        
        
    @action(detail=False, methods=['get'], url_path='last_session')
    def last_session(self, request):
        last_session = self.get_queryset().order_by('end_date').last()

        if not last_session:
            return Response(
                {"detail": "কোনো কাজের সেশন পাওয়া যায়নি।"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(last_session)
        return Response(serializer.data, status=status.HTTP_200_OK)

        
        
class CurrentWorkSession(APIView):
    """
    Permissions:
    GET:
    1. main_manager:
        - Can retrieve current WorkSession for any employee.

    2. viewer:
        - Can retrieve current WorkSession for any employee.

    3. site_manager:
        - Can retrieve current WorkSession of their own site employees only.

    4. employee:
        - Can only retrieve their own current WorkSession.

    POST:
    1. site_manager:
        - Can create a new WorkSession for their own site employees only.
        - Other user types are not allowed to create WorkSessions.

    Methods Allowed:
        - GET: Return calculated current work session data for a given employee.
        - POST: Create a new WorkSession with calculated data.
    """
    permission_classes = [IsAuthenticated, CurrentWorkSessionPermission]
    
    def get(self, request, *args, **kwargs):
        employee_id = self.kwargs['emp_id']
        current_worksession = get_current_worksession(employee_id)        

        current_worksession.pop('last_record')

        return Response(current_worksession)

    def post(self, request, *args, **kwargs):
        employee_id = self.kwargs['emp_id']
        pay_or_return = request.data.get('pay_or_return', 0)
        try:
            result = create_worksession(employee_id, pay_or_return)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(result, status=status.HTTP_201_CREATED)
    
    
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