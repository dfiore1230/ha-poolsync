from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import aiohttp

_LOGGER = logging.getLogger(__name__)

class PoolSyncApi:
    """Async client for PoolSync."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str, auth: str, user: str) -> None:
        self._session = session
        self._base = base_url.rstrip("/")
        self._auth = auth
        self._user = user

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": self._auth, "user": self._user}

    async def get_poolsync_all(self) -> Dict[str, Any]:
        """
        Known-good endpoint that returns the devices block when 'all=' (with equals).
        GET {base}/api/poolsync?cmd=poolSync&all=
        """
        url = f"{self._base}/api/poolsync"
        params = {"cmd": "poolSync", "all": ""}  # produces ?cmd=poolSync&all=
        _LOGGER.debug("GET %s params=%s", url, params)
        async with self._session.get(url, headers=self._headers(), params=params, timeout=30) as resp:
            text = await resp.text()
            _LOGGER.debug("PoolSync %s -> %s; body[0:1000]=%s", url, resp.status, text[:1000])
            resp.raise_for_status()
            # accept JSON even if content-type is wrong
            return await resp.json(content_type=None)

    @staticmethod
    def extract_device(data: Dict[str, Any], device_index: str = "0") -> Optional[Dict[str, Any]]:
        if not isinstance(data, dict):
            return None
        devices = data.get("devices")
        if not isinstance(devices, dict):
            return None
        dev = devices.get(device_index)
        return dev if isinstance(dev, dict) else None
