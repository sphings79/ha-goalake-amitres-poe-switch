"""Buttons: restart a PoE port, reboot the switch."""

from __future__ import annotations

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GoalakeConfigEntry
from .entity import GoalakeEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: GoalakeConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entities: list[ButtonEntity] = [RebootButton(coordinator)]
    entities += [RestartPortButton(coordinator, p.index) for p in coordinator.data.ports if p.is_poe]
    async_add_entities(entities)


class RestartPortButton(GoalakeEntity, ButtonEntity):
    """Power-cycles a port (web UI action 'reboot port')."""

    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, index: int) -> None:
        super().__init__(coordinator, "port_restart", index)

    async def async_press(self) -> None:
        await self._write(self.coordinator.client.restart_port(self._index))


class RebootButton(GoalakeEntity, ButtonEntity):
    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "reboot")

    async def async_press(self) -> None:
        await self._write(self.coordinator.client.reboot())
