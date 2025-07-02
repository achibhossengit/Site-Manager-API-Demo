from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from site_profiles.models import Site, SiteCost
from site_profiles.serializers import SiteSerializer, SiteCostSerializer, SiteCostUpdatePermissionSerializer
from users.permissions import IsAdminMainManagerOrReadOnly
from site_profiles.permissions import IsAdminOrConditionalPermission

class SiteViewSet(ModelViewSet):
    """
    Permissions:
        - **Admins and Main Managers:** Can create, retrieve, update, and delete site data.
        - **Other authenticated users:** Can view site data (GET only).
        - **Anonymous users:** Can view site data (GET only). **This will help to show site profile in homepage**

    """
    serializer_class = SiteSerializer
    permission_classes = [IsAuthenticated, IsAdminMainManagerOrReadOnly]
    queryset = Site.objects.all()
    
    
class SiteCostViewSet(ModelViewSet):
    """
    Permissions (via IsAdminOrConditionalPermission + IsAuthenticated):
        - Admin (is_staff):
            * LIST, RETRIEVE any SiteCost
            * UPDATE or DELETE any SiteCost
            * CREATE any SiteCost
        - Main Manager:
            * LIST, RETRIEVE all SiteCost
            * UPDATE (PUT) only when permission_level == 1
            * DELETE when permission_level == 2
            * No CREATE permission
        - Viewer:
            * LIST and RETRIEVE only (read‑only)
        - Site Manager:
            * LIST and RETRIEVE SiteCost for own site
            * CREATE (POST) new SiteCost for own site
            * PARTIAL UPDATE (PATCH) of permission_level on own site records
    """
    
    permission_classes = [IsAuthenticated,  IsAdminOrConditionalPermission]
    
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