from django.db import models
from django.core.validators import MinValueValidator
from users.models import CustomUser
from site_profiles.models import Site
from django.core.validators import MaxValueValidator
from site_profiles.models import PERMISSION_CHOICES
from api.services.get_salary_by_employee import get_salary_by_employee

PRESENT_CHOICES = [
    (0, 'Absent'),
    (0.5, 'Half Day'),
    (1, 'Full Day'),
    (1.5, '1.5 Day'),
    (2, '2 Day'),
    (2.5, '2.5 Day'),
    (3, '3 Day'),
]

class DailyRecord(models.Model):
    
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='daily_records')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='daily_records')
    date = models.DateField()
    present = models.FloatField(choices=PRESENT_CHOICES, default=0)
    khoraki = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(1000)])
    advance = models.PositiveIntegerField(default=0)
    comment = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    permission_level = models.IntegerField(choices=PERMISSION_CHOICES, default=0)

    @property
    def today_salary(self):
        return get_salary_by_employee(self.employee, self.date)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['employee', 'date'], name='unique_daily_record_per_employee')
        ]
    
    def __str__(self):
        return f"{self.employee.first_name} - {self.date}"


class WorkSession(models.Model):
    employee = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='work_sessions'
    )
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='created_worksessions') # which site create it
    start_date = models.DateField()  # first daily record date
    end_date = models.DateField()    # last daily record date
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    update_permission = models.BooleanField(default=False)
    
    total_work = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    last_session_payable = models.IntegerField(default=0)
    this_session_payable = models.IntegerField()
    pay_or_return = models.IntegerField(default=0) # payment during session creation time
    
    @property
    def rest_payable(self):
        return (self.this_session_payable + self.last_session_payable) - self.pay_or_return

    def __str__(self):
        return f"{self.employee.first_name +" "+ self.employee.last_name}  | {self.created_at}"
        

class SiteWorkRecord(models.Model):
    work_session = models.ForeignKey(
        WorkSession,
        on_delete=models.CASCADE,
        related_name='records'
    )
    site = models.ForeignKey('site_profiles.Site', on_delete=models.CASCADE, related_name='work_records')
    work = models.FloatField()
    total_salary = models.PositiveIntegerField()
    khoraki_taken = models.PositiveIntegerField()
    advance_taken = models.PositiveIntegerField()
    
    @property
    def payable(self):
        return self.total_salary - (self.khoraki_taken + self.advance_taken)

    def __str__(self):
        return f"Site: {self.site} | Work: {self.work} days"
    
    
class DailyRecordSnapshot(models.Model):
    """
    Snapshot of DailyRecord BEFORE deletion — used for today's reporting when original DailyRecord is removed.
    """
    site = models.ForeignKey(Site, related_name='daily_record_snapshots', on_delete=models.CASCADE)
    employee = models.ForeignKey(CustomUser, related_name='daily_record_snapshots', on_delete=models.CASCADE)
    date = models.DateField()
    present = models.FloatField(choices=PRESENT_CHOICES, default=0)
    khoraki = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(1000)])
    advance = models.PositiveIntegerField(default=0)
    comment = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Employee: {self.employee.first_name + "" + self.employee.last_name} | {self.site} | {self.date}"