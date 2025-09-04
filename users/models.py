from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator
from django.db.models import Sum
from api.services.get_salary import get_salary

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('main_manager', 'Main Manager'),
        ('site_manager', 'Site Manager'),
        ('employee', 'Employee'),
        ('viewer', 'Viewer'),
    ]
    DESIGNATION_CHOICES = [
        ('4MAN', 'ফোর ম্যান'),
        ('MISTRI', 'মিস্ত্রি'),
        ('HELPER', 'হেল্পার'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default= 'employee')
    designation = models.CharField(max_length=20, choices=DESIGNATION_CHOICES, default= 'HELPER')
    address = models.TextField(max_length=200, blank=True, null=True)
    current_site = models.ForeignKey('site_profiles.Site', on_delete=models.SET_NULL, null=True, related_name='employees')    

    
    @property
    def last_session_end_date(self):
        last_session = self.work_sessions.all().order_by('end_date').last()
        if last_session:
            return last_session.end_date
        return None

    def __str__(self):
        return self.first_name

class Promotion(models.Model):
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='promotions')
    date = models.DateField()
    current_salary = models.PositiveIntegerField(validators=[MaxValueValidator(5000)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['employee', 'date'], name='unique_employee_date')
        ]

    def __str__(self):
        return f"{self.employee.first_name} - {self.date}"