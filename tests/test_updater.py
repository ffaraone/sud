import logging
from urllib.parse import urljoin

import pytest
import telegram
from requests import RequestException
from responses import matchers

from sud.config import Config
from sud.constants import (
    CHECK_IP_ADDRESS,
    SCALEWAY_API_BASE_URL,
    TG_CREATED_MSG,
    TG_UPDATED_MSG,
)
from sud.exceptions import SudException
from sud.updater import ARecordInfo, Updater


def test_arecord_info_from_hostname():
    info = ARecordInfo.from_hostname("test.example.com")

    assert isinstance(info, ARecordInfo)
    assert info.name == "test"
    assert info.domain == "example.com"
    assert info.ttl == 300

    info2 = ARecordInfo.from_hostname("example.com")
    assert info2.name == ""
    assert info2.domain == "example.com"

    info3 = ARecordInfo.from_hostname("x.y.z.example.com")
    assert info3.name == "x.y.z"
    assert info3.domain == "example.com"

    with pytest.raises(SudException) as raised:
        ARecordInfo.from_hostname("xxxx")

    assert raised.value.message == "Invalid hostname: xxxx"

    with pytest.raises(SudException) as raised:
        ARecordInfo.from_hostname(None)

    assert raised.value.message == "Hostname is required"


def test_get_dns_name():
    info = ARecordInfo.from_hostname("test.example.com")
    assert info.get_dns_name() == "test.example.com."

    info2 = ARecordInfo.from_hostname("example.com")
    assert info2.get_dns_name() == "example.com."


def test_discover_address(requests_mocker):
    requests_mocker.get(
        CHECK_IP_ADDRESS,
        body="1.2.3.4",
    )

    assert Updater.discover_address() == "1.2.3.4"


def test_discover_address_fail(requests_mocker):
    requests_mocker.get(
        CHECK_IP_ADDRESS,
        status=500,
    )

    with pytest.raises(SudException) as raised:
        Updater.discover_address()

    assert raised.value.message == (
        "Cannot determine current public ip address: "
        "500 Server Error: Internal Server Error for "
        "url: https://checkip.amazonaws.com/."
    )


def test_init(config):
    upd = Updater(config)
    assert upd._config == config


def test_get_record_found(requests_mocker, config):
    info = ARecordInfo.from_hostname(config.hostname)

    requests_mocker.get(
        urljoin(
            SCALEWAY_API_BASE_URL,
            f"dns-zones/{info.domain}/records",
        ),
        status=200,
        match=[
            matchers.header_matcher({"X-Auth-Token": config.api_secret}),
            matchers.query_param_matcher(
                {
                    "type": "A",
                    "name": info.name,
                },
            ),
        ],
        json={
            "records": [
                {
                    "name": info.name,
                    "ttl": 300,
                    "data": "1.2.3.4",
                },
            ],
        },
    )

    upd = Updater(config)
    result = upd.get_record()

    assert isinstance(result, ARecordInfo)
    assert result.name == "my"
    assert result.domain == "host.name"
    assert result.ttl == 300
    assert result.address == "1.2.3.4"


@pytest.mark.parametrize(
    "records",
    [
        [],
        [{"name": "other"}],
    ],
)
def test_get_record_not_found(requests_mocker, config, records):
    info = ARecordInfo.from_hostname(config.hostname)

    requests_mocker.get(
        urljoin(
            SCALEWAY_API_BASE_URL,
            f"dns-zones/{info.domain}/records",
        ),
        status=200,
        json={"records": records},
    )

    upd = Updater(config)
    result = upd.get_record()

    assert result is None


def test_get_record_http_error(requests_mocker, config):
    info = ARecordInfo.from_hostname(config.hostname)

    requests_mocker.get(
        urljoin(
            SCALEWAY_API_BASE_URL,
            f"dns-zones/{info.domain}/records",
        ),
        status=500,
    )

    upd = Updater(config)

    with pytest.raises(SudException) as raised:
        upd.get_record()

    assert raised.value.message.startswith(
        f"Cannot retrieve information for A record `{info.name}` "
        f"from zone `{info.domain}`: 500 Server Error"
    )


def test_get_record_request_exception(mocker, config):
    mocker.patch(
        "sud.updater.requests.get",
        side_effect=RequestException("msg"),
    )

    info = ARecordInfo.from_hostname(config.hostname)

    upd = Updater(config)

    with pytest.raises(SudException) as raised:
        upd.get_record()

    assert raised.value.message.startswith(
        f"Cannot retrieve information for A record `{info.name}` "
        f"from zone `{info.domain}`: msg"
    )


def test_add_record(mocker, requests_mocker, config):
    info = ARecordInfo.from_hostname(config.hostname)

    requests_mocker.patch(
        urljoin(
            SCALEWAY_API_BASE_URL,
            f"dns-zones/{info.domain}/records",
        ),
        status=200,
        match=[
            matchers.header_matcher({"X-Auth-Token": config.api_secret}),
            matchers.json_params_matcher(
                {
                    "changes": [
                        {
                            "add": {
                                "records": [
                                    {
                                        "name": info.get_dns_name(),
                                        "type": "A",
                                        "ttl": info.ttl,
                                        "data": "1.2.3.4",
                                    },
                                ],
                            },
                        },
                    ],
                    "disallow_new_zone_creation": True,
                    "return_all_records": False,
                },
            ),
        ],
        json={
            "records": [
                {
                    "name": info.name,
                    "ttl": 300,
                    "data": "1.2.3.4",
                },
            ],
        },
    )

    upd = Updater(config)
    result = upd.add_record("1.2.3.4")

    assert isinstance(result, ARecordInfo)
    assert result.name == "my"
    assert result.domain == "host.name"
    assert result.ttl == 300
    assert result.address == "1.2.3.4"


def test_add_record_http_error(requests_mocker, config):
    info = ARecordInfo.from_hostname(config.hostname)

    requests_mocker.patch(
        urljoin(
            SCALEWAY_API_BASE_URL,
            f"dns-zones/{info.domain}/records",
        ),
        status=500,
        json={},
    )

    upd = Updater(config)

    with pytest.raises(SudException) as raised:
        upd.add_record("1.2.3.4")

    assert raised.value.message.startswith(
        f"Cannot add A record for `{info.name}` "
        f"to zone `{info.domain}`: 500 Server Error"
    )


def test_add_record_request_exception(mocker, config):
    mocker.patch(
        "sud.updater.requests.patch",
        side_effect=RequestException("msg"),
    )

    info = ARecordInfo.from_hostname(config.hostname)

    upd = Updater(config)

    with pytest.raises(SudException) as raised:
        upd.add_record("1.2.3.4")

    assert raised.value.message.startswith(
        f"Cannot add A record for `{info.name}` " f"to zone `{info.domain}`: msg"
    )


def test_change_record(mocker, requests_mocker, config):
    info = ARecordInfo.from_hostname(config.hostname)

    requests_mocker.patch(
        urljoin(
            SCALEWAY_API_BASE_URL,
            f"dns-zones/{info.domain}/records",
        ),
        status=200,
        match=[
            matchers.header_matcher({"X-Auth-Token": config.api_secret}),
            matchers.json_params_matcher(
                {
                    "changes": [
                        {
                            "set": {
                                "id_fields": {
                                    "name": info.get_dns_name(),
                                    "type": "A",
                                },
                                "records": [
                                    {
                                        "name": info.get_dns_name(),
                                        "type": "A",
                                        "ttl": info.ttl,
                                        "data": "5.6.7.8",
                                    },
                                ],
                            },
                        }
                    ],
                    "disallow_new_zone_creation": True,
                    "return_all_records": False,
                },
            ),
        ],
        json={
            "records": [
                {
                    "name": info.name,
                    "ttl": 300,
                    "data": "5.6.7.8",
                },
            ],
        },
    )

    upd = Updater(config)
    result = upd.change_record("5.6.7.8")

    assert isinstance(result, ARecordInfo)
    assert result.name == "my"
    assert result.domain == "host.name"
    assert result.ttl == 300
    assert result.address == "5.6.7.8"


def test_run(mocker, caplog, config):
    mocker.patch.object(
        Updater,
        "update",
        side_effect=[None, SudException("error"), KeyboardInterrupt()],
    )
    m_sleep = mocker.patch(
        "sud.updater.time.sleep",
    )
    upd = Updater(config)
    with caplog.at_level(logging.INFO):
        upd.run()

    assert m_sleep.call_count == 2
    assert m_sleep.mock_calls[0].args[0] == config.frequency.seconds
    assert len(caplog.records) == 3
    assert caplog.records[0].levelname == "INFO"
    assert caplog.records[0].message.startswith("Wait 5 minutes before")

    assert caplog.records[1].levelname == "ERROR"
    assert caplog.records[1].message == "Error while updating: error"

    assert caplog.records[2].levelname == "INFO"
    assert caplog.records[2].message == "Exiting..."


def test_update_no_record(mocker, config):
    mocker.patch.object(Updater, "get_record", return_value=None)
    mocker.patch.object(Updater, "discover_address", return_value="9.8.7.6")
    info = ARecordInfo.from_hostname(config.hostname)
    info.address = "9.8.7.6"
    m_add_record = mocker.patch.object(Updater, "add_record", return_value=info)
    m_notify = mocker.patch.object(Updater, "notify")

    upd = Updater(config)
    upd.update()

    m_add_record.assert_called_once_with("9.8.7.6")
    m_notify.assert_awaited_once_with("9.8.7.6")


def test_update_no_change(mocker, caplog, config):
    info = ARecordInfo.from_hostname(config.hostname)
    info.address = "9.8.7.6"
    mocker.patch.object(Updater, "get_record", return_value=info)
    mocker.patch.object(Updater, "discover_address", return_value="9.8.7.6")

    upd = Updater(config)
    with caplog.at_level(logging.INFO):
        upd.update()

    assert f"No IP change detected for {config.hostname}" in caplog.text


def test_update_change(mocker, config):
    original = ARecordInfo.from_hostname(config.hostname)
    original.address = "9.8.7.6"
    mocker.patch.object(Updater, "get_record", return_value=original)
    mocker.patch.object(Updater, "discover_address", return_value="1.2.3.4")
    new = ARecordInfo.from_hostname(config.hostname)
    new.address = "1.2.3.4"
    m_change_record = mocker.patch.object(Updater, "change_record", return_value=new)
    m_notify = mocker.patch.object(Updater, "notify")

    upd = Updater(config)
    upd.update()

    m_change_record.assert_called_once_with("1.2.3.4")
    m_notify.assert_awaited_once_with("1.2.3.4", previous="9.8.7.6")


@pytest.mark.asyncio()
async def test_notify_add(mocker, config):
    m_bot = mocker.AsyncMock()
    m_bot_ctxt = mocker.AsyncMock()
    m_bot_ctxt.__aenter__.return_value = m_bot
    m_bot_ctor = mocker.patch("sud.updater.telegram.Bot", return_value=m_bot_ctxt)

    upd = Updater(config)

    msg = TG_CREATED_MSG.format(name=config.hostname, address="1.2.3.4")

    await upd.notify("1.2.3.4")

    m_bot_ctor.assert_called_once_with(config.telegram.token)
    m_bot.send_message.assert_awaited_once_with(
        config.telegram.chat_id,
        msg,
        parse_mode=telegram.constants.ParseMode.HTML,
    )


@pytest.mark.asyncio()
async def test_notify_change(mocker, config):
    m_bot = mocker.AsyncMock()
    m_bot_ctxt = mocker.AsyncMock()
    m_bot_ctxt.__aenter__.return_value = m_bot
    m_bot_ctor = mocker.patch("sud.updater.telegram.Bot", return_value=m_bot_ctxt)

    upd = Updater(config)

    msg = TG_UPDATED_MSG.format(
        name=config.hostname, address="1.2.3.4", previous="5.6.7.8"
    )

    await upd.notify("1.2.3.4", previous="5.6.7.8")

    m_bot_ctor.assert_called_once_with(config.telegram.token)
    m_bot.send_message.assert_awaited_once_with(
        config.telegram.chat_id,
        msg,
        parse_mode=telegram.constants.ParseMode.HTML,
    )


@pytest.mark.asyncio()
async def test_notify_no_config(mocker, config_file_factory):
    c = Config(mocker.MagicMock())
    c._config = config_file_factory()
    m_bot_ctor = mocker.patch("sud.updater.telegram.Bot")

    upd = Updater(c)

    await upd.notify("1.2.3.4")

    m_bot_ctor.assert_not_called()
