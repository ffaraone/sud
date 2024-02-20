import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

import humanize
import requests
import telegram

from sud.config import Config
from sud.exceptions import SudException

CHECK_IP_ADDRESS = "https://checkip.amazonaws.com/"
SCALEWAY_API_BASE_URL = "https://api.scaleway.com/domain/v2beta1/"
TG_CREATED_MSG = """
The DNS record (A) for <b><u>{name}</u></b> has been created:

<span class="tg-spoiler"><b>{address}</b></span>
"""
TG_UPDATED_MSG = """
The DNS record (A) for <b><u>{name}</u></b> has been updated:

previous: <s>{previous}</s>
current: <span class="tg-spoiler"><b>{address}</b></span>
"""


logger = logging.getLogger(__name__)


@dataclass
class ARecordInfo:
    name: str
    domain: str
    ttl: Optional[int] = 300
    address: Optional[str] = None

    @classmethod
    def from_hostname(cls, hostname) -> "ARecordInfo":
        if not hostname:
            raise SudException("Hostname is required")

        parts = hostname.split(".")

        if len(parts) < 2:
            raise SudException(f"Invalid hostname: {hostname}")

        domain = ".".join(parts[-2:])
        name = ".".join(parts[:-2])

        return cls(name, domain)

    def get_dns_name(self):
        return (
            f"{self.name}.{self.domain}." if self.name else f"{self.domain}."
        )


class Updater:
    def __init__(self, config: Config):
        self._config: Config = config

    @staticmethod
    def discover_address() -> str:
        try:
            resp = requests.get(CHECK_IP_ADDRESS)
            resp.raise_for_status()
            return resp.text.strip()
        except requests.RequestException as e:
            raise SudException(
                f"Cannot determine current public ip address: {str(e)}.",
            )

    def get_record(self) -> ARecordInfo | None:
        info = ARecordInfo.from_hostname(self._config.hostname)

        url = urljoin(
            SCALEWAY_API_BASE_URL,
            f"dns-zones/{info.domain}/records",
        )

        try:
            resp = requests.get(
                url,
                headers={"X-Auth-Token": self._config.api_secret},
                params={
                    "type": "A",
                    "name": info.name,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            for record in data["records"]:
                if record["name"] == info.name:
                    return ARecordInfo(
                        record["name"],
                        info.domain,
                        ttl=record["ttl"],
                        address=record["data"],
                    )

        except requests.RequestException as e:
            raise SudException(
                "Cannot retrieve information for A "
                f"record {info.name} from zone {info.domain}: {e}",
            )

    def add_record(self, address: str) -> ARecordInfo:
        info = ARecordInfo.from_hostname(self._config.hostname)
        changes = [
            {
                "add": {
                    "records": [
                        {
                            "name": info.get_dns_name(),
                            "type": "A",
                            "ttl": info.ttl,
                            "data": address,
                        },
                    ],
                },
            },
        ]
        return self._update_zone(info, changes)

    def change_record(self, address: str) -> ARecordInfo:
        info = ARecordInfo.from_hostname(self._config.hostname)
        changes = [
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
                            "data": address,
                        },
                    ],
                },
            }
        ]
        return self._update_zone(info, changes)

    def run(self) -> None:
        while True:
            try:
                self.update()
            except SudException as e:
                logger.error(f"Error while updating: {e}")
            logger.info(
                f"Wait {humanize.naturaldelta(self._config.frequency)} "
                "before next check ..zzZZ..",
            )
            time.sleep(self._config.frequency.seconds)

    def update(self) -> None:
        previous_record = self.get_record()
        detected_address = Updater.discover_address()
        if not previous_record:
            logger.info(f"No 'A' record found for {self._config.hostname}")
            new_record = self.add_record(detected_address)
            logger.info(
                f"'A' record added for {self._config.hostname}: "
                f"{new_record.address}",
            )
            asyncio.run(self.notify(detected_address))
            return

        if previous_record.address == detected_address:
            logger.info(
                "No IP change detected for "
                f"{self._config.hostname}: {previous_record.address}",
            )
            return

        logger.info(
            f"IP address for {self._config.hostname} have changed: "
            f"{previous_record.address} -> {detected_address}",
        )
        updated_record = self.change_record(detected_address)
        logger.info(
            f"'A' record modified for {self._config.hostname}: "
            f"{previous_record.address} -> {updated_record.address}",
        )
        asyncio.run(
            self.notify(detected_address, previous=previous_record.address),
        )

    async def notify(self, address: str, previous: str | None = None) -> None:
        template = TG_UPDATED_MSG
        data = {
            "name": self._config.hostname,
            "address": address,
            "previous": previous,
        }
        if not previous:
            template = TG_CREATED_MSG
            del data["previous"]

        if self._config.telegram:
            async with telegram.Bot(self._config.telegram["token"]) as bot:
                await bot.send_message(
                    self._config.telegram["chat_id"],
                    template.format(data),
                    parse_mode=telegram.constants.ParseMode.HTML,
                )

    def _update_zone(self, info, changes):
        url = urljoin(
            SCALEWAY_API_BASE_URL,
            f"dns-zones/{info.domain}/records",
        )

        try:
            resp = requests.patch(
                url,
                headers={"X-Auth-Token": self._config.api_secret},
                json={
                    "changes": changes,
                    "disallow_new_zone_creation": True,
                    "return_all_records": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            record = data["records"][0]
            return ARecordInfo(
                record["name"],
                info.domain,
                ttl=record["ttl"],
                address=record["data"],
            )
        except requests.RequestException as e:
            message = str(e)
            if isinstance(e, requests.HTTPError):
                message = e.response.json()

            raise SudException(
                f"Cannot add A record for {info.name} "
                f"to zone {info.domain}: {message}",
            )
