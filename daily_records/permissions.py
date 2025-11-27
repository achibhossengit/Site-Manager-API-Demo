from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission, SAFE_METHODS
from users.models import CustomUser

class DailyRecordPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        
        if user.is_staff:
            return True
            
        user_permissions = {
            'viewer': SAFE_METHODS,
            'employee': SAFE_METHODS,
            'main_manager': ['GET', 'PUT', 'DELETE'],
            'site_manager': SAFE_METHODS + ('POST', 'PATCH')
        }
        
        allowed_methods = user_permissions.get(user.user_type, [])
        return request.method in allowed_methods

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if user.is_staff:
            return True
            
        # Read access for most user types
        if request.method in SAFE_METHODS:
            return user.user_type in ['viewer', 'main_manager', 'site_manager', 'employee']
            
        # Write access based on user type
        if user.user_type == 'main_manager':
            return ((obj.permission_level == 1 and request.method == 'PUT') or
                   (obj.permission_level == 2 and request.method == 'DELETE'))
                   
        elif user.user_type == 'site_manager':
            return (obj.site == user.current_site and 
                   request.method in ['POST', 'PATCH'])
        
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
        
class WorkSessionAccessPermission(BasePermission):
    def has_permission(self, request, view):
        if(request.method not in SAFE_METHODS):
            return False

        user = request.user
        emp_id = view.kwargs.get('user_pk')
        employee = get_object_or_404(CustomUser, id=emp_id)
        
        # Check access levels
        if user.user_type in ['main_manager', 'viewer']:
            return True
        if user.user_type == 'site_manager':
            return user.current_site_id == employee.current_site_id
        if user.user_type == 'employee':
            return user.id == employee.id
        
        return False