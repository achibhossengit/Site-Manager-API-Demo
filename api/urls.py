from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import EmployeeViewSet
from site_profiles.views import SiteViewSet, SiteCostViewSet, SiteCashViewSet, SiteBillViewSet
from daily_records.views import DailyRecordViewSet

router = DefaultRouter()
router.register('employees', EmployeeViewSet, basename='employees')
router.register('sites', SiteViewSet, basename='sites')
router.register('site-costs', SiteCostViewSet, basename='site-costs')
router.register('site-cashes', SiteCashViewSet, basename='site-cashes')
router.register('site-bills', SiteBillViewSet, basename='site-bills')
router.register('daily-records', DailyRecordViewSet, basename='daily-records')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('', include(router.urls)),
]