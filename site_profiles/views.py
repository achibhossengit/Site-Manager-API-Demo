from datetime import datetime
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from site_profiles.models import Site, SiteCost, SiteCash, SiteBill
from site_profiles.serializers import SiteSerializerList, SiteSerializerDetails, SiteCostSerializer, SiteCostUpdatePermissionSerializer, SiteCashSerializer, SiteCashUpdatePermissionSerializer, SiteBillSerializer
from site_profiles.permissions import SiteRecordAccessPermission, SiteBillAccessPermission, SiteProfileAccessPermissions, DateBasedSiteSummaryPermission, TotalSiteSummaryPermission
from api.filters import SiteCostFilterClass, SiteCashFilterClass, SiteBillFilterClass
from site_profiles.services.site_summary import get_date_based_site_summary, get_total_site_summary

class SiteViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, SiteProfileAccessPermissions]
    queryset = Site.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SiteSerializerList
        return SiteSerializerDetails

class DateBasedSiteSummaryView(APIView):
    permission_classes = [IsAuthenticated, DateBasedSiteSummaryPermission]
    def get(self, request, site_id, date):
        user_type = request.user.user_type
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            
        date_based_site_summary = get_date_based_site_summary(site_id, parsed_date, user_type)
        return Response(date_based_site_summary, status=status.HTTP_200_OK)

class TotalSiteSummaryView(APIView):
    permission_classes = [IsAuthenticated, TotalSiteSummaryPermission]
    def get(self, request, site_id):
        date_based_site_summary = get_total_site_summary(site_id)
        return Response(date_based_site_summary, status=status.HTTP_200_OK)


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
        return SiteCost.objects.filter(site=site_id).order_by('date')

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
        return SiteCash.objects.filter(site=site_id).order_by('date')
    
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
        return SiteBill.objects.filter(site=site_id).order_by('date')
        
    def perform_create(self, serializer):
        site_id = self.kwargs.get('site_pk')  # from nested router
        site = Site.objects.get(pk=site_id)
        serializer.save(site=site)
