"""Select: port mode (speed and duplex) of the PoE ports."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GoalakeConfigEntry
from .api import PORT_MODES
from .entity import GoalakeEntity

MODE_BY_OPTION = {name: value for value, name in PORT_MODES.items()}


async def async_setup_entry(
    hass: HomeAssistant, entry: GoalakeConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    # only the PoE ports: 'down' on an uplink could cut the management connection
    async_add_entities(PortMode(coordinator, p.index) for p in coordinator.data.ports if p.is_poe)


class PortMode(GoalakeEntity, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False
    _attr_options = list(PORT_MODES.values())

    def __init__(self, coordinator, index: int) -> None:
        super().__init__(coordinator, "port_mode", index)

    @property
    def current_option(self) -> str | None:
        return PORT_MODES.get(self.port.phy_mode)

    async def async_select_option(self, option: str) -> None:
        await self._write(self.coordinator.client.set_port_mode(self._index, MODE_BY_OPTION[option]))
