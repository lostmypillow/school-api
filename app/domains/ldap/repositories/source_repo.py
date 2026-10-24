from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exec_sql import exec_sql


async def load_employees() -> List[dict]:
    """
    Load all employees from the database.
    Executes `app/database/sql/get_all_employees.sql` via exec_sql.
    """
    employees = await exec_sql(command_name="ldap/ldap_get_all_employees")
    return employees or []


class SourceRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session



