from __future__ import annotations

from homeassistant.components.climate import ClimateEntity, HVACMode, ClimateEntityFeature
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import PoolSyncCoordinator
from .util import _g


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up PoolSync climate entity if a heat pump is present."""
    coordinator: PoolSyncCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    data = coordinator.data or {}
    device_types = _g(data, "deviceType", default={}) or {}
    heatpump_idx = next(
        (idx for idx, dev in device_types.items() if dev == "heatPump"),
        None,
    )

    entities: list[ClimateEntity] = []
    if heatpump_idx is not None:
        entities.append(
            PoolSyncHeatPumpClimate(coordinator, entry, device_index=int(heatpump_idx))
        )

    if entities:
        async_add_entities(entities, update_before_add=True)


class PoolSyncHeatPumpClimate(CoordinatorEntity[PoolSyncCoordinator], ClimateEntity):
    """Climate entity representing the PoolSync heat pump."""

    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]

    def __init__(
        self, coordinator: PoolSyncCoordinator, entry: ConfigEntry, device_index: int
    ) -> None:
        super().__init__(coordinator)
        self._device_index = device_index
        mac = coordinator.api.mac_address or entry.data.get("mac") or "poolsync"
        self._attr_unique_id = f"{mac}_heat_pump_{device_index}"
        self._attr_name = "Heat Pump"

        unit = coordinator.hass.config.units.temperature_unit
        self._attr_temperature_unit = unit
        if unit == UnitOfTemperature.FAHRENHEIT:
            self._attr_min_temp = 40
            self._attr_max_temp = 104
            self._attr_target_temperature_step = 1
        else:
            self._attr_min_temp = 5
            self._attr_max_temp = 40
            self._attr_target_temperature_step = 0.5

        self._attr_device_info = {
            "identifiers": {(DOMAIN, mac)},
            "manufacturer": "AquaCal",
            "name": "PoolSync",
            "model": "PoolSync",
        }

    @property
    def hvac_mode(self) -> HVACMode:
        data = self.coordinator.data or {}
        mode = _g(data, "devices", str(self._device_index), "config", "mode")
        try:
            mode_int = int(mode)
        except Exception:
            mode_int = 0
        return {
            0: HVACMode.OFF,
            1: HVACMode.HEAT,
            2: HVACMode.COOL,
        }.get(mode_int, HVACMode.OFF)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        mode_val = {
            HVACMode.OFF: 0,
            HVACMode.HEAT: 1,
            HVACMode.COOL: 2,
        }.get(hvac_mode)
        if mode_val is None:
            raise ValueError(f"Unsupported hvac_mode: {hvac_mode}")
        await self.coordinator.api.set_heatpump_mode(self._device_index, mode_val)
        await self.coordinator.async_request_refresh()

    @property
    def current_temperature(self) -> float | None:
        data = self.coordinator.data or {}
        temp = _g(data, "devices", str(self._device_index), "status", "waterTemp")
        try:
            return float(temp)
        except Exception:
            return None

    @property
    def target_temperature(self) -> float | None:
        data = self.coordinator.data or {}
        temp = _g(data, "devices", str(self._device_index), "config", "setpoint")
        try:
            return float(temp)
        except Exception:
            return None

    async def async_set_temperature(self, **kwargs) -> None:
        temp = kwargs.get("temperature")
        if temp is None:
            return
        await self.coordinator.api.set_heatpump_setpoint(self._device_index, float(temp))
        await self.coordinator.async_request_refresh()
