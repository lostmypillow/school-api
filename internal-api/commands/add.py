# mssql2freeipa/commands/add.py
import typer

from lib.csv_store import CSVStore
from lib.ipa_client import IPAClient
from rich import print
csv_store = CSVStore()
ipa_client = IPAClient()
def add(
) -> None:
    """Simulate adding exactly one user from CSV — just prints actions for now."""
    # user = csv_store.load_row(row_index=row_index)
    # ipa_client.add_user(user=user)
    all_users = csv_store.load_all_users()
    ipa_client.login()
    for user in all_users:
        if ipa_client.check_user(uid=user.uid) is False:
            ipa_client.add_user(user=user)
