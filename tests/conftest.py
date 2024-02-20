import pytest
import responses

from sud.config import Config


@pytest.fixture()
def requests_mocker():
    """
    `requests` mocker.
    """
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture()
def config_file_factory():
    def _config(
        hostname="my.host.name",
        api_secret="my-secret-key",
        frequency=None,
        notifications=None,
    ):
        config_file = {}
        if hostname:
            config_file["hostname"] = hostname
        if api_secret:
            config_file["api_secret"] = api_secret
        if frequency:
            config_file["frequency"] = frequency
        if notifications:
            config_file["notifications"] = notifications

        return config_file

    return _config


@pytest.fixture()
def telegram_config_factory():
    def _telegram(
        token="my-bot-token",
        chat_id=-1234567890,
    ):
        data = {}
        if token:
            data["token"] = token
        if chat_id:
            data["chat_id"] = chat_id

        return data

    return _telegram


@pytest.fixture()
def config(mocker, config_file_factory, telegram_config_factory):
    config_file = config_file_factory(
        notifications={"telegram": telegram_config_factory},
    )
    mocker.patch.object(Config, "_load_config", return_value=config_file)
    return Config(mocker.MagicMock())
