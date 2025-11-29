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
    def has_permission(self, request, view):
        user = request.user
        emp_id = view.kwargs.get('emp_id')
        employee = get_object_or_404(CustomUser, id=emp_id)
        
        # Role based access
        if user.user_type in ['main_manager', 'viewer']:
            return request.method in SAFE_METHODS
        elif user.user_type == 'site_manager':
            return user.current_site_id == employee.current_site_id
        elif user.user_type == 'employee':
            return request.method in SAFE_METHODS and user.id == employee.id
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