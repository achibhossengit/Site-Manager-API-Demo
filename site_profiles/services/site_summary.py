from django.db.models import Sum, Count, Value, F, Q
from django.db.models.functions import Coalesce
from site_profiles.models import SiteCost, SiteCash, SiteBill
from daily_records.models import DailyRecord, DailyRecordSnapshot, SiteWorkRecord

def get_date_based_site_summary(site, date, user_type):
    isViewer = user_type == "viewer"
    
    # Fetch all aggregates
    cash_agg = _get_cash_aggregates(site, date, date_based=True)
    cost_agg = _get_cost_aggregates(site, date, date_based=True)
    records_agg = _get_records_aggregates(site, date, date_based=True, isViewer=isViewer)
    snapshot_agg = _get_snapshot_aggregates(site, date, date_based=True, isViewer=isViewer)
    sitework_agg = _get_sitework_aggregates(site, date, date_based=True, isViewer=isViewer)
    
    # this day values
    cash_of_date = cash_agg["cash_of_date"]
    st_of_date = cost_agg["st_of_date"] # st -> equipment_cost
    ot_of_date = cost_agg["ot_of_date"]
    site_cost_of_date = ot_of_date + st_of_date
    present_of_date = records_agg["present_of_date"] + snapshot_agg["present_of_date"]
    emp_count_of_date = records_agg["emp_count_of_date"] + snapshot_agg["emp_count_of_date"]
    khoraki_of_date = records_agg["khoraki_of_date"] + snapshot_agg["khoraki_of_date"]
    advance_of_date = records_agg["advance_of_date"] + snapshot_agg["advance_of_date"]
    session_count_of_date= sitework_agg["session_count_of_date"]
    session_pay_of_date = sitework_agg["session_pay_of_date"]
    emp_cost_of_date = khoraki_of_date + advance_of_date + session_pay_of_date
    cost_of_date = site_cost_of_date + emp_cost_of_date

    # this day balance calculation
    site_cost_until_date = cost_agg["site_cost_until_date"]
    emp_cost_until_date_dailyrecord = records_agg['emp_cost_until_date']

    total_emp_cost_sitework = sitework_agg['total_emp_cost']
    emp_cost_after_date = snapshot_agg["emp_cost_after_date"]
    pay_or_return_after_date = sitework_agg['pay_or_return_after_date']
    emp_cost_until_date_sitework = total_emp_cost_sitework - emp_cost_after_date - pay_or_return_after_date

    emp_cost_until_date = emp_cost_until_date_dailyrecord + emp_cost_until_date_sitework
        
    cash_until_date = cash_agg["cash_until_date"]
    cost_until_date = site_cost_until_date + emp_cost_until_date
    balance_of_date = cash_until_date - cost_until_date

    # day_before
    cash_until_day_before = cash_until_date - cash_of_date
    cost_until_day_before = cost_until_date - cost_of_date
    balance_of_day_before = cash_until_day_before - cost_until_day_before

    # payload
    today_summary = {
        "date": date,
        "cash_of_date": cash_of_date,

        "st_of_date": st_of_date,
        "ot_of_date": ot_of_date,
        "site_cost_of_date": site_cost_of_date,
        
        "emp_count_of_date": emp_count_of_date,
        "present_of_date": present_of_date,
        "khoraki_of_date": khoraki_of_date,
        "advance_of_date": advance_of_date,
        "session_count_of_date": session_count_of_date,
        "session_pay_of_date": session_pay_of_date,
        "emp_cost_of_date": emp_cost_of_date,

        "cost_of_date": cost_of_date,

        # these fieds not needed to send to the backend
        # "cash_until_date": cash_until_date,
        # "site_cost_until_date": site_cost_until_date,
        # "emp_cost_until_date": emp_cost_until_date,

        "balance_of_date": balance_of_date,
        "balance_of_day_before":balance_of_day_before,
    }
        
    if isViewer:
        bill_agg = _get_bill_aggregates(site, date, date_based=True)
        emp_salary_of_date = records_agg["emp_salary_of_date"] + snapshot_agg["emp_salary_of_date"]
        
        today_summary["emp_salary_of_date"] = emp_salary_of_date
        # today_summary["emp_payable_of_date"] = emp_salary_of_date - emp_cost_of_date
        today_summary["bill_of_date"] = bill_agg["bill_of_date"]
    
    return today_summary


def get_total_site_summary(site):

    # Fetch all aggregates
    bill_agg = _get_bill_aggregates(site, date=None)
    cash_agg = _get_cash_aggregates(site, date=None, date_based=False)
    cost_agg = _get_cost_aggregates(site, date=None, date_based=False)
    # isViewer=true, because only viewer can call this api/function
    records_agg = _get_records_aggregates(site, date=None, date_based=False, isViewer=True) 
    sitework_agg = _get_sitework_aggregates(site, date=None, date_based=False, isViewer=True)
    
    # extract values from aggregation
    total_bill = bill_agg["total_bill"]
    total_cash = cash_agg["total_cash"]
    
    total_ot = cost_agg["total_ot"]
    total_st = cost_agg["total_st"]
    total_site_cost = total_ot + total_st
    
    total_present = records_agg["total_present"] + sitework_agg["total_present"]
    total_khoraki = records_agg["total_khoraki"] + sitework_agg["total_khoraki"]
    total_advance = records_agg["total_advance"] + sitework_agg["total_advance"]
    total_emp_cost = total_khoraki + total_advance + sitework_agg["total_pay_or_return"]

    total_emp_salary = records_agg["total_emp_salary"] + sitework_agg["total_emp_salary"]
    total_emp_payable = total_emp_salary - total_emp_cost
    
    total_cost = total_site_cost + total_emp_cost
    balance = total_cash - total_cost

    total_actual_cost = total_site_cost + total_emp_salary
    total_profit = total_bill - total_actual_cost

    # payload
    summary = {
        "total_cash": total_cash,
        "total_st": total_st,
        "total_ot": total_ot,
        "total_site_cost": total_site_cost,

        "total_present": total_present,
        "total_khoraki": total_khoraki,
        "total_advance": total_advance,
        "site_pay_or_return": sitework_agg["total_pay_or_return"],
        "total_emp_cost": total_emp_cost,
        "total_cost": total_cost,
        "balance": balance,

        "total_bill": total_bill,
        "total_emp_salary": total_emp_salary,
        "total_actual_cost": total_actual_cost,
        "total_emp_payable": total_emp_payable,
        "total_profit":total_profit,
    }
    
    return summary


def _get_bill_aggregates(site, date, date_based=False):
    agg_fields = {}
    
    if date_based:
        agg_fields.update({
        "bill_of_date":Coalesce(Sum("amount", filter=Q(date=date)), Value(0)),
        })
    else:
        agg_fields.update({
        "total_bill":Coalesce(Sum("amount"), Value(0)),
        })

    return SiteBill.objects.filter(site=site).aggregate(**agg_fields)

def _get_cash_aggregates(site, date, date_based=True):
    agg_fields = {}
    
    if date_based:
        agg_fields.update({
        "cash_of_date":Coalesce(Sum("amount", filter=Q(date=date)), Value(0)),
        "cash_until_date":Coalesce(Sum("amount", filter=Q(date__lte=date)), Value(0)),
        })

    else:
        agg_fields.update({
        "total_cash":Coalesce(Sum("amount"), Value(0)),
        })

    return SiteCash.objects.filter(site=site).aggregate(**agg_fields)

def _get_cost_aggregates(site, date, date_based=True):
    agg_fields = {}

    if date_based:
        agg_fields.update({
        "st_of_date":Coalesce(Sum("amount", filter=Q(type="st", date=date)), Value(0)),
        "ot_of_date":Coalesce(Sum("amount", filter=Q(type="ot", date=date)), Value(0)),
        "site_cost_until_date":Coalesce(Sum("amount", filter=Q(date__lte=date)), Value(0)),
        })
    else:
        agg_fields.update({
        "total_st":Coalesce(Sum("amount", filter=Q(type="st")), Value(0)),
        "total_ot":Coalesce(Sum("amount", filter=Q(type="ot")), Value(0)),
        })
        
    return SiteCost.objects.filter(site=site).aggregate(**agg_fields)

def _get_records_aggregates(site, date, date_based=True, isViewer=True):
    agg_fields = {}

    if date_based:
        agg_fields.update({
        'present_of_date': Coalesce(Sum("present", filter=Q(date=date)), Value(0.0)),
        'emp_count_of_date': Coalesce(Count("employee", filter=Q(date=date, present__gt=0), distinct=True), (0)),
        'khoraki_of_date': Coalesce(Sum("khoraki", filter=Q(date=date)), Value(0)),
        'advance_of_date': Coalesce(Sum("advance", filter=Q(date=date)), Value(0)),
        'emp_cost_until_date': Coalesce(Sum(F("khoraki") + F("advance"), filter=Q(date__lte=date)), Value(0)),
        })

        if isViewer:
            agg_fields.update({
                'emp_salary_of_date': Coalesce(Sum(F("present") * F("employee__current_salary"), filter=Q(date=date)), Value(0.0)),
            })
        
    else:
        agg_fields.update({
        'total_present': Coalesce(Sum("present"), Value(0.0)),
        'total_khoraki': Coalesce(Sum("khoraki"), Value(0)),
        'total_advance': Coalesce(Sum("advance"), Value(0)),
        'total_emp_salary': Coalesce(Sum(F("present") * F("employee__current_salary")), Value(0.0)),
        })


    return DailyRecord.objects.filter(site=site).aggregate(**agg_fields)

def _get_snapshot_aggregates(site, date, date_based=True, isViewer=True):
    agg_fields = {}
    
    if date_based:
        agg_fields.update({
        'present_of_date': Coalesce(Sum("present", filter=Q(date=date)), Value(0.0)),
        'emp_count_of_date': Coalesce(Count("employee", filter=Q(date=date, present__gt=0), distinct=True), Value(0)),
        'khoraki_of_date': Coalesce(Sum("khoraki", filter=Q(date=date)), Value(0)),
        'advance_of_date': Coalesce(Sum("advance", filter=Q(date=date)), Value(0)),
        'emp_cost_after_date': Coalesce(Sum(F("khoraki") + F("advance"), filter=Q(date__gt=date)), Value(0)),
        })

        if isViewer:
            agg_fields.update({
                "emp_salary_of_date":Coalesce(Sum(F("present") * F("current_salary"), filter=Q(date=date)), Value(0.0)),
            })
    
    return DailyRecordSnapshot.objects.filter(site=site).aggregate(**agg_fields)

def _get_sitework_aggregates(site, date, date_based=True, isViewer=True):
    agg_fields = {}
    
    if date_based:
        agg_fields.update({
        'session_count_of_date': Coalesce(Count("id", filter=Q(session_owner=True, created_date=date)), Value(0)),
        'session_pay_of_date': Coalesce(Sum("pay_or_return", filter=Q(session_owner=True, created_date=date)), Value(0.0)),
        'total_emp_cost': Coalesce(Sum(F("khoraki") + F("advance") + F("pay_or_return")), Value(0.0)),
        'pay_or_return_after_date': Coalesce(Sum(F("pay_or_return"), filter=Q(created_date__gt=date)), Value(0.0)),
        })

    else:
        agg_fields.update({
        'total_present': Coalesce(Sum(F("present")), Value(0.0)),
        'total_khoraki': Coalesce(Sum(F("khoraki")), Value(0)),
        'total_advance': Coalesce(Sum(F("advance")), Value(0)),
        'total_pay_or_return': Coalesce(Sum(F("pay_or_return")), Value(0.0)),
        'total_emp_salary': Coalesce(Sum(F("present") * F("session_salary")), Value(0.0)),
        })
    
    return SiteWorkRecord.objects.filter(site=site).aggregate(**agg_fields)
