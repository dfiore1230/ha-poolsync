
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PoolSyncApi

_LOGGER = logging.getLogger(__name__)

class PoolSyncCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, api: PoolSyncApi, scan_interval: timedelta) -> None:
        super().__init__(hass, _LOGGER, name="PoolSync Coordinator", update_interval=scan_interval)
        self.api = api

    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            data = await self.api.get_poolsync_all()
            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with PoolSync API: {err}") from err
