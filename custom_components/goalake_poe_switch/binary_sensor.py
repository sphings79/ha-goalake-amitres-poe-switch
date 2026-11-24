"""Binary sensors: link state per port, cloud connection."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GoalakeConfigEntry
from .entity import GoalakeEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: GoalakeConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = [PortLink(coordinator, p.index) for p in coordinator.data.ports]
    entities.append(CloudConnected(coordinator))
    async_add_entities(entities)


class PortLink(GoalakeEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, index: int) -> None:
        super().__init__(coordinator, "port_link", index)

    @property
    def is_on(self) -> bool:
        return self.port.connected


class CloudConnected(GoalakeEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "cloud")

    @property
    def is_on(self) -> bool | None:
        status = self.data.cloud_status
        return None if status is None else bool(status)
