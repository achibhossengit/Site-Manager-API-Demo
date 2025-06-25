from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator

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
    phone = models.CharField(max_length=20, blank=True, null=True)
    current_site = models.ForeignKey('site_profiles.Site', on_delete=models.SET_NULL, null=True, related_name='employees')

    def __str__(self):
        return self.username

class Promotion(models.Model):
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='promotions')
    date = models.DateField()
    increment = models.IntegerField()
    current_salary = models.PositiveIntegerField(validators=[MaxValueValidator(5000)])
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['employee', 'date'], name='unique_employee_date')
        ]

    def __str__(self):
        return f"{self.employee.username} - {self.date}"