from rest_framework.permissions import BasePermission, SAFE_METHODS
from users.models import CustomUser

class DailyRecordPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.is_staff:
            return True
        if user.user_type in ['viewer', 'employee']:
            return request.method in SAFE_METHODS
        if user.user_type == 'main_manager':
            return request.method in ['GET', 'PUT', 'DELETE']
        if user.user_type == 'site_manager':
            return request.method in SAFE_METHODS or request.method in ['POST', 'PATCH']
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff:
            return True
        if user.user_type == 'viewer':
            return request.method in SAFE_METHODS
        if user.user_type == 'main_manager':
            if request.method in SAFE_METHODS:
                return True
            if obj.permission_level == 1 and request.method == 'PUT':
                return True
            if obj.permission_level == 2 and request.method == 'DELETE':
                return True
        if user.user_type == 'site_manager':
            if request.method in SAFE_METHODS:
                return True
            if obj.site == user.current_site and request.method in ['POST', 'PATCH']:
                return True
        if user.user_type == 'employee':
            return obj.employee == user and request.method in SAFE_METHODS
        return False
    
        
class CurrentWorkSessionPermission(BasePermission):
    """
    - GET: 
        main_manager/viewer → any employee
        site_manager        → only same-site employee
        employee            → only own session
    - POST:
        site_manager        → only same-site employee
    """

    def has_permission(self, request, view):
        user = request.user
        emp_id = view.kwargs.get('emp_id')
        
        try:
            employee = CustomUser.objects.get(id=emp_id)
        except CustomUser.DoesNotExist:
            return False
        
        # GET logic
        if request.method == 'GET':
            if user.user_type in ['main_manager', 'viewer']:
                return True

            elif user.user_type == 'site_manager':
                return user.current_site == employee.current_site

            elif user.user_type == 'employee':
                return user.id == employee.id

            return False

        # POST logic
        elif request.method == 'POST':
            return (request.user.user_type == 'site_manager' and request.user.current_site == employee.current_site)

        return False


class IsManagerUpdateOrConditionalReadonly(BasePermission):
    def has_permission(self, request, view):
        return True
    
    def has_object_permission(self, request, view, obj):
        if request.user.user_type == 'viewer':
            return request.method in SAFE_METHODS
        elif request.user.user_type == 'main_manager':
            # main manager can update pay_or_return field based on update permission
            return obj.update_permission == True or request.method in SAFE_METHODS
        elif request.user.user_type == 'site_manager':
            # only created site manager can update only update permission filed this field
            return request.user.current_site == obj.site
        elif request.user.user_type == 'employee':
            return request.method in SAFE_METHODS and request.user == obj.employee
        else: return False