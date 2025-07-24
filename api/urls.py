from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from users.views import EmployeeViewSet, PromotionViewSet
from site_profiles.views import SiteViewSet, SiteCostViewSet, SiteCashViewSet, SiteBillViewSet
from daily_records.views import DailyRecordViewSet, WorkSessionViewSet, CurrentWorkSession

router = DefaultRouter()
router.register('employees', EmployeeViewSet, basename='employees')
router.register('sites', SiteViewSet, basename='sites')
router.register('site-costs', SiteCostViewSet, basename='site-costs')
router.register('site-cashes', SiteCashViewSet, basename='site-cashes')
router.register('site-bills', SiteBillViewSet, basename='site-bills')
router.register('daily-records', DailyRecordViewSet, basename='daily-records')
router.register('work-sessions', WorkSessionViewSet, basename='work-sessions')

employee_router = NestedDefaultRouter(router, 'employees', lookup='employee')
employee_router.register('promotions', PromotionViewSet, basename='employee-promotions')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('', include(router.urls)),
    path('', include(employee_router.urls)),
    path('current-worksession/<int:emp_id>/', CurrentWorkSession.as_view(), name='current-work-session'),
]