import typer

from commands.add import add_app
from commands.check import check
from commands.delete import delete

app = typer.Typer(help="FreeIPA: check/add/delete a single user from a CSV row")
app.command()(check)
app.add_typer(add_app, name="add")
app.command()(delete)

if __name__ == "__main__":
    app()
