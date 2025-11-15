from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Value, F, Q
from django.db.models.functions import Coalesce
from site_profiles.models import SiteCost, SiteCash, SiteBill
from daily_records.models import DailyRecord, DailyRecordSnapshot, SiteWorkRecord

# chanage this module name from get_site_summary.py -> site_summary.py 


def get_site_summary(site, user_type):
    today_date = timezone.localdate()
    yesterday_date = today_date - timedelta(days=1)
    
    # Determine what data to fetch based on user type
    include_detailed_totals = user_type == "viewer"
    
    # Fetch all aggregates
    bill_agg = _get_bill_aggregates(site) if include_detailed_totals else None
    cash_agg = _get_cash_aggregates(site, today_date, yesterday_date)
    cost_agg = _get_cost_aggregates(site, today_date, yesterday_date)
    records_agg = _get_records_aggregates(site, today_date, yesterday_date, include_detailed_totals)
    snapshot_agg = _get_snapshot_aggregates(site, today_date, yesterday_date, include_detailed_totals)
    sitework_agg = _get_sitework_aggregates(site, today_date, yesterday_date, include_detailed_totals)
    
    # extract values from aggregation
    # today's
    today_cash = cash_agg["today_total"]
    today_eq_cost = cost_agg["today_st_total"] # st -> eq_cost(equipment_cost)
    today_other_cost = cost_agg["today_ot_total"]
    today_site_cost = today_eq_cost + today_other_cost
    
    today_session_count= sitework_agg["today_session_count"]
    today_present = records_agg["today_present"] + snapshot_agg["today_present"]
    today_emp_count = records_agg["today_emp_count"] + snapshot_agg["today_emp_count"]
    today_khoraki = records_agg["today_khoraki"] + snapshot_agg["today_khoraki"]
    today_advance = records_agg["today_advance"] + snapshot_agg["today_advance"]
    today_session_payment = sitework_agg["today_pay"]
    today_emp_cost = today_khoraki + today_advance + today_session_payment

    today_total_cost = today_site_cost + today_emp_cost

    # yesterday's
    yesterday_cash = cash_agg["yesterday_total"]
    yesterday_eq_cost = cost_agg["yesterday_st_total"] # st -> eq_cost(equipment_cost)
    yesterday_other_cost = cost_agg["yesterday_ot_total"]
    yesterday_site_cost = yesterday_eq_cost + yesterday_other_cost

    yesterday_session_count = sitework_agg["yesterday_session_count"]
    yesterday_present = records_agg["yesterday_present"] + snapshot_agg["yesterday_present"]
    yesterday_emp_count = records_agg["yesterday_emp_count"] + snapshot_agg["yesterday_emp_count"]
    yesterday_khoraki = records_agg["yesterday_khoraki"] + snapshot_agg["yesterday_khoraki"]
    yesterday_advance = records_agg["yesterday_advance"] + snapshot_agg["yesterday_advance"]
    yesterday_session_payment = sitework_agg['yesterday_pay']
    yesterday_emp_cost = yesterday_khoraki + yesterday_advance + yesterday_session_payment
    
    yesterday_total_cost = yesterday_site_cost + yesterday_emp_cost

    # totals
    total_cash = cash_agg["total"]
    total_eq_cost = cost_agg["st_total"]
    total_other_cost = cost_agg["ot_total"]
    total_site_cost = total_eq_cost + total_other_cost

    emp_cost_from_dailyrecords = records_agg["total_emp_cost"]
    emp_cost_from_siteworkrecords = sitework_agg['total_pay']
    total_emp_cost = emp_cost_from_dailyrecords + emp_cost_from_siteworkrecords

    total_cost = total_site_cost + total_emp_cost

    # balance
    today_balance = total_cash - total_cost
    yesterday_balance = total_cash - total_cost + today_total_cost

    # payload
    today_summary = {
        "eq_cost": today_eq_cost,
        "other_cost": today_other_cost,

        "present": today_present,
        "khoraki": today_khoraki,
        "advance": today_advance,
        "session_payment": today_session_payment,
        "session_created": today_session_count,
        "emp_count": today_emp_count,

        "site_cash": today_cash,
        "total_cost": today_total_cost,
        "balance": today_balance,
    }

    yesterday_summary = {
        "eq_cost": yesterday_eq_cost,
        "other_cost": yesterday_other_cost,

        "present": yesterday_present,
        "emp_count": yesterday_emp_count,
        "khoraki": yesterday_khoraki,
        "advance": yesterday_advance,
        "session_payment": yesterday_session_payment,
        "session_created": yesterday_session_count,

        "site_cash": yesterday_cash,
        "total_cost": yesterday_total_cost,
        "balance": yesterday_balance,
    }
    
    # Build response
    summary = {"today_summary": today_summary, "yesterday_summary": yesterday_summary}
    
    if include_detailed_totals:
        today_emp_salary = records_agg["today_emp_salary"] + snapshot_agg["today_emp_salary"]
        yesterday_emp_salary = records_agg["yesterday_emp_salary"] + snapshot_agg["yesterday_emp_salary"]
        total_emp_salary = records_agg["total_emp_salary"] + sitework_agg["total_emp_salary"]

        total_present = records_agg["total_present"] + sitework_agg["total_present"]
        actual_total_cost = total_site_cost + total_emp_salary
        total_bill = bill_agg["total"]
        profit = total_bill - actual_total_cost
        
        total_summary = {
            "site_cash": total_cash,
            "eq_cost": total_eq_cost,
            "other_cost": total_other_cost,
            "site_cost": total_site_cost, # eq_cost + other_cost

            "present": total_present,
            "emp_cost": total_emp_cost,            
            "total_cost": total_cost,
            "balance": today_balance,

            "site_bill": total_bill,
            "emp_salary": total_emp_salary,
            "actual_cost": actual_total_cost,
            "profit": profit,
        }

        summary["total_summary"] = total_summary
        summary["today_summary"]["emp_salary"] = today_emp_salary
        summary["yesterday_summary"]["emp_salary"] = yesterday_emp_salary
    
    return summary


def _get_bill_aggregates(site):
    return SiteBill.objects.filter(site=site).aggregate(
        total=Coalesce(Sum("amount"), Value(0)),
    )

def _get_cash_aggregates(site, today, yesterday):
    return SiteCash.objects.filter(site=site).aggregate(
        today_total=Coalesce(Sum("amount", filter=Q(date=today)), Value(0)),
        yesterday_total=Coalesce(Sum("amount", filter=Q(date=yesterday)), Value(0)),
        total=Coalesce(Sum("amount"), Value(0)),
    )

def _get_cost_aggregates(site, today, yesterday):
    agg_fields = {
        'today_st_total': Coalesce(Sum("amount", filter=Q(type="st", date=today)), Value(0)),
        'today_ot_total': Coalesce(Sum("amount", filter=Q(type="ot", date=today)), Value(0)),
        'yesterday_st_total': Coalesce(Sum("amount", filter=Q(type="st", date=yesterday)), Value(0)),
        'yesterday_ot_total': Coalesce(Sum("amount", filter=Q(type="ot", date=yesterday)), Value(0)),
        'st_total': Coalesce(Sum("amount", filter=Q(type="st")), Value(0)),
        'ot_total': Coalesce(Sum("amount", filter=Q(type="ot")), Value(0)),
    }
    return SiteCost.objects.filter(site=site).aggregate(**agg_fields)

def _get_records_aggregates(site, today, yesterday, include_detailed_totals):
    agg_fields = {
        'today_present': Coalesce(Sum("present", filter=Q(date=today)), Value(0.0)),
        'today_emp_count': Coalesce(Count("employee", filter=Q(date=today, present__gt=0), distinct=True), Value(0)),
        'today_khoraki': Coalesce(Sum("khoraki", filter=Q(date=today)), Value(0)),
        'today_advance': Coalesce(Sum("advance", filter=Q(date=today)), Value(0)),

        'yesterday_present': Coalesce(Sum("present", filter=Q(date=yesterday)), Value(0.0)),
        'yesterday_emp_count': Coalesce(Count("employee", filter=Q(date=yesterday, present__gt=0), distinct=True), Value(0)),
        'yesterday_khoraki': Coalesce(Sum("khoraki", filter=Q(date=yesterday)), Value(0)),
        'yesterday_advance': Coalesce(Sum("advance", filter=Q(date=yesterday)), Value(0)),

        'total_present': Coalesce(Sum("present"), Value(0.0)),
        'total_emp_cost': Coalesce(Sum(F("khoraki") + F("advance")), Value(0)),
    }

    if include_detailed_totals:
        agg_fields.update({
            'today_emp_salary': Coalesce(Sum(F("present") * F("employee__current_salary"), filter=Q(date=today)), Value(0.0)),
            'yesterday_emp_salary': Coalesce(Sum(F("present") * F("employee__current_salary"), filter=Q(date=yesterday)), Value(0.0)),
            'total_emp_salary': Coalesce(Sum(F("present") * F("employee__current_salary")), Value(0.0)),
        })

    return DailyRecord.objects.filter(site=site).aggregate(**agg_fields)

def _get_snapshot_aggregates(site, today, yesterday, include_detailed_totals):
    agg_fields = {
        'today_present': Coalesce(Sum("present", filter=Q(date=today)), Value(0.0)),
        'today_emp_count': Coalesce(Count("employee", filter=Q(date=today, present__gt=0), distinct=True), Value(0)),
        'today_khoraki': Coalesce(Sum("khoraki", filter=Q(date=today)), Value(0)),
        'today_advance': Coalesce(Sum("advance", filter=Q(date=today)), Value(0)),

        'yesterday_present': Coalesce(Sum("present", filter=Q(date=yesterday)), Value(0.0)),
        'yesterday_emp_count': Coalesce(Count("employee", filter=Q(date=yesterday, present__gt=0), distinct=True), Value(0)),
        'yesterday_khoraki': Coalesce(Sum("khoraki", filter=Q(date=yesterday)), Value(0)),
        'yesterday_advance': Coalesce(Sum("advance", filter=Q(date=yesterday)), Value(0)),
    }
    
    if include_detailed_totals:
        agg_fields.update({
            "today_emp_salary":Coalesce(Sum(F("present") * F("current_salary"), filter=Q(date=today)), Value(0.0)),
            "yesterday_emp_salary":Coalesce(Sum(F("present") * F("current_salary"), filter=Q(date=yesterday)), Value(0.0)),
        })
    
    return DailyRecordSnapshot.objects.filter(site=site).aggregate(**agg_fields)

def _get_sitework_aggregates(site, today, yesterday, include_detailed_totals):
    agg_fields = {
        'today_session_count': Coalesce(Count("id", filter=Q(session_owner=True, created_date=today)), Value(0)),
        'today_pay': Coalesce(Sum("pay_or_return", filter=Q(session_owner=True, created_date=today)), Value(0.0)),
        'yesterday_session_count': Coalesce(Count("id", filter=Q(session_owner=True, created_date=yesterday)), Value(0)),
        'yesterday_pay': Coalesce(Sum("pay_or_return", filter=Q(session_owner=True, created_date=yesterday)), Value(0.0)),

        'total_pay': Coalesce(Sum(F("khoraki") + F("advance") + F("pay_or_return")), Value(0.0)),
    }
    
    if include_detailed_totals:
        agg_fields.update({
            # 'total_session_count' : Coalesce(Count("id", filter=Q(session_owner=True)), Value(0)),
            'total_present': Coalesce(Sum("present"), Value(0.0)),
            'total_emp_salary': Coalesce(Sum(F("present") * F("session_salary")),Value(0.0)),
        })
    
    return SiteWorkRecord.objects.filter(site=site).aggregate(**agg_fields)
