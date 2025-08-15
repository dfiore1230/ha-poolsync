from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature

from .const import DOMAIN
from .coordinator import PoolSyncCoordinator
from .util import _g


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator: PoolSyncCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[NumberEntity] = [
        PoolSyncChlorOutputNumber(coordinator, entry, device_index=0),
    ]

    data = coordinator.data or {}
    device_types = _g(data, "deviceType", default={}) or {}
    heatpump_idx = next(
        (idx for idx, dev in device_types.items() if dev == "heatPump"),
        None,
    )

    if heatpump_idx is not None:
        hp_idx = int(heatpump_idx)
        entities.extend(
            [
                PoolSyncHeatSetpointNumber(coordinator, entry, device_index=hp_idx),
                PoolSyncHeatModeNumber(coordinator, entry, device_index=hp_idx),
            ]
        )

    async_add_entities(entities, update_before_add=True)


class PoolSyncChlorOutputNumber(CoordinatorEntity[PoolSyncCoordinator], NumberEntity):
    """Number for ChlorSync output percentage (0-100%)."""

    _attr_min_value = 0
    _attr_max_value = 100
    _attr_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self, coordinator: PoolSyncCoordinator, entry: ConfigEntry, device_index: int = 0
    ) -> None:
        super().__init__(coordinator)
        self._device_index = device_index
        mac = coordinator.api.mac_address or entry.data.get("mac") or "poolsync"
        self._attr_unique_id = f"{mac}_chlor_output_{device_index}"
        self._attr_name = "Chlor Output"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, mac)},
            "manufacturer": "AquaCal",
            "name": "PoolSync",
            "model": "PoolSync",
        }

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        val = _g(data, "devices", str(self._device_index), "config", "chlorOutput")
        try:
            return float(val)
        except Exception:
            return None

    async def async_set_native_value(self, value: float) -> None:
        # Clamp/round to int 0..100 for API
        pct = max(0, min(100, int(round(value))))
        await self.coordinator.api.set_chlor_output(self._device_index, pct)
        await self.coordinator.async_request_refresh()


class PoolSyncHeatSetpointNumber(CoordinatorEntity[PoolSyncCoordinator], NumberEntity):
    """Number for heat pump temperature setpoint."""

    _attr_mode = NumberMode.SLIDER

    def __init__(
        self, coordinator: PoolSyncCoordinator, entry: ConfigEntry, device_index: int
    ) -> None:
        super().__init__(coordinator)
        self._device_index = device_index
        mac = coordinator.api.mac_address or entry.data.get("mac") or "poolsync"
        self._attr_unique_id = f"{mac}_heat_setpoint_{device_index}"
        self._attr_name = "Heat Pump Setpoint"

        unit = coordinator.hass.config.units.temperature_unit
        if unit == UnitOfTemperature.FAHRENHEIT:
            self._attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
            self._attr_min_value = 40
            self._attr_max_value = 104
            self._attr_step = 1
            self._attr_mode = NumberMode.BOX
        else:
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_min_value = 5
            self._attr_max_value = 40
            self._attr_step = 0.5

        self._attr_device_info = {
            "identifiers": {(DOMAIN, mac)},
            "manufacturer": "AquaCal",
            "name": "PoolSync",
            "model": "PoolSync",
        }

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        val = _g(data, "devices", str(self._device_index), "config", "setpoint")
        try:
            return float(val)
        except Exception:
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api.set_heatpump_setpoint(self._device_index, value)
        await self.coordinator.async_request_refresh()


class PoolSyncHeatModeNumber(CoordinatorEntity[PoolSyncCoordinator], NumberEntity):
    """Number for heat pump mode selection."""

    _attr_min_value = 0
    _attr_max_value = 2
    _attr_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(
        self, coordinator: PoolSyncCoordinator, entry: ConfigEntry, device_index: int
    ) -> None:
        super().__init__(coordinator)
        self._device_index = device_index
        mac = coordinator.api.mac_address or entry.data.get("mac") or "poolsync"
        self._attr_unique_id = f"{mac}_heat_mode_{device_index}"
        self._attr_name = "Heat Pump Mode"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, mac)},
            "manufacturer": "AquaCal",
            "name": "PoolSync",
            "model": "PoolSync",
        }

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        val = _g(data, "devices", str(self._device_index), "config", "mode")
        try:
            return float(val)
        except Exception:
            return None

    async def async_set_native_value(self, value: float) -> None:
        mode = int(value)
        await self.coordinator.api.set_heatpump_mode(self._device_index, mode)
        await self.coordinator.async_request_refresh()

