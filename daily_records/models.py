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
    
    employee = models.ForeignKey(CustomUser, on_delete=models.RESTRICT, related_name='daily_records')
    site = models.ForeignKey(Site, on_delete=models.RESTRICT, related_name='daily_records')
    date = models.DateField()
    present = models.FloatField(choices=PRESENT_CHOICES, default=0)
    khoraki = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(1000)])
    advance = models.PositiveIntegerField(default=0)
    comment = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    permission_level = models.IntegerField(choices=PERMISSION_CHOICES, default=0)
    
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
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, related_name='created_worksessions') # which site create it
    start_date = models.DateField()  # first daily record date
    end_date = models.DateField()    # last daily record date
    created_date = models.DateField(auto_now_add=True)
    
    present = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    # It should be positive integers, but some existing session_salary values are floats.
    session_salary = models.FloatField(default=0, validators=[MaxValueValidator(5000), MinValueValidator(0)])
    khoraki = models.PositiveIntegerField(default=0)
    advance = models.PositiveIntegerField(default=0)

    last_session_payable = models.FloatField(default=0)
    pay_or_return = models.FloatField(default=0) # payment during session creation
    
    @property
    def earned_salary(self):
        return self.present * self.session_salary

    @property
    def total_taken(self):
        return self.khoraki + self.advance
    
    @property
    def this_session_payable(self):
        return self.earned_salary - self.total_taken

    @property
    def total_payable(self):
        return self.last_session_payable + self.this_session_payable
    
    @property
    def rest_payable(self):
        return self.total_payable - self.pay_or_return

    def __str__(self):
        return f"{self.employee.first_name +" "+ self.employee.last_name}  | {self.created_at}"
        

class SiteWorkRecord(models.Model):
    work_session = models.ForeignKey(WorkSession, on_delete=models.SET_NULL,null=True, related_name='records')
    site = models.ForeignKey('site_profiles.Site', on_delete=models.CASCADE, related_name='work_records')
    session_owner = models.BooleanField(default=False)
    created_date = models.DateField(auto_now_add=True)
    present = models.FloatField(default=0)
    # It should be positive integers, but some existing session_salary values are floats.
    session_salary = models.FloatField(default=0, validators=[MinValueValidator(0)])    
    khoraki = models.PositiveIntegerField(default=0)
    advance = models.PositiveIntegerField(default=0)
    pay_or_return = models.FloatField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(session_owner=True) | models.Q(pay_or_return=0),
                name='check_pay_or_return'
            )
        ]
    
    @property
    def total_salary(self):
        return self.present * self.session_salary

    @property
    def payable(self):
        return self.total_salary - (self.khoraki + self.advance)

    def __str__(self):
        return f"Site: {self.site} | Work: {self.present} days"
    
    
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