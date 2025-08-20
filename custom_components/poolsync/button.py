from __future__ import annotations


from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PoolSyncCoordinator
from .api import PoolSyncApi

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PoolSyncCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api: PoolSyncApi = hass.data[DOMAIN][entry.entry_id]["api"]
    async_add_entities([PoolSyncPingButton(api, coordinator, entry)])

class PoolSyncPingButton(ButtonEntity):
    """Ping button that is always available and can attempt to recover the integration."""

    def __init__(self, api: PoolSyncApi, coordinator: PoolSyncCoordinator, entry: ConfigEntry) -> None:
        self.api = api
        self.coordinator = coordinator
        mac = api.mac_address or entry.data.get("mac") or "poolsync"
        self._attr_unique_id = f"{mac}_ping"
        self._attr_name = "Ping"
        self._attr_icon = "mdi:lan-connect"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, mac)},
            "manufacturer": "AquaCal",
            "name": "PoolSync",
            "model": "PoolSync",
        }

    @property
    def available(self) -> bool:
        # Always available, even if coordinator is unavailable
        return True

    async def async_press(self) -> None:
        """Try to fetch data directly and then refresh the coordinator."""
        try:
            await self.api.get_poolsync_all()
        except Exception:
            pass
        await self.coordinator.async_request_refresh()
