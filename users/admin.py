from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import CustomUser, Promotion

# Register Promotion model
@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'date', 'employee', 'current_salary']
    list_filter = ['created_at', 'employee']

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Custom User Admin with additional fields and password encryption"""
    
    model = CustomUser
    
    # Display custom fields in list view
    list_display = ['username', 'first_name', 'last_name', 'current_site', 'user_type', 'is_staff']
    list_filter = ['current_site', 'user_type', 'is_staff', 'is_active']
    
    # Add custom fields to user change form
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('current_site', 'address', 'user_type')}),
    )
    
    # Add custom fields to user creation form
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('current_site', 'address', 'user_type',)}),
    )
    
    # Ensure password is properly encrypted
    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data or not change:
            raw_password = form.cleaned_data.get('password')
            if raw_password:
                obj.set_password(raw_password)
        super().save_model(request, obj, form, change)
