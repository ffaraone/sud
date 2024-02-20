from datetime import timedelta

import pytest
import yaml

from sud.config import Config
from sud.exceptions import SudException


def test_load_basic_config(mocker, config_file_factory):
    config_file = config_file_factory()
    safe_load = mocker.patch(
        "sud.config.yaml.safe_load",
        return_value=config_file,
    )
    fake_file_obj = mocker.MagicMock()

    c = Config(fake_file_obj)

    safe_load.assert_called_once_with(fake_file_obj)
    assert c.hostname == config_file["hostname"]
    assert c.api_secret == config_file["api_secret"]
    assert isinstance(c.frequency, timedelta)
    assert c.frequency.seconds == Config.DEFAULT_FREQUENCY
    assert c.telegram is None


def test_load_full_config(
    mocker, config_file_factory, telegram_config_factory
):
    telegram_config = telegram_config_factory()
    config_file = config_file_factory(
        frequency=123,
        notifications={"telegram": telegram_config},
    )
    safe_load = mocker.patch(
        "sud.config.yaml.safe_load",
        return_value=config_file,
    )
    fake_file_obj = mocker.MagicMock()

    c = Config(fake_file_obj)

    safe_load.assert_called_once_with(fake_file_obj)
    assert c.hostname == config_file["hostname"]
    assert c.api_secret == config_file["api_secret"]
    assert isinstance(c.frequency, timedelta)
    assert c.frequency.seconds == 123
    assert c.telegram == telegram_config


def test_yaml_parse_error(mocker):
    mocker.patch(
        "sud.config.yaml.safe_load",
        side_effect=yaml.YAMLError("parse error"),
    )
    fake_file_obj = mocker.MagicMock()

    with pytest.raises(SudException) as raised:
        Config(fake_file_obj)

    assert (
        raised.value.message == "Invalid SUD configuration file: parse error"
    )
