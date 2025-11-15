from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from site_profiles.models import Site, SiteCost, SiteCash, SiteBill
from site_profiles.serializers import SiteSerializerList, SiteSerializerDetails, SiteCostSerializer, SiteCostUpdatePermissionSerializer, SiteCashSerializer, SiteCashUpdatePermissionSerializer, SiteBillSerializer
from site_profiles.permissions import SiteRecordAccessPermission, SiteBillAccessPermission, SiteProfileAccessPermissions, SiteSummaryAccessPermission
from api.filters import SiteCostFilterClass, SiteCashFilterClass, SiteBillFilterClass
from site_profiles.services.site_summary import get_site_summary

class SiteViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, SiteProfileAccessPermissions]
    queryset = Site.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SiteSerializerList
        return SiteSerializerDetails

    @action(detail=True, methods=['get'], url_path='summary', permission_classes=[IsAuthenticated, SiteSummaryAccessPermission])
    def summary(self, request, pk=None):
        """
        Returns different data based on user type:
        - site_manager: Today's summary with balance
        - viewer/main_manager: Today's summary with balance + total summary
        """
        user_type = request.user.user_type
        site = self.get_object()
        
        site_summary = get_site_summary(site, user_type)
        return Response(site_summary, status=status.HTTP_200_OK)

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
