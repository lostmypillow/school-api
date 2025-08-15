from pathlib import Path
from pprint import pformat

import requests
import typer

from config import IPA_CA, IPA_HOST, IPA_PASS, IPA_USER
from lib.user_dataclass import UserData

STATUS_OK = 200


class IPAClient:
    def __init__(
        self,
        host: str = IPA_HOST,
        admin_user: str = IPA_USER,
        admin_pass: str = IPA_PASS,
        ca_path: Path = IPA_CA,
    ) -> None:
        self.host = host.rstrip("/")
        self.admin_user = admin_user
        self.admin_pass = admin_pass
        self.ca_path = Path(ca_path)
        self.json_url = f"{self.host}/ipa/session/json"
        self.login_url = f"{self.host}/ipa/session/login_password"
        self.login_headers = {"Referer": f"{self.host}/ipa"}
        self.call_headers = {"Referer": f"{self.host}/ipa", "Content-Type": "application/json"}
        self.session = requests.Session()

    def login(self) -> None:
        if not self.admin_pass:
            typer.echo("Set IPA_ADMIN_PASS in env (admin password).")
            raise typer.Exit()

        r = self.session.post(
            self.login_url,
            data={"user": self.admin_user, "password": self.admin_pass},
            headers=self.login_headers,
            verify=str(self.ca_path),
        )
        if r.status_code != STATUS_OK:
            typer.echo(f"Login failed: HTTP {r.status_code}")
            raise typer.Exit()

    def call(self, method: str, params_list, params_):  # noqa: ANN001, ANN201
        payload = {"method": method, "params": [params_list, params_]}
        typer.echo(f"payload: {pformat(payload, indent=2)}")

        r = self.session.post(
            self.json_url,
            json=payload,
            headers=self.call_headers,
            verify=str(self.ca_path),
        )
        if r.status_code != STATUS_OK:
            typer.echo(f"IPA call {method} failed HTTP {r.status_code}: {r.text[:STATUS_OK]}")
            raise typer.Exit()
        data = r.json()
        if data.get("error"):
            code = data["error"].get("code")
            msg = data["error"].get("message")
            typer.echo(f"IPA error {code}: {msg}")
        return data.get("result")

    # --- Real IPA operations ---
    def add_user(
        self,
        user: UserData,
    ) -> None:
        """Add a given user to FreeIPA.

        For documentation on the commands used:
        - Main API reference: https://freeipa.readthedocs.io/en/ipa-4-11/api/index.html
        - "user_add": https://freeipa.readthedocs.io/en/ipa-4-11/api/user_add.html
        - "passwd": https://freeipa.readthedocs.io/en/ipa-4-11/api/passwd.html
        - "user_mod": https://freeipa.readthedocs.io/en/ipa-4-11/api/user_mod.html

        Parameters
        ----------
        user : UserData
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

        typer.echo(f"Created user {'E' + user.uid}, set password, and updated group membership.")

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
            typer.echo(f"Added group {cn} with desc of {description}")
        typer.echo("All roups added successfully.")
