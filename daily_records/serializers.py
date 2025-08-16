from datetime import datetime
from django.utils import timezone
from rest_framework.serializers import ModelSerializer
from daily_records.models import DailyRecord
from rest_framework import serializers
from daily_records.models import WorkSession, SiteWorkRecord
from users.models import CustomUser

class DailyRecordAccessSerializer(ModelSerializer):
    today_salary = serializers.IntegerField(read_only=True)

    class Meta:
        model = DailyRecord
        fields = '__all__'
        read_only_fields = ['employee', 'site', 'date', 'permission_level']
    
    def update(self, instance, validated_data):
        instance.permission_level = 0
        return super().update(instance, validated_data)
    
class DailyRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyRecord
        fields = '__all__'
        read_only_fields = ['site', 'permission_level']

    def _validate_employee_date(self, employee_obj, record_date):
        # Ensure record_date is a date object
        if isinstance(record_date, str):
            record_date = timezone.datetime.strptime(record_date, "%Y-%m-%d").date()
        elif isinstance(record_date, timezone.datetime):
            record_date = record_date.date()

        # 1. date can't be before date_joined
        date_joined_local = timezone.localtime(employee_obj.date_joined).date()
        if record_date < date_joined_local:
            raise serializers.ValidationError(
                f"({employee_obj.username}) এর যোগদানের তারিখ ({date_joined_local}) এর আগে হাজিরা যোগ করা সম্ভব নয়।"
                )
            
        # 2. date can't be equal or before last WorkSession end_date
        last_session = WorkSession.objects.filter(employee=employee_obj).order_by('end_date').last()
        if last_session:
            last_end_date = last_session.end_date
            if isinstance(last_end_date, timezone.datetime):
                last_end_date = last_end_date.date()
            if record_date <= last_end_date:
                raise serializers.ValidationError(
                    f"({employee_obj.username}) এর সর্বশেষ হিসাব দেওয়া হয়েছে ({last_end_date}) তারিখে। একই দিনে দুইবার হাজিরা যোগ করা যাবে না।"
                )

        return record_date

    def validate_date(self, value):
        # Bulk creation
        if isinstance(self.initial_data, list):
            for record in self.initial_data:
                employee_id = record.get('employee')
                record_date = record.get('date')
                if not employee_id or not record_date:
                    continue

                employee_obj = CustomUser.objects.get(pk=employee_id)
                self._validate_employee_date(employee_obj, record_date)

        else:
            # Single creation
            employee_id = self.initial_data.get('employee')
            if employee_id:
                employee_obj = CustomUser.objects.get(pk=employee_id)
                self._validate_employee_date(employee_obj, value)

        return value

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['site'] = request.user.current_site
        return super().create(validated_data)

    
class DailyRecordUpdatePermissionSerializer(ModelSerializer):
    class Meta:
        model = DailyRecord
        fields = ['permission_level']
        


class SiteWorkRecordSerializer(ModelSerializer):
    site = serializers.CharField(source='site.name', read_only=True)

    class Meta:
        model = SiteWorkRecord
        fields = [
            'site',
            'work',
            'total_salary',
            'khoraki_taken',
            'advance_taken',
            'payable'
        ]
        
        read_only_fields = fields
        

class WorkSessionSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source='site.name', read_only=True)
    employee_username = serializers.CharField(source='employee.username', read_only=True)
    site_records = SiteWorkRecordSerializer(source='records', many=True, read_only=True)
    
    class Meta:
        model = WorkSession
        fields = [
            'id',
            'site_name',
            'employee',
            'employee_username',
            'start_date',
            'end_date',
            'update_permission',
            'pay_or_return',
            'last_session_payable',
            'this_session_payable',
            'rest_payable',
            'created_at',
            'updated_at',
            'site_records',
        ]
        
        read_only_fields = fields


class WorkSessionPermissionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkSession
        fields = ['update_permission']

class WorkSessionPayOrReturnFieldUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkSession
        fields = ['pay_or_return']
    
    def save(self, **kwargs):
        instance = super().save(**kwargs)
        instance.update_permission = False
        instance.save(update_fields=['update_permission'])
        return instance