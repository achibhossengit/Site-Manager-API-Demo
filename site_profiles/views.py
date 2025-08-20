from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from site_profiles.models import Site, SiteCost, SiteCash, SiteBill
from site_profiles.serializers import SiteSerializer, SiteSerializerForViewer, SiteSerializerForManager,SiteCostSerializer, SiteCostUpdatePermissionSerializer, SiteCashSerializer, SiteCashUpdatePermissionSerializer, SiteBillSerializer
from site_profiles.permissions import IsAdminOrConditionalPermission, SiteBillAccessPermission, SiteProfileAccessPermissions

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