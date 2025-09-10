from django.contrib import admin
from site_profiles.models import Site, SiteCash, SiteCost, SiteBill

# Register your models here.
admin.site.register(Site)
@admin.register(SiteCash)
class SiteCashAdmin(admin.ModelAdmin):
    list_display = ['date','site', 'title', 'amount']
    list_filter = ['date', 'site']

@admin.register(SiteCost)
class SiteCostAdmin(admin.ModelAdmin):
    list_display = ['date','site', 'title', 'amount', 'type']
    list_filter = ['date', 'site', 'type']

@admin.register(SiteBill)
class SiteBillAdmin(admin.ModelAdmin):
    list_display = ['date','site', 'title', 'amount']
    list_filter = ['date', 'site']