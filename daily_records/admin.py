from django.contrib import admin
from daily_records.models import DailyRecord, WorkSession, SiteWorkRecord

# Register your models here.
admin.site.register(DailyRecord)
admin.site.register(WorkSession)
admin.site.register(SiteWorkRecord)
