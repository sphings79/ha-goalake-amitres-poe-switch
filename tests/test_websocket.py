"""WebSocket API of the panel: read for everyone, write for administrators only."""

from __future__ import annotations

import itertools
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.goalake_poe_switch import panel
from custom_components.goalake_poe_switch.const import DOMAIN

MAC = "020000000001"
PORT1 = 7


@pytest.fixture(autouse=True)
def _enable(enable_custom_integrations):
    yield


async def setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=MAC, title="GPS208 (0001)",
                            data={CONF_HOST: "192.0.2.10", CONF_PASSWORD: "S3cret-Pw!x"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_devices_payload_hides_identifiers(hass: HomeAssistant, hass_ws_client, device) -> None:
    entry = await setup(hass)
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": f"{DOMAIN}/devices"})
    msg = await ws.receive_json()
    assert msg["success"]
    (dev,) = msg["result"]
    assert dev["entry_id"] == entry.entry_id and dev["model"] == "GPS208"
    assert dev["host"] == "192.0.2.10"  # administrators get the host
    assert len(dev["ports"]) == 10 and dev["ports"][PORT1]["label"] == "1" and dev["ports"][PORT1]["power_w"] == 1.3
    text = json.dumps(msg)
    for secret in ("S3cret-Pw!x", MAC, "SIMULATED"):
        assert secret not in text


async def test_read_only_user_gets_no_host_and_cannot_write(
    hass: HomeAssistant, hass_ws_client, hass_read_only_access_token, device
) -> None:
    await setup(hass)
    ws = await hass_ws_client(hass, hass_read_only_access_token)
    await ws.send_json({"id": 1, "type": f"{DOMAIN}/devices"})
    msg = await ws.receive_json()
    assert msg["success"] and "host" not in msg["result"][0]
    await ws.send_json({"id": 2, "type": f"{DOMAIN}/write", "entry_id": "x", "action": "poe", "index": PORT1, "value": False})
    msg = await ws.receive_json()
    assert not msg["success"] and msg["error"]["code"] == "unauthorized"
    device.set_poe.assert_not_awaited()


_ids = itertools.count(100)  # a websocket connection needs ever-increasing message ids


async def write(ws, entry, action, mid=None, **kw):
    await ws.send_json({"id": next(_ids), "type": f"{DOMAIN}/write", "entry_id": entry.entry_id, "action": action, **kw})
    return await ws.receive_json()


async def test_admin_writes(hass: HomeAssistant, hass_ws_client, device) -> None:
    entry = await setup(hass)
    ws = await hass_ws_client(hass)
    assert (await write(ws, entry, "poe", index=PORT1, value=False))["success"]
    device.set_poe.assert_awaited_once_with(PORT1, False)
    assert (await write(ws, entry, "mode", index=PORT1, value="100m_full"))["success"]
    device.set_port_mode.assert_awaited_once_with(PORT1, 4)
    assert (await write(ws, entry, "priority", index=PORT1, value=3))["success"]
    assert device.set_priority.await_args.args[0][PORT1] == 3
    assert (await write(ws, entry, "limit_up", index=PORT1, value=10))["success"]
    up, down = device.set_limits.await_args.args
    assert up[PORT1] == 10 * 1024 and down[PORT1] == 0
    assert (await write(ws, entry, "flow", index=PORT1, value=False))["success"]
    assert device.set_flow.await_args.args[0][PORT1] == 0
    assert (await write(ws, entry, "lldp", value=False))["success"]
    device.set_lldp.assert_awaited_once_with(False)
    assert (await write(ws, entry, "power_warn", value=90))["success"]
    device.set_power_warn.assert_awaited_once_with(90)
    assert (await write(ws, entry, "extend", index=PORT1, value=True))["success"]
    device.set_port_mode.assert_awaited_with(PORT1, 2)
    assert (await write(ws, entry, "extend", index=PORT1, value=False))["success"]
    device.set_port_mode.assert_awaited_with(PORT1, 5)
    assert (await write(ws, entry, "restart_port", index=PORT1))["success"]
    device.restart_port.assert_awaited_once_with(PORT1)


@pytest.mark.parametrize(
    ("action", "kw"),
    [
        ("poe", {"index": 9, "value": False}),  # uplink LAN1
        ("poe", {"index": 8, "value": False}),  # uplink LAN2
        ("poe", {"index": 40, "value": False}),
        ("extend", {"index": 9, "value": True}),  # uplink: 10M could cut the management connection
        ("extend", {"index": PORT1, "value": "yes"}),
        ("poe", {"index": PORT1, "value": 1}),  # not a boolean
        ("priority", {"index": PORT1, "value": 9}),
        ("limit_down", {"index": PORT1, "value": 5000}),
        ("mode", {"index": PORT1, "value": "warp_speed"}),
        ("reboot", {}),  # no confirm
        ("power_warn", {"value": True}),
    ],
)
async def test_invalid_writes_are_refused(hass: HomeAssistant, hass_ws_client, device, action, kw) -> None:
    entry = await setup(hass)
    ws = await hass_ws_client(hass)
    msg = await write(ws, entry, action, **kw)
    assert not msg["success"] and msg["error"]["code"] == "invalid_format"
    for name in ("set_poe", "set_priority", "set_limits", "set_port_mode", "reboot", "set_power_warn"):
        getattr(device, name).assert_not_awaited()


async def test_reboot_with_confirm_and_failure_reporting(hass: HomeAssistant, hass_ws_client, device) -> None:
    from custom_components.goalake_poe_switch import api

    entry = await setup(hass)
    ws = await hass_ws_client(hass)
    assert (await write(ws, entry, "reboot", confirm=True))["success"]
    device.reboot.assert_awaited_once()
    device.set_poe.side_effect = api.ApiError(1003, "nope")
    msg = await write(ws, entry, "poe", index=PORT1, value=True, mid=2)
    assert not msg["success"] and msg["error"]["code"] == "write_failed"


async def test_unknown_switch(hass: HomeAssistant, hass_ws_client, device) -> None:
    entry = await setup(hass)
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": f"{DOMAIN}/write", "entry_id": "nope", "action": "lldp", "value": True})
    msg = await ws.receive_json()
    assert not msg["success"] and msg["error"]["code"] == "not_found"


async def test_subscription_pushes_updates(hass: HomeAssistant, hass_ws_client, device) -> None:
    entry = await setup(hass)
    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": f"{DOMAIN}/subscribe"})
    assert (await ws.receive_json())["success"]
    first = await ws.receive_json()
    assert first["type"] == "event" and first["event"]["devices"][0]["total_power_w"] == 1.3
    await entry.runtime_data.async_refresh()
    again = await ws.receive_json()
    assert again["type"] == "event"


async def test_settings_are_per_user(hass: HomeAssistant, hass_ws_client, hass_read_only_access_token, device) -> None:
    await setup(hass)
    admin = await hass_ws_client(hass)
    other = await hass_ws_client(hass, hass_read_only_access_token)
    await admin.send_json({"id": 1, "type": f"{DOMAIN}/settings/set", "settings": {"scheme": "cockpit"}})
    assert (await admin.receive_json())["success"]
    await admin.send_json({"id": 2, "type": f"{DOMAIN}/settings/get"})
    assert (await admin.receive_json())["result"] == {"scheme": "cockpit"}
    await other.send_json({"id": 1, "type": f"{DOMAIN}/settings/get"})
    assert (await other.receive_json())["result"] == {}
    await other.send_json({"id": 2, "type": f"{DOMAIN}/settings/set", "settings": {"x": "y" * 5000}})
    assert not (await other.receive_json())["success"]


async def test_panel_is_registered_once_and_removed(hass: HomeAssistant, device, tmp_path) -> None:
    bundle = panel.Path(panel.__file__).parent / "frontend" / panel.BUNDLE_NAME
    if not bundle.is_file():
        pytest.skip("frontend bundle not built")
    hass.config.components.update({"panel_custom", "http"})
    # only this method of the http component is a coroutine, an AsyncMock for all would leave others unawaited
    hass.http = MagicMock(async_register_static_paths=AsyncMock())
    with (
        patch.object(panel.panel_custom, "async_register_panel", AsyncMock()) as register,
        patch.object(panel.frontend, "async_remove_panel") as remove,
        patch.object(panel.frontend, "add_extra_js_url") as extra_js,
    ):
        entry = await setup(hass)
        await panel.async_register_panel(hass)  # a second entry must not register again
        register.assert_awaited_once()
        extra_js.assert_called_once()  # the Lovelace card bundle, once
        assert extra_js.call_args.args[1].startswith("/goalake_poe_switch-frontend/goalake-poe-switch-card.js?v=")
        kwargs = register.await_args.kwargs
        assert kwargs["frontend_url_path"] == "goalake-poe-switch" and kwargs["require_admin"] is False
        assert kwargs["module_url"].startswith("/goalake_poe_switch-frontend/goalake-poe-switch-panel.js?v=")
        await hass.config_entries.async_unload(entry.entry_id)
        remove.assert_called_once_with(hass, "goalake-poe-switch")
