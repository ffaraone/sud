import pytest

from sud.exceptions import SudException
from sud.updater import CHECK_IP_ADDRESS, ARecordInfo, Updater


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


def test_init(config):
    upd = Updater(config)
    assert upd._config == config


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
