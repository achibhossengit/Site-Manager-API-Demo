from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Value, F
from django.db.models.functions import Coalesce
from django.db.models import FloatField, IntegerField
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from site_profiles.models import Site, SiteCost, SiteCash, SiteBill
from site_profiles.serializers import SiteSerializer, SiteSerializerForViewer, SiteSerializerForManager,SiteCostSerializer, SiteCostUpdatePermissionSerializer, SiteCashSerializer, SiteCashUpdatePermissionSerializer, SiteBillSerializer
from site_profiles.permissions import SiteRecordAccessPermission, SiteBillAccessPermission, SiteProfileAccessPermissions, GetSiteTotalByDateViewPermission
from daily_records.models import DailyRecord, WorkSession, DailyRecordSnapshot
from api.filters import SiteCostFilterClass, SiteCashFilterClass, SiteBillFilterClass

class SiteViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, SiteProfileAccessPermissions]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['main_manager', 'viewer']:
            return Site.objects.all()
        elif user.user_type == 'site_manager':
            return Site.objects.filter(id=user.current_site_id)
        return Site.objects.none()
    
    def get_serializer_class(self):
        user = self.request.user
        if self.action == 'list':
            return SiteSerializer
        if user.user_type == 'viewer':
            return SiteSerializerForViewer
        elif user.user_type in ['main_manager', 'site_manager']:
            return SiteSerializerForManager
        return SiteSerializer
    
class SiteInfoView(ModelViewSet):
    serializer_class = SiteSerializer
    queryset = Site.objects.all()
    http_method_names = ['get', 'head', 'options']
    
    
class SiteCostViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated,  SiteRecordAccessPermission]
    filterset_class = SiteCostFilterClass

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return SiteCostUpdatePermissionSerializer
        return SiteCostSerializer

    def get_queryset(self):
        user = self.request.user
        site_id = self.kwargs.get('site_pk')
        if not site_id:
            return SiteCost.objects.none()
        if (user.user_type == 'site_manager'  and user.current_site_id != int(site_id)):
            raise PermissionDenied('Site Manager Only can see his Site Records.')
        return SiteCost.objects.filter(site=site_id).order_by('-date')

    def perform_create(self, serializer):
        site_id = self.kwargs.get('site_pk')  # from nested router
        site = Site.objects.get(pk=site_id)
        serializer.save(site=site)
        
        
class SiteCashViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated,  SiteRecordAccessPermission]
    filterset_class = SiteCashFilterClass

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return SiteCashUpdatePermissionSerializer
        return SiteCashSerializer

    def get_queryset(self):
        user = self.request.user
        site_id = self.kwargs.get('site_pk')
        if not site_id:
            return SiteCash.objects.none()
        if (user.user_type == 'site_manager'  and user.current_site_id != int(site_id)):
            raise PermissionDenied('Site Manager Only can see his Site Records.')
        return SiteCash.objects.filter(site=site_id).order_by('-date')
    
    def perform_create(self, serializer):
        site_id = self.kwargs.get('site_pk')  # from nested router
        site = Site.objects.get(pk=site_id)
        serializer.save(site=site)
    
    
class SiteBillViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, SiteBillAccessPermission]
    filterset_class = SiteBillFilterClass
    serializer_class = SiteBillSerializer
        
    def get_queryset(self):
        site_id = self.kwargs.get('site_pk')
        if not site_id:
            return SiteBill.objects.none()
        return SiteBill.objects.filter(site=site_id).order_by('-date')
        
    def perform_create(self, serializer):
        site_id = self.kwargs.get('site_pk')  # from nested router
        site = Site.objects.get(pk=site_id)
        serializer.save(site=site)
    
    
class GetSiteTotalByDateView(APIView):
    """
    URL: path('site-total/<int:site_id>/<date>/', GetSiteTotalByDateView.as_view(), name='site-total')
    date format: YYYY-MM-DD
    """
    
    permission_classes=[IsAuthenticated, GetSiteTotalByDateViewPermission]

    def get(self, request, *args, **kwargs):
        site_id = self.kwargs.get('site_id')
        today = datetime.today()
        site = get_object_or_404(Site, pk=site_id)

        # site_cash.amount is PositiveIntegerField -> use IntegerField for Value fallback
        site_cash_total = SiteCash.objects.filter(site=site, date=today) \
            .aggregate(total=Coalesce(Sum('amount'), Value(0, output_field=IntegerField())))['total']

        # site cost / other cost / bill amounts are integers -> IntegerField
        site_cost_total = SiteCost.objects.filter(site=site, date=today, type='st') \
            .aggregate(total=Coalesce(Sum('amount'), Value(0, output_field=IntegerField())))['total']
        other_cost_total = SiteCost.objects.filter(site=site, date=today, type='ot') \
            .aggregate(total=Coalesce(Sum('amount'), Value(0, output_field=IntegerField())))['total']

        # daily record sums:
        daily_qs = DailyRecord.objects.filter(site=site, date=today).select_related('employee')
        snap_qs = DailyRecordSnapshot.objects.filter(date = datetime.today()).select_related('employee')

        # total khoraki, advance and present from DailyRecordTable
        present_from_dailyRecord = daily_qs.aggregate(total=Coalesce(Sum('present'), Value(0.0, output_field=FloatField())))['total']
        khoraki_from_dailyRecord = daily_qs.aggregate(total=Coalesce(Sum('khoraki'), Value(0, output_field=IntegerField())))['total']
        advance_from_dailyRecord = daily_qs.aggregate(total=Coalesce(Sum('advance'), Value(0, output_field=IntegerField())))['total']

        # total khoraki and advance from DailyRecordSnapShot (today)
        present_from_dailyRecordSnapshot = snap_qs.aggregate(total=Coalesce(Sum('present'), Value(0.0, output_field=FloatField())))['total']
        khoraki_from_dailyRecordSnapshot = snap_qs.aggregate(total=Coalesce(Sum('khoraki'), Value(0, output_field=IntegerField())))['total']
        advance_from_dailyRecordSnapshot = snap_qs.aggregate(total=Coalesce(Sum('advance'), Value(0, output_field=IntegerField())))['total']


        emp_present_total = present_from_dailyRecord + present_from_dailyRecordSnapshot
        emp_khoraki_total = khoraki_from_dailyRecord + khoraki_from_dailyRecordSnapshot
        emp_advance_total = advance_from_dailyRecord + advance_from_dailyRecordSnapshot

        # work sessions (count int, pay_or_return is IntegerField)
        start_of_day = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        end_of_day = timezone.make_aware(datetime.combine(today + timedelta(days=1), datetime.min.time()))

        sessions_agg = WorkSession.objects.filter(
            site=site,
            created_at__gte=start_of_day,
            created_at__lt=end_of_day
        ).aggregate(
            count=Coalesce(Count('id'), Value(0, output_field=IntegerField())),
            total_pay_or_return=Coalesce(Sum('pay_or_return'), Value(0, output_field=IntegerField()))
        )

        response_data = {
            "site": {"id": site.id, "name": str(site)},
            "date": today.isoformat(),
            "site_cash": site_cash_total,
            "site_cost": site_cost_total,
            "other_cost": other_cost_total,
            "present": emp_present_total,
            "khoraki": emp_khoraki_total,
            "advance": emp_advance_total,
            "session_created": sessions_agg.get('count') or 0,
            "from_session": sessions_agg.get('total_pay_or_return') or 0
        }

        return Response(response_data, status=status.HTTP_200_OK)
