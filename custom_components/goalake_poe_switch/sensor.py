"""Sensors: supply voltage, power, temperature, per-port power, link speed and traffic."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfDataRate,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import GoalakeConfigEntry
from .api import Port, SwitchData
from .entity import GoalakeEntity


@dataclass(frozen=True, kw_only=True)
class DeviceSensorDescription(SensorEntityDescription):
    value_fn: Callable[[SwitchData], float | None]


@dataclass(frozen=True, kw_only=True)
class PortSensorDescription(SensorEntityDescription):
    value_fn: Callable[[Port], float | None]
    poe_only: bool = False


DEVICE_SENSORS = (
    DeviceSensorDescription(
        key="voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.voltage_v,
    ),
    DeviceSensorDescription(
        key="total_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.total_power_w,
    ),
    DeviceSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.temperature_c,
    ),
)

PORT_SENSORS = (
    PortSensorDescription(
        key="port_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        poe_only=True,
        value_fn=lambda p: p.power_w,
    ),
    PortSensorDescription(
        key="port_speed",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda p: p.speed_mbps,
    ),
    PortSensorDescription(
        key="port_tx",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda p: p.tx_kbps,
    ),
    PortSensorDescription(
        key="port_rx",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.KILOBITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda p: p.rx_kbps,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: GoalakeConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [DeviceSensor(coordinator, d) for d in DEVICE_SENSORS]
    for port in coordinator.data.ports:
        for desc in PORT_SENSORS:
            if desc.poe_only and not port.is_poe:
                continue
            entities.append(PortSensor(coordinator, desc, port.index))
    async_add_entities(entities)


class DeviceSensor(GoalakeEntity, SensorEntity):
    entity_description: DeviceSensorDescription

    def __init__(self, coordinator, description: DeviceSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        return self.entity_description.value_fn(self.data)


class PortSensor(GoalakeEntity, SensorEntity):
    entity_description: PortSensorDescription

    def __init__(self, coordinator, description: PortSensorDescription, index: int) -> None:
        super().__init__(coordinator, description.key, index)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        return self.entity_description.value_fn(self.port)
