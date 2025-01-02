from ..database import execute_SQL
from datetime import datetime, timedelta




class Employee:
    def __init__(self, id):
        self.card_id = id
        self.picture = None

    @property
    def dep_number(self):
        return int(execute_SQL(
            'employee/department',
            'one',
            employee_id=self.card_id
        )[0])
