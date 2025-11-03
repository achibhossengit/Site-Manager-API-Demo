from rest_framework.permissions import BasePermission, SAFE_METHODS


class CustomUserPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['POST']:
            return request.user.user_type in ['main_manager', 'site_manager']
        return True
    
    def has_object_permission(self, request, view, obj):
        if request.method in ['PUT']:
            return request.user.user_type in ['main_manager', 'site_manager']
        elif request.method == 'PATCH':
            return request.user.user_type in ['viewer', 'main_manager', 'site_manager']
        # elif request.method == 'DELETE':
        #     return request.user.user_type == 'main_manager'
        
        return request.method in SAFE_METHODS



class PromotionPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.user_type == 'site_manager':
            return True
        return request.method in SAFE_METHODS
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.user_type in ['main_manager', 'viewer']:
            return True
        elif user.user_type == 'site_manager':
            return obj.employee.current_site == user.current_site
        elif user.user_type == 'employee':
            return obj.employee == user

        return False