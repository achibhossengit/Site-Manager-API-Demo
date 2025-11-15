from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from site_profiles.models import Site, SiteCost, SiteCash, SiteBill
from api.validators import validate_today_or_yesterday

class SiteSerializerList(ModelSerializer):
    class Meta:
        model = Site
        fields = ['id', 'name', 'handover']

class SiteSerializerDetails(ModelSerializer):
    site_manager = serializers.SerializerMethodField()
    class Meta:
        model = Site
        fields = '__all__'
        
    def get_site_manager(self, obj):
        result = obj.employees.filter(user_type='site_manager').first()
        if result:
            return {
                "id": result.id,
                "first_name": result.first_name,
                "last_name" : result.last_name
            }
        return None        
    
# serializers for SiteCost model
class SiteCostSerializer(ModelSerializer):
    class Meta:
        model = SiteCost
        fields = '__all__'
        read_only_fields = ['site', 'permission_level']
        
    def validate_date(self, value):
        if not validate_today_or_yesterday(value):
            raise serializers.ValidationError({"date": "শুধু আজ বা গতকালের তারিখই অনুমোদিত।"})
        return value
    
    def update(self, instance, validated_data):
        instance.permission_level = 0
        return super().update(instance, validated_data)
    
class SiteCostUpdatePermissionSerializer(ModelSerializer):
    class Meta:
        model = SiteCost
        fields = ['permission_level']
        
        
        
# serializers for SiteCash model
class SiteCashSerializer(ModelSerializer):
    class Meta:
        model = SiteCash
        fields = '__all__'
        read_only_fields = ['site', 'permission_level']

    def validate_date(self, value):
        if not validate_today_or_yesterday(value):
            raise serializers.ValidationError({"date": "শুধু আজ বা গতকালের তারিখই অনুমোদিত।"})
        return value
    
    def update(self, instance, validated_data):
        instance.permission_level = 0
        return super().update(instance, validated_data)
    
class SiteCashUpdatePermissionSerializer(ModelSerializer):
    class Meta:
        model = SiteCash
        fields = ['permission_level']
        

# site Bills serializer
class SiteBillSerializer(ModelSerializer):
    class Meta:
        model = SiteBill
        exclude = ['site']