"""Goalake / Amitres PoE switch integration."""

from __future__ import annotations

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import GoalakeClient, SwitchData, model_from_serial
from .const import DOMAIN, MANUFACTURER
from .coordinator import GoalakeCoordinator
from .panel import async_register_panel, async_remove_panel_if_unused
from .scanner import async_start_scanner, async_stop_scanner_if_unused

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

type GoalakeConfigEntry = ConfigEntry[GoalakeCoordinator]


def format_mac(mac: str) -> str:
    """Normalise a MAC to 12 lowercase hex digits without separators."""
    return mac.replace(":", "").replace("-", "").lower()


async def async_setup_entry(hass: HomeAssistant, entry: GoalakeConfigEntry) -> bool:
    # no cookie jar: the client sends the session id itself, devices must not share cookies
    session = async_create_clientsession(hass, cookie_jar=aiohttp.DummyCookieJar())
    client = GoalakeClient(session, entry.data[CONF_HOST], entry.data[CONF_PASSWORD])
    coordinator = GoalakeCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    _register_device(hass, entry, coordinator.data)

    async def _logout(_: Event) -> None:
        await client.close()

    # free the device's single session when Home Assistant stops
    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _logout))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_register_panel(hass)
    async_start_scanner(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GoalakeConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.client.close()
        async_remove_panel_if_unused(hass)
        async_stop_scanner_if_unused(hass)
    return unloaded


def _register_device(hass: HomeAssistant, entry: ConfigEntry, data: SwitchData) -> None:
    mac = format_mac(data.mac)
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, mac)},
        identifiers={(DOMAIN, mac)},
        manufacturer=MANUFACTURER,
        model=model_from_serial(data.serial),
        name=entry.title,
        sw_version=data.firmware,
        configuration_url=f"http://{entry.data[CONF_HOST]}",
    )
