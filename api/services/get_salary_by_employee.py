from users.models import Promotion
from api.services.get_salary import get_salary

def get_salary_by_employee(emp, work_date):
    promotions = Promotion.objects.filter(employee=emp).order_by('-date')
    return get_salary(promotions, work_date)