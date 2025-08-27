from rest_framework.permissions import BasePermission, SAFE_METHODS

class SiteRecordAccessPermission(BasePermission):
        
    def has_permission(self, request, view):
        user = request.user

        if user.user_type == 'viewer':
            return request.method in SAFE_METHODS
        
        if user.user_type == 'main_manager':
            return request.method in ['GET', 'PUT', 'DELETE']

        if user.user_type == 'site_manager':
            return request.method in ['GET', 'POST', 'PATCH']
        return False
        
    # has_object_permission for update, delete, detail
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if user.user_type == 'main_manager':
            if obj.permission_level == 1:
                return request.method in ['GET', 'PUT']
            if obj.permission_level == 2:
                return request.method in ['GET', 'DELETE']

        if user.user_type == 'site_manager':
            return obj.site == user.current_site and request.method in ['GET', 'POST', 'PATCH']
            
        return request.method in SAFE_METHODS
        
    
class SiteBillAccessPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.user_type == 'main_manager':
            return True
                
        if user.user_type == 'viewer':
            return request.method in SAFE_METHODS

        return False
    
    
class SiteProfileAccessPermissions(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.user_type == 'main_manager':
            return True
        return request.method in SAFE_METHODS
    
class GetSiteTotalByDateViewPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.user_type in ['main_manager', 'site_manager', 'viewer']
