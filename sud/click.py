# flake8: noqa: F401
from typing import Any, Sequence

import rich_click
from click.types import ParamType
from rich_click import Context as Context
from rich_click import Abort as Abort
from rich_click import ClickException as ClickException
from rich_click import Path as Path
from rich_click import version_option as version_option

from sud.prompt import confirm, prompt


class SudOption(rich_click.Option):
    def __init__(
        self,
        param_decls: Sequence[str] | None = None,
        show_default: bool | str | None = None,
        prompt: bool | str = False,
        confirmation_prompt: bool | str = False,
        prompt_required: bool = True,
        hide_input: bool = False,
        is_flag: bool | None = None,
        flag_value: Any | None = None,
        multiple: bool = False,
        count: bool = False,
        allow_from_autoenv: bool = True,
        type: ParamType | Any | None = None,
        help: str | None = None,
        hidden: bool = False,
        show_choices: bool = True,
        show_envvar: bool = False,
        **attrs: Any,
    ) -> None:
        self.default_is_missing = "default" not in attrs
        super().__init__(
            param_decls,
            show_default,
            prompt,
            confirmation_prompt,
            prompt_required,
            hide_input,
            is_flag,
            flag_value,
            multiple,
            count,
            allow_from_autoenv,
            type,
            help,
            hidden,
            show_choices,
            show_envvar,
            **attrs,
        )

    def prompt_for_value(self, ctx: Context) -> Any:
        assert self.prompt is not None

        # Calculate the default before prompting anything to be stable.
        default = self.get_default(ctx)
        # If this is a prompt for a flag we need to handle this
        # differently.
        if self.is_bool_flag:
            return confirm(self.prompt, default)

        return prompt(
            self.prompt,
            default=default,
            type=self.type,
            hide_input=self.hide_input,
            show_choices=self.show_choices,
            confirmation_prompt=self.confirmation_prompt,
            value_proc=lambda x: self.process_value(ctx, x),
            default_is_missing=self.default_is_missing,
        )


class MutuallyExclusiveOption(SudOption):
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
            raise rich_click.UsageError(
                f"Illegal usage: `{self.name}` is mutually exclusive with "
                f"options `{', '.join(self.mutually_exclusive)}`."
            )


class SudCommand(rich_click.Command):
    def __init__(self, *args, **kwargs):
        self.load_config = kwargs.pop("load_config", True)
        super().__init__(*args, **kwargs)

    def invoke(self, ctx):
        if self.load_config:
            ctx.obj.load()
        return super().invoke(ctx)


class SudGroup(rich_click.Group):
    def command(self, *args, **kwargs):
        from rich_click.decorators import command

        kwargs["cls"] = SudCommand

        def decorator(f):
            cmd = command(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd

        return decorator

    def group(self, *args, **kwargs):
        from rich_click.decorators import group

        kwargs["cls"] = SudGroup

        def decorator(f):
            cmd = group(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd

        return decorator


def group(name=None, **attrs):
    attrs.setdefault("cls", SudGroup)
    return rich_click.command(name, **attrs)


def option(
    *param_decls: str,
    **attrs: Any,
):
    attrs.setdefault("cls", SudOption)
    return rich_click.option(
        *param_decls,
        **attrs,
    )


def mutually_exclusive_option(
    *param_decls: str,
    **attrs: Any,
):
    attrs.setdefault("cls", MutuallyExclusiveOption)
    return rich_click.option(
        *param_decls,
        **attrs,
    )
