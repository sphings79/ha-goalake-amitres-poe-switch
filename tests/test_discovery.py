"""Multicast discovery: protocol helpers, the user step with found switches, the scanner."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.goalake_poe_switch import discovery, scanner
from custom_components.goalake_poe_switch.const import DOMAIN

MAC = "020000000001"
FOUND = {"ip": "192.0.2.20", "sn": "GPS208000000000SIMULATED00", "mac": "02:00:00:00:00:01", "model": "GPS208 V3", "V": "6.1.260430"}


# -- protocol helpers (plain functions, verified against a real switch) ------------------------


@pytest.mark.parametrize(
    ("plain", "cipher"),
    [
        (b"hello", "qGWMrK8="),
        (b"12345678", "l9h5AdwHcYQ="),
        (
            b'{"cmd":"calludp","syn":"abcd1234","data":{"callcmd":"search"}}',
            "CmxVP+dXWNlTvt1GA1kXn8JbNB96mZ4Lh4+UnMiABIHd7rODRYWz0VNpheN0rzB9mOaJW1UHV5OyY4hivV0=",
        ),
    ],
)
def test_encryption_vectors(plain: bytes, cipher: str) -> None:
    assert discovery.encrypt(plain) == cipher
    assert discovery.decrypt(cipher) == plain


def test_round_trip_for_every_length() -> None:
    for n in range(0, 70):
        data = bytes((i * 31 + n) % 256 for i in range(n))
        assert discovery.decrypt(discovery.encrypt(data)) == data


def test_search_request_content() -> None:
    packet = discovery.build_search("abcd1234")
    assert packet.endswith(b"\r\n")
    assert json.loads(discovery.decrypt(packet.decode().strip())) == {
        "cmd": "calludp", "syn": "abcd1234", "data": {"callcmd": "search"}
    }


def reply(syn: str, **over) -> bytes:
    message = {"ack": "calludp", "syn": syn, "errcode": 0, "data": {"sn": "X", "ip": "192.0.2.5", **over}}
    return (discovery.encrypt(json.dumps(message).encode()) + "\r\n").encode()


def test_parse_reply() -> None:
    assert discovery.parse_reply(reply("abcd1234"), "abcd1234")["ip"] == "192.0.2.5"
    assert discovery.parse_reply(reply("other"), "abcd1234") is None  # not our request
    assert discovery.parse_reply(b"garbage!!\r\n", "abcd1234") is None
    assert discovery.parse_reply(b"", "abcd1234") is None
    assert discovery.parse_reply((discovery.encrypt(b"not json") + "\r\n").encode(), "abcd1234") is None


def test_syn_is_random_alphanumeric() -> None:
    a, b = discovery.new_syn(), discovery.new_syn()
    assert len(a) == 8 and a.isalnum() and a != b


# -- config flow --------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _enable(enable_custom_integrations):
    yield


async def test_user_step_offers_found_switches(hass: HomeAssistant, device) -> None:
    with patch("custom_components.goalake_poe_switch.config_flow.async_scan", AsyncMock(return_value=[FOUND])):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    host_selector = next(v for k, v in result["data_schema"].schema.items() if k == CONF_HOST)
    options = host_selector.config["options"]
    assert options == [{"value": "192.0.2.20", "label": "GPS208 V3 (192.0.2.20)"}]
    assert host_selector.config["custom_value"] is True  # typing another address stays possible
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_HOST: "192.0.2.20", CONF_PASSWORD: "pw-123456"})
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_step_hides_configured_switches(hass: HomeAssistant, device) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id=MAC, data={CONF_HOST: "192.0.2.20", CONF_PASSWORD: "x"}).add_to_hass(hass)
    with patch("custom_components.goalake_poe_switch.config_flow.async_scan", AsyncMock(return_value=[FOUND])):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert next(v for k, v in result["data_schema"].schema.items() if k == CONF_HOST) is str


async def test_integration_discovery_flow(hass: HomeAssistant, device) -> None:
    info = {CONF_HOST: "192.0.2.20", "mac": MAC, "model": "GPS208 V3", "firmware": "6.1.260430"}
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "integration_discovery"}, data=info)
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "discovery_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_PASSWORD: "pw-123456"})
    assert result["type"] is FlowResultType.CREATE_ENTRY and result["result"].unique_id == MAC


# -- background scanner -------------------------------------------------------------------------


async def test_scanner_reports_new_switch(hass: HomeAssistant) -> None:
    with (
        patch.object(scanner, "async_scan", AsyncMock(return_value=[FOUND])),
        patch.object(scanner.discovery_flow, "async_create_flow") as create,
    ):
        await scanner._scan_and_report(hass)
    create.assert_called_once()
    assert create.call_args.kwargs["data"] == {CONF_HOST: "192.0.2.20", "mac": MAC, "model": "GPS208 V3", "firmware": "6.1.260430"}


async def test_scanner_follows_a_changed_address(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=MAC, data={CONF_HOST: "192.0.2.99", CONF_PASSWORD: "x"})
    entry.add_to_hass(hass)
    with (
        patch.object(scanner, "async_scan", AsyncMock(return_value=[FOUND])),
        patch.object(scanner.discovery_flow, "async_create_flow") as create,
        patch.object(hass.config_entries, "async_schedule_reload") as reload,
    ):
        await scanner._scan_and_report(hass)
    assert entry.data[CONF_HOST] == "192.0.2.20" and entry.data[CONF_PASSWORD] == "x"
    reload.assert_called_once_with(entry.entry_id)
    create.assert_not_called()


async def test_scanner_ignores_a_known_switch_at_the_same_address(hass: HomeAssistant) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id=MAC, data={CONF_HOST: "192.0.2.20", CONF_PASSWORD: "x"}).add_to_hass(hass)
    with (
        patch.object(scanner, "async_scan", AsyncMock(return_value=[FOUND])),
        patch.object(scanner.discovery_flow, "async_create_flow") as create,
        patch.object(hass.config_entries, "async_schedule_reload") as reload,
    ):
        await scanner._scan_and_report(hass)
    create.assert_not_called()
    reload.assert_not_called()


async def test_scan_survives_failing_interfaces(hass: HomeAssistant) -> None:
    with (
        patch("custom_components.goalake_poe_switch.scanner.network.async_get_enabled_source_ips", AsyncMock(return_value=[])),
        patch.object(scanner.discovery, "discover", side_effect=OSError("no route")),
    ):
        assert await scanner.async_scan(hass) == []
