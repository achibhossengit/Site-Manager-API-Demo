def get_salary(promotions, work_date):
    # promotions order : desending
    for promo in promotions:
        if promo.date <= work_date:
            return promo.current_salary
    return 0