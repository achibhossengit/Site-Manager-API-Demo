from collections import defaultdict
from daily_records.models import DailyRecord, WorkSession
from api.services.get_salary_by_employee import get_salary_by_employee

def get_current_worksession(employee_id):
    # Step 1: fetch all dailyrecords for an employee
    daily_records = DailyRecord.objects.filter(employee=employee_id).select_related('site').order_by('date')

    # Validation
    if not daily_records.exists():
        return None

    first_record = daily_records.first()
    # collect last daily_record for snapshot
    last_record = daily_records.last()

    # Step 2: create group based on site
    site_data = defaultdict(lambda: {
        'work': 0,
        'khoraki_taken': 0,
        'advance_taken': 0,
        'total_salary': 0,
    })

    total_work = 0
    total_salary = 0
    total_advance = 0
    total_khoraki = 0

    for record in daily_records:
        site_id = record.site.id
        site_name = record.site.name
        today_salary = get_salary_by_employee(record.employee, record.date)
        today_earned_salary = today_salary * record.present

        total_work += record.present
        total_salary += today_earned_salary
        total_advance += record.advance or 0
        total_khoraki += record.khoraki or 0

        site_data[site_id]['site'] = site_name
        site_data[site_id]['work'] += record.present
        site_data[site_id]['khoraki_taken'] += record.khoraki or 0
        site_data[site_id]['advance_taken'] += record.advance or 0
        site_data[site_id]['total_salary'] += today_earned_salary

    # Step 3: calculate payable
    work_records = []
    for site_id, data in site_data.items():
        payable = data['total_salary'] - (data['khoraki_taken'] + data['advance_taken'])
        work_records.append({
            "site_id": site_id,
            "site": data['site'],
            "work": data['work'],
            "khoraki_taken": data['khoraki_taken'],
            "advance_taken": data['advance_taken'],
            "total_salary": int(data['total_salary']),
            "payable": int(payable),
        })

    # Step 4: fetch last worksession
    last_worksession = WorkSession.objects.filter(employee=employee_id).order_by('created_at').last()
    last_session_payable = 0
    if last_worksession: 
        last_session_payable = last_worksession.rest_payable
        
    # Step 5:create current_worksession dict
    current_worksession = {
        "start_date": first_record.date,
        "end_date": last_record.date,
        "total_work": total_work,
        "total_salary": total_salary,
        "total_advance": total_advance,
        "total_khoraki": total_khoraki,
        "last_session_payable": last_session_payable,
        "work_records": work_records,
        "last_record": last_record,
    }

    return current_worksession
