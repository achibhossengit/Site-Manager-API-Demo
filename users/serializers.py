from django.shortcuts import get_object_or_404
from django.db import transaction, IntegrityError
from rest_framework import serializers
from users.models import CustomUser, Promotion
from daily_records.models import DailyRecord, WorkSession
from django.utils.timezone import localtime

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
        fields = ['id', 'first_name', 'last_name','username', 'current_site', 'phone', 'address','password', 'designation']
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
        fields = ['id', 'date', 'current_salary']

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

        promos = Promotion.objects.filter(employee=employee).order_by('date')
        if not promos.exists():
            # if has no existing promos
            joined = employee.date_joined
            if hasattr(joined, "date"):
                joined_date = localtime(joined).date()
            else:
                joined_date = joined
            if value != joined_date:
                raise serializers.ValidationError(f"প্রথম প্রোমোশনের তারিখ অবশ্যই যোগদানের তারিখ ({joined_date}) এর সমান হতে হবে।")
        else:
            last_promo_date = promos.last().date
            last_session = WorkSession.objects.filter(employee=employee).order_by('end_date').last()
            check_date = max(last_promo_date, last_session.end_date) if last_session else last_promo_date
            if value <= check_date:
                raise serializers.ValidationError(
                    f"নতুন প্রোমোশনের তারিখ অবশ্যই ({check_date}) এর পরে হতে হবে।"
                )
    
        return value

    def create(self, validated_data):
        # Employee ইনজেকশন
        employee = self._get_employee()
        return Promotion.objects.create(employee=employee, **validated_data)
    

class PromotionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = ['id', 'date', 'current_salary']

    def _get_employee(self):
        view = self.context.get('view')
        if not view:
            raise serializers.ValidationError("Invalid context: view missing.")
        emp_id = view.kwargs.get('user_pk')
        if not emp_id:
            raise serializers.ValidationError("Employee id not provided in URL.")
        return get_object_or_404(CustomUser, pk=emp_id)
    
    def validate(self, attrs):  # ✅ Fixed: Now properly indented inside the class
        if not hasattr(self, 'instance') or self.instance is None:
            raise serializers.ValidationError("আপডেট করার জন্য একটি বিদ্যমান রেকর্ড প্রয়োজন।")

        # Get employee
        employee = self._get_employee()

        # Step 1: If entry is restricted
        work_sessions = list(WorkSession.objects.filter(employee=employee).order_by('end_date'))
        if work_sessions and self.instance.date <= work_sessions[-1].end_date:
            raise serializers.ValidationError(
                "এই পদোন্নতি entry তে ইতিমধ্যেই কাজের সেশন রয়েছে — কোনো field update করা যাবে না।"
            )

        # Step 2: If entry is not restricted, proceed with date validation (if date is being changed)
        new_date = attrs.get('date')
        if new_date and new_date != self.instance.date:        
            promos = list(Promotion.objects.filter(employee=employee).order_by('date'))
            
            # Case 1: First promotion → date cannot be changed
            if self.instance == promos[0]:
                raise serializers.ValidationError({"date": "প্রথম পদোন্নতির তারিখ পরিবর্তন করা যাবে না।"})

            # Case 2: Last promotion
            elif self.instance == promos[-1]:
                check_date = max(work_sessions[-1].end_date, promos[-2].date) if work_sessions else promos[-2].date
                if new_date <= check_date:
                    raise serializers.ValidationError(
                        {"date": f"নতুন তারিখ অবশ্যই ({check_date}) এর পরে হতে হবে।"}
                    )

            # Case 3: Middle promotion → must be between previous and next promotion dates
            else:
                index = promos.index(self.instance)
                check_date = max(work_sessions[-1].end_date, promos[index - 1].date) if work_sessions else promos[-1].date
                if not (check_date < new_date < promos[index + 1].date):
                    raise serializers.ValidationError(
                        {"date": f"নতুন তারিখ অবশ্যই ({check_date} এবং {promos[index + 1].date}) এর মধ্যে হতে হবে।"}
                    )

        return attrs