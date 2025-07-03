from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from daily_records.models import DailyRecord
from daily_records.serializers import DailyRecordAccessSerializer, DailyRecordCreateSerializer, DailyRecordUpdatePermissionSerializer
from daily_records.permissions import IsAdminOrConditionalPermissionForDailyRecord

class DailyRecordViewSet(ModelViewSet):
    
    """
    Permissions:
        - Admins:
            → Can create, retrieve, update, and delete any daily record.
        - Main Managers:
            → Can retrieve (GET) all daily records.
            → Can update (PUT) only when permission_level == 1.
            → Can delete (DELETE) only when permission_level == 2.
            → Cannot create (POST) daily records.
        - Site Managers:
            → Can retrieve (GET) daily records for their own site.
            → Can create (POST) daily records for their employees.
            → Can partially update (PATCH) permission_level of records in their site.
        - Viewers:
            → Can only retrieve (GET) daily records.
        - Employees:
            → Can retrieve (GET) only their own daily records.
            → Cannot create, update, or delete any records.
    """
    
    permission_classes = [IsAuthenticated,  IsAdminOrConditionalPermissionForDailyRecord]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DailyRecordCreateSerializer
        
        if self.request.method == 'PATCH':
            return DailyRecordUpdatePermissionSerializer

        return DailyRecordAccessSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.user_type in ['main_manager', 'viewer']:
            return DailyRecord.objects.all()
        
        if user.user_type == 'site_manager':
            return DailyRecord.objects.filter(site=user.current_site)

        if user.user_type == 'employee':
            return DailyRecord.objects.filter(employee = user)
        
        return DailyRecord.objects.none()
    
    