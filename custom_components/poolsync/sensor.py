from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfElectricPotential,
    UnitOfElectricCurrent,
    UnitOfTime,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    PERCENTAGE,
)
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .coordinator import PoolSyncCoordinator
from .const import DOMAIN
from .util import _g


@dataclass(frozen=True)
class PoolSyncSensorDesc(SensorEntityDescription):
    """Extend SensorEntityDescription with a value extractor."""
    value_fn: Callable[[dict[str, Any]], Any] | None = None
    attr_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _dev0(data: dict) -> dict:
    return _g(data, "devices", "0", default={}) or {}


# ---------- Value helpers / unit conversions ----------
def _mv_to_v(mv: Any) -> Optional[float]:
    try:
        return round(float(mv) / 1000.0, 3)
    except Exception:
        return None


def _ma_to_a(ma: Any) -> Optional[float]:
    try:
        return round(float(ma) / 1000.0, 3)
    except Exception:
        return None


# ---------- Sensor map ----------
SENSORS: list[PoolSyncSensorDesc] = [
    # --- PoolSync hub stats/system ---
    PoolSyncSensorDesc(
        key="board_temp_c",
        name="PoolSync Board Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: _g(d, "poolSync", "status", "boardTemp"),
    ),
    PoolSyncSensorDesc(
        key="rssi_dbm",
        name="PoolSync RSSI",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        value_fn=lambda d: _g(d, "poolSync", "status", "rssi"),
    ),
    PoolSyncSensorDesc(
        key="uptime_secs",
        name="PoolSync Uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda d: _g(d, "poolSync", "stats", "upTimeSecs"),
    ),
    PoolSyncSensorDesc(
        key="device_info",
        name="PoolSync System Details",
        value_fn=lambda d: _g(d, "poolSync", "config", "name"),
        attr_fn=lambda d: {
            "macAddr": _g(d, "poolSync", "system", "macAddr"),
            "bssid": _g(d, "poolSync", "system", "bssid"),
            "fwVersion": _g(d, "poolSync", "system", "fwVersion"),
            "hwVersion": _g(d, "poolSync", "system", "hwVersion"),
        },
    ),
    PoolSyncSensorDesc(
        key="status_info",
        name="PoolSync Status",
        value_fn=lambda d: "online" if _g(d, "poolSync", "status", "online") else "offline",
        attr_fn=lambda d: {
            "online": _g(d, "poolSync", "status", "online"),
            "flags": _g(d, "poolSync", "status", "flags"),
            "dateTime": _g(d, "poolSync", "status", "dateTime"),
        },
    ),
    PoolSyncSensorDesc(
        key="diagnostics",
        name="PoolSync Diagnostics",
        value_fn=lambda d: "diagnostics",
        attr_fn=lambda d: {
            "wifiDisconnects": _g(d, "poolSync", "stats", "wifiDisconnects"),
            "awsDisconnects": _g(d, "poolSync", "stats", "awsDisconnects"),
            "minRssi": _g(d, "poolSync", "stats", "minRssi"),
            "maxRssi": _g(d, "poolSync", "stats", "maxRssi"),
            "minBoardTemp": _g(d, "poolSync", "stats", "minBoardTemp"),
            "maxBoardTemp": _g(d, "poolSync", "stats", "maxBoardTemp"),
            "systemRestarts": _g(d, "poolSync", "stats", "systemRestarts"),
            "numDeviceMsgNoResp": _g(d, "poolSync", "stats", "numDeviceMsgNoResp"),
        },
    ),

    # --- Device 0: ChlorSync status / config ---
    PoolSyncSensorDesc(
        key="water_temp_c",
        name="Pool Water Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: _g(_dev0(d), "status", "waterTemp"),
    ),
    PoolSyncSensorDesc(
        key="flow_rate_gpm",
        name="Salt Cell Flow Rate",
        native_unit_of_measurement="gal/min",
        value_fn=lambda d: _g(_dev0(d), "status", "flowRate"),
    ),
    PoolSyncSensorDesc(
        key="salt_ppm",
        name="Salt PPM",
        native_unit_of_measurement="ppm",
        value_fn=lambda d: _g(_dev0(d), "status", "saltPPM"),
    ),
    PoolSyncSensorDesc(
        key="chlor_output_pct",
        name="Chlor Output",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: _g(_dev0(d), "config", "chlorOutput"),
    ),
    PoolSyncSensorDesc(
        key="boost_remaining_min",
        name="Chlor Boost Remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda d: _g(_dev0(d), "status", "boostRemaining"),
    ),
    PoolSyncSensorDesc(
        key="raw_salt_adc",
        name="Cell Raw Salt ADC",
        value_fn=lambda d: _g(_dev0(d), "status", "cellRawSaltADC"),
    ),
    PoolSyncSensorDesc(
        key="cell_rail_voltage_v",
        name="Cell Rail Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda d: _mv_to_v(_g(_dev0(d), "status", "cellRailVoltage")),
    ),
    PoolSyncSensorDesc(
        key="fwd_current_a",
        name="Cell Forward Current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda d: _ma_to_a(_g(_dev0(d), "status", "fwdCurrent")),
    ),
    PoolSyncSensorDesc(
        key="rev_current_a",
        name="Cell Reverse Current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda d: _ma_to_a(_g(_dev0(d), "status", "revCurrent")),
    ),
    PoolSyncSensorDesc(
        key="out_voltage_v",
        name="Cell Output Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda d: _mv_to_v(_g(_dev0(d), "status", "outVoltage")),
    ),
    PoolSyncSensorDesc(
        key="device_config",
        name="ChlorSync Config",
        value_fn=lambda d: _g(_dev0(d), "nodeAttr", "name") or "ChlorSync",
        attr_fn=lambda d: {
            "poolCoverCtrl": _g(_dev0(d), "config", "poolCoverCtrl"),
            "gallons": _g(_dev0(d), "config", "gallons"),
            "polarityChangeTime": _g(_dev0(d), "config", "polarityChangeTime"),
            "userSaltCalib": _g(_dev0(d), "config", "userSaltCalib"),
        },
    ),
    PoolSyncSensorDesc(
        key="cell_system",
        name="Cell System",
        value_fn=lambda d: _g(_dev0(d), "nodeAttr", "name") or "ChlorSync",
        attr_fn=lambda d: {
            "drvFwVersion": _g(_dev0(d), "system", "drvFwVersion"),
            "cellFwVersion": _g(_dev0(d), "system", "cellFwVersion"),
            "cellHwVersion": _g(_dev0(d), "system", "cellHwVersion"),
            "cellCalib": _g(_dev0(d), "system", "cellCalib"),
            "numBlades": _g(_dev0(d), "system", "numBlades"),
            "cellSerialNum": _g(_dev0(d), "system", "cellSerialNum"),
        },
    ),
    PoolSyncSensorDesc(
        key="cell_faults",
        name="Cell Faults",
        value_fn=lambda d: (_g(_dev0(d), "faults") or [0])[0],
    ),
    PoolSyncSensorDesc(
        key="device_stats",
        name="ChlorSync Stats",
        value_fn=lambda d: "stats",
        attr_fn=lambda d: {
            "stat0": _g(_dev0(d), "stats", 0),
            "stat1": _g(_dev0(d), "stats", 1),
            "stat2": _g(_dev0(d), "stats", 2),
            "stat3": _g(_dev0(d), "stats", 3),
            "stat4": _g(_dev0(d), "stats", 4),
            "stat5": _g(_dev0(d), "stats", 5),
            "stat6": _g(_dev0(d), "stats", 6),
            "stat7": _g(_dev0(d), "stats", 7),
            "stat8": _g(_dev0(d), "stats", 8),
            "stat9": _g(_dev0(d), "stats", 9),
        },
    ),
]


class PoolSyncSensor(CoordinatorEntity[PoolSyncCoordinator], SensorEntity):
    """Generic PoolSync sensor wired to the coordinator."""

    entity_description: PoolSyncSensorDesc

    def __init__(
        self,
        coordinator: PoolSyncCoordinator,
        entry: ConfigEntry,
        description: PoolSyncSensorDesc,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description

        mac = coordinator.api.mac_address or entry.data.get("mac") or "poolsync"
        self._attr_unique_id = f"{mac}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_name = description.name
        self._attr_native_value = None

        # Device info groups all sensors under the PoolSync device
        self._attr_device_info = {
            "identifiers": {(DOMAIN, mac)},
            "manufacturer": "AquaCal",
            "name": "PoolSync",
            "sw_version": str(_g(self.coordinator.data or {}, "poolSync", "system", "fwVersion")),
            "model": "PoolSync",
        }

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if self.entity_description.value_fn:
            try:
                return self.entity_description.value_fn(data)
            except Exception:
                return None
        return None

    @property
    def extra_state_attributes(self) -> Optional[dict[str, Any]]:
        data = self.coordinator.data or {}
        if self.entity_description.attr_fn:
            try:
                return self.entity_description.attr_fn(data)
            except Exception:
                return None
        return None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PoolSyncCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[PoolSyncSensor] = [
        PoolSyncSensor(coordinator, entry, desc) for desc in SENSORS
    ]

    data = coordinator.data or {}
    device_types = _g(data, "deviceType", default={}) or {}
    heatpump_idx = next(
        (idx for idx, dev in device_types.items() if dev == "heatPump"),
        None,
    )

    if heatpump_idx is not None:
        hp_idx = str(heatpump_idx)
        hp_sensors = [
            PoolSyncSensorDesc(
                key="hp_water_temp_c",
                name="Heat Pump Water Temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                value_fn=lambda d, i=hp_idx: _g(d, "devices", i, "status", "waterTemp"),
            ),
            PoolSyncSensorDesc(
                key="hp_air_temp_c",
                name="Heat Pump Air Temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                value_fn=lambda d, i=hp_idx: _g(d, "devices", i, "status", "airTemp"),
            ),
            PoolSyncSensorDesc(
                key="hp_mode",
                name="Heat Pump Mode",
                value_fn=lambda d, i=hp_idx: _g(d, "devices", i, "config", "mode"),
            ),
            PoolSyncSensorDesc(
                key="hp_setpoint_temp_c",
                name="Heat Pump SetPoint Temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                value_fn=lambda d, i=hp_idx: _g(d, "devices", i, "config", "setpoint"),
            ),
        ]
        for desc in hp_sensors:
            entities.append(PoolSyncSensor(coordinator, entry, desc))

    async_add_entities(entities, update_before_add=True)

