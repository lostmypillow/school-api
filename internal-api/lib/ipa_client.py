from pathlib import Path
from pprint import pformat

import requests
import typer

from config import IPA_CA, IPA_HOST, IPA_PASS, IPA_USER
from lib.csv_store import UserData
from lib.die import _die

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
        self.session = requests.Session()

    def login(self) -> None:
        if not self.admin_pass:
            _die("Set IPA_ADMIN_PASS in env (admin password).")
        headers = {"Referer": f"{self.host}/ipa"}
        r = self.session.post(
            self.login_url,
            data={"user": self.admin_user, "password": self.admin_pass},
            headers=headers,
            verify=str(self.ca_path),
        )
        if r.status_code != STATUS_OK:
            _die(f"Login failed: HTTP {r.status_code}")

    def call(self, method: str, params_list, params_):  # noqa: ANN001, ANN201
        headers = {"Referer": f"{self.host}/ipa", "Content-Type": "application/json"}
        payload = {"method": method, "params": [params_list, params_]}
        typer.echo(f"headers: {pformat(headers, indent=2)}")
        typer.echo(f"payload: {pformat(payload, indent=2)}")

        r = self.session.post(
            self.json_url,
            json=payload,
            headers=headers,
            verify=str(self.ca_path),
        )
        if r.status_code != STATUS_OK:
            _die(f"IPA call {method} failed HTTP {r.status_code}: {r.text[:STATUS_OK]}")
        data = r.json()
        if data.get("error"):
            code = data["error"].get("code")
            msg = data["error"].get("message")
            _die(f"IPA error {code}: {msg}")
        return data.get("result")

    # --- Real IPA operations ---
    def add_user(
        self,
        user: UserData,
    ) -> None:
        self.call(
            "user_add",
            [user.uid],
            {
                "cn": user.cn,
                "givenname": user.givenname,
                "sn": user.sn,
                "random": False,
            },
        )
        self.call("user_mod", [user.uid], {"mail": user.mail})

        self.call("passwd", [user.uid], {"password": user.pwd})
        self.call(
            "user_mod",
            [user.uid],
            {"setattr": ["krbPasswordExpiration=20380101000000Z"]},
        )
        if user.main_grp:
            self.call("group_add_member", [str(user.main_grp)], {"user": [user.uid]})
        if user.other_grp:
            for group in user.other_grp:
                self.call("group_add_member", [str(group)], {"user": [user.uid]})
        typer.echo(f"Created user {'' + user.uid}, set password, and updated group membership.")

    def delete_user(self, uid: str) -> None:
        self.login()
        self.call("user_del", [uid], {"continue": True, "preserve": False})

    def check_user(self, uid: str):  # noqa: ANN201
        result = self.call("user_show", [uid], {"all": False, "raw": False})
        return isinstance(result, dict)
