from rest_framework.permissions import BasePermission, SAFE_METHODS

class DenyAll(BasePermission):
    def has_permission(self, request, view):
        return False

    def has_object_permission(self, request, view, obj):
        return False

class IsAdminOrMainManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        # Get user_type safely using getattr
        user_type = getattr(user, 'user_type', None)
        return user.is_staff or user_type == 'main_manager'

class IsAdminMainManagerOrSiteManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        # Get user_type safely using getattr
        user_type = getattr(user, 'user_type', None)
        return user.is_staff or user_type == 'main_manager' or user_type == 'site_manager'

