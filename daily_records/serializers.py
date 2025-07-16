from rest_framework.serializers import ModelSerializer
from daily_records.models import DailyRecord
from rest_framework import serializers

class DailyRecordAccessSerializer(ModelSerializer):
    today_salary = serializers.IntegerField(read_only=True)

    class Meta:
        model = DailyRecord
        fields = '__all__'
        read_only_fields = ['employee', 'site', 'date', 'permission_level']
    
    def update(self, instance, validated_data):
        instance.permission_level = 0
        return super().update(instance, validated_data)
    
class DailyRecordCreateSerializer(ModelSerializer):
    class Meta:
        model = DailyRecord
        fields = '__all__'
        read_only_fields = ['site', 'permission_level']
        
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['site'] = request.user.current_site
        return super().create(validated_data)
    
class DailyRecordUpdatePermissionSerializer(ModelSerializer):
    class Meta:
        model = DailyRecord
        fields = ['permission_level']