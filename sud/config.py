import os
from dataclasses import dataclass
from datetime import timedelta

import yaml

from sud.exceptions import SudException


@dataclass
class TelegramConfig:
    chat_id: int
    token: str


class Config:
    DEFAULT_FREQUENCY = 300

    def __init__(self, config_file):
        self._config_file = config_file
        self._config = {}

    @property
    def hostname(self) -> str:
        return self._config["hostname"]

    @hostname.setter
    def hostname(self, value: str) -> None:
        self._config["hostname"] = value

    @property
    def frequency(self) -> timedelta:
        return timedelta(
            seconds=int(self._config.get("frequency", Config.DEFAULT_FREQUENCY)),
        )

    @frequency.setter
    def frequency(self, value: timedelta) -> None:
        self._config["frequency"] = value.seconds

    @property
    def api_secret(self) -> str:
        return self._config["api_secret"]

    @api_secret.setter
    def api_secret(self, value: str) -> None:
        self._config["api_secret"] = value

    @property
    def telegram(self) -> TelegramConfig | None:
        tg = self._config.get("notifications", {}).get("telegram")
        if tg:
            return TelegramConfig(
                tg["chat_id"],
                tg["token"],
            )

    @telegram.setter
    def telegram(self, value: TelegramConfig) -> None:
        self._config["notifications"] = {
            "telegram": {
                "chat_id": value.chat_id,
                "token": value.token,
            },
        }

    def load(self):
        try:
            with open(self._config_file) as f:
                self._config = yaml.safe_load(f)
        except (OSError, yaml.YAMLError) as e:
            raise SudException(
                f"Cannot load the SUD configuration file: {str(e)}",
            ) from e

    def store(self):
        try:
            dirname = os.path.abspath(os.path.dirname(self._config_file))
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            with open(self._config_file, "w") as f:
                yaml.dump(self._config, f)
        except OSError as e:
            raise SudException(
                f"Cannot save the SUD configuration file: {str(e)}",
            ) from e

    def validate(self):  # pragma: no cover
        pass
