import logging
from datetime import timedelta
from pathlib import Path
from typing import Annotated, Optional, Tuple

import typer
from rich import print
from rich.logging import RichHandler

from sud import get_version
from sud.config import Config, TelegramConfig
from sud.prompt import APISecretPrompt, HostnamePrompt
from sud.updater import Updater

app = typer.Typer(
    add_completion=False,
    rich_markup_mode="rich",
)


def version_callback(value: bool):
    if value:
        print(f"[bold dark_orange]SUD[/] version: {get_version()}")
        raise typer.Exit()


def validate_frequency_callback(value: int):
    if value < 60:
        raise typer.BadParameter("Minimum frequency is once per minutes (60 seconds).")
    return value


@app.command()
def init(
    ctx: typer.Context,
    hostname: Annotated[
        Optional[str],
        typer.Option(
            "--hostname",
            "-H",
            show_default=False,
            help="Hostname that must be created/updated.",
        ),
    ] = None,
    api_secret: Annotated[
        Optional[str],
        typer.Option(
            "--api-secret",
            "-s",
            show_default=False,
            help="Scaleway API secret.",
        ),
    ] = None,
    frequency: Annotated[
        Optional[int],
        typer.Option(
            "--frequency",
            "-f",
            callback=validate_frequency_callback,
            help="Number of seconds between checks.",
        ),
    ] = 300,
    telegram: Annotated[
        Optional[Tuple[int, str]],
        typer.Option(
            "--telegram-notifications",
            "-t",
            metavar="CHAT_ID TOKEN",
            help="Add telegram configuration for notifications.",
        ),
    ] = (None, None),
):
    """Generate a SUD configuration file."""
    if not hostname:
        hostname = HostnamePrompt.ask(
            "Enter the hostname that must be created or update",
        )

    if not api_secret:
        api_secret = APISecretPrompt.ask(
            "Enter the Scaleway API secret",
            password=True,
        )

    config: Config = ctx.obj
    config.hostname = hostname
    config.api_secret = api_secret
    config.frequency = timedelta(seconds=frequency)
    if telegram != (None, None):
        config.telegram = TelegramConfig(
            telegram[0],
            telegram[1],
        )
    config.store()


@app.command()
def run(ctx: typer.Context):
    """Run the [magenta][link=https://scaleway.com]Scaleway[/link][/magenta] \
DNS Updater."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
    updater = Updater(ctx.obj)
    updater.run()


@app.callback()
def main(
    ctx: typer.Context,
    config_file: Annotated[
        Optional[Path],
        typer.Option(
            "--config-file",
            "-c",
            help="Load the configuration file from a specific location.",
        ),
    ] = "/etc/sud/sud-config.yml",
    version: Annotated[
        Optional[bool],
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
):
    """
    [bold dark_orange]SUD[/] is a small DDNS updater utility for the
    Scaleway DNS service.
    It periodically (default: 300 seconds) check for the IP public IP
    address from through the utility goes to internet
    and create or update a [cyan]Host (A)[/] record in the DNS zone of the
    specified domain name.
    """
    config = Config(config_file)
    ctx.obj = config
    if ctx.invoked_subcommand != "init":
        config.load()
