from rest_framework.permissions import BasePermission, SAFE_METHODS
from users.models import CustomUser

class IsAdminOrConditionalPermissionForDailyRecord(BasePermission):
    """
    Permissions:
        - Admin (is_staff):
            * LIST, RETRIEVE any SiteCost
            * UPDATE or DELETE any SiteCost
            * CREATE any SiteCost
        - Main Manager:
            * LIST, RETRIEVE all SiteCost
            * UPDATE (PUT) only when permission_level == 1
            * DELETE when permission_level == 2
            * No CREATE permission
        - Viewer:
            * LIST and RETRIEVE only (read‑only)
        - Employee: 
            * LIST and RETRIEVE only (read‑only) his own data. 
        - Site Manager:
            * LIST and RETRIEVE SiteCost for own site
            * CREATE (POST) new SiteCost for own site
            * PARTIAL UPDATE (PATCH) of permission_level on own site records
    """
    # has_permission for list and create. Allow to check object level permission.
    def has_permission(self, request, view):
        user = request.user
        if user.is_staff:
            return True

        if user.user_type in ['viewer', 'employee']:
            return request.method in SAFE_METHODS
        
        if user.user_type == 'main_manager':
            return request.method in ['GET', 'PUT', 'DELETE']

        if user.user_type == 'site_manager':
            return request.method in ['GET', 'POST', 'PATCH']
        
        return False
        
    # has_object_permission for update, delete
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff:
            return True

        if user.user_type == 'viewer':
            return request.method in SAFE_METHODS
            
        if user.user_type == 'main_manager':
            if obj.permission_level == 1:
                return request.method in ['GET', 'PUT']
            if obj.permission_level == 2:
                return request.method in ['GET', 'DELETE']

        if user.user_type == 'site_manager':
            return obj.site == user.current_site and request.method in ['GET', 'POST', 'PATCH']

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