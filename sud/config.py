from datetime import timedelta
from functools import update_wrapper

import yaml
from click import pass_context

from sud.exceptions import SudException


class Config:

    DEFAULT_FREQUENCY = 300

    def __init__(self, config_file):
        self._config_file = config_file
        self._config = None

    @property
    def hostname(self) -> str:
        return self._config["hostname"]

    @property
    def frequency(self) -> timedelta:
        return timedelta(
            seconds=int(
                self._config.get("frequency", Config.DEFAULT_FREQUENCY)
            ),
        )

    @property
    def api_secret(self) -> str:
        return self._config["api_secret"]

    @property
    def telegram(self) -> dict | None:
        return self._config.get("notifications", {}).get("telegram")

    def load(self):
        try:
            with open(self._config_file, "r") as f:
                self._config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise SudException(
                f"Invalid SUD configuration file: {str(e)}",
            ) from e

    def validate(self):
        pass


def pass_config(f):
    @pass_context
    def new_func(ctx, *args, **kwargs):
        obj = ctx.find_object(Config)
        if not obj:
            ctx.obj = obj = Config(ctx.params["config_file"])
        return ctx.invoke(f, obj, *args, **kwargs)

    return update_wrapper(new_func, f)
