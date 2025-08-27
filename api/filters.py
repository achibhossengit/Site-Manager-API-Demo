from django_filters import rest_framework as filters
from site_profiles.models import SiteCost, SiteCash, SiteBill

class SiteCostFilterClass(filters.FilterSet):
    # date range filter -> client uses date_after and date_before
    date = filters.DateFromToRangeFilter()

    class Meta:
        model = SiteCost
        fields = ['date']

class SiteCashFilterClass(filters.FilterSet):
    date = filters.DateFromToRangeFilter()

    class Meta:
        model = SiteCash
        fields = ['date']

class SiteBillFilterClass(filters.FilterSet):
    date = filters.DateFromToRangeFilter()

    class Meta:
        model = SiteBill
        fields = ['date']
