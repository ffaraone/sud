import logging

import click
from click import Abort, ClickException, Option, UsageError
from rich.console import Console
from rich.logging import RichHandler

from sud.config import Config
from sud.updater import Updater

console = Console()


class MutuallyExclusiveOption(Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop("mutually_exclusive", []))
        help = kwargs.get("help", "")
        if self.mutually_exclusive:
            ex_str = ", ".join(self.mutually_exclusive)
            kwargs["help"] = help + (
                " NOTE: This option is mutually exclusive "
                f"with options: [{ex_str}]."
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise UsageError(
                f"Illegal usage: `{self.name}` is mutually exclusive with "
                f"options `{', '.join(self.mutually_exclusive)}`."
            )


@click.group()
@click.option(
    "-c",
    "--config-file",
    type=click.File("rb"),
    default="/etc/sud/sud-config.yml",
)
@click.pass_context
def cli(ctx, config_file):
    """
    SUD the Python Scaleway DNS Updater utility.
    """
    ctx.obj = Config(config_file)


@cli.command()
@click.pass_obj
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
    except ClickException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    except Abort:
        pass
    except Exception:
        console.print_exception()
