from uuid import uuid4

import pytest

from sud.prompt import APISecretPrompt, APISecretType, HostnamePrompt, HostnameType


@pytest.mark.parametrize("hostname", ["my.host.name", "my.host.name."])
def test_hostname_type(hostname):
    t = HostnameType(hostname)
    assert t.value == hostname


@pytest.mark.parametrize("hostname", ["invalid", "i"])
def test_hostname_type_invalid(hostname):
    with pytest.raises(ValueError) as raised:
        HostnameType(hostname)

    assert str(raised.value) == "Invalid hostname, it must be a fqdn"


def test_apisecret_type():
    uuid = str(uuid4())
    t = APISecretType(uuid)

    assert t.value == uuid

    with pytest.raises(ValueError) as raised:
        APISecretType("invalid")

    assert str(raised.value) == "badly formed hexadecimal UUID string"


def test_hostname_prompt():
    assert HostnamePrompt.response_type == HostnameType


def test_apisecret_prompt():
    assert APISecretPrompt.response_type == APISecretType
