# mssql2freeipa/commands/add.py
import typer
from rich import print

from lib.csv_store import CSVStore
from lib.ipa_client import IPAClient

csv_store = CSVStore()
ipa_client = IPAClient()
add_app = typer.Typer(help="Commands for adding users and groups.")


@add_app.command()
def users() -> None:
    """Add all users from CSV to FreeIPA."""
    all_users = csv_store.load_all_users()
    ipa_client.login()
    for user in all_users:
        if ipa_client.check_user(uid=user.uid) is False:
            ipa_client.add_user(user=user)


@add_app.command()
def groups() -> None:
    """Add all groups from CSV to FreeIPA."""
    # This is where you would put the logic to add groups.
    # For example:
    # all_groups = csv_store.load_all_groups()
    # ipa_client.login()
    # for group in all_groups:
    #     if ipa_client.check_group(cn=group.cn) is False:
    #         ipa_client.add_group(group=group)
    all_deps = csv_store.load_all_deps()
    ipa_client.login()
    ipa_client.add_groups(all_deps)

