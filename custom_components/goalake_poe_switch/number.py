"""Numbers: PoE warning threshold, per-port priority and rate limits."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import EntityCategory, UnitOfDataRate, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GoalakeConfigEntry
from .api import LIMIT_FACTOR
from .entity import GoalakeEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: GoalakeConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entities: list[NumberEntity] = [PowerWarn(coordinator)]
    for port in coordinator.data.ports:
        if port.is_poe:  # an uplink may carry the management connection
            entities += [
                PortPriority(coordinator, port.index),
                PortLimit(coordinator, port.index, "up"),
                PortLimit(coordinator, port.index, "down"),
            ]
    async_add_entities(entities)


class PowerWarn(GoalakeEntity, NumberEntity):
    """Total PoE power warning threshold. The web UI shows no bounds; 0 is the current factory value."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = NumberDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_native_min_value = 0
    _attr_native_max_value = 1000
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "power_warn")

    @property
    def native_value(self) -> float | None:
        return self.data.settings.get("power_warn")

    async def async_set_native_value(self, value: float) -> None:
        await self._write(self.coordinator.client.set_power_warn(int(value)))


class PortPriority(GoalakeEntity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False
    _attr_native_min_value = 0
    _attr_native_max_value = 6  # range of the web UI
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, index: int) -> None:
        super().__init__(coordinator, "port_priority", index)

    @property
    def native_value(self) -> float | None:
        return self.port.priority

    async def async_set_native_value(self, value: float) -> None:
        prio = list(self.data.priority)
        prio[self._index] = int(value)
        await self._write(self.coordinator.client.set_priority(prio))


class PortLimit(GoalakeEntity, NumberEntity):
    """Rate limit in Mbit/s, 0 = unlimited. The device stores kbit/s (Mbit/s * 1024)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False
    _attr_native_unit_of_measurement = UnitOfDataRate.MEGABITS_PER_SECOND
    _attr_native_min_value = 0
    _attr_native_max_value = 1000  # range of the web UI
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, index: int, direction: str) -> None:
        super().__init__(coordinator, f"port_limit_{direction}", index)
        self._direction = direction

    @property
    def native_value(self) -> float | None:
        raw = self.port.limit_up if self._direction == "up" else self.port.limit_down
        return None if raw is None else raw / LIMIT_FACTOR

    async def async_set_native_value(self, value: float) -> None:
        up, down = list(self.data.limit_up), list(self.data.limit_down)
        (up if self._direction == "up" else down)[self._index] = int(value) * LIMIT_FACTOR
        await self._write(self.coordinator.client.set_limits(up, down))
