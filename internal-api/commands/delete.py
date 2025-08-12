# mssql2freeipa/commands/delete.py
import requests
import typer

from config import (
    USERS_CSV_PATH,
    ipa_call,
    ipa_login,
    load_row,
)


def delete(
    row_index: int = typer.Argument(..., help="0-based row index in CSV"),
    csv_path: str = typer.Option(USERS_CSV_PATH, "--csv"),
):
    """Delete one user from CSV by row index."""
    row = load_row(csv_path, row_index)
    uid = row["uid"]
    s = requests.Session()
    ipa_login(s)
    ipa_call(s, "user_del", [uid], {"continue": True, "preserve": False})
    typer.echo(f"Deleted user {uid}")
