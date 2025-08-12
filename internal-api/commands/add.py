# mssql2freeipa/commands/add.py
import pandas as pd
import typer

from config import (
    DEPS_CSV_PATH,
    IPA_HOST,
    IPA_USER,
    USERS_CSV_PATH,
    decrypt_pwd,
    load_row,
)


def add(
    row_index: int = typer.Argument(..., help="0-based row index in CSV"),
) -> None:
    """Simulate adding exactly one user from CSV — just prints actions for now."""
    row = load_row(USERS_CSV_PATH, row_index)
    uid, cn = row["uid"], row["cn"]

    # choose plaintext password
    plaintext = decrypt_pwd(row["pwd"]) if not plaintext and row["pwd"] else row["uid"]

    dep_df = pd.read_csv(DEPS_CSV_PATH)

    main_grp_id: int = 0
    dep_row = dep_df.loc[dep_df["自動編號"] == int(row["main_grp"]), "group"]

    if not dep_row.empty:
        main_grp_id = dep_row.iloc[0]
        typer.echo(main_grp_id)
    else:
        typer.echo(f"No group found for 自動編號 {dep_df["自動編號"]}")

    typer.echo(f"[DRY RUN] Would log in to IPA server at {IPA_HOST} with admin user {IPA_USER}")
    typer.echo(f"[DRY RUN] Would create user {uid} with:")
    typer.echo(f"  - CN: {cn}")
    typer.echo(f"  - Given name: {cn}")
    typer.echo(f"  - Surname: {cn}")
    typer.echo(f"  - Password: {plaintext}")
    typer.echo("[DRY RUN] Would set password via IPA (Kerberos-ready)")
    if row["main_grp"] == row["other_grp"] or row["other_grp"] is None:
        typer.echo(
            f"[DRY RUN] Would add to main group {row['main_grp']}, other_grp is duplicate or None",
        )
    else:
        typer.echo(
            f"[DRY RUN] Would add to main group {row['main_grp']} and other group {row['other_grp']}",  # noqa: E501
        )
