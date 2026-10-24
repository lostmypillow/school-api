import asyncio
import logging
from pathlib import Path

import requests_async as requests
from requests_async import AsyncSession

from app.domains.ldap.schemas.ipa_formatted_user import IpaFormattedUser
from app.domains.ldap.settings import settings

logger = logging.getLogger(__name__)
STATUS_OK = 200


class LdapRepository:
    """Handles direct FreeIPA API communication (supports DRY_RUN mode)."""

    def __init__(self) -> None:
        self.host = settings.IPA_HOST.rstrip("/")
        self.admin_user = settings.IPA_USER
        self.admin_pass = settings.IPA_ADMIN_PASS
        self.ca_path = Path(settings.IPA_CA)
        self.json_url = f"{self.host}/ipa/session/json"
        self.login_url = f"{self.host}/ipa/session/login_password"
        self.login_headers = {"Referer": f"{self.host}/ipa"}
        self.call_headers = {
            "Referer": f"{self.host}/ipa",
            "Content-Type": "application/json",
        }
        self.dry_run = settings.DRY_RUN



    async def login(self, session: AsyncSession):
        """Authenticate unless DRY_RUN is enabled."""
        if self.dry_run:
            logger.debug("Skipping login (DRY_RUN mode).")
            return

        if not self.admin_pass:
            error_message = "IPA_ADMIN_PASS environment variable is missing."
            logger.error(error_message)
            raise ValueError(error_message)

        logger.debug(f"Attempting FreeIPA login for user '{self.admin_user}'.")
        try:
            r = await session.post(
                self.login_url,
                data={"user": self.admin_user, "password": self.admin_pass},
                headers=self.login_headers,
            )
            if r.status_code != STATUS_OK:
                logger.error(f"FreeIPA login failed (HTTP {r.status_code}).")
                raise RuntimeError(f"FreeIPA login failed: HTTP {r.status_code}")
            logger.debug("FreeIPA login successful.")

        except Exception as e:
            logger.exception(e)


    async def call(self, method: str, params_list, params_):
        """Perform a JSON-RPC call to the FreeIPA API (or simulate in DRY_RUN mode)."""
        await asyncio.sleep(1)
        payload = {"method": method, "params": [params_list, params_]}
        logger.debug(f"Preparing FreeIPA call: method={method}, payload={payload}")
        # Real call
        try:
            async with requests.AsyncSession(verify=str(self.ca_path)) as session:
                await self.login(session=session)
                r = await session.post(
                    self.json_url,
                    json=payload,
                    headers=self.call_headers,
                )
                if r.status_code != STATUS_OK:
                    logger.error(f"IPA call '{method}' failed (HTTP {r.status_code}).")
                    raise RuntimeError(f"IPA call {method} failed HTTP {r.status_code}")
                data = r.json()
                if data.get("error"):
                    err_msg = data["error"].get("message", "Unknown IPA error")
                    logger.error(f"IPA call '{method}' returned error: {err_msg}")
                    return ""
                logger.debug(f"IPA call '{method}' successful.")
                return data.get("result")
        except Exception as e:
            logger.exception(f"Exception during IPA call '{method}': {e}")
            raise

    # --- Low-level FreeIPA operations ---
    async def check_user_exists(self, uid: str) -> tuple[bool, bool]:
        """Return True if the user exists, False otherwise."""
        logger.debug(f"Checking if user '{uid}' exists in FreeIPA.")
        # if self.dry_run:
        #     scenarios = [
        #         (True, False),
        #         (True, True),
        #         (False, False),
        #     ]
        #     simulated = random.choice(scenarios)
        #     exists, locked = simulated
        #     if exists and locked:
        #         logger.info(f"[DRY_RUN] Simulating: user {uid} exists but is DISABLED.")
        #     elif exists:
        #         logger.info(f"[DRY_RUN] Simulating: user {uid} exists and is ACTIVE.")
        #     else:
        #         logger.info(f"[DRY_RUN] Simulating: user {uid} does NOT exist.")
        #     return simulated


        try:
            result = await self.call("user_show", [uid], {"all": True})
            if isinstance(result, str):
                return False, False

            user_data = result.get("result")
            if not user_data:
                logger.debug(f"User '{uid}' not found in FreeIPA.")
                return False, False
            locked = user_data.get("nsaccountlock", False)
            logger.debug(f"User '{uid}' found. Locked={locked}")
            return True, locked
        except Exception as e:
            if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                logger.debug(f"User '{uid}' not found (exception message matched).")
                return False, False
            logger.exception(f"Error checking existence for user '{uid}': {e}")
            raise

    async def create_user(self, user: IpaFormattedUser) -> None:
        """Create a new user (no checks)."""
        logger.info(f"Creating user '{user.uid}'.")

        try:
            await self.call(
                "user_add",
                [user.uid],
                {
                    "cn": user.cn,
                    "givenname": user.givenname,
                    "sn": user.sn,
                    "employeenumber": user.employeenumber,
                    "departmentnumber": user.departmentnumber,
                    "ou": user.main_grp,
                    "mail": user.mail,
                    "random": False,
                },
            )
            await self.call("passwd", [user.uid], {"password": user.pwd})
            logger.debug(f"User '{user.uid}' creation completed successfully.")
        except Exception as e:
            logger.exception(f"Failed to create user '{user.uid}': {e}")
            raise

    async def update_user(self, user: IpaFormattedUser) -> None:
        """Modify existing user attributes."""
        logger.info(f"Updating user '{user.uid}'.")

        try:
            await self.call(
                "user_mod",
                [user.uid],
                {
                    "setattr": [
                        f"cn={user.cn}",
                        f"givenname={user.givenname}",
                        f"sn={user.sn}",
                        f"employeenumber={user.employeenumber}",
                        f"departmentnumber={user.departmentnumber}",
                        f"ou={user.main_grp}",
                        f"mail={user.mail}",
                    ]
                },
            )
            await self.call("passwd", [user.uid], {"password": user.pwd})
            logger.debug(f"User '{user.uid}' updated successfully.")
        except Exception as e:
            logger.exception(f"Failed to update user '{user.uid}': {e}")
            raise

    async def delete_user(self, uid: str) -> None:
        """Delete a user."""
        logger.info(f"Deleting user '{uid}'.")

        try:
            await self.call("user_del", [uid], {"continue": True, "preserve": False})
            logger.debug(f"User '{uid}' deleted successfully.")
        except Exception as e:
            logger.exception(f"Failed to delete user '{uid}': {e}")
            raise

    async def get_user_groups(self, uid: str) -> set[str]:
        """Return a set of group names the user belongs to."""
        logger.debug(f"Fetching groups for user '{uid}'.")

        try:
            result = await self.call("user_show", [uid], {"all": True})
            groups = result["result"].get("memberof_group", [])
            logger.debug(f"User '{uid}' belongs to groups: {groups}")
            return set(groups)
        except Exception as e:
            logger.exception(f"Failed to get groups for user '{uid}': {e}")
            raise

    async def add_user_to_group(self, uid: str, group: str) -> None:
        """Add user to a group."""
        logger.info(f"Adding user '{uid}' to group '{group}'.")

        try:
            await self.call("group_add_member", [group], {"user": [uid]})
            logger.debug(f"User '{uid}' added to group '{group}'.")
        except Exception as e:
            logger.exception(f"Failed to add user '{uid}' to group '{group}': {e}")
            raise

    async def remove_user_from_group(self, uid: str, group: str) -> None:
        """Remove user from a group."""
        logger.info(f"Removing user '{uid}' from group '{group}'.")

        try:
            await self.call("group_remove_member", [group], {"user": [uid]})
            logger.debug(f"User '{uid}' removed from group '{group}'.")
        except Exception as e:
            logger.exception(f"Failed to remove user '{uid}' from group '{group}': {e}")
            raise

    async def add_group(self, group_name: str, description: str) -> None:
        """Create a group."""
        logger.info(f"Creating group '{group_name}'.")

        try:
            await self.call("group_add", [group_name], {"description": description, "nonposix": True})
            logger.debug(f"Group '{group_name}' created successfully.")
        except Exception as e:
            logger.exception(f"Failed to create group '{group_name}': {e}")
            raise

    async def disable_user(self, uid: str) -> None:
        """Disable a user account (lock it instead of deleting)."""
        logger.info(f"Disabling user '{uid}'.")

        try:
            await self.call("user_mod", [uid], {"nsaccountlock": True})
            logger.info(f"User '{uid}' has been disabled in FreeIPA.")
        except Exception as e:
            logger.exception(f"Failed to disable user '{uid}': {e}")
            raise

    async def enable_user(self, uid: str) -> None:
        """Re-enable a previously disabled user account."""
        logger.info(f"Re-enabling user '{uid}'.")

        try:
            await self.call("user_mod", [uid], {"nsaccountlock": False})
            logger.info(f"User '{uid}' has been re-enabled in FreeIPA.")
        except Exception as e:
            logger.exception(f"Failed to enable user '{uid}': {e}")
            raise
