# mssql2freeipa/commands/delete.py
import typer

from lib.ipa_client import IPAClient

ipa_client = IPAClient()

def delete(
    uid: str = typer.Argument(..., help="UID of the person to delete"),
) -> None:
    """Delete one user from CSV by row index."""
    ipa_client.delete_user(uid=uid)
    typer.echo(f"Deleted user with uid {uid} with no problems.")
