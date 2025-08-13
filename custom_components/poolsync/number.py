from __future__ import annotations

import logging
from typing import Optional

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, COORDINATOR_NAME, CONF_DEVICE_INDEX
from .coordinator import PoolSyncCoordinator
from .api import PoolSyncApi

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: PoolSyncCoordinator = data[COORDINATOR_NAME]
    api: PoolSyncApi = data["api"]
    device_index = entry.data.get(CONF_DEVICE_INDEX, "0")
    async_add_entities([PoolSyncChlorOutputNumber(coordinator, entry, api, device_index)], True)

class PoolSyncChlorOutputNumber(CoordinatorEntity[PoolSyncCoordinator], NumberEntity):
    _attr_name = "Chlor Output"
    _attr_icon = "mdi:percent"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = "slider"
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, api: PoolSyncApi, device_index: str) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._api = api
        self._device_index = str(device_index)
        self._attr_unique_id = f"{entry.entry_id}_number_chlor_output"

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data or {}
        sys = ((data.get("poolSync") or {}).get("system") or {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            manufacturer="PoolSync",
            name="PoolSync Bridge",
            sw_version=str(sys.get("fwVersion", "")),
            model=str(sys.get("hwVersion", "")),
        )

    @property
    def native_value(self) -> Optional[float]:
        data = self.coordinator.data or {}
        devices = data.get("devices") or {}
        dev = devices.get(self._device_index) or {}
        cfg = dev.get("config") or {}
        val = cfg.get("chlorOutput")
        try:
            return float(val) if val is not None else None
        except Exception:
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self._api.set_chlor_output(self._device_index, int(round(value)))
        await self.coordinator.async_request_refresh()
