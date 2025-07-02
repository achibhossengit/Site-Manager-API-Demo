from datetime import date, timedelta
from django.core.exceptions import ValidationError

def validate_today_or_yesterday(value):
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    if value > today or value < yesterday:
        raise ValidationError("Only today or yesterday's date is allowed.")
    
def validate_not_future_date(value):
    today = date.today()
    if value > today:
        raise ValidationError("Future dates are not allowed.")