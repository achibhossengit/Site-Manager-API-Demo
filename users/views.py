from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from users.models import CustomUser, Promotion
from daily_records.models import WorkSession
from users.serializers import PromotionSerializer, PromotionCreateSerializer,PromotionUpdateSerializer, CustomUserGetSerializer, CustomUserCreateSerializer, CustomUserIDsSerializer, CustomUserUpdateBioSerializer, UpdateUserTypeSerializer, UpdateCurrentSiteSerializer
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
    
    @action(detail=False, methods=['get'], url_path='ids')
    def ids(self, request):
        # get base queryset according to user's permissions
        base_qs = self.get_queryset()
        # apply DRF filter backends (so filterset_fields works)
        filtered_qs = self.filter_queryset(base_qs)
        serializer = CustomUserIDsSerializer(filtered_qs, many=True)
        return Response(serializer.data)
    
    
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response({'detail': 'Both old and new passwords are required.'}, status=400)

        if not user.check_password(old_password):
            return Response({'detail': 'Old password is incorrect.'}, status=400)

        user.set_password(new_password)
        user.save()

        return Response({'detail': 'Password changed successfully.'})
    
    
class ResetPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'User with this email does not exist.'}, status=404)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        front_end_domain = settings.FRONTEND_URL
        reset_link = f"{front_end_domain}/reset-password/{uid}/{token}/"

        send_mail(
            subject="Reset your password",
            message=f"Click this link to reset your password:\n{reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response({'detail': 'Password reset link sent to your email.'}, status=200)


class ResetPasswordConfirmView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response({'detail': 'Invalid user.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

        new_password = request.data.get('password')
        if not new_password:
            return Response({'detail': 'Password is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'detail': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)

    
class PromotionViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, PromotionPermission]
    
    def get_queryset(self):
        user = self.request.user
        emp_id = self.kwargs.get('user_pk')

        queryset = Promotion.objects.filter(employee_id=emp_id).order_by('-date')

        if user.user_type in ['main_manager', 'viewer']:
            return queryset

        elif user.user_type == 'site_manager':
            return queryset.filter(employee__current_site=user.current_site)

        elif user.user_type == 'employee':
            return queryset.filter(employee=user)

        return Promotion.objects.none()

    def get_serializer_class(self):
        if(self.request.method == 'POST'):
            return PromotionCreateSerializer
        elif(self.request.method == 'PUT'):
            return PromotionUpdateSerializer
        return PromotionSerializer
    
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        employee = instance.employee

        # Get promotions for this employee ordered by date (ascending)
        promos = list(Promotion.objects.filter(employee=employee).order_by('date'))

        # 1) First promotion cannot be deleted
        if promos and instance == promos[0]:
            raise ValidationError({"detail": "প্রথম পদোন্নতি মুছে ফেলা যাবে না।"})

        # 2) If there are work sessions and the last session's end_date
        #    is >= this promotion date, prevent deletion.
        work_sessions = list(WorkSession.objects.filter(employee=employee).order_by('end_date'))
        if work_sessions and instance.date <= work_sessions[-1].end_date:
            raise ValidationError({
                "detail": "এই প্রোমোশনের পরে/সময়ে কাজের সেশন তৈরি হয়েছে — মুছে ফেলা যাবে না।"
            })

        # otherwise proceed with normal destroy
        return super().destroy(request, *args, **kwargs)