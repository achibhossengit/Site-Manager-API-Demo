from datetime import datetime
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Value, F
from django.db.models.functions import Coalesce
from django.db.models import FloatField, IntegerField
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from site_profiles.models import Site, SiteCost, SiteCash, SiteBill
from site_profiles.serializers import SiteSerializer, SiteSerializerForViewer, SiteSerializerForManager,SiteCostSerializer, SiteCostUpdatePermissionSerializer, SiteCashSerializer, SiteCashUpdatePermissionSerializer, SiteBillSerializer
from site_profiles.permissions import IsAdminOrConditionalPermission, SiteBillAccessPermission, SiteProfileAccessPermissions, GetSiteTotalByDateViewPermission
from daily_records.models import DailyRecord, WorkSession, DailyRecordSnapshot

class SiteViewSet(ModelViewSet):
    """
    Permissions:
        - Admins and Main Managers:
            → Can create, retrieve, update, and delete site data.
        - Authenticated Users (other roles):
            → Can only retrieve (GET) site data.
        - Anonymous Users:
            → Can also retrieve (GET) site data.
            → Useful for displaying site profiles on public homepages.
    Notes:
        - All users (authenticated or not) can view site data.
        - Only Admins and Main Managers have full modification rights.
    """
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
    """
    Permissions:
        - Admin (is_staff):
            → Can list, retrieve, create, update, and delete any SiteCost.
        - Main Manager:
            → Can list and retrieve all SiteCost.
            → Can update (PUT) only if `permission_level == 1`.
            → Can delete only if `permission_level == 2`.
            → Cannot create SiteCost.
        - Viewer:
            → Can only list and retrieve (read-only access).
        - Site Manager:
            → Can list and retrieve SiteCost records for their assigned site.
            → Can create (POST) new SiteCost for their own site.
            → Can partially update (PATCH) the `permission_level` of their own site records.
    Notes:
        - All actions require authenticated users.
        - Other user types are denied access.
    """
    
    permission_classes = [IsAuthenticated,  IsAdminOrConditionalPermission]
    filterset_fields = ['site', 'date']
    
    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return SiteCostUpdatePermissionSerializer
        return SiteCostSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.user_type in ['main_manager', 'viewer']:
            return SiteCost.objects.all()
        if user.user_type == 'site_manager':
            return SiteCost.objects.filter(site=user.current_site)
        return SiteCost.objects.none()
        
        
        
class SiteCashViewSet(ModelViewSet):
    """
    Permissions:
        - Admin (is_staff):
            → Can list, retrieve, create, update, and delete any SiteCash.
        - Main Manager:
            → Can list and retrieve all SiteCash.
            → Can update (PUT) only if `permission_level == 1`.
            → Can delete only if `permission_level == 2`.
            → Cannot create SiteCash.
        - Viewer:
            → Can only list and retrieve (read-only access).
        - Site Manager:
            → Can list and retrieve SiteCash belonging to their own site.
            → Can create (POST) new SiteCash for their own site.
            → Can partially update (PATCH) `permission_level` for their own site's records.
    Notes:
        - All users must be authenticated.
        - Other user types are denied access.
    """
    
    permission_classes = [IsAuthenticated,  IsAdminOrConditionalPermission]
    filterset_fields = ['site', 'date']
    
    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return SiteCashUpdatePermissionSerializer
        return SiteCashSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.user_type in ['main_manager', 'viewer']:
            return SiteCash.objects.all()
        if user.user_type == 'site_manager':
            return SiteCash.objects.filter(site=user.current_site)
        return SiteCash.objects.none()
    
    
class SiteBillViewSet(ModelViewSet):
    """
    Permissions:
        - Admin → can get, create, update, delete.
        - Main Manager → can get, create, update, delete.
        - Viewer → can only view (
    """
    permission_classes = [IsAuthenticated, SiteBillAccessPermission]
    serializer_class = SiteBillSerializer
    queryset = SiteBill.objects.all().order_by('-date')
    filterset_fields = ['site']
    
    
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
        sessions_agg = WorkSession.objects.filter(site=site, start_date__lte=today, end_date__gte=today) \
            .aggregate(
                count=Coalesce(Count('id'), Value(0, output_field=IntegerField())),
                total_pay_or_return=Coalesce(Sum('pay_or_return'), Value(0, output_field=IntegerField()))
            )

        response_data = {
            "site": {"id": site.id, "name": str(site)},
            "date": today.isoformat(),
            "site_cash_total": site_cash_total,
            "site_cost_total": site_cost_total,
            "other_cost_total": other_cost_total,
            "employees": {
                "present_total": emp_present_total,
                "khoraki_total": emp_khoraki_total,
                "advance_total": emp_advance_total,
            },
            "work_sessions": {
                "count": sessions_agg.get('count') or 0,
                "total_pay_or_return": sessions_agg.get('total_pay_or_return') or 0
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)
