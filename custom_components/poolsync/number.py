from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE

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

