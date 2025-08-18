from django.contrib import admin
from site_profiles.models import Site, SiteCash, SiteCost, SiteBill

# Register your models here.
admin.site.register(Site)
admin.site.register(SiteCash)
admin.site.register(SiteCost)
admin.site.register(SiteBill)