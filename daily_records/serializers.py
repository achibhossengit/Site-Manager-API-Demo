from rest_framework.serializers import ModelSerializer
from daily_records.models import DailyRecord
from rest_framework import serializers
from daily_records.models import WorkSession, SiteWorkRecord

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
        


class SiteWorkRecordSerializer(ModelSerializer):
    site_name = serializers.CharField(source='site.name', read_only=True)

    class Meta:
        model = SiteWorkRecord
        fields = [
            'site',
            'site_name',
            'work',
            'total_salary',
            'khoraki_taken',
            'advance_taken',
            'payable'
        ]
        
        read_only_fields = fields
        

class WorkSessionSerializer(serializers.ModelSerializer):
    employee_username = serializers.CharField(source='employee.username', read_only=True)
    site_records = SiteWorkRecordSerializer(source='records', many=True, read_only=True)
    
    class Meta:
        model = WorkSession
        fields = [
            'id',
            'site',
            'employee',
            'employee_username',
            'start_date',
            'end_date',
            'is_paid',
            'update_permission',
            'pay',
            'last_session_payable',
            'payable',
            'rest',
            'created_at',
            'updated_at',
            'site_records',
        ]
        
        read_only_fields = fields


class WorkSessionPermissionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkSession
        fields = ['update_permission']

class WorkSessionIsPaidUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkSession
        fields = ['is_paid']
    
    def save(self, **kwargs):
        instance = super().save(**kwargs)
        instance.update_permission = False
        instance.save(update_fields=['update_permission'])
        return instance