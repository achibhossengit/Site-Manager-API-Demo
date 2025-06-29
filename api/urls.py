from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import EmployeeViewSet

router = DefaultRouter()
router.register('employees', EmployeeViewSet, basename='employees')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('', include(router.urls)),
]