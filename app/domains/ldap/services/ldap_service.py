# app/features/ldap/services/ldap_service.py

import logging
from typing import List


from app.domains.ldap.schemas.ipa_formatted_user import IpaFormattedUser
from app.domains.ldap.repositories.ldap_repo import LdapRepository
from app.domains.ldap.services.source_service import SourceService
DEPS: dict = {
    "教務處": 2,
    "學務處": 4,
    "總務處": 8,
    "研發處": 9,
    "圖書館": 11,
            }

logger = logging.getLogger(__name__)


class LdapService:
    """High-level logic for user and group operations in FreeIPA."""

    def __init__(self) -> None:
        self.ldap_repo = LdapRepository()
        self.source_service = SourceService()


    async def sync_all_employees(self) -> List[str]:
        """
        Sync all employees from MSSQL → FreeIPA.

        Creates or updates as needed, then syncs group memberships.
        """
        logger.info("Starting full user synchronization process.")

        employees = await self.source_service.return_modified_employees()
        logger.debug(
            f"Fetched modified employees from source: "
            f"{len(employees.employees_to_add)} to add/update, "
            f"{len(employees.employees_to_disable)} to disable."
        )
        # return

        added_or_updated = []
        actual_added_or_updated = 0
        actual_disabled = 0
        actual_not_modified = 0
        for user_to_add in employees.employees_to_add:
            logger.info(f"Processing addition/update for user '{user_to_add.uid}'.")
            try:
                await self.add_or_update_user(user_to_add)
                added_or_updated.append(user_to_add.uid)
                actual_added_or_updated += 1
            except Exception as e:
                logger.exception(f"Failed to add or update user '{user_to_add.uid}': {e}")

        for user_to_disable in employees.employees_to_disable:
            try:
                exists, locked = await self.ldap_repo.check_user_exists(user_to_disable.uid)
                if exists:
                    logger.info("Disabling user %s", user_to_disable.uid)
                    await self.ldap_repo.disable_user(user_to_disable.uid)
                    actual_disabled += 1
                else:
                    logger.info(
                        f"Skipping '{user_to_disable.uid}' — not found in FreeIPA."
                    )
                    actual_not_modified += 1
            except Exception as e:
                logger.exception(f"Failed to disable user '{user_to_disable.uid}': {e}")


        logger.info(
            f"Sync summary: {actual_added_or_updated} added/updated, "
            f"{actual_disabled} disabled, {actual_not_modified} not modified."
        )

        return added_or_updated

    async def add_or_update_user(self, user: IpaFormattedUser):
        """
        Add a new user or overwrite existing user attributes in FreeIPA.
        Also synchronizes groups, preserving protected groups.
        """
        logger.debug(f"Starting add/update for user '{user.uid}'.")
        try:
            exists, locked = await self.ldap_repo.check_user_exists(user.uid)

            if exists:
                if locked:
                    logger.info(f"User '{user.uid}' exists but is locked — re-enabling.")
                    await self.ldap_repo.enable_user(user.uid)
                logger.info(f"Updating existing user '{user.uid}'.")
                await self.ldap_repo.update_user(user)
            else:
                logger.info(f"Creating new user '{user.uid}'.")
                await self.ldap_repo.create_user(user)

            await self._set_password_expiration(user.uid)

            if user.other_grp:
                protected_groups = ["full_time", "ipaemployees", "openproject"]
                await self._sync_groups_with_protection(
                    user.uid,
                    [str(g) for g in user.other_grp],
                    protected_groups,
                )

            if user.main_grp:
                logger.debug(f"Re-adding main group '{user.main_grp}' for user '{user.uid}'.")
                await self.ldap_repo.add_user_to_group(user.uid, str(user.main_grp))

            logger.info(f"Completed sync for user '{user.uid}'.")
        except Exception as e:
            logger.exception(f"Error while adding/updating user '{user.uid}': {e}")

    async def delete_user(self, uid: str) -> None:
        """Delete one user from FreeIPA."""
        logger.info(f"Deleting user '{uid}'.")
        try:
            await self.ldap_repo.delete_user(uid=uid)
            logger.info(f"Successfully deleted user '{uid}'.")
        except Exception as e:
            logger.exception(f"Failed to delete user '{uid}': {e}")

    async def add_all_groups(self) -> List[str]:
        """Add all departments/groups defined in settings to FreeIPA."""
        logger.info("Adding all configured groups to FreeIPA.")
        created_groups = []
        for dep in DEPS:
            try:
                await self.ldap_repo.add_group(dep["group"], dep["description"])
                created_groups.append(dep["group"])
                logger.debug(f"Added group '{dep['group']}'.")
            except Exception as e:
                logger.warning(f"Failed to add group '{dep['group']}': {e}")
        logger.info(f"Created groups: {created_groups}")
        return created_groups

    async def check_user_exists(self, uid: str) -> tuple[bool, bool]:
        """Check if user exists in FreeIPA."""
        logger.debug(f"Checking if user '{uid}' exists.")
        try:
            return await self.ldap_repo.check_user_exists(uid)
        except Exception as e:
            logger.exception(f"Error checking existence of user '{uid}': {e}")
            return False, False

    # -------------------------
    # Internal helpers
    # -------------------------

    async def _sync_groups_with_protection(
        self,
        uid: str,
        target_groups: List[str],
        protected_groups: List[str],
    ) -> None:
        """Add/remove user from groups except protected ones."""
        logger.debug(f"Syncing group memberships for user '{uid}'.")
        try:
            current_groups = set(await self.ldap_repo.get_user_groups(uid))
            target_groups = set(target_groups)
            protected_groups = set(protected_groups)

            to_add = target_groups - current_groups
            to_remove = (current_groups - target_groups) - protected_groups

            for g in to_add:
                try:
                    await self.ldap_repo.add_user_to_group(uid, g)
                    logger.info(f"Added '{uid}' to group '{g}'.")
                except Exception as e:
                    logger.warning(f"Failed to add '{uid}' to group '{g}': {e}")

            for g in to_remove:
                try:
                    await self.ldap_repo.remove_user_from_group(uid, g)
                    logger.info(f"Removed '{uid}' from group '{g}'.")
                except Exception as e:
                    logger.warning(f"Failed to remove '{uid}' from group '{g}': {e}")

        except Exception as e:
            logger.exception(f"Group sync failed for user '{uid}': {e}")

    async def _set_password_expiration(self, uid: str) -> None:
        """Standardize password expiration date."""
        logger.debug(f"Setting password expiration for user '{uid}'.")
        try:
            await self.ldap_repo.call(
                "user_mod",
                [uid],
                {"setattr": ["krbPasswordExpiration=20380101000000Z"]},
            )
        except Exception as e:
            logger.warning(f"Failed to set password expiration for '{uid}': {e}")
