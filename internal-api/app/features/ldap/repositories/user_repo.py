import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.features.ldap.settings import DEPS
from app.features.ldap.models.ipa_formatted_user import IpaFormattedUser
from app.database.exec_sql import exec_sql



class UserRepository:

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

    async def transform_dict_to_ldap(self) -> list[IpaFormattedUser]:
        raw_users: list[dict] = await self.load_users()
        deps = DEPS
        user_list: List[IpaFormattedUser] = []

        # Pre-build a lookup dictionary for quick access
        dep_lookup = {str(d["自動編號"]): d["group"] for d in deps}

        for row in raw_users:

            main_grp_name = dep_lookup.get(str(row["main_grp"]), "")
            other_grp_names = []

            if row.get("other_grp") and row["other_grp"] != row["main_grp"]:
                dep_ids = str(row["other_grp"]).split(",")
                for dep_id in dep_ids:
                    dep_id = dep_id.strip()
                    if dep_id and dep_id in dep_lookup:
                        other_grp_names.append(dep_lookup[dep_id])

            user_list.append(
                IpaFormattedUser(
                    uid="E" + str(row["uid"]) if pd.notna(row.get("uid")) else "",
                    employeenumber=str(row["uid"]) if pd.notna(row.get("uid")) else "",
                    cn=str(row["cn"]) if pd.notna(row.get("cn")) else "",
                    givenname=self._split_chinese_name(row["cn"])[1]
                    if pd.notna(row.get("cn"))
                    else "",
                    sn=self._split_chinese_name(row["cn"])[0] if pd.notna(row.get("cn")) else "",
                    pwd=self.decrypt_pwd(row["pwd"]) if pd.notna(row.get("pwd")) else str(row["uid"]),
                    main_grp=main_grp_name,
                    main_grp_id=row["main_grp"] if row["main_grp"] else "0",
                    other_grp=other_grp_names,
                    other_grp_ids=str(row["other_grp"]).split(",") if str(row["other_grp"]) else [],
                    mail=str(row["uid"]) + "@km.",
                    departmentnumber=row["main_grp"] if row["main_grp"] else "0"
                ),
            )

        return user_list




    @staticmethod
    def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
        null_sentinels = {"null", "nan", "none", ""}

        return df.map(
            lambda x: (
                None
                if (
                        x is None
                        or (isinstance(x, float) and pd.isna(x))
                        or (isinstance(x, str) and x.strip().lower() in null_sentinels)
                )
                else (x.strip() if isinstance(x, str) else x)
            ),
        )


