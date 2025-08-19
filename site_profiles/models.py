from django.db import models
from django.core.exceptions import ValidationError
from datetime import date
from django.db.models import Sum, F
from site_profiles.validators import validate_today_or_yesterday, validate_not_future_date
from users.models import Promotion
from api.services.get_salary import get_salary

PERMISSION_CHOICES = [
    (0, 'No Permission'),
    (1, 'Update Only'),
    (2, 'Delete Only'),
]

COST_TYPE_CHOICES = [
    ('st', 'Site Cost'),
    ('ot', 'Other Cost'),
]

class Site(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=500)
    location = models.CharField(max_length=100)
    start_at = models.DateField(default=date.today)
    handover = models.DateField(null=True, blank=True)
    
    def get_current_actual_emp_cost(self):
        daily_records = self.daily_records.select_related('employee')
        # Step 1: Get unique employee list from records
        employee_ids = set(daily_records.values_list('employee_id', flat=True))
        # Step 2: Preload promotions grouped by employee_id
        promotions_by_employee = {
            emp_id: list(Promotion.objects.filter(employee_id=emp_id).order_by('-date'))
            for emp_id in employee_ids
        }
        current = 0
        for record in daily_records:
            emp_id = record.employee_id
            promotions = promotions_by_employee.get(emp_id, [])
            today_salary = get_salary(promotions, record.date)
            current += today_salary * record.present
        return current
    
    def get_previous_actual_emp_cost(self):
        previous = self.work_records.aggregate(total=Sum('total_salary'))
        return previous.get('total') or 0
        
    
    def get_current_emp_taken_cost(self):
        current_taken_cost = self.daily_records.annotate(total = F('khoraki') + F('advance')).aggregate(total_taken=Sum('total'))
        return current_taken_cost.get('total_taken') or 0

    def get_previous_emp_taken_cost(self):
        workrecords = self.work_records.annotate(total = F('khoraki_taken') + F('advance_taken')).aggregate(total_taken=Sum('total'))
        worksessions = self.created_worksessions.aggregate(total_taken=Sum('pay_or_return'))
        
        result = (workrecords.get('total_taken') or 0) + (worksessions.get('total_taken') or 0)
        return result
        

    @property
    def total_site_bill(self):
        result = self.site_bills.aggregate(total=Sum('amount'))
        return result.get('total') or 0

    @property
    def total_rose_taken(self):
        previous = self.work_records.aggregate(total=Sum('work'))
        current = self.daily_records.aggregate(total=Sum('present'))
        result = (previous.get('total') or 0) + (current.get('total') or 0)
        return result
    
    @property
    def actual_employee_cost(self):
        previous_emp_cost = self.get_previous_actual_emp_cost()
        current_emp_cost = self.get_current_actual_emp_cost()
        result = previous_emp_cost + current_emp_cost
        return result

    @property
    def total_site_cost(self):
        result = self.site_costs.filter(type='st').aggregate(total=Sum('amount'))
        return result.get('total') or 0

    @property
    def total_other_cost(self):
        result = self.site_costs.filter(type='ot').aggregate(total=Sum('amount'))
        return result.get('total') or 0
    
    @property
    def profit(self):
        result = self.total_site_bill - (self.total_site_cost + self.actual_employee_cost)
        return result

    @property
    def total_site_cash(self):
        result = self.site_cashes.aggregate(total=Sum('amount'))
        return result.get('total') or 0
    
    @property
    def taken_employee_cost(self):
        previous_taken_cost = self.get_previous_emp_taken_cost()
        current_taken_cost = self.get_current_emp_taken_cost()
        return previous_taken_cost + current_taken_cost
    
    @property
    def site_balance(self):
        result = self.total_site_cash - (self.total_site_cost + self.total_other_cost + self.taken_employee_cost)
        return result


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
    date = models.DateField(default=date.today, validators=[validate_today_or_yesterday])
    title = models.CharField(max_length=50)
    amount = models.PositiveIntegerField()
    type = models.CharField(choices=COST_TYPE_CHOICES, default='st')
    updated_at = models.DateTimeField(auto_now=True)
    permission_level = models.IntegerField(choices=PERMISSION_CHOICES, default=0)

    def __str__(self):
        return self.title
    

class SiteCash(models.Model):
    site = models.ForeignKey(Site, related_name='site_cashes', on_delete=models.CASCADE)
    date = models.DateField(default=date.today, validators=[validate_today_or_yesterday])
    title = models.CharField(max_length=50)
    amount = models.PositiveIntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    permission_level = models.IntegerField(choices=PERMISSION_CHOICES, default=0)


    
    def __str__(self):
        return self.title
    
    
class SiteBill(models.Model):
    site = models.ForeignKey(Site, related_name='site_bills', on_delete=models.CASCADE)
    date = models.DateField(default=date.today, validators=[validate_not_future_date])
    title = models.CharField(max_length=200)
    amount = models.PositiveIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    
    def __str__(self):
        return self.title