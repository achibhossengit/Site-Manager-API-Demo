from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from site_profiles.models import Site
from site_profiles.serializers import SiteSerializer
from users.permissions import IsAdminMainManagerOrReadOnly

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