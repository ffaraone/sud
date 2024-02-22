import logging

from rich.console import Console
from rich.logging import RichHandler

from sud import click as click
from sud import config, get_version
from sud.updater import Updater

console = Console()


@click.group()
@click.option(
    "-c",
    "--config-file",
    type=click.Path(
        dir_okay=False,
        readable=True,
        writable=True,
    ),
    default="/etc/sud/sud-config.yml",
    help="Load the configuration file from a specific location.",
)
@click.version_option(get_version())
@config.pass_config
def cli(ctx, config_file):
    """
    SUD the Python Scaleway DNS Updater utility.
    """


@cli.command(load_config=False)
# @click.option(
#     "-H",
#     "--hostname",
#     required=True,
#     prompt="[cyan]Hostname[/cyan]",
# )
# @click.option(
#     "-s",
#     "--api-secret",
#     required=True,
#     prompt="[cyan]Scaleway API secret[/cyan]",
#     hide_input=True,
#     confirmation_prompt=True,
# )
@click.option(
    "-s",
    "--frequency",
    required=True,
    prompt="Check frequency",
    default=300,
    show_default=True,
)
@config.pass_config
def init(config, frequency):
    pass


@cli.command()
@config.pass_config
def run(config):
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
    updater = Updater(config)
    updater.run()


def main():
    try:
        cli(standalone_mode=False)
    except click.ClickException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except click.Abort:
        pass
    except Exception:
        console.print_exception()
