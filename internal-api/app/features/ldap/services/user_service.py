from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ldap.models.filtered_response import FilteredList
from app.features.ldap.models.raw_user_data import RawUserData
from app.features.ldap.repositories.user_repo import UserRepository
from app.features.ldap.settings import DEPS
from typing import List
from app.features.ldap.models.ipa_formatted_user import IpaFormattedUser
class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session=session)
    async def return_filtered_users(self):
        # raw_users: list[RawUserData] =
        # # clean user repo
        # for user in raw_users:
        #     user.uid = str(user.uid).strip()
        #
        raw_dicts: list[dict] = await self.user_repo.load_users()
        raw_users: list[RawUserData] = [RawUserData(**u) for u in raw_dicts]
        users_to_add: List[IpaFormattedUser] = []
        users_to_disable: list[str] = []
        print(f"type: {type(raw_users)}")
        print(f"len: {len(raw_users)}")
        dep_lookup = {str(d["自動編號"]): d["group"] for d in DEPS}

        for user in raw_users:
            if user.employment_status == 2:
                users_to_disable.append(user.uid.strip())

            elif user.employment_status == 1:

                main_grp_name = dep_lookup.get(str(user.main_grp), "")
                other_grp_names = []

                if user.other_grp and user.other_grp != user.main_grp:
                    dep_ids = str(user.other_grp).split(",")
                    for dep_id in dep_ids:
                        dep_id = dep_id.strip()
                        if dep_id and dep_id in dep_lookup:
                            other_grp_names.append(dep_lookup[dep_id])

                users_to_add.append(
                    IpaFormattedUser(
                        uid="E" + str(user.uid.strip()) if user.uid is not None else "",
                        employeenumber=str(user.uid.strip()) if user.uid is not None else "",
                        cn=str(user.cn.strip()) if user.cn is not None else "",
                        givenname=self._split_chinese_name(user.cn.strip())[1]
                        if user.cn is not None
                        else "",
                        sn=self._split_chinese_name(user.cn.strip())[0] if user.cn else "",
                        pwd=self.decrypt_pwd(user.pwd) if user.pwd is not None else str(user.uid),
                        main_grp=main_grp_name,
                        main_grp_id=user.main_grp if user.main_grp else "0",
                        other_grp=other_grp_names,
                        other_grp_ids=str(user.other_grp).split(",") if str(user.other_grp) else [],
                        mail=str(user.uid).strip() + "@km.",
                        departmentnumber=user.main_grp if user.main_grp else "0"
                    ),
                )
        return FilteredList(users_to_disable=users_to_disable, users_to_add=users_to_add)


    @staticmethod
    def _split_chinese_name(full_name: str) -> tuple:
            """Split a Chinese name into a last name (surname) and first name based on length.

            Args
            -------
                full_name (str): The full Chinese name (e.g., "张伟", "欧阳修").

            Returns
            -------
                tuple: A tuple containing (last_name, first_name).
            """
            name_length = len(full_name)

            # For names with 2 characters
            if name_length == 2:  # noqa: PLR2004
                last_name = full_name[0]
                first_name = full_name[1]

            # For names with 3 characters
            elif name_length == 3:  # noqa: PLR2004
                # We assume single-character surnames are more common than double-character ones
                last_name = full_name[0]
                first_name = full_name[1:]

            # For names with 4 or more characters
            elif name_length >= 4:  # noqa: PLR2004
                # Double surnames are more likely here
                last_name = full_name[:2]
                first_name = full_name[2:]

            # For names with 1 character, it's ambiguous
            else:
                last_name = full_name
                first_name = ""

            return last_name, first_name

        # def _load_users_df(self) -> pd.DataFrame:
        #     df = pd.read_csv(self.users_csv)
        #     return self._clean_df(df)


