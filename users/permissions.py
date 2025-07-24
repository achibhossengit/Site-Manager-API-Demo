from rest_framework.permissions import BasePermission, SAFE_METHODS

class DenyAll(BasePermission):
    def has_permission(self, request, view):
        return False

    def has_object_permission(self, request, view, obj):
        return False

class IsAdminMainManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        
        # Get user_type safely using getattr
        user_type = getattr(user, 'user_type', None)

        if user.is_staff or user_type == 'main_manager':
            return True
        
        return request.method in SAFE_METHODS


class IsAdminMainManagerOrSiteManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        # Get user_type safely using getattr
        user_type = getattr(user, 'user_type', None)
        return user.is_staff or user_type == 'main_manager' or user_type == 'site_manager'


class PromotionPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.user_type == 'main_manager':
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