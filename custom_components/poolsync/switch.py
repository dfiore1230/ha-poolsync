from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
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
    async_add_entities([PoolSyncBoostSwitch(coordinator, entry, api, device_index)], True)

class PoolSyncBoostSwitch(CoordinatorEntity[PoolSyncCoordinator], SwitchEntity):
    _attr_name = "Salt Boost (24h)"
    _attr_icon = "mdi:flash"
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, api: PoolSyncApi, device_index: str) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._api = api
        self._device_index = str(device_index)
        self._attr_unique_id = f"{entry.entry_id}_switch_boost_mode"

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
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        devices = data.get("devices") or {}
        dev = devices.get(self._device_index) or {}
        cfg = dev.get("config") or {}
        status = dev.get("status") or {}
        if "boostMode" in cfg:
            try:
                return bool(cfg.get("boostMode"))
            except Exception:
                return False
        try:
            return int(status.get("boostRemaining") or 0) > 0
        except Exception:
            return False

    async def async_turn_on(self, **kwargs) -> None:
        await self._api.set_boost_mode(self._device_index, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self._api.set_boost_mode(self._device_index, False)
        await self.coordinator.async_request_refresh()
