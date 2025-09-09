from datetime import date, timedelta
from django.utils import timezone

def to_date(record_date):
    if isinstance(record_date, str):
        return timezone.datetime.strptime(record_date, "%Y-%m-%d").date()
    if isinstance(record_date, timezone.datetime):
        record_date = timezone.localtime(record_date).date()
    return record_date

def validate_today_or_yesterday(record_date): 
    today = date.today() 
    yesterday = today - timedelta(days=1) 
    record_date = to_date(record_date)

    return (record_date == today or record_date == yesterday)