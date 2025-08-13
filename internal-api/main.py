import typer

from commands.add import add
from commands.check import check
from commands.delete import delete

app = typer.Typer(help="FreeIPA: check/add/delete a single user from a CSV row")
app.command()(check)
app.command()(add)
app.command()(delete)

if __name__ == "__main__":
    app()
