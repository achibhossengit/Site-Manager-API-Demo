from django.db import models
from users.models import CustomUser
from site_profiles.models import Site
from datetime import date
from django.core.validators import MaxValueValidator
from site_profiles.models import PERMISSION_CHOICES
from site_profiles.validators import validate_today_or_yesterday


class DailyRecord(models.Model):
    PRESENT_CHOICES = [
        (0.0, 'Absent'),
        (0.5, 'Half Day'),
        (1.0, 'Full Day'),
    ]
    
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='daily_records')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='daily_records')
    date = models.DateField(default=date.today, validators=[validate_today_or_yesterday])
    present = models.FloatField(choices=PRESENT_CHOICES, default=0.0)
    khoraki = models.PositiveIntegerField(validators=[MaxValueValidator(1000)])
    advance = models.PositiveIntegerField(blank=True, null=True)
    comment = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    permission_level = models.IntegerField(choices=PERMISSION_CHOICES, default=0)


    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['employee', 'date'], name='unique_daily_record_per_employee')
        ]
    
    def __str__(self):
        return f"{self.employee} - {self.date}"


class WorkSession(models.Model):
    employee = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='work_sessions'
    )
    start_date = models.DateField()  # first daily record date
    end_date = models.DateField()    # last daily record date
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # only can update is_paid filed -> "mistake" not intentionally
    
    is_paid = models.BooleanField(default=False)
    
    @property
    def total_payable(self):
        total = 0
        for record in self.records.all():
            total += record.payable
        return total

    def __str__(self):
        return f"{self.employee.username} | {self.start_date} - {self.end_date}"
        

class SiteWorkRecord(models.Model):
    work_session = models.ForeignKey(
        WorkSession,
        on_delete=models.CASCADE,
        related_name='records'
    )
    site = models.ForeignKey('site_profiles.Site', on_delete=models.CASCADE, related_name='work_records')
    work = models.PositiveIntegerField()
    total_salary = models.PositiveIntegerField()
    khoraki_taken = models.PositiveIntegerField()
    advance_taken = models.PositiveIntegerField()
    
    @property
    def payable(self):
        return self.total_salary - (self.khoraki_taken + self.advance_taken)

    def __str__(self):
        return f"Site: {self.site} | Work: {self.work} days"