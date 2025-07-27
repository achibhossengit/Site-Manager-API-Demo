from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import CustomUser, Promotion
from users.serializers import PromotionSerializer, CustomUserGetSerializer, CustomUserCreateSerializer, CustomUserUpdateBioSerializer, UpdateUserTypeSerializer, UpdateCurrentSiteSerializer
from users.permissions import PromotionPermission, CustomUserPermission

class CustomUserViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, CustomUserPermission]
    filterset_fields = ['current_site', 'designation']    

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return CustomUser.objects.all()
        elif user.user_type in ['viewer', 'main_manager']:
            return CustomUser.objects.filter(is_staff = False)
        elif user.user_type == 'site_manager':
            if(user.current_site is None):
                return CustomUser.objects.none()
            return CustomUser.objects.filter(is_staff = False, current_site = user.current_site)

        elif user.user_type == 'employee':
            return CustomUser.objects.filter(id = user.id)
        
        return CustomUser.objects.none()
        
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CustomUserCreateSerializer
        elif self.request.method == 'PUT':
            return CustomUserUpdateBioSerializer
        elif self.request.method == 'PATCH':
            if self.request.user.user_type == 'viewer':
                return UpdateUserTypeSerializer
            return UpdateCurrentSiteSerializer
        # for get, head etc
        return CustomUserGetSerializer
    
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        serializer = CustomUserGetSerializer(request.user)
        return Response(serializer.data)
    
class PromotionViewSet(ModelViewSet):
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticated, PromotionPermission]
    
    def get_queryset(self):
        user = self.request.user
        emp_id = self.kwargs.get('user_pk')

        queryset = Promotion.objects.filter(employee_id=emp_id)

        if user.user_type in ['main_manager', 'viewer']:
            return queryset

        elif user.user_type == 'site_manager':
            return queryset.filter(employee__current_site=user.current_site)

        elif user.user_type == 'employee':
            return queryset.filter(employee=user)

        return Promotion.objects.none()
    