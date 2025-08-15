import os
import sys
import types

# Ensure repository root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Stub custom_components package to avoid executing __init__ modules
custom_components_pkg = types.ModuleType("custom_components")
custom_components_pkg.__path__ = [os.path.join(os.path.dirname(__file__), "..", "custom_components")]
sys.modules.setdefault("custom_components", custom_components_pkg)

poolsync_pkg = types.ModuleType("custom_components.poolsync")
poolsync_pkg.__path__ = [os.path.join(custom_components_pkg.__path__[0], "poolsync")]
sys.modules["custom_components.poolsync"] = poolsync_pkg

const_stub = types.ModuleType("custom_components.poolsync.const")
const_stub.DOMAIN = "poolsync"
sys.modules["custom_components.poolsync.const"] = const_stub

coordinator_stub = types.ModuleType("custom_components.poolsync.coordinator")
class PoolSyncCoordinator:
    pass
coordinator_stub.PoolSyncCoordinator = PoolSyncCoordinator
sys.modules["custom_components.poolsync.coordinator"] = coordinator_stub

# Stub homeassistant modules used by sensor
ha = types.ModuleType("homeassistant")
sys.modules.setdefault("homeassistant", ha)

components = types.ModuleType("homeassistant.components")
sys.modules["homeassistant.components"] = components

sensor_mod = types.ModuleType("homeassistant.components.sensor")
sys.modules["homeassistant.components.sensor"] = sensor_mod

sensor_const_mod = types.ModuleType("homeassistant.components.sensor.const")
sys.modules["homeassistant.components.sensor.const"] = sensor_const_mod

helpers_mod = types.ModuleType("homeassistant.helpers")
sys.modules["homeassistant.helpers"] = helpers_mod

update_coordinator_mod = types.ModuleType("homeassistant.helpers.update_coordinator")
sys.modules["homeassistant.helpers.update_coordinator"] = update_coordinator_mod

entity_platform_mod = types.ModuleType("homeassistant.helpers.entity_platform")
sys.modules["homeassistant.helpers.entity_platform"] = entity_platform_mod

core_mod = types.ModuleType("homeassistant.core")
sys.modules["homeassistant.core"] = core_mod

config_entries_mod = types.ModuleType("homeassistant.config_entries")
sys.modules["homeassistant.config_entries"] = config_entries_mod

typing_mod = types.ModuleType("homeassistant.helpers.typing")
typing_mod.ConfigType = dict
sys.modules["homeassistant.helpers.typing"] = typing_mod

ha_const_mod = types.ModuleType("homeassistant.const")
sys.modules["homeassistant.const"] = ha_const_mod

class Dummy:
    pass

class SensorEntity:
    pass

from dataclasses import dataclass

@dataclass(frozen=True)
class SensorEntityDescription:
    key: str = ""
    name: str | None = None
    device_class: str | None = None
    native_unit_of_measurement: str | None = None

sensor_mod.SensorEntity = SensorEntity
sensor_mod.SensorEntityDescription = SensorEntityDescription

class SensorDeviceClass:
    TEMPERATURE = "temperature"
    SIGNAL_STRENGTH = "signal_strength"
    DURATION = "duration"
    VOLTAGE = "voltage"
    CURRENT = "current"

sensor_const_mod.SensorDeviceClass = SensorDeviceClass
class CoordinatorEntity:
    @classmethod
    def __class_getitem__(cls, item):
        return cls

update_coordinator_mod.CoordinatorEntity = CoordinatorEntity
entity_platform_mod.AddEntitiesCallback = Dummy
core_mod.HomeAssistant = Dummy
config_entries_mod.ConfigEntry = Dummy

class UnitOfTemperature:
    CELSIUS = "°C"

class UnitOfElectricPotential:
    VOLT = "V"

class UnitOfElectricCurrent:
    AMPERE = "A"

class UnitOfTime:
    SECONDS = "s"
    MINUTES = "min"

ha_const_mod.UnitOfTemperature = UnitOfTemperature
ha_const_mod.UnitOfElectricPotential = UnitOfElectricPotential
ha_const_mod.UnitOfElectricCurrent = UnitOfElectricCurrent
ha_const_mod.UnitOfTime = UnitOfTime
ha_const_mod.SIGNAL_STRENGTH_DECIBELS_MILLIWATT = "dBm"
ha_const_mod.PERCENTAGE = "%"
