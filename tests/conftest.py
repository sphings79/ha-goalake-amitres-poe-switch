"""Shared fixtures for the tests that run with the Home Assistant plugin."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

CLIENT = "custom_components.goalake_poe_switch.api.GoalakeClient"
WRITES = (
    "set_poe", "set_port_mode", "restart_port", "set_flow", "set_priority", "set_limits",
    "set_lldp", "set_storm", "set_watchdog", "set_ai_auto_extend", "set_power_warn", "reboot",
)


@pytest.fixture
def device():
    """Patch every client method that talks to the switch."""
    import json
    from pathlib import Path

    from custom_components.goalake_poe_switch import api

    fixture = Path(__file__).parent.parent / "dev-sim" / "fixtures" / "gps208.json"
    data = api.parse_all(json.loads(fixture.read_text()))
    mocks = {}
    patches = [
        patch(f"{CLIENT}.is_switch", AsyncMock(return_value=True)),
        patch(f"{CLIENT}.validate", AsyncMock(return_value=None)),
        patch(f"{CLIENT}.fetch_all", AsyncMock(return_value=data)),
        patch(f"{CLIENT}.close", AsyncMock(return_value=None)),
        # no network scan in tests (the scanner and the flow both call it)
        patch("custom_components.goalake_poe_switch.scanner.async_scan", AsyncMock(return_value=[])),
        patch("custom_components.goalake_poe_switch.config_flow.async_scan", AsyncMock(return_value=[])),
        *[patch(f"{CLIENT}.{name}", AsyncMock(return_value=None)) for name in WRITES],
    ]
    names = ["is_switch", "validate", "fetch", "close", "scan", "flow_scan", *WRITES]
    for name, p in zip(names, patches):
        mocks[name] = p.start()
    yield type("Mocks", (), mocks)
    for p in patches:
        p.stop()
