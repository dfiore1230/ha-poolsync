from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

from .const import DOMAIN, COORDINATOR_NAME, CONF_DEVICE_INDEX, CONF_ASSUME_FAHRENHEIT
from .coordinator import PoolSyncCoordinator

_LOGGER = logging.getLogger(__name__)

# path tuples relative to coordinator.data; ('devices', ...) means devices["<index>"] first
SPECS = [
    # Temperatures
    (("devices","status","waterTemp"), "Pool Water Temperature", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, SensorStateClass.MEASUREMENT, True),
    (("poolSync","status","boardTemp"), "Controller Board Temperature", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, SensorStateClass.MEASUREMENT, False),

    # Requested list (exact names/units)
    (("devices","status","flowRate"), "Pool Salt Cell Flow Rate", None, "gal/min", SensorStateClass.MEASUREMENT, False),
    (("devices","status","saltPPM"), "Pool Salt Cell PPM", None, "ppm", SensorStateClass.MEASUREMENT, False),
    (("devices","config","chlorOutput"), "Pool Salt Cell Output", None, "%", SensorStateClass.MEASUREMENT, False),
    (("devices","status","boostRemaining"), "Pool Salt Cell Output Boost", None, "min", SensorStateClass.MEASUREMENT, False),

    # Diagnostics
    (("poolSync","status","rssi"), "Controller RSSI", None, "dBm", SensorStateClass.MEASUREMENT, False),
    (("devices","config","gallons"), "Pool Volume", None, "gal", SensorStateClass.MEASUREMENT, False),
    (("devices","config","polarityChangeTime"), "Polarity Change Time", None, "h", SensorStateClass.MEASUREMENT, False),
    (("devices","status","cellRailVoltage"), "Cell Rail Voltage", None, "mV", SensorStateClass.MEASUREMENT, False),
    (("devices","status","cellRawSaltADC"), "Cell Raw Salt ADC", None, None, SensorStateClass.MEASUREMENT, False),

    # Online
    (("devices","nodeAttr","online"), "Device Online", None, None, None, False),
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: PoolSyncCoordinator = data[COORDINATOR_NAME]
    device_index = entry.data.get(CONF_DEVICE_INDEX, "0")
    assume_f = entry.data.get(CONF_ASSUME_FAHRENHEIT, False)

    ents: list[SensorEntity] = []
    for path, name, dclass, unit, sclass, is_temp in SPECS:
        ents.append(PoolSyncSensor(coordinator, entry, device_index, name, path, dclass, unit, sclass, is_temp, assume_f))

    # Attribute sensors
    ents.append(PoolSyncAttrSensor(
        coordinator, entry,
        name="Pool Salt Cell System Details",
        unique_key="cell_system_details",
        state_path=("devices", str(device_index), "nodeAttr", "name"),
        attrs_path=("devices", str(device_index), "system"),
        attrs_keys=["drvFwVersion","cellFwVersion","cellHwVersion","cellCalib","numBlades","cellSerialNum"],
    ))
    ents.append(PoolSyncAttrSensor(
        coordinator, entry,
        name="PoolSync System Details",
        unique_key="poolsync_system_details",
        state_path=("poolSync", "config", "name"),
        attrs_path=("poolSync", "system"),
        attrs_keys=["macAddr","bssid","fwVersion","hwVersion"],
    ))
    ents.append(PoolSyncAttrSensor(
        coordinator, entry,
        name="PoolSync System Status",
        unique_key="poolsync_system_status",
        state_path=("poolSync", "status", "online"),
        attrs_path=("poolSync", "status"),
        attrs_keys=["online","rssi","boardTemp"],
    ))

    async_add_entities(ents, True)

class PoolSyncSensor(CoordinatorEntity[PoolSyncCoordinator], SensorEntity):
    def __init__(self, coordinator, entry, device_index, name, path, dclass, unit, sclass, is_temp, assume_f) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._device_index = str(device_index)
        self._name = name
        self._path = path
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{'_'.join(path)}"
        self._attr_device_class = dclass
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = sclass
        self._is_temp = is_temp
        self._assume_f = assume_f

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data or {}
        sys = ((data.get("poolSync") or {}).get("system") or {})
        mac = sys.get("macAddr")
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            manufacturer="PoolSync",
            name="PoolSync Bridge",
            sw_version=str(sys.get("fwVersion", "")),
            model=str(sys.get("hwVersion", "")),
            connections={(CONNECTION_NETWORK_MAC, mac)} if mac else None,
        )

    def _walk(self) -> Optional[Any]:
        data = self.coordinator.data or {}
        node: Any = data
        if self._path and self._path[0] == "devices":
            devices = data.get("devices")
            if not isinstance(devices, dict):
                return None
            node = devices.get(str(self._device_index))
            if not isinstance(node, dict):
                return None
            keys = self._path[1:]
        else:
            keys = self._path

        for k in keys:
            if not isinstance(node, dict):
                return None
            node = node.get(k)
        return node

    @property
    def native_value(self) -> Optional[Any]:
        val = self._walk()
        if val is None:
            return None
        if self._is_temp and isinstance(val, (int, float)):
            if self._assume_f or val > 45:  # looks like °F
                return round((val - 32) * 5.0 / 9.0, 1)
            return round(float(val), 1)
        return val

    @property
    def available(self) -> bool:
        return super().available and (self._walk() is not None)

class PoolSyncAttrSensor(CoordinatorEntity[PoolSyncCoordinator], SensorEntity):
    _attr_icon = "mdi:information-outline"
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, name, unique_key, state_path, attrs_path, attrs_keys):
        super().__init__(coordinator)
        self._entry = entry
        self._name = name
        self._state_path = state_path
        self._attrs_path = attrs_path
        self._attrs_keys = attrs_keys or []
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{unique_key}"

    def _get_path(self, path):
        data = self.coordinator.data or {}
        node = data
        for k in path:
            if not isinstance(node, dict):
                return None
            node = node.get(k)
        return node

    @property
    def native_value(self):
        if not self._state_path:
            return "OK"
        val = self._get_path(self._state_path)
        if isinstance(val, bool):
            return "Online" if val else "Offline"
        return val if val is not None else "Unknown"

    @property
    def extra_state_attributes(self):
        base = self._get_path(self._attrs_path)
        if not isinstance(base, dict):
            return None
        out = {}
        for k in self._attrs_keys:
            out[k] = base.get(k)
        return out
