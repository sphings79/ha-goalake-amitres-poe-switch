"""WebSocket API of the dashboard panel.

Reading is open to every logged-in user, writing needs an administrator (checked here on the server,
the panel only hides the controls). Writes are limited to PoE ports: an uplink may carry the
management connection. Serial number and MAC are never sent; the host only to administrators.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .api import LIMIT_FACTOR, MODE_DEFAULT, MODE_EXTEND, PORT_MODES, GoalakeError, SwitchData, model_from_serial
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

WS_DEVICES = f"{DOMAIN}/devices"
WS_SUBSCRIBE = f"{DOMAIN}/subscribe"
WS_WRITE = f"{DOMAIN}/write"
WS_SETTINGS_GET = f"{DOMAIN}/settings/get"
WS_SETTINGS_SET = f"{DOMAIN}/settings/set"

DATA_API_REGISTERED = "api_registered"
DATA_STORE = "settings_store"
STORAGE_KEY = f"{DOMAIN}.panel_settings"
MAX_SETTINGS_CHARS = 4096

PORT_ACTIONS = {"poe", "extend", "mode", "flow", "priority", "limit_up", "limit_down", "restart_port"}
DEVICE_ACTIONS = {"lldp", "storm", "watchdog", "ai_auto_extend", "power_warn", "reboot"}
ACTIONS = sorted(PORT_ACTIONS | DEVICE_ACTIONS)


def device_payload(entry, data: SwitchData, admin: bool, available: bool) -> dict[str, Any]:
    """What the panel gets to see of one switch."""
    payload: dict[str, Any] = {
        "entry_id": entry.entry_id,
        "title": entry.title,
        "available": available,
        "model": model_from_serial(data.serial),
        "firmware": data.firmware,
        "voltage_v": data.voltage_v,
        "total_power_w": data.total_power_w,
        "temperature_c": data.temperature_c,
        "cloud_status": data.cloud_status,
        "settings": data.settings,
        "ports": [
            {
                "index": p.index,
                "label": p.label,
                "is_poe": p.is_poe,
                "connected": p.connected,
                "speed_mbps": p.speed_mbps,
                "admin_enabled": p.admin_enabled,
                "poe_enabled": p.poe_enabled,
                "power_w": p.power_w,
                "tx_kbps": p.tx_kbps,
                "rx_kbps": p.rx_kbps,
                "phy_mode": PORT_MODES.get(p.phy_mode),
                "flow_control": p.flow_control,
                "priority": p.priority,
                "limit_up_mbps": None if p.limit_up is None else p.limit_up / LIMIT_FACTOR,
                "limit_down_mbps": None if p.limit_down is None else p.limit_down / LIMIT_FACTOR,
            }
            for p in data.ports
        ],
    }
    if admin:
        payload["host"] = entry.data.get("host")
    return payload


def _loaded(hass: HomeAssistant):
    return [e for e in hass.config_entries.async_loaded_entries(DOMAIN) if getattr(e, "runtime_data", None)]


def devices_payload(hass: HomeAssistant, admin: bool) -> list[dict[str, Any]]:
    out = []
    for entry in _loaded(hass):
        coordinator = entry.runtime_data
        if coordinator.data is not None:
            out.append(device_payload(entry, coordinator.data, admin, coordinator.last_update_success))
    return out


@callback
def async_register_api(hass: HomeAssistant) -> None:
    """Register the commands once per Home Assistant run."""
    data = hass.data.setdefault(DOMAIN, {})
    if data.get(DATA_API_REGISTERED):
        return
    for command in (ws_devices, ws_subscribe, ws_write, ws_settings_get, ws_settings_set):
        websocket_api.async_register_command(hass, command)
    data[DATA_API_REGISTERED] = True


@websocket_api.websocket_command({vol.Required("type"): WS_DEVICES})
@callback
def ws_devices(hass, connection, msg) -> None:
    connection.send_result(msg["id"], devices_payload(hass, connection.user.is_admin))


@websocket_api.websocket_command({vol.Required("type"): WS_SUBSCRIBE})
@callback
def ws_subscribe(hass, connection, msg) -> None:
    """Push the full device list now and on every update of any switch."""
    admin = connection.user.is_admin

    @callback
    def push() -> None:
        connection.send_message(
            websocket_api.event_message(msg["id"], {"devices": devices_payload(hass, admin)})
        )

    removers = [e.runtime_data.async_add_listener(push) for e in _loaded(hass)]

    @callback
    def unsubscribe() -> None:
        for remove in removers:
            remove()

    connection.subscriptions[msg["id"]] = unsubscribe
    connection.send_result(msg["id"])
    push()


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_WRITE,
        vol.Required("entry_id"): str,
        vol.Required("action"): vol.In(ACTIONS),
        vol.Optional("index"): vol.All(int, vol.Range(min=0, max=31)),
        vol.Optional("value"): vol.Any(bool, int, str),
        vol.Optional("confirm"): bool,
    }
)
@websocket_api.async_response
async def ws_write(hass, connection, msg) -> None:
    entry = next((e for e in _loaded(hass) if e.entry_id == msg["entry_id"]), None)
    if entry is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "switch not found")
        return
    coordinator = entry.runtime_data
    action, index, value = msg["action"], msg.get("index"), msg.get("value")
    try:
        call = _build_call(coordinator, action, index, value, msg.get("confirm", False))
    except ValueError as err:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, str(err))
        return
    try:
        await call
    except GoalakeError as err:
        connection.send_error(msg["id"], "write_failed", f"The switch did not accept the change: {err}")
        return
    await coordinator.async_refresh()  # immediate, a debounced refresh would show the old state for ~10 s
    connection.send_result(msg["id"])


def _int(value: Any, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"value must be an integer from {low} to {high}")
    return value


def _build_call(coordinator, action: str, index: int | None, value: Any, confirm: bool):
    """Validate a write request and return the client coroutine. Raises ValueError for bad input."""
    client, data = coordinator.client, coordinator.data
    if action in PORT_ACTIONS:
        if index is None or index >= len(data.ports) or not data.ports[index].is_poe:
            raise ValueError("this action is limited to PoE ports")
        if action == "poe":
            return client.set_poe(index, _bool(value))
        if action == "extend":
            return client.set_port_mode(index, MODE_EXTEND if _bool(value) else MODE_DEFAULT)
        if action == "restart_port":
            return client.restart_port(index)
        if action == "mode":
            modes = {name: number for number, name in PORT_MODES.items()}
            if value not in modes:
                raise ValueError("unknown port mode")
            return client.set_port_mode(index, modes[value])
        if action == "flow":
            flow = list(data.flow)
            flow[index] = 1 if _bool(value) else 0
            return client.set_flow(flow)
        if action == "priority":
            prio = list(data.priority)
            prio[index] = _int(value, 0, 6)
            return client.set_priority(prio)
        up, down = list(data.limit_up), list(data.limit_down)
        (up if action == "limit_up" else down)[index] = _int(value, 0, 1000) * LIMIT_FACTOR
        return client.set_limits(up, down)
    if action == "reboot":
        if not confirm:
            raise ValueError("reboot needs confirm=true")
        return client.reboot()
    if action == "power_warn":
        return client.set_power_warn(_int(value, 0, 1000))
    setter = {"lldp": client.set_lldp, "storm": client.set_storm, "watchdog": client.set_watchdog,
              "ai_auto_extend": client.set_ai_auto_extend}[action]
    return setter(_bool(value))


def _bool(value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError("value must be true or false")
    return value


# -- per-user panel settings (palette, light/dark, language, last device) ----------------------


def _store(hass: HomeAssistant) -> Store:
    data = hass.data.setdefault(DOMAIN, {})
    if DATA_STORE not in data:
        data[DATA_STORE] = Store(hass, 1, STORAGE_KEY)
    return data[DATA_STORE]


async def _all_settings(hass: HomeAssistant) -> dict[str, Any]:
    stored = await _store(hass).async_load()
    users = stored.get("users") if isinstance(stored, dict) else None
    return users if isinstance(users, dict) else {}


@websocket_api.websocket_command({vol.Required("type"): WS_SETTINGS_GET})
@websocket_api.async_response
async def ws_settings_get(hass, connection, msg) -> None:
    # the user id comes from the connection, never from the message
    settings = (await _all_settings(hass)).get(connection.user.id)
    connection.send_result(msg["id"], settings if isinstance(settings, dict) else {})


@websocket_api.websocket_command({vol.Required("type"): WS_SETTINGS_SET, vol.Required("settings"): dict})
@websocket_api.async_response
async def ws_settings_set(hass, connection, msg) -> None:
    if len(str(msg["settings"])) > MAX_SETTINGS_CHARS:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, "settings too large")
        return
    users = dict(await _all_settings(hass))
    users[connection.user.id] = msg["settings"]
    await _store(hass).async_save({"users": users})
    connection.send_result(msg["id"])
