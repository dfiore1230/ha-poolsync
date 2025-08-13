from __future__ import annotations

import logging
from typing import Any, Dict, Union
import aiohttp

_LOGGER = logging.getLogger(__name__)

class PoolSyncApi:
    """Async client for PoolSync."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str, auth: str, user: str, timeout: int = 30) -> None:
        self._session = session
        self._base = base_url.rstrip("/")
        self._auth = auth
        self._user = user
        self._timeout = max(5, int(timeout))

    def set_timeout(self, timeout: int) -> None:
        self._timeout = max(5, int(timeout))

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": self._auth, "user": self._user}

    async def get_poolsync_all(self) -> Dict[str, Any]:
        """GET {base}/api/poolsync?cmd=poolSync&all="""
        url = f"{self._base}/api/poolsync"
        params = {"cmd": "poolSync", "all": ""}
        _LOGGER.debug("GET %s params=%s", url, params)
        async with self._session.get(url, headers=self._headers(), params=params, timeout=self._timeout) as resp:
            text = await resp.text()
            _LOGGER.debug("PoolSync %s -> %s; body[0:1000]=%s", url, resp.status, text[:1000])
            resp.raise_for_status()
            return await resp.json(content_type=None)

    async def _patch_devices(self, device_index: Union[str, int], payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self._base}/api/poolsync"
        params = {"cmd": "devices", "device": str(device_index)}
        _LOGGER.debug("PATCH %s params=%s json=%s", url, params, payload)
        async with self._session.patch(url, headers=self._headers(), params=params, json=payload, timeout=self._timeout) as resp:
            text = await resp.text()
            _LOGGER.debug("PoolSync PATCH %s -> %s; body[0:1000]=%s", url, resp.status, text[:1000])
            resp.raise_for_status()
            return await resp.json(content_type=None)

    async def set_chlor_output(self, device_index: Union[str, int], percent: int) -> Dict[str, Any]:
        percent = max(0, min(100, int(percent)))
        payload = {"config": {"chlorOutput": percent}}
        return await self._patch_devices(device_index, payload)

    async def set_boost_mode(self, device_index: Union[str, int], enabled: bool) -> Dict[str, Any]:
        payload = {"boostMode": bool(enabled)}
        return await self._patch_devices(device_index, payload)
