import re
from uuid import UUID

from rich.prompt import PromptBase


class HostnameType:
    def __new__(cls, value: str):
        if cls.is_fqdn(value):
            return super().__new__(cls)

        raise ValueError("Invalid hostname, it must be a fqdn")

    def __init__(self, value: str):
        self.value = value

    @classmethod
    def is_fqdn(cls, hostname: str) -> bool:
        """
        https://en.m.wikipedia.org/wiki/Fully_qualified_domain_name
        """
        if not 1 < len(hostname) < 253:
            return False

        # Remove trailing dot
        if hostname[-1] == ".":
            hostname = hostname[0:-1]

        labels = hostname.split(".")
        if len(labels) < 2:
            return False

        fqdn = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)
        return all(fqdn.match(label) for label in labels)

    def __str__(self):
        return self.value


class APISecretType:
    def __new__(cls, value: str):
        UUID(value, version=4)
        return super().__new__(cls)

    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return self.value


class HostnamePrompt(PromptBase[HostnameType]):
    response_type = HostnameType
    validate_error_message = "[prompt.invalid]Please enter a valid hostname"


class APISecretPrompt(PromptBase[APISecretType]):
    response_type = APISecretType
    validate_error_message = "[prompt.invalid]Please enter a valid Scaleway API secret"
