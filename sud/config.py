from datetime import timedelta

import yaml

from sud.exceptions import SudException


class Config:

    DEFAULT_FREQUENCY = 300

    def __init__(self, config_file):
        self._config = self._load_config(config_file)
        self._validate_config()

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

    def _load_config(self, config_file):
        try:
            return yaml.safe_load(config_file)
        except yaml.YAMLError as e:
            raise SudException(
                f"Invalid SUD configuration file: {str(e)}",
            ) from e

    def _validate_config(self):
        pass
