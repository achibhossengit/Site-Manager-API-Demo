from django.contrib import admin
from daily_records.models import DailyRecord, WorkSession, SiteWorkRecord, DailyRecordSnapshot

# Register your models here.
@admin.register(DailyRecord)
class DailyRecordAdmin(admin.ModelAdmin):
    list_display = ['date', 'employee', 'site',] 
    list_filter = ['date', 'site'] 
    ordering = ['-date']

@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'employee', 'site']
    list_filter = ['created_at', 'end_date', 'site', 'employee'] 
    ordering = ['-created_at']

@admin.register(SiteWorkRecord)
class SiteWorkRecordAdmin(admin.ModelAdmin):
    list_display = ['work_session', 'site', 'work']
    list_filter = ['site', 'work_session',]

@admin.register(DailyRecordSnapshot)
class DailyRecordSnapshotAdmin(admin.ModelAdmin):
    readonly_fields = [field.name for field in DailyRecordSnapshot._meta.fields]
    list_filter = ['date', 'site', 'employee']
    
    def has_change_permission(self, request, obj=None):
        return False
