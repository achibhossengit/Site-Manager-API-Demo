from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from site_profiles.models import Site, SiteCost, SiteCash, SiteBill

class SiteSerializer(ModelSerializer):
    class Meta:
        model = Site
        fields = '__all__'
        
class SiteSerializerForViewer(ModelSerializer):
    total_site_bill = serializers.IntegerField(read_only=True)
    total_site_cost = serializers.IntegerField(read_only=True)
    total_rose_taken = serializers.FloatField(read_only=True)
    actual_employee_cost = serializers.IntegerField(read_only=True)
    profit = serializers.IntegerField(read_only=True)
    total_site_cash = serializers.IntegerField(read_only=True)
    taken_employee_cost = serializers.IntegerField(read_only=True)
    site_balance = serializers.IntegerField(read_only=True)

    class Meta:
        model = Site
        fields = '__all__'
        
class SiteSerializerForManager(ModelSerializer):
    total_site_cost = serializers.IntegerField(read_only=True)
    total_site_cash = serializers.IntegerField(read_only=True)
    taken_employee_cost = serializers.IntegerField(read_only=True)
    site_balance = serializers.IntegerField(read_only=True)

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
        
        
        
# serializers for SiteCash model
class SiteCashSerializer(ModelSerializer):
    class Meta:
        model = SiteCash
        fields = '__all__'
        read_only_fields = ['site', 'permission_level']
        
    def create(self, validated_data):
        request = self.context.get('request')
        if not hasattr(request.user, 'current_site'):
            raise serializers.ValidationError("User has no current_site assigned.")
        validated_data['site'] = request.user.current_site
        return super().create(validated_data)
    
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
        fields = '__all__'