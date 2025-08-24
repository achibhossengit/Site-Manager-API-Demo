from django.contrib import admin
from daily_records.models import DailyRecord, WorkSession, SiteWorkRecord, DailyRecordSnapshot

# Register your models here.
admin.site.register(DailyRecord)
admin.site.register(WorkSession)
admin.site.register(SiteWorkRecord)

@admin.register(DailyRecordSnapshot)
class DailyRecordSnapshotAdmin(admin.ModelAdmin):
    readonly_fields = [field.name for field in DailyRecordSnapshot._meta.fields]
    
    def has_change_permission(self, request, obj=None):
        return False
