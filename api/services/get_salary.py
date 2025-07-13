def get_salary(promotions, work_date):
    for promo in reversed(promotions):
        if promo.date <= work_date:
            return promo.current_salary
    return 0