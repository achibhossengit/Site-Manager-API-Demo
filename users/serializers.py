from django.shortcuts import get_object_or_404
from django.db import transaction, IntegrityError
from rest_framework import serializers
from users.models import CustomUser, Promotion
from daily_records.models import DailyRecord

class CustomUserIDsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username']

class CustomUserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'

class CustomUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name','username', 'current_site', 'phone', 'address','password', 'designation']
        extra_kwargs = {
            'password': {'write_only': True}
        }
        
    def create(self, validated_data):
        # Remove the password from validated_data to handle it securely
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)  # Encrypt the password
        user.save()
        return user
               
class CustomUserUpdateBioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username','email', 'phone', 'address']

class UpdateCurrentSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['current_site']

class UpdateUserTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['current_site', 'user_type']
        


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = '__all__'
        
        
class PromotionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = ['date', 'current_salary']

    def _get_employee(self):
        view = self.context.get('view')
        if not view:
            raise serializers.ValidationError("Invalid context: view missing.")
        emp_id = view.kwargs.get('user_pk')
        if not emp_id:
            raise serializers.ValidationError("Employee id not provided in URL.")
        employee = get_object_or_404(CustomUser, pk=emp_id)
        return employee

    def validate_date(self, value):
        employee = self._get_employee()

        # chronological constraint with existing promotions
        promos = Promotion.objects.filter(employee=employee).order_by('date')
        if not promos.exists():
            # if has no existing promos first promo date have to be the equal of this labour join_date
            joined = employee.date_joined
            if hasattr(joined, "date"):
                joined_date = joined.date()
            else:
                joined_date = joined
            if value != joined_date:
                raise serializers.ValidationError(f"প্রথম প্রোমোশনের তারিখ অবশ্যই যোগদানের তারিখ ({joined_date}) এর সমান হতে হবে।")
        else:
            last_promo_date = promos.last().date
            if value <= last_promo_date:
                raise serializers.ValidationError(
                    "নতুন প্রোমোশনের তারিখ অবশ্যই পূর্ববর্তী প্রোমোশনের তারিখের পরে হতে হবে।"
                )

            # daily records পরীক্ষা
            dr_qs = DailyRecord.objects.filter(employee=employee).order_by('date')
            if not dr_qs.exists():
                raise serializers.ValidationError(
                    "কর্মীর দৈনিক রেকর্ড খালি আছে — নতুন প্রোমোশন যোগ করা যাবে না।"
                )
                
            first_dr = dr_qs.first().date
            last_dr = dr_qs.last().date
            if not (first_dr <= value <= last_dr):
                raise serializers.ValidationError(
                    f"প্রোমোশনের তারিখ অবশ্যই দৈনিক রেকর্ডের সময়সীমা ({first_dr} - {last_dr}) এর মধ্যে হতে হবে।"
                )
                
        return value

    def create(self, validated_data):
        # Employee ইনজেকশন
        employee = self._get_employee()
        return Promotion.objects.create(employee=employee, **validated_data)