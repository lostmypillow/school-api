from app.database.operations import fetch_one_sql


def get_dep_number(card_id):
    return int(fetch_one_sql(
        'employee/department',
        employee_id=card_id
    )[0])
