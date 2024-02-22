import copy
from typing import Any, Callable, List

from click.types import Choice, ParamType, convert_type
from rich import print
from rich.console import Console
from rich.prompt import Confirm, DefaultType, InvalidResponse
from rich.prompt import Prompt as _Prompt
from rich.text import Text


def confirm(
    text: str,
    default: bool | None = False,
):
    return Confirm.ask(text, default=default)


class Prompt(_Prompt):

    def __init__(
        self,
        prompt: str | Text = "",
        *,
        console: Console | None = None,
        password: bool = False,
        choices: List[str] | None = None,
        show_default: bool = True,
        show_choices: bool = True,
        value_proc: Callable[[str], Any] | None = None,
    ) -> None:
        self.value_proc = value_proc
        super().__init__(
            prompt,
            console=console,
            password=password,
            choices=choices,
            show_default=show_default,
            show_choices=show_choices,
        )

    def make_prompt(self, default: DefaultType) -> Text:
        prompt = self.prompt.copy()
        prompt.end = ""

        if self.show_choices and self.choices:
            _choices = "/".join(self.choices)
            choices = f"[{_choices}]"
            prompt.append(" ")
            prompt.append(choices, "prompt.choices")

        if default != ... and self.show_default:
            prompt.append(" ")
            _default = self.render_default(default)
            prompt.append(_default)

        prompt.append(self.prompt_suffix)

        return prompt

    def process_response(self, value: str) -> str:
        value = value.strip()
        try:
            return_value = self.value_proc(value) if self.value_proc else value
        except ValueError:
            raise InvalidResponse(self.validate_error_message)

        if self.choices is not None and not self.check_choice(value):
            raise InvalidResponse(self.illegal_choice_message)

        return return_value


def prompt(
    text: str,
    default: Any | None = None,
    hide_input: bool = False,
    confirmation_prompt: bool | str = False,
    type: ParamType | Any | None = None,
    value_proc: Callable[[str], Any] | None = None,
    prompt_suffix: str = ": ",
    show_default: bool = True,
    err: bool = False,
    show_choices: bool = True,
    default_is_missing: bool = True,
):
    if value_proc is None:
        value_proc = convert_type(type, default)

    prompt_kwargs: dict[str, Any] = {
        "prompt": text,
        "password": hide_input,
        "show_default": show_default,
        "show_choices": show_choices,
        "value_proc": value_proc,
    }

    if type is not None and show_choices and isinstance(type, Choice):
        prompt_kwargs["choices"] = type.choices

    if confirmation_prompt:
        if confirmation_prompt is True:
            confirmation_prompt = "Repeat for confirmation"

        prompt2_kwargs = copy.copy(prompt_kwargs)
        prompt2_kwargs["prompt"] = confirmation_prompt

    prompt = Prompt(**prompt_kwargs)
    prompt.prompt_suffix = prompt_suffix
    prompt.value_proc = value_proc

    while True:
        value = prompt(default=default if not default_is_missing else ...)

        if not confirmation_prompt:
            return value

        prompt2 = Prompt(**prompt2_kwargs)
        prompt2.prompt_suffix = prompt_suffix

        while True:
            value2 = prompt2(
                default=default if not default_is_missing else ...,
            )
            is_empty = not value and not value2
            if value2 or is_empty:
                break

        if value == value2:
            return value

        print("Error: The two entered values do not match.")
