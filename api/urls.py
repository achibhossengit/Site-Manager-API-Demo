from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import EmployeeViewSet
from site_profiles.views import SiteViewSet

router = DefaultRouter()
router.register('employees', EmployeeViewSet, basename='employees')
router.register('sites', SiteViewSet, basename='sites')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('', include(router.urls)),
]