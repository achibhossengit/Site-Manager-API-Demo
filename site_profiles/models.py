from django.db import models
from django.core.exceptions import ValidationError
from datetime import date

PERMISSION_CHOICES = [
    (0, 'No Permission'),
    (1, 'Update Only'),
    (2, 'Delete Only'),
]

class Site(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=500)
    location = models.CharField(max_length=100)
    start_at = models.DateField(default=date.today)
    handover = models.DateField(null=True, blank=True)

    def clean(self):
        if self.handover and self.handover <= self.start_at:
            raise ValidationError("Handover date must be after the start date.")

    def save(self, *args, **kwargs):
        self.full_clean()  
        super(Site, self).save(*args, **kwargs)
        
    def __str__(self):
        return self.name
    
    
class SiteCost(models.Model):
    site = models.ForeignKey(Site, related_name='site_costs', on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    title = models.CharField(max_length=300)
    amount = models.PositiveIntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    permission_level = models.IntegerField(choices=PERMISSION_CHOICES, default=0)

    def __str__(self):
        return self.title
    

class SiteCash(models.Model):
    site = models.ForeignKey(Site, related_name='site_cashes', on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    title = models.CharField(max_length=200)
    amount = models.PositiveIntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    permission_level = models.IntegerField(choices=PERMISSION_CHOICES, default=0)


    
    def __str__(self):
        return self.title
    
    
class SiteBill(models.Model):
    site = models.ForeignKey(Site, related_name='site_bills', on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    title = models.CharField(max_length=200)
    amount = models.PositiveIntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    permission_level = models.IntegerField(choices=PERMISSION_CHOICES, default=0)

    
    def __str__(self):
        return self.title