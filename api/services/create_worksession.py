from django.db import transaction
from django.core.exceptions import ValidationError
from daily_records.models import DailyRecord, WorkSession, SiteWorkRecord
from users.models import CustomUser
from api.services.get_current_worksession import get_current_worksession

def create_worksession(emp_id, is_paid, pay):
    try:
        employee = CustomUser.objects.get(id=emp_id)
    except CustomUser.DoesNotExist:
        return {
            "message": "Employee not found.",
            "error": f"No employee exists with ID: {emp_id}"
        }
        
    if employee.current_site_id:
        employee_current_site = employee.current_site_id
    else:
        raise ValidationError(f"Current_site is not set yet of employee: {employee}!")

    # Get current worksession
    current_worksession = get_current_worksession(emp_id)
    

    try:
        with transaction.atomic():
            # Step 1: Create WorkSession
            work_session = WorkSession.objects.create(
                employee = employee,
                site_id = employee_current_site,
                start_date= current_worksession['start_date'],
                end_date= current_worksession['end_date'],
                
                total_work = current_worksession['total_work'],
                last_session_payable = current_worksession['last_session_payable'],
                payable = current_worksession['total_salary'] - (current_worksession['total_advance'] + current_worksession['total_khoraki']),
                pay = pay,
                is_paid=is_paid,
            )

            # Step 2: Create related SiteWorkRecord entries
            for record in current_worksession['work_records']:
                SiteWorkRecord.objects.create(
                    work_session=work_session,
                    site_id=record['site_id'],
                    work=record['work'],
                    total_salary=record['total_salary'],
                    khoraki_taken=record['khoraki_taken'],
                    advance_taken=record['advance_taken'],
                )

            # Step 3: Delete all DailyRecords of this employee
            DailyRecord.objects.filter(employee=employee).delete()

    except Exception as e:
        return {
            "message": "Failed to create work session.",
            "error": str(e)
        }

    return {
        "message": "Work session created successfully.",
        "session_id": work_session.id
    }
