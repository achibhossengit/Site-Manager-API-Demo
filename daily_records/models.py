from django.db import models
from users.models import CustomUser
from site_profiles.models import Site
from datetime import date
from django.core.validators import MaxValueValidator


class DailyRecord(models.Model):
    PRESENT_CHOICES = [
    (0.0, 'Absent'),
    (0.5, 'Half Day'),
    (1.0, 'Full Day'),
    ]
    
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='daily_records')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='daily_records')
    date = models.DateField(default=date.today)
    present = models.FloatField(choices=PRESENT_CHOICES, default=0.0)
    khoraki = models.PositiveIntegerField(validators=[MaxValueValidator(1000)])
    advance = models.PositiveIntegerField(blank=True, null=True)
    comment = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    update_permission = models.BooleanField(default=False)

    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['employee', 'date'], name='unique_daily_record_per_employee')
        ]
    
    def __str__(self):
        return f"{self.employee} - {self.date}"

