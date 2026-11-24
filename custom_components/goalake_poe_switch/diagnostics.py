"""Diagnostics with secrets redacted."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import GoalakeConfigEntry

TO_REDACT = {"password", "host", "mac", "serial", "ip", "gw", "mask", "dns", "unique_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: GoalakeConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(
            {"data": dict(entry.data), "options": dict(entry.options), "unique_id": entry.unique_id},
            TO_REDACT,
        ),
        "last_update_success": coordinator.last_update_success,
        "data": async_redact_data(asdict(coordinator.data), TO_REDACT),
    }
