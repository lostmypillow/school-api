# /commands/check.py
import typer

from lib.ipa_client import IPAClient

ipa_client = IPAClient()


def check(
    uid: str = typer.Argument(..., help="uid in FreeIPA/LDAP"),
) -> None:
    """Check if the row's uid exists in FreeIPA."""
    typer.echo(f"{ipa_client.show_user(uid)}")
