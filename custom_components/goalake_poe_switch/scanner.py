"""Finds switches in the network and tells Home Assistant about them."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.components import network
from homeassistant.config_entries import SOURCE_INTEGRATION_DISCOVERY
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery_flow
from homeassistant.helpers.event import async_track_time_interval

from . import discovery
from .const import CONF_HOST, DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=15)
DATA_SCANNER = "scanner_started"


def mac_key(mac: str) -> str:
    return mac.replace(":", "").replace("-", "").lower()


async def async_scan(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Search on every enabled IPv4 interface. Never raises: no answer simply means nothing found."""
    try:
        sources = [str(ip) for ip in await network.async_get_enabled_source_ips(hass) if ip.version == 4 and not ip.is_loopback]
    except Exception:  # noqa: BLE001 - the network integration may be missing in odd setups
        sources = []

    async def _one(ip: str) -> list[dict[str, Any]]:
        try:
            return await hass.async_add_executor_job(discovery.discover, ip or None, 3.0)
        except Exception as err:  # noqa: BLE001 - one broken interface must not stop the others
            _LOGGER.debug("discovery failed on one interface: %s", type(err).__name__)
            return []

    found: dict[str, dict[str, Any]] = {}
    for devices in await asyncio.gather(*(_one(ip) for ip in (sources or [""]))):
        for device in devices:
            if device.get("mac"):
                found[mac_key(str(device["mac"]))] = device
    return list(found.values())


async def _scan_and_report(hass: HomeAssistant) -> None:
    configured = {e.unique_id: e for e in hass.config_entries.async_entries(DOMAIN) if e.unique_id}
    for device in await async_scan(hass):
        mac = mac_key(str(device["mac"]))
        host = device.get("ip")
        if not host:
            continue
        entry = configured.get(mac)
        if entry is not None:
            if entry.data.get(CONF_HOST) != host:
                # the switch got another address (DHCP): follow it
                _LOGGER.info("A switch changed its address, updating the configuration")
                hass.config_entries.async_update_entry(entry, data={**entry.data, CONF_HOST: host})
                hass.config_entries.async_schedule_reload(entry.entry_id)
            continue
        discovery_flow.async_create_flow(
            hass,
            DOMAIN,
            context={"source": SOURCE_INTEGRATION_DISCOVERY},
            data={
                CONF_HOST: host,
                "mac": mac,
                "model": device.get("model"),
                "firmware": device.get("V"),
            },
        )


def async_start_scanner(hass: HomeAssistant) -> None:
    """Scan once now and then every 15 minutes while at least one switch is loaded."""
    data = hass.data.setdefault(DOMAIN, {})
    if data.get(DATA_SCANNER):
        return

    async def _tick(_: Any = None) -> None:
        try:
            await _scan_and_report(hass)
        except Exception:  # noqa: BLE001 - a failed scan must never break the integration
            _LOGGER.debug("scan failed", exc_info=True)

    hass.async_create_background_task(_tick(), f"{DOMAIN} scan")
    data[DATA_SCANNER] = async_track_time_interval(hass, _tick, SCAN_INTERVAL)


def async_stop_scanner_if_unused(hass: HomeAssistant) -> None:
    """Stop the periodic scan when the last switch is unloaded."""
    data = hass.data.get(DOMAIN, {})
    cancel = data.get(DATA_SCANNER)
    if cancel and not hass.config_entries.async_loaded_entries(DOMAIN):
        cancel()
        data.pop(DATA_SCANNER)
