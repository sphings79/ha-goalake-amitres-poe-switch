"""Config flow, setup and diagnostics tests. The device client is patched, no network."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.goalake_poe_switch import api
from custom_components.goalake_poe_switch.const import CONF_SCAN_INTERVAL, DOMAIN

FIXTURE = Path(__file__).parent.parent / "dev-sim" / "fixtures" / "gps208.json"
DATA = api.parse_all(json.loads(FIXTURE.read_text()))
MAC = "020000000001"
PW = "S3cret-Pw!x"
CLIENT = "custom_components.goalake_poe_switch.api.GoalakeClient"


@pytest.fixture(autouse=True)
def _enable(enable_custom_integrations):
    yield


def make_entry(**kw) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=MAC,
        title="GPS208 (0001)",
        data={CONF_HOST: "192.0.2.10", CONF_PASSWORD: PW},
        **kw,
    )


async def test_user_flow(hass: HomeAssistant, device) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: " 192.0.2.10 ", CONF_PASSWORD: PW}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "GPS208 (0001)"
    assert result["data"] == {CONF_HOST: "192.0.2.10", CONF_PASSWORD: PW}
    assert result["result"].unique_id == MAC
    device.close.assert_awaited()  # the single session was freed again


@pytest.mark.parametrize(
    ("exc", "error"),
    [(api.InvalidAuth("x"), "invalid_auth"), (api.CannotConnect("x"), "cannot_connect"), (RuntimeError("x"), "unknown")],
)
async def test_user_flow_errors_then_success(hass: HomeAssistant, device, exc, error) -> None:
    device.validate.side_effect = exc
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.0.2.10", CONF_PASSWORD: PW}
    )
    assert result["type"] is FlowResultType.FORM and result["errors"] == {"base": error}
    device.validate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.0.2.10", CONF_PASSWORD: PW}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_not_a_switch(hass: HomeAssistant, device) -> None:
    device.is_switch.return_value = False
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.0.2.10", CONF_PASSWORD: PW}
    )
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_already_configured_updates_host(hass: HomeAssistant, device) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    with patch("custom_components.goalake_poe_switch.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "192.0.2.77", CONF_PASSWORD: PW}
        )
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == "192.0.2.77"


DHCP = DhcpServiceInfo(ip="192.0.2.20", hostname="switch", macaddress=MAC)


async def test_dhcp_flow(hass: HomeAssistant, device) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "dhcp"}, data=DHCP)
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "discovery_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_PASSWORD: PW})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: "192.0.2.20", CONF_PASSWORD: PW}
    assert result["result"].unique_id == MAC


async def test_dhcp_not_a_switch(hass: HomeAssistant, device) -> None:
    device.is_switch.return_value = False
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "dhcp"}, data=DHCP)
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "not_supported"


async def test_dhcp_updates_host_of_existing_entry(hass: HomeAssistant, device) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    with patch("custom_components.goalake_poe_switch.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "dhcp"}, data=DHCP)
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == "192.0.2.20"


async def test_setup_registers_device_and_unloads(hass: HomeAssistant, device) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is config_entries.ConfigEntryState.LOADED
    # works on old and new Home Assistant versions (async_get_device is deprecated in recent ones)
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    dev = next((d for d in devices if (DOMAIN, MAC) in d.identifiers), None)
    assert dev and dev.model == "GPS208" and dev.sw_version == "6.1.260430"
    device.fetch.assert_awaited()
    device.close.reset_mock()
    assert await hass.config_entries.async_unload(entry.entry_id)
    device.close.assert_awaited_once()  # logout on unload


async def test_setup_auth_failure_starts_reauth(hass: HomeAssistant, device) -> None:
    device.fetch.side_effect = api.InvalidAuth("x")
    entry = make_entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is config_entries.ConfigEntryState.SETUP_ERROR
    assert any(f["context"]["source"] == "reauth" for f in hass.config_entries.flow.async_progress())


async def test_setup_unreachable_retries(hass: HomeAssistant, device) -> None:
    device.fetch.side_effect = api.CannotConnect("x")
    entry = make_entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is config_entries.ConfigEntryState.SETUP_RETRY
    assert entry.error_reason_translation_key == "cannot_connect"  # the user sees a readable text


async def test_reauth_flow(hass: HomeAssistant, device) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    with patch("custom_components.goalake_poe_switch.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_PASSWORD: "New-Pw-456"})
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "New-Pw-456"


async def test_reauth_wrong_device(hass: HomeAssistant, device) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    device.fetch.return_value = api.parse_all({**json.loads(FIXTURE.read_text()), "detail": {**json.loads(FIXTURE.read_text())["detail"], "mac": "0200000000ff"}})
    result = await entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_PASSWORD: PW})
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "wrong_device"


async def test_reconfigure_flow(hass: HomeAssistant, device) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    with patch("custom_components.goalake_poe_switch.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "192.0.2.99", CONF_PASSWORD: PW}
        )
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == "192.0.2.99"


async def test_options_flow(hass: HomeAssistant, device) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {CONF_SCAN_INTERVAL: 60})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_SCAN_INTERVAL] == 60
    await hass.async_block_till_done()
    assert entry.runtime_data.update_interval.total_seconds() == 60


async def test_diagnostics_redacts_secrets(hass: HomeAssistant, device) -> None:
    from custom_components.goalake_poe_switch.diagnostics import async_get_config_entry_diagnostics

    entry = make_entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    text = json.dumps(await async_get_config_entry_diagnostics(hass, entry))
    for secret in (PW, "192.0.2.10", MAC, DATA.serial, "192.0.2.1"):
        assert secret not in text
    assert "ports" in text and "6.1.260430" in text
