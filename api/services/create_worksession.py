from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from daily_records.models import DailyRecord, WorkSession, SiteWorkRecord, DailyRecordSnapshot
from users.models import CustomUser
from api.services.get_current_worksession import get_current_worksession

def create_worksession(emp_id, pay_or_return):
    employee = CustomUser.objects.get(id=emp_id) # if employee not found then django automatically raised a execption
    if not employee.current_site_id:
        raise ValidationError(f"Current_site is not set yet for employee: {employee}!")

    employee_current_site = employee.current_site_id
    current_worksession = get_current_worksession(emp_id)
    last_record = current_worksession.pop('last_record')
    is_same_day = last_record.date == timezone.localdate() # last record date == this_session_creating date

    with transaction.atomic():
        # Step 1: Create WorkSession
        work_session = WorkSession.objects.create(
            employee = employee,
            site_id = employee_current_site,
            start_date= current_worksession['start_date'],
            end_date= current_worksession['end_date'],
            
            total_work = current_worksession['total_work'],
            last_session_payable = current_worksession['last_session_payable'],
            this_session_payable = current_worksession['total_salary'] - (current_worksession['total_advance'] + current_worksession['total_khoraki']),
            pay_or_return = pay_or_return,
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

        # Step 3: Creating Snapshot of last daily records conditionally
        if is_same_day:
            DailyRecordSnapshot.objects.create(
                site=last_record.site,
                employee=last_record.employee,
                date=last_record.date,
                present=last_record.present,
                khoraki=last_record.khoraki,
                advance=last_record.advance,
                comment=last_record.comment
            )

        # Step 3: Delete all DailyRecords of this employee
        DailyRecord.objects.filter(employee=employee).delete()

    return {
        "message": "Work session created successfully.",
        "session_id": work_session.id
    }
