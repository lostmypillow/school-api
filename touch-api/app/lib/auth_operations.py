from app.database.operations import fetch_one_sql, fetch_all_sql, commit_sql
from datetime import datetime


def check_existence(student_id: str, class_id, name):
    # def getStudentName(self, id):
    try:
        details = fetch_one_sql(
            'student_details',
            card_id=student_id
        )

        return False if details is None else {
            "student_id": student_id,
            "name": details[1].strip(),
            "gender": 'female' if details[2] == '女' else 'male'
        }
    except Exception as e:
        print(e)
        return False


def check_match(class_name, student_id: str):
    match_class = fetch_all_sql(
        'student_match_class',
        student_id=student_id
    )
    return False if match_class[0][0] != class_name else True


def check_already_selected(class_id, student_id: str):
    already_selected = fetch_all_sql(
        'student_already_selected',
        class_id=class_id,
        student_id=student_id
    )
    return True if already_selected != [] else False


# def dep_name_from_num(target_value):
    


def check_rateable_employees(student_id: str):
    #  def GetVotedEmployeeByStudentIdWeekly(self, student_id):
    today = datetime.now()
    today = datetime(2020, 9, 16).date()
    weekday = today.weekday()
    # monday = (today - timedelta(days=weekday)).strftime("%Y-%m-%d")
    monday = '2020-12-15 00:00:00.000'
    employees_working_today = fetch_all_sql(
        'student_today_employees',
        'all',
        current_date='2020-09-16'
    )
    voted_employees = [x[0].strip() for x in fetch_all_sql(
        'student_voted_employees',
        monday=monday,
        student_id=student_id
    )]
    rateable_employees = [
        {
            "id": data[0].strip(),
            "name": data[1].strip(),
            "department_number": data[2],
            "department_name": dep_name_from_num(data[2])
        } for data in employees_working_today if data[0].strip() not in voted_employees
    ]
    return rateable_employees if rateable_employees is not [] else None