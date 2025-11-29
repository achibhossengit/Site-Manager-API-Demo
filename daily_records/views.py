from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction 
from django.db.models import Sum, Min, Max
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from daily_records.models import DailyRecord, WorkSession, DailyRecordSnapshot, SiteWorkRecord
from daily_records.serializers import DailyRecordAccessSerializer, DailyRecordCreateSerializer, DailyRecordUpdatePermissionSerializer, WorkSessionDetailsSerializer,  WorkSessionListSerializer,DailyRecordSnapshotSerializer
from daily_records.permissions import DailyRecordPermission, WorkSessionAccessPermission, CurrentWorkSessionPermission
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
    http_method_names = ['get']
    permission_classes = [IsAuthenticated, WorkSessionAccessPermission]
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_date']
    ordering = ['created_date']

    def get_queryset(self):
        emp_id = self.kwargs.get('user_pk')
        if(self.action == 'list'):
            return WorkSession.objects.filter(employee_id=emp_id)
        return WorkSession.objects.filter(employee_id=emp_id).prefetch_related('records')
    
    def get_serializer_class(self):
        if(self.action == 'list'):
            return WorkSessionListSerializer
        return WorkSessionDetailsSerializer
    
    @action(detail=False, methods=['get'], url_path='last_session')
    def last_session(self, request, *args, **kwargs):
        last_session = self.get_queryset().order_by("-created_date").first()
        
        if not last_session:
            return Response({"detail": "No work sessions found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(last_session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CurrentWorkSession(APIView):
    permission_classes = [IsAuthenticated, CurrentWorkSessionPermission]
    
    def get(self, request, *args, **kwargs):
        emp_id = self.kwargs['emp_id']
        employee = get_object_or_404(CustomUser, id=emp_id)
        current_session = DailyRecord.objects.filter(employee_id=emp_id).aggregate(
            present=Sum('present', default=0),
            khoraki=Sum('khoraki', default=0),
            advance=Sum('advance', default=0)
            )
        last_worksession = WorkSession.objects.filter(employee_id=emp_id).order_by("-created_date").first()

        current_salary = employee.current_salary
        prev_payable = last_worksession.rest_payable if last_worksession else 0

        current_session["salary"] = current_salary
        current_session['total_salary'] = current_session["present"] * current_salary
        current_session["prev_payable"] = prev_payable

        return Response(current_session)


    def post(self, request, *args, **kwargs):
        emp_id = self.kwargs.get('emp_id')
        employee = get_object_or_404(CustomUser, id=emp_id)
        
        try:
            with transaction.atomic():
                today = timezone.localdate()
                yesterday = today - timedelta(days=1)
                # 0. Fetch Dailyrecords
                daily_records = DailyRecord.objects.filter(employee_id=emp_id)
                # 1. Calculate totals
                totals = daily_records.aggregate(
                    total_present=Sum('present', default=0),
                    total_khoraki=Sum('khoraki', default=0),
                    total_advance=Sum('advance', default=0),
                    # if no Dailyrecord exits
                    start_date=Min('date', default=today),
                    end_date=Max('date', default=today)
                )
                # 2. Fetch last worksession
                last_worksession = WorkSession.objects.filter(employee_id=emp_id).order_by("-created_date").first()
                
                current_salary = employee.current_salary
                prev_payable = last_worksession.rest_payable if last_worksession else 0
                pay_or_return = request.data.get('pay_or_return', 0) # from request body
                site_id = request.user.current_site_id # site_manager site who create it
                
                # 3. Validate before create
                if(last_worksession and last_worksession.created_date == today):
                    return Response(
                        {"error": "session_exists_today"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
                if not daily_records.exists() and pay_or_return == 0:
                    return Response(
                        {"error": "no_daily_records_and_no_payment"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # 4. Create WorkSession
                work_session = WorkSession.objects.create(
                    employee_id=emp_id,
                    site_id=site_id,
                    start_date=totals['start_date'],
                    end_date=totals['end_date'],
                    present=totals['total_present'],
                    khoraki=totals['total_khoraki'],
                    advance=totals['total_advance'],
                    session_salary=current_salary,
                    last_session_payable=prev_payable,
                    pay_or_return=pay_or_return
                )
                
                # 5. Calculate totals by site for SiteWorkRecord
                totals_by_site_qs = daily_records.values('site').annotate(
                    total_present=Sum('present', default=0),
                    total_khoraki=Sum('khoraki', default=0),
                    total_advance=Sum('advance', default=0)
                )

                # Employee has no daily records but has previous payable amount
                totals_by_site = totals_by_site_qs if totals_by_site_qs else [
                    # empty record
                    {
                        "site": request.user.current_site_id,
                        "total_present": 0,
                        "total_khoraki": 0,
                        "total_advance": 0,
                    }
                ]
                            
                # 6. Create SiteWorkRecord for each site
                site_work_records = []
                for site_data in totals_by_site:
                    is_session_owner = (site_data['site'] == site_id)
                    
                    site_work_record = SiteWorkRecord(
                        work_session=work_session,
                        site_id=site_data['site'],
                        session_owner=is_session_owner,
                        present=site_data['total_present'],
                        session_salary=current_salary,
                        khoraki=site_data['total_khoraki'],
                        advance=site_data['total_advance'],
                        pay_or_return=pay_or_return if is_session_owner else 0
                    )
                    site_work_records.append(site_work_record)
                
                SiteWorkRecord.objects.bulk_create(site_work_records)
                
                # 7. Create DailyRecordSnapshot for today and yesterday
                records_to_snapshot = daily_records.filter(date__in=[today, yesterday])
                
                snapshots = []
                for record in records_to_snapshot:
                    snapshot = DailyRecordSnapshot(
                        site=record.site,
                        employee=record.employee,
                        date=record.date,
                        present=record.present,
                        khoraki=record.khoraki,
                        advance=record.advance,
                        comment=record.comment,
                        current_salary=current_salary
                    )
                    snapshots.append(snapshot)
                
                DailyRecordSnapshot.objects.bulk_create(snapshots)
                
                # 8. Delete all daily records for this employee
                deleted_count = daily_records.delete()[0]
                
                # 9. Return success response
                return Response({
                    "message": "WorkSession created successfully",
                    "work_session_id": work_session.id,
                    "total_present": totals['total_present'],
                    "total_khoraki": totals['total_khoraki'],
                    "total_advance": totals['total_advance'],
                    "earned_salary": work_session.earned_salary,
                    "total_payable": work_session.total_payable,
                    "pay_or_return": pay_or_return,
                    "rest_payable": work_session.rest_payable,
                    "site_work_records_created": len(site_work_records),
                    "snapshots_created": len(snapshots),
                    "daily_records_deleted": deleted_count
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
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
