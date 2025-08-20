from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PoolSyncCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the PoolSync Ping button."""
    coordinator: PoolSyncCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([PoolSyncPingButton(coordinator, entry)])


class PoolSyncPingButton(CoordinatorEntity[PoolSyncCoordinator], ButtonEntity):
    """Button to trigger an immediate PoolSync data refresh."""

    def __init__(self, coordinator: PoolSyncCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        mac = coordinator.api.mac_address or entry.data.get("mac") or "poolsync"
        self._attr_unique_id = f"{mac}_ping"
        self._attr_name = "Ping"
        self._attr_icon = "mdi:lan-connect"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, mac)},
            "manufacturer": "AquaCal",
            "name": "PoolSync",
            "model": "PoolSync",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_request_refresh()
