from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from users.views import CustomUserViewSet, PromotionViewSet, ChangePasswordView, ResetPasswordView, ResetPasswordConfirmView
from site_profiles.views import SiteViewSet, SiteCostViewSet, SiteCashViewSet, SiteBillViewSet, SiteInfoView, GetSiteTotalByDateView
from daily_records.views import DailyRecordViewSet, WorkSessionViewSet, CurrentWorkSession

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('sites', SiteViewSet, basename='sites')
router.register('sites-info', SiteInfoView, basename='sites-info')
router.register('site-costs', SiteCostViewSet, basename='site-costs')
router.register('site-cashes', SiteCashViewSet, basename='site-cashes')
router.register('site-bills', SiteBillViewSet, basename='site-bills')
router.register('daily-records', DailyRecordViewSet, basename='daily-records')
router.register('work-sessions', WorkSessionViewSet, basename='work-sessions')

employee_router = NestedDefaultRouter(router, 'users', lookup='user')
employee_router.register('promotions', PromotionViewSet, basename='employee-promotions')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(employee_router.urls)),
    path('current-worksession/<int:emp_id>/', CurrentWorkSession.as_view(), name='current-work-session'),
    path('site-total/<int:site_id>/', GetSiteTotalByDateView.as_view(), name='site-total'),


    path('token/create/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('reset-password-confirm/<uidb64>/<token>/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'
    ),
]