from rest_framework.serializers import ModelSerializer
from site_profiles.models import Site, SiteCost

class SiteSerializer(ModelSerializer):
    class Meta:
        model = Site
        fields = '__all__'
        
        
        
class SiteCostSerializer(ModelSerializer):
    class Meta:
        model = SiteCost
        fields = '__all__'
        read_only_fields = ['site', 'permission_level']
        
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['site'] = request.user.current_site
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        instance.permission_level = 0
        return super().update(instance, validated_data)
    
class SiteCostUpdatePermissionSerializer(ModelSerializer):
    class Meta:
        model = SiteCost
        fields = ['permission_level']