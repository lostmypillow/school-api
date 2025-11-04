import re
from pathlib import Path
import requests
from app.features.ldap.settings import settings
from app.features.ldap.models.ipa_formatted_user import IpaFormattedUser
import logging
logger = logging.getLogger(__name__)

STATUS_OK = 200


class LdapRepository:
    def __init__(self) -> None:
        self.host = settings.IPA_HOST.rstrip("/")
        self.admin_user = settings.IPA_USER
        self.admin_pass = settings.IPA_PASS
        self.ca_path = Path(settings.IPA_CA)
        self.json_url = f"{self.host}/ipa/session/json"
        self.login_url = f"{self.host}/ipa/session/login_password"
        self.login_headers = {"Referer": f"{self.host}/ipa"}
        self.call_headers = {"Referer": f"{self.host}/ipa", "Content-Type": "application/json"}
        self.session = requests.Session()

    def login(self) -> None:
        if not self.admin_pass:
            logger.info("Set IPA_ADMIN_PASS in env (admin password).")
            raise ValueError("IPA_ADMIN_PASS environment variable is required.")

        r = self.session.post(
            self.login_url,
            data={"user": self.admin_user, "password": self.admin_pass},
            headers=self.login_headers,
            verify=str(self.ca_path),
        )
        if r.status_code != STATUS_OK:
            logger.info(f"Login failed: HTTP {r.status_code}")
            raise RuntimeError(f"Login failed: HTTP {r.status_code}")

    def call(self, method: str, params_list, params_):  # noqa: ANN001, ANN201
        payload = {"method": method, "params": [params_list, params_]}
        # logger.info(f"payload: {pformat(payload, indent=2)}")

        r = self.session.post(
            self.json_url,
            json=payload,
            headers=self.call_headers,
            verify=str(self.ca_path),
        )
        if r.status_code != STATUS_OK:
            logger.info(f"IPA call {method} failed HTTP {r.status_code}: {r.text[:STATUS_OK]}")
            raise RuntimeError(f"IPA call {method} failed HTTP {r.status_code}: {r.text[:STATUS_OK]}")
        data = r.json()
        if data.get("error"):
            code = data["error"].get("code")
            msg = data["error"].get("message")
            logger.info(f"IPA error {code}: {msg}")
        return data.get("result")

    # --- Real IPA operations ---
    def add_user(
            self,
            user: IpaFormattedUser,
    ) -> None:
        """Add a given user to FreeIPA.

        For documentation on the commands used:
        - Main API reference: https://freeipa.readthedocs.io/en/ipa-4-11/api/index.html
        - "user_add": https://freeipa.readthedocs.io/en/ipa-4-11/api/user_add.html
        - "passwd": https://freeipa.readthedocs.io/en/ipa-4-11/api/passwd.html
        - "user_mod": https://freeipa.readthedocs.io/en/ipa-4-11/api/user_mod.html

        Parameters
        ----------
        user : IpaFormattedUser
            See `lib.user_dataclass`.
        """
        # Add initial data
        # We do not set  userPassword  here because FreeIPA would ask for password reset on first login.
        self.call(
            "user_add",
            [user.uid],
            {
                "cn": user.cn,
                "givenname": user.givenname,
                "sn": user.sn,
                "random": False,
                "employeenumber": user.employeenumber,
                "departmentnumber": user.departmentnumber,
                "ou": user.main_grp,
                "mail": user.mail,
            },
        )

        # Set password
        self.call("passwd", [user.uid], {"password": user.pwd})

        # Set password expiration to 2035
        self.call(
            "user_mod",
            [user.uid],
            {"setattr": ["krbPasswordExpiration=20380101000000Z"]},
        )
        # If user has a main group, aka department
        if user.main_grp:
            self.call("group_add_member", [str(user.main_grp)], {"user": [user.uid]})

        # If user has other groups
        if user.other_grp and user.other_grp_ids:
            for group in user.other_grp:
                self.call("group_add_member", [str(group)], {"user": [user.uid]})
            for group_id in user.other_grp_ids:
                attribute = f"departmentnumber={group_id}"
                self.call(
                    "user_mod",
                    [user.uid],
                    {"addattr": [attribute]},
                )

        logger.info(f"Created user {'E' + user.uid}, set password, and updated group membership.")

    def delete_user(self, uid: str) -> None:
        self.login()
        self.call("user_del", [uid], {"continue": True, "preserve": False})

    def check_user(self, uid: str):  # noqa: ANN201
        result = self.call("user_show", [uid], {"all": False, "raw": False})
        return isinstance(result, dict)

    def add_groups(self, groups_data: list[dict]) -> None:
        """
        Add a list of groups to FreeIPA.

        Parameters
        ----------
        groups_data : list[dict]
            A list of dictionaries, where each dictionary represents a group
            with 'group' and 'description' keys.
        """
        for group_info in groups_data:
            cn = group_info["group"]
            description = group_info["description"]
            # Use the 'group_add' command with cn, description, and nonposix
            self.call(
                "group_add",
                [cn],
                {
                    "description": description,
                    "nonposix": True,
                },
            )
            logger.info(f"Added group {cn} with desc of {description}")
        logger.info("All roups added successfully.")

    def _get_user_entry(self, uid: str) -> dict | None:
        """
        Return the user entry dict (attributes as lists) or None if not found.
        Tries user_show first (exact uid), then user_find filtered by uid.
        """
        self.login()

        # Try exact lookup
        entry = None
        show = self.call("user_show", [str(uid)], {"all": True, "raw": False})
        if isinstance(show, dict) and show.get("result"):
            entry = show["result"]

        # Fallback to search by uid (NO criteria dict; uid filter goes into options)
        if not entry:
            found = self.call(
                "user_find",
                [],
                {"uid": str(uid), "all": True, "sizelimit": 2}
            )
            items = (found or {}).get("result") or []
            entry = items[0] if items else None

        return entry

    def get_user_ou_number(self, uid: str) -> int | None:
        entry = self._get_user_entry(uid)
        if not entry:
            logger.info(f"User '{uid}' not found.")
            return None

        # Get OU value (attribute is usually a list, but take first)
        ou_attr = entry.get("ou")
        ou_val = None
        if isinstance(ou_attr, list) and ou_attr:
            ou_val = str(ou_attr[0])
        elif isinstance(ou_attr, str):
            ou_val = ou_attr

        # Fallback: parse DN if no ou attribute present
        if not ou_val:
            dn = entry.get("dn")
            if isinstance(dn, str):
                for part in dn.split(","):
                    p = part.strip()
                    if p.lower().startswith("ou="):
                        ou_val = p[3:]
                        break

        if not ou_val:
            return None

        # Extract number part
        match = re.search(r"\d+", ou_val)
        if match:
            return int(match.group())

        return None
