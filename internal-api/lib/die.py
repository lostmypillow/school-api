from typing import Never

import typer


def _die(msg: str) -> Never:
    typer.echo(msg)
