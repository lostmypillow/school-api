from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ldap.models.filtered_response import FilteredList
from app.features.ldap.models.raw_user_data import RawUserData
from app.features.ldap.repositories.source_repo import SourceRepository
from app.features.ldap.settings import DEPS
from typing import List
from app.features.ldap.models.ipa_formatted_user import IpaFormattedUser
class SourceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = SourceRepository(session=session)

    async def return_modified_users(self) -> FilteredList:
        # raw_users: list[RawUserData] =
        # # clean user repo
        # for user in raw_users:
        #     user.uid = str(user.uid).strip()
        #
        raw_dicts: list[dict] = await self.user_repo.load_users()
        raw_users: list[RawUserData] = [RawUserData(**u) for u in raw_dicts]
        users_to_add: List[IpaFormattedUser] = []
        users_to_disable: List[IpaFormattedUser] = []
        # print(f"type: {type(raw_users)}")
        # print(f"len: {len(raw_users)}")
        dep_lookup = {str(d["自動編號"]): d["group"] for d in DEPS}

        for raw_user in raw_users:
                main_grp_name = dep_lookup.get(str(raw_user.main_grp), "")
                other_grp_names = []

                if raw_user.other_grp and raw_user.other_grp != raw_user.main_grp:
                    # print(raw_user.uid)
                    dep_ids = str(raw_user.other_grp).split(",")
                    for dep_id in dep_ids:
                        dep_id = dep_id.strip()
                        if dep_id and dep_id in dep_lookup and dep_lookup[dep_id] is not None:

                            other_grp_names.append(dep_lookup[dep_id])
                formatted_user = IpaFormattedUser(
                        uid="e" + str(raw_user.uid.strip()) if raw_user.uid is not None else "",
                        employeenumber=str(raw_user.uid.strip()) if raw_user.uid is not None else "",
                        cn=str(raw_user.cn.strip()) if raw_user.cn is not None else "",
                        givenname=self._split_chinese_name(raw_user.cn.strip())[1]
                        if raw_user.cn is not None
                        else "",
                        sn=self._split_chinese_name(raw_user.cn.strip())[0] if raw_user.cn else "",
                        pwd=self.decrypt_pwd(raw_user.pwd.strip()) if raw_user.pwd is not None else str(raw_user.uid).strip(),
                        main_grp=main_grp_name,
                        main_grp_id=raw_user.main_grp if raw_user.main_grp else "0",
                        other_grp=other_grp_names,
                        other_grp_ids=str(raw_user.other_grp).split(",") if raw_user.other_grp is not None else [],
                        mail=str(raw_user.uid).strip() + "@km.",
                        departmentnumber=raw_user.main_grp if raw_user.main_grp else "0"
                    )
                if raw_user.employment_status == 2:
                    users_to_disable.append(formatted_user)
                elif raw_user.employment_status == 1:
                    users_to_add.append(formatted_user)
        return FilteredList(users_to_disable=users_to_disable, users_to_add=users_to_add)
