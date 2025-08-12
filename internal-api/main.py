import typer

from commands.check import check
from commands.hello import hello

app = typer.Typer(help="FreeIPA: check/add/delete a single user from a CSV row")
app.command()(check)
app.command()(hello)

if __name__ == "__main__":
    app()
