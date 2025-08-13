from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PoolSyncApi
from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class PoolSyncCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Polls PoolSync and shares data with platforms."""

    def __init__(self, hass: HomeAssistant, api: PoolSyncApi, scan_interval: int | None):
        super().__init__(
            hass,
            _LOGGER,
            name="PoolSync Coordinator",
            update_interval=timedelta(seconds=max(15, scan_interval or DEFAULT_SCAN_INTERVAL)),
        )
        self.api = api

    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            return await self.api.get_poolsync_all()
        except Exception as err:
            raise UpdateFailed(f"PoolSync update failed: {err}") from err
