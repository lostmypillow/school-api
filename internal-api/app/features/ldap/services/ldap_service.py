# app/features/ldap/services/ldap_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ldap.repositories.ldap_repo import LdapRepository
from app.features.ldap.repositories.user_repo import UserRepository
from app.features.ldap.settings import DEPS
import logging
logger = logging.getLogger(__name__)

class LdapService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.ldap_repo = LdapRepository()
        self.user_repo = UserRepository(session=session)  # will later load from MSSQL

    async def add_all_users(self) -> List[str]:
        """Add all users from MSSQL to FreeIPA."""
        users = await self.user_repo.transform_dict_to_ldap()
        self.ldap_repo.login()
        added_users = []

        for user in users:
            if not self.ldap_repo.check_user(uid=user.uid):
                self.ldap_repo.add_user(user=user)
                added_users.append(user.uid)

        logger.info(f"Added {len(added_users)} users.")
        return added_users

    def add_all_groups(self) -> List[str]:
        """Add all groups to FreeIPA."""
        deps = DEPS
        self.ldap_repo.login()
        self.ldap_repo.add_groups(deps)
        return [d["group"] for d in deps]

    def delete_user(self, uid: str) -> None:
        """Delete one user from FreeIPA."""
        self.ldap_repo.delete_user(uid=uid)

    def check_user_exists(self, uid: str) -> bool:
        """Check if user exists in FreeIPA."""
        return self.ldap_repo.check_user(uid)

    def get_user_ou_number(self, uid: str) -> Optional[int]:
        """Return OU number for the user."""
        return self.ldap_repo.get_user_ou_number(uid)
