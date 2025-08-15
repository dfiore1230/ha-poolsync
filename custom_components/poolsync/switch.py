from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import PoolSyncCoordinator
from .util import _g


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator: PoolSyncCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # For now we only know about device index 0 (chlorSync)
    entities: list[SwitchEntity] = [
        PoolSyncBoostSwitch(coordinator, entry, device_index=0),
    ]
    async_add_entities(entities, update_before_add=True)


class PoolSyncBoostSwitch(CoordinatorEntity[PoolSyncCoordinator], SwitchEntity):
    """24h Salt Boost toggle for ChlorSync."""

    def __init__(
        self, coordinator: PoolSyncCoordinator, entry: ConfigEntry, device_index: int = 0
    ) -> None:
        super().__init__(coordinator)
        self._device_index = device_index
        mac = coordinator.api.mac_address or entry.data.get("mac") or "poolsync"
        self._attr_unique_id = f"{mac}_boost_{device_index}"
        self._attr_name = "Salt Boost (24h)"
        self._attr_icon = "mdi:rocket-launch"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, mac)},
            "manufacturer": "AquaCal",
            "name": "PoolSync",
            "model": "PoolSync",
        }

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        # No explicit boolean in sample JSON; infer from boostRemaining minutes > 0
        remaining = _g(
            data,
            "devices",
            str(self._device_index),
            "status",
            "boostRemaining",
            default=0,
        )
        try:
            return int(remaining) > 0
        except Exception:
            return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_boost_mode(self._device_index, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_boost_mode(self._device_index, False)
        await self.coordinator.async_request_refresh()

