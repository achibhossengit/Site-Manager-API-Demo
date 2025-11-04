from rest_framework.serializers import ModelSerializer
from daily_records.models import DailyRecord, DailyRecordSnapshot
from rest_framework import serializers
from daily_records.models import WorkSession, SiteWorkRecord
from api.validators import to_date, validate_today_or_yesterday

class DailyRecordAccessSerializer(ModelSerializer):
    # today_salary = serializers.IntegerField(read_only=True)

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
        
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['site'] = request.user.current_site
        return super().create(validated_data)
    

    def _date_validations(self, employee_obj, record_date):
        # ensure convertible to date and catch parse errors
        try:
            record_date = to_date(record_date)
        except (ValueError, TypeError):
            raise serializers.ValidationError({ "date": "তারিখের ফরম্যাট সঠিক নয় — YYYY-MM-DD ফরম্যাট ব্যবহার করুন।"})

        # 1. date can't be before date_joined
        try:
            date_joined_local = to_date(employee_obj.date_joined)
        except AttributeError:
            raise serializers.ValidationError(
                f"{employee_obj.first_name} -এর যোগদানের তারিখ পাওয়া যায়নি — কর্মচারীর প্রোফাইল আপডেট করুন।")
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                f"({getattr(employee_obj, 'first_name', 'কর্মচারী')})-এর যোগদানের তারিখের ফরম্যাট ভুল আছে।"
            )
        if record_date < date_joined_local:
            raise serializers.ValidationError({"employee":
                f"({employee_obj.first_name}) এর যোগদানের তারিখ ({date_joined_local}) এর আগে হাজিরা যোগ করা সম্ভব নয়।"
                })

        # 2. Check today or yesterday
        if not validate_today_or_yesterday(record_date):
            raise serializers.ValidationError({"date": "শুধু আজ বা গতকালের তারিখই অনুমোদিত।"})

        # 3. date can't be equal or before last WorkSession end_date
        last_session = WorkSession.objects.filter(employee=employee_obj).order_by('end_date').last()
        if last_session:
            try:
                last_end_date = to_date(last_session.end_date)
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    "date": f"{employee_obj.first_name} -এর পূর্বের সেশন এর তারিখে সমস্যা আছে। অনুগ্রহ করে সিস্টেম অ্যাডমিনিস্ট্রেটরের সাথে যোগাযোগ করুন।"})

            if record_date <= last_end_date:
                raise serializers.ValidationError({
                    "date": f"({employee_obj.first_name}) এর সর্বশেষ হিসাব দেওয়া হয়েছে ({last_end_date}) তারিখে। একই দিনে দুইবার হাজিরা যোগ করা যাবে না।"})

        return record_date
       
    def _employee_validation(self, employee_obj, request_user):
        if request_user.current_site.id != employee_obj.current_site.id:
            raise serializers.ValidationError({
                "employee": f"{employee_obj.first_name} আপনার সাইটের অন্তর্ভুক্ত নয়।"
            })
        if employee_obj.is_active == False:
            raise serializers.ValidationError({
                "employee": f"{employee_obj.first_name} একজন inactive ইউজার।"
            })
        return employee_obj

    def validate(self, attrs):
        request_user = self.context.get("request").user
        employee_obj = attrs['employee']
        
        attrs['employee'] = self._employee_validation(employee_obj, request_user)
        attrs['date'] = self._date_validations(employee_obj, attrs['date'])
        return attrs
    

    
class DailyRecordUpdatePermissionSerializer(ModelSerializer):
    class Meta:
        model = DailyRecord
        fields = ['permission_level']
        

class SiteWorkRecordSerializer(ModelSerializer):
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
    site_records = SiteWorkRecordSerializer(source='records', many=True, read_only=True)
    
    class Meta:
        model = WorkSession
        fields = [
            'id',
            'site',
            'employee',
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
    
    
class DailyRecordSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyRecordSnapshot
        fields = '__all__'