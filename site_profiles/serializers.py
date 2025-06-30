from rest_framework.serializers import ModelSerializer
from site_profiles.models import Site

class SiteSerializer(ModelSerializer):
    class Meta:
        model = Site
        fields = '__all__'