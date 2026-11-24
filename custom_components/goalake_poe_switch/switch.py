"""Switches: PoE per port, flow control per port, device features (LLDP, storm control, ...)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GoalakeConfigEntry
from .api import MODE_DEFAULT, MODE_EXTEND, PORT_MODES, GoalakeClient
from .entity import GoalakeEntity


@dataclass(frozen=True, kw_only=True)
class FeatureDescription(SwitchEntityDescription):
    setting: str
    setter: Callable[[GoalakeClient], Callable[[bool], Any]]


FEATURES = (
    FeatureDescription(key="lldp", setting="lldp", setter=lambda c: c.set_lldp, entity_category=EntityCategory.CONFIG),
    FeatureDescription(key="storm_control", setting="storm", setter=lambda c: c.set_storm, entity_category=EntityCategory.CONFIG),
    FeatureDescription(key="watchdog", setting="watchdog", setter=lambda c: c.set_watchdog, entity_category=EntityCategory.CONFIG),
    FeatureDescription(key="ai_auto_extend", setting="ai_auto_extend", setter=lambda c: c.set_ai_auto_extend, entity_category=EntityCategory.CONFIG),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: GoalakeConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entities: list[SwitchEntity] = [FeatureSwitch(coordinator, d) for d in FEATURES]
    for port in coordinator.data.ports:
        # writes are limited to the PoE ports: an uplink may carry the management connection
        if port.is_poe:
            entities.append(PoeSwitch(coordinator, port.index))
            entities.append(ExtendSwitch(coordinator, port.index))
            entities.append(FlowControlSwitch(coordinator, port.index))
    async_add_entities(entities)


class PoeSwitch(GoalakeEntity, SwitchEntity):
    def __init__(self, coordinator, index: int) -> None:
        super().__init__(coordinator, "port_poe", index)

    @property
    def is_on(self) -> bool | None:
        return self.port.poe_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._write(self.coordinator.client.set_poe(self._index, True))

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._write(self.coordinator.client.set_poe(self._index, False))


class ExtendSwitch(GoalakeEntity, SwitchEntity):
    """Extend mode for long cables: the port runs at 10 Mbit/s. Off restores the factory mode."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:transmission-tower"

    def __init__(self, coordinator, index: int) -> None:
        super().__init__(coordinator, "port_extend", index)

    @property
    def is_on(self) -> bool | None:
        mode = PORT_MODES.get(self.port.phy_mode)
        return None if mode is None else mode in ("10m_half", "10m_full")

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._write(self.coordinator.client.set_port_mode(self._index, MODE_EXTEND))

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._write(self.coordinator.client.set_port_mode(self._index, MODE_DEFAULT))


class FlowControlSwitch(GoalakeEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator, index: int) -> None:
        super().__init__(coordinator, "port_flow_control", index)

    @property
    def is_on(self) -> bool | None:
        return self.port.flow_control

    async def _set(self, on: bool) -> None:
        flow = list(self.data.flow)
        flow[self._index] = 1 if on else 0
        await self._write(self.coordinator.client.set_flow(flow))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)


class FeatureSwitch(GoalakeEntity, SwitchEntity):
    entity_description: FeatureDescription

    def __init__(self, coordinator, description: FeatureDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        value = self.data.settings.get(self.entity_description.setting)
        return None if value is None else bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._write(self.entity_description.setter(self.coordinator.client)(True))

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._write(self.entity_description.setter(self.coordinator.client)(False))
