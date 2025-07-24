from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from users.models import CustomUser, Promotion
from users.serializers import CustomUserSerializer, CustomUserSerializerForMainManager, CustomUserSerializerForViewer, CustomUserSerializerForSiteManager, PromotionSerializer
from users.permissions import IsAdminMainManagerOrReadOnly, PromotionPermission

class EmployeeViewSet(ModelViewSet):
    """
    Overview:
        - This API handles user management based on their roles and permissions.
        - All users can have daily records (handled elsewhere), so this viewset focuses on user management.
        - Employees do not have direct access to this viewset and should use the 'auth/users/me' endpoint for their profile.

    Permissions:
        - **Admins (is_staff):** Can list, retrieve, update (all fields), and delete any user.
        - **Main Managers:** Can list, retrieve, update permitted fields, and delete users except viewers.
        - **Viewers:** Can list users and partially update the `user_type` field only.
        - **Site Managers:** Can list users assigned to their current site.
        - **Employees:** No direct access.
        
    """
    permission_classes = [IsAuthenticated, IsAdminMainManagerOrReadOnly]
    filterset_fields = ['current_site', 'designation']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return CustomUser.objects.all()

        if self.request.user.user_type in ['viewer', 'main_manager']:
            return CustomUser.objects.filter(is_staff = False)
        
        if self.request.user.user_type == 'site_manager':
            if(self.request.user.current_site is None):
                return None
            return CustomUser.objects.filter(is_staff = False, current_site = self.request.user.current_site)
        
        # employee can access their won profile djoser endpoint ('auth/users/me')
        return CustomUser.objects.none()
        
    def get_serializer_class(self):
        if self.request.user.is_staff:
            return CustomUserSerializer
        
        if self.request.user.user_type == 'viewer':
            return CustomUserSerializerForViewer

        if self.request.user.user_type == 'main_manager':
            return CustomUserSerializerForMainManager
        
        return CustomUserSerializerForSiteManager
                
    def partial_update(self, request, *args, **kwargs):
        if not (self.request.user.is_staff or self.request.user.user_type == 'viewer'):
            raise PermissionDenied("Only Admins and viewers are allowed to update user_type.")

        # Check if the user is attempting to update `user_type`
        if 'user_type' not in request.data:
            return Response(
                {"detail": "Only `user_type` field can be updated."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Restrict other fields from being updated
        if len(request.data) > 1:
            return Response(
                {"detail": "You can only update the `user_type` field."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Perform the update
        return super().partial_update(request, *args, **kwargs)
    
    
    
class PromotionViewSet(ModelViewSet):
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticated, PromotionPermission]
    
    def get_queryset(self):
        user = self.request.user
        emp_id = self.kwargs.get('employee_pk')

        queryset = Promotion.objects.filter(employee_id=emp_id)

        if user.user_type in ['main_manager', 'viewer']:
            return queryset

        elif user.user_type == 'site_manager':
            return queryset.filter(employee__current_site=user.current_site)

        elif user.user_type == 'employee':
            return queryset.filter(employee=user)

        return Promotion.objects.none()
    