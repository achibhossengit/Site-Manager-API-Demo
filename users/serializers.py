from django.shortcuts import get_object_or_404
from rest_framework import serializers
from users.models import CustomUser, Promotion
from daily_records.models import WorkSession, DailyRecord
from django.utils.timezone import localtime

class CustomUserIDsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'last_session_end_date']

class CustomUserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'current_site', 'designation']

class CustomUserGetDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'

class CustomUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name','username', 'current_site', 'address','password', 'designation']
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
        fields = ['first_name', 'last_name', 'username','email', 'address', 'designation']

class UpdateCurrentSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['current_site']
 
    def validate(self, attrs):
        user = self.instance
        if user.user_type == 'site_manager':
            raise serializers.ValidationError({
                'current_site': f'{user.first_name} একজন সাইট ম্যানেজার, তাই তার বর্তমান সাইট পরিবর্তন করা যাবে না।'
            })
        return super().validate(attrs)
    
    def update(self, instance, validated_data):
        # if not found any updated current_site set existing one to avoid error
        new_current_site = validated_data.get('current_site', instance.current_site)
        instance.current_site = new_current_site
        instance.save()
        return instance

class UpdateUserTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['user_type']

    # check which field gona change
    def update(self, instance, validated_data):
        new_user_type = validated_data.get('user_type', instance.user_type)

        if new_user_type == 'site_manager' and instance.current_site:
            site = instance.current_site

            # if already has a site manager for this site. so, firstly make him employee to avoid two site sitemanager for same site issue
            existing_manager = CustomUser.objects.filter(
                current_site=site, user_type='site_manager'
            ).exclude(id=instance.id).first()

            if existing_manager:
                existing_manager.user_type = 'employee'
                existing_manager.save()

        # Now set newuser user_type
        instance.user_type = new_user_type
        instance.save()
        return instance

class UserActivationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['is_active']
        
        
    def validate(self, attrs):
        user = self.instance
        has_daily_records = DailyRecord.objects.filter(employee = user).exists()

        if user.user_type in ['main_manager', 'site_manager', 'viewer']:
            raise serializers.ValidationError({
                'current_site': f'{user.first_name} একজন ম্যানেজার/ঠিকাদার, তাই তার অ্যাক্টিভ স্ট্যাটাস পরিবর্তন করা যাবে না।'
            })
        if has_daily_records:
            raise serializers.ValidationError({
                'current_site': f'{user.first_name} এর চলমান হিসাব পাওয়া গেছে, তাই তার অ্যাক্টিভ স্ট্যাটাস পরিবর্তন করা যাবে না।'
            })
        return super().validate(attrs)
    
    def update(self, instance, validated_data):
        # if not found any updated "is_active" set existing one to avoid error
        new_active_status = validated_data.get('is_active', instance.is_active)
        instance.is_active = new_active_status
        instance.save()
        return instance
    

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