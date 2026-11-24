"""Base entities."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Any

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import GoalakeError, Port, SwitchData
from .const import DOMAIN
from .coordinator import GoalakeCoordinator


class GoalakeEntity(CoordinatorEntity[GoalakeCoordinator]):
    """An entity of the switch itself, or of one of its ports when `index` is given."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GoalakeCoordinator, key: str, index: int | None = None) -> None:
        super().__init__(coordinator)
        mac = coordinator.data.mac.replace(":", "").lower()
        self._index = index
        self._attr_translation_key = key
        self._attr_unique_id = f"{mac}_{key}" if index is None else f"{mac}_{key}_{index}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, mac)})
        if index is not None:
            self._attr_translation_placeholders = {"port": coordinator.data.ports[index].label}

    @property
    def data(self) -> SwitchData:
        return self.coordinator.data

    @property
    def port(self) -> Port:
        assert self._index is not None
        return self.coordinator.data.ports[self._index]

    async def _write(self, call: Awaitable[Any]) -> None:
        """Run a client write, report failures to the user, then refresh the state."""
        try:
            await call
        except GoalakeError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        await self.coordinator.async_refresh()  # not the debounced request: the state must not lag behind a write
