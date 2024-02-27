from datetime import timedelta

import pytest
import yaml

from sud.config import Config, TelegramConfig
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
    m_open.assert_called_once_with("config.yml")
    m_safe_load.assert_called_once_with(file_obj)
    assert c.hostname == config_file["hostname"]
    assert c.api_secret == config_file["api_secret"]
    assert isinstance(c.frequency, timedelta)
    assert c.frequency.seconds == Config.DEFAULT_FREQUENCY
    assert c.telegram is None


def test_load_full_config(mocker, config_file_factory, telegram_config_factory):
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
    m_open.assert_called_once_with("config.yml")
    m_safe_load.assert_called_once_with(file_obj)

    assert c.hostname == config_file["hostname"]
    assert c.api_secret == config_file["api_secret"]
    assert isinstance(c.frequency, timedelta)
    assert c.frequency.seconds == 123
    assert c.telegram == TelegramConfig(**telegram_config)


@pytest.mark.parametrize("exc", [OSError, yaml.YAMLError])
def test_load_exceptions(mocker, exc):
    mocker.patch(
        "sud.config.yaml.safe_load",
        side_effect=exc("msg"),
    )
    mocker.patch("sud.config.open")
    c = Config("config.yml")

    with pytest.raises(SudException) as raised:
        c.load()

    assert raised.value.message == ("Cannot load the SUD configuration file: msg")
    assert isinstance(raised.value.__cause__, exc)


def test_store_config_dir_exists(mocker):
    file_obj = mocker.MagicMock()
    m_open_ctxt_mgr = mocker.MagicMock()
    m_open_ctxt_mgr.__enter__.return_value = file_obj
    m_open = mocker.patch("sud.config.open", return_value=m_open_ctxt_mgr)
    m_dump = mocker.patch("sud.config.yaml.dump")
    mocker.patch("sud.config.os.path.exists", return_value=True)

    c = Config("/dir/config.yml")
    c.hostname = "a.host.name"
    c.frequency = timedelta(seconds=200)
    c.api_secret = "a-super-duper-secret"
    c.store()

    m_open.assert_called_once_with("/dir/config.yml", "w")
    m_dump.assert_called_once_with(
        {
            "hostname": "a.host.name",
            "frequency": 200,
            "api_secret": "a-super-duper-secret",
        },
        file_obj,
    )


def test_store_config_create_dir(mocker):
    file_obj = mocker.MagicMock()
    m_open_ctxt_mgr = mocker.MagicMock()
    m_open_ctxt_mgr.__enter__.return_value = file_obj
    m_open = mocker.patch("sud.config.open", return_value=m_open_ctxt_mgr)
    m_dump = mocker.patch("sud.config.yaml.dump")
    mocker.patch("sud.config.os.path.exists", return_value=False)
    m_makedirs = mocker.patch("sud.config.os.makedirs")

    c = Config("/dir/config.yml")
    c.hostname = "a.host.name"
    c.frequency = timedelta(seconds=200)
    c.api_secret = "a-super-duper-secret"
    c.store()

    m_open.assert_called_once_with("/dir/config.yml", "w")
    m_dump.assert_called_once_with(
        {
            "hostname": "a.host.name",
            "frequency": 200,
            "api_secret": "a-super-duper-secret",
        },
        file_obj,
    )
    m_makedirs.assert_called_once_with("/dir")


def test_store_exception(mocker):
    mocker.patch("sud.config.os.path.exists", return_value=True)
    mocker.patch("sud.config.open", side_effect=OSError("msg"))

    c = Config("/dir/config.yml")
    c.hostname = "a.host.name"
    c.frequency = timedelta(seconds=200)
    c.api_secret = "a-super-duper-secret"
    with pytest.raises(SudException) as raised:
        c.store()

    assert raised.value.message == ("Cannot save the SUD configuration file: msg")
