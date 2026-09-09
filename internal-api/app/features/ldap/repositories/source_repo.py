from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.new_exec_sql import exec_sql


class SourceRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def load_users(self) -> List[dict]:
        """
        Load all users from the database.
        Executes `app/database/sql/get_all_users.sql` via exec_sql.
        """
        users = await exec_sql(
            mode="all",
            command_name="ldap_get_all_users",
            session=self.session,
        )
        return users or []



