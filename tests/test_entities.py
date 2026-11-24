"""Entity tests: state mapping and write calls. The device client is patched."""

from __future__ import annotations

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.goalake_poe_switch import api
from custom_components.goalake_poe_switch.const import DOMAIN

MAC = "020000000001"
PORT1 = 7  # port 1 is array index 7 on a GPS208


@pytest.fixture(autouse=True)
def _enable(enable_custom_integrations):
    yield


async def setup(hass: HomeAssistant, enabled: tuple[tuple[str, str], ...] = ()) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=MAC, title="GPS208 (0001)",
                            data={CONF_HOST: "192.0.2.10", CONF_PASSWORD: "S3cret-Pw!x"})
    entry.add_to_hass(hass)
    reg = er.async_get(hass)
    for platform, unique in enabled:  # enable entities that are disabled by default
        reg.async_get_or_create(platform, DOMAIN, f"{MAC}_{unique}", config_entry=entry)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def eid(hass: HomeAssistant, platform: str, unique: str) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"{MAC}_{unique}")
    assert entity_id, f"no {platform} entity {unique}"
    return entity_id


async def test_states_from_the_device(hass: HomeAssistant, device) -> None:
    await setup(hass)
    s = hass.states.get
    assert s(eid(hass, "sensor", "total_power")).state == "1.3"
    assert s(eid(hass, "sensor", "voltage")).state == "52.4"
    assert s(eid(hass, "sensor", "temperature")).state == "38.2"
    assert s(eid(hass, "sensor", f"port_power_{PORT1}")).state == "1.3"
    assert s(eid(hass, "sensor", f"port_speed_{PORT1}")).state == "100"
    assert s(eid(hass, "sensor", f"port_tx_{PORT1}")).state == "112"
    assert s(eid(hass, "binary_sensor", f"port_link_{PORT1}")).state == "on"
    assert s(eid(hass, "binary_sensor", "port_link_0")).state == "off"  # port 8, nothing connected
    assert s(eid(hass, "binary_sensor", "port_link_9")).state == "on"  # LAN1 uplink
    assert s(eid(hass, "binary_sensor", "cloud")).state == "off"
    assert s(eid(hass, "switch", f"port_poe_{PORT1}")).state == "on"
    assert s(eid(hass, "switch", "lldp")).state == "on"
    assert s(eid(hass, "switch", "storm_control")).state == "off"


async def test_port_names_use_printed_labels(hass: HomeAssistant, device) -> None:
    await setup(hass)
    state = hass.states.get(eid(hass, "switch", f"port_poe_{PORT1}"))
    assert state.attributes["friendly_name"] == "GPS208 (0001) Port 1 PoE"
    assert hass.states.get(eid(hass, "binary_sensor", "port_link_9")).attributes["friendly_name"].endswith("Port LAN1 link")


async def test_uplinks_have_no_write_entities(hass: HomeAssistant, device) -> None:
    await setup(hass)
    reg = er.async_get(hass)
    for platform, key in (("switch", "port_poe"), ("select", "port_mode"), ("number", "port_priority"),
                          ("number", "port_limit_up"), ("button", "port_restart"), ("switch", "port_extend")):
        assert reg.async_get_entity_id(platform, DOMAIN, f"{MAC}_{key}_9") is None
        assert reg.async_get_entity_id(platform, DOMAIN, f"{MAC}_{key}_8") is None
        assert reg.async_get_entity_id(platform, DOMAIN, f"{MAC}_{key}_7") is not None


async def test_poe_switch_writes_and_refreshes(hass: HomeAssistant, device) -> None:
    await setup(hass)
    calls = device.fetch.await_count
    await hass.services.async_call("switch", "turn_off", {"entity_id": eid(hass, "switch", f"port_poe_{PORT1}")}, blocking=True)
    device.set_poe.assert_awaited_once_with(PORT1, False)
    await hass.services.async_call("switch", "turn_on", {"entity_id": eid(hass, "switch", f"port_poe_{PORT1}")}, blocking=True)
    device.set_poe.assert_awaited_with(PORT1, True)
    await hass.async_block_till_done()
    assert device.fetch.await_count > calls  # state is read back after a write


async def test_write_failure_is_reported(hass: HomeAssistant, device) -> None:
    await setup(hass)
    device.set_poe.side_effect = api.ApiError(1003, "nope")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call("switch", "turn_off", {"entity_id": eid(hass, "switch", f"port_poe_{PORT1}")}, blocking=True)


async def test_feature_switches(hass: HomeAssistant, device) -> None:
    await setup(hass)
    for key, method in (("lldp", device.set_lldp), ("storm_control", device.set_storm),
                        ("watchdog", device.set_watchdog), ("ai_auto_extend", device.set_ai_auto_extend)):
        await hass.services.async_call("switch", "turn_on", {"entity_id": eid(hass, "switch", key)}, blocking=True)
        method.assert_awaited_once_with(True)


async def test_power_warn_number(hass: HomeAssistant, device) -> None:
    await setup(hass)
    await hass.services.async_call("number", "set_value", {"entity_id": eid(hass, "number", "power_warn"), "value": 90}, blocking=True)
    device.set_power_warn.assert_awaited_once_with(90)


async def test_disabled_by_default_entities_work_when_enabled(hass: HomeAssistant, device) -> None:
    await setup(hass, enabled=(
        ("number", f"port_limit_up_{PORT1}"), ("number", f"port_priority_{PORT1}"),
        ("select", f"port_mode_{PORT1}"), ("switch", f"port_flow_control_{PORT1}"),
        ("button", f"port_restart_{PORT1}"), ("button", "reboot"),
    ))
    await hass.services.async_call("number", "set_value", {"entity_id": eid(hass, "number", f"port_limit_up_{PORT1}"), "value": 10}, blocking=True)
    up, down = device.set_limits.await_args.args
    assert up[PORT1] == 10 * 1024 and down[PORT1] == 0 and len(up) == 10  # complete arrays, Mbit/s -> kbit/s
    await hass.services.async_call("number", "set_value", {"entity_id": eid(hass, "number", f"port_priority_{PORT1}"), "value": 4}, blocking=True)
    assert device.set_priority.await_args.args[0][PORT1] == 4
    assert hass.states.get(eid(hass, "select", f"port_mode_{PORT1}")).state == "1000m_full"
    await hass.services.async_call("select", "select_option", {"entity_id": eid(hass, "select", f"port_mode_{PORT1}"), "option": "100m_full"}, blocking=True)
    device.set_port_mode.assert_awaited_once_with(PORT1, 4)
    await hass.services.async_call("switch", "turn_off", {"entity_id": eid(hass, "switch", f"port_flow_control_{PORT1}")}, blocking=True)
    assert device.set_flow.await_args.args[0][PORT1] == 0
    await hass.services.async_call("button", "press", {"entity_id": eid(hass, "button", f"port_restart_{PORT1}")}, blocking=True)
    device.restart_port.assert_awaited_once_with(PORT1)
    await hass.services.async_call("button", "press", {"entity_id": eid(hass, "button", "reboot")}, blocking=True)
    device.reboot.assert_awaited_once()


async def test_rates_and_speed_are_shown_without_decimals(hass: HomeAssistant, device) -> None:
    await setup(hass)
    reg = er.async_get(hass)
    for key in (f"port_speed_{PORT1}", f"port_tx_{PORT1}", f"port_rx_{PORT1}"):
        entry = reg.async_get(eid(hass, "sensor", key))
        assert entry.options["sensor"]["suggested_display_precision"] == 0


async def test_extend_switch(hass: HomeAssistant, device) -> None:
    import dataclasses

    await setup(hass)
    entity = eid(hass, "switch", f"port_extend_{PORT1}")
    assert hass.states.get(entity).state == "off"  # factory mode 1000M full
    assert hass.states.get(entity).attributes["friendly_name"].endswith("Port 1 extend")
    await hass.services.async_call("switch", "turn_on", {"entity_id": entity}, blocking=True)
    device.set_port_mode.assert_awaited_with(PORT1, 2)  # 10M full duplex
    await hass.services.async_call("switch", "turn_off", {"entity_id": entity}, blocking=True)
    device.set_port_mode.assert_awaited_with(PORT1, 5)  # factory mode
    # the state follows the port mode of the device
    data = device.fetch.return_value
    ports = [dataclasses.replace(p, phy_mode=1 if p.index == PORT1 else p.phy_mode) for p in data.ports]
    device.fetch.return_value = dataclasses.replace(data, ports=ports)
    await hass.config_entries.async_reload(hass.config_entries.async_entries(DOMAIN)[0].entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(entity).state == "on"  # 10M half counts as extend as well
