from datetime import timedelta

import pytest
import yaml

from sud.config import Config
from sud.exceptions import SudException


def test_load_basic_config(mocker, config_file_factory):
    config_file = config_file_factory()
    m_safe_load = mocker.patch(
        "sud.config.yaml.safe_load",
        return_value=config_file,
    )
    file_obj = mocker.MagicMock()
    m_open_ctxt_mgr = mocker.MagicMock()
    m_open_ctxt_mgr.__enter__.return_value = file_obj
    m_open = mocker.patch("sud.config.open", return_value=m_open_ctxt_mgr)
    c = Config("config.yml")
    c.load()
    m_open.assert_called_once_with("config.yml", "r")
    m_safe_load.assert_called_once_with(file_obj)
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
    m_safe_load = mocker.patch(
        "sud.config.yaml.safe_load",
        return_value=config_file,
    )
    file_obj = mocker.MagicMock()
    m_open_ctxt_mgr = mocker.MagicMock()
    m_open_ctxt_mgr.__enter__.return_value = file_obj
    m_open = mocker.patch("sud.config.open", return_value=m_open_ctxt_mgr)
    c = Config("config.yml")
    c.load()
    m_open.assert_called_once_with("config.yml", "r")
    m_safe_load.assert_called_once_with(file_obj)

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
    mocker.patch("sud.config.open")
    c = Config("config.yml")

    with pytest.raises(SudException) as raised:
        c.load()

    assert (
        raised.value.message == "Invalid SUD configuration file: parse error"
    )
