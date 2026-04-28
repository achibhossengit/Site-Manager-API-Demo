from django.urls import path, include
from debug_toolbar.toolbar import debug_toolbar_urls
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from users.views import CustomUserViewSet, PromotionViewSet, ChangePasswordView, ResetPasswordView, ResetPasswordConfirmView
from site_profiles.views import SiteViewSet, SiteCostViewSet, SiteCashViewSet, SiteBillViewSet, DateBasedSiteSummaryView, TotalSiteSummaryView
from daily_records.views import DailyRecordViewSet, WorkSessionViewSet, CurrentWorkSession, DailyRecordSnapshotViewset

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('sites', SiteViewSet, basename='sites')
router.register('daily-records', DailyRecordViewSet, basename='daily-records')
router.register('daily-records-snapshot', DailyRecordSnapshotViewset, basename='daily-records-snapshot')

employee_router = NestedDefaultRouter(router, 'users', lookup='user')
employee_router.register('promotions', PromotionViewSet, basename='employee-promotions')
employee_router.register('work-sessions', WorkSessionViewSet, basename='work-sessions')


site_router = NestedDefaultRouter(router, 'sites', lookup='site')
site_router.register('cost-records', SiteCostViewSet, basename='cost-records')
site_router.register('cash-records', SiteCashViewSet, basename='cash-records')
site_router.register('bill-records', SiteBillViewSet, basename='bill-records')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(employee_router.urls)),
    path('', include(site_router.urls)),
    path('current-worksession/<int:emp_id>/', CurrentWorkSession.as_view(), name='current-work-session'),

    path('site-summary/<int:site_id>/<str:date>/', DateBasedSiteSummaryView.as_view()),
    path('total-site-summary/<int:site_id>/', TotalSiteSummaryView.as_view()),


    path('token/create/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('reset-password-confirm/<uidb64>/<token>/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'
    ),
] + debug_toolbar_urls()