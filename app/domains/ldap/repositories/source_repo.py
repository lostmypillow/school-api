from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exec_mssql_async import exec_mssql_async


async def load_users() -> List[dict]:
    """
    Load all users from the database.
    Executes `app/database/sql/get_all_users.sql` via exec_sql.
    """
    users = await exec_mssql_async(command_name="ldap/ldap_get_all_users")
    return users or []


class SourceRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session



