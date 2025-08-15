# custom_components/poolsync/api.py
from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from typing import Any, Dict, Optional, Tuple

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)
UNMASK_LOGS = bool(int(os.environ.get("POOLSYNC_UNMASK_LOGS", "0")))


class PoolSyncApi:
    """HTTP client for the local PoolSync device API."""

    def __init__(
        self,
        hass: HomeAssistant,
        base_url: str,
        token: Optional[str] = None,
        user_id: Optional[str] = None,
        session: Optional[ClientSession] = None,
        request_timeout: Optional[float] = None,
    ) -> None:
        self.hass = hass
        self._base_url = base_url.rstrip("/")
        self.token = token or None
        self.user_id = user_id or None  # device expects a lower-case 'user' header; may be None
        self.mac_address: Optional[str] = None
        self._session: ClientSession = session or async_get_clientsession(hass)
        # default timeout used when a call doesn't provide one explicitly
        self._default_timeout: float = float(request_timeout) if request_timeout else 15.0

    # -----------------------
    # Internal request helper
    # -----------------------
    async def _request_json(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        timeout_total: Optional[float] = None,
    ) -> Tuple[int, str, Optional[Dict[str, Any]]]:
        """Send an HTTP request and return (status, text, json_or_none)."""
        url = f"{self._base_url}{path}"
        params = params or {}
        headers = headers or {}

        base_headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
        }
        if self.token:
            base_headers["Authorization"] = self.token
        if self.user_id:
            base_headers["user"] = self.user_id  # device requires a lowercase 'user' header

        base_headers.update(headers)

        total = timeout_total if timeout_total is not None else self._default_timeout

        try:
            async with self._session.request(
                method=method,
                url=url,
                params=params,
                headers=base_headers,
                json=json_body,
                timeout=ClientTimeout(total=total),
            ) as resp:
                text = await resp.text()
                _LOGGER.debug(
                    "%s %s %s -> %s, body[%d]=%s",
                    method, url, params, resp.status, len(text), text[:300],
                )
                parsed: Optional[Dict[str, Any]] = None
                if text:
                    try:
                        parsed = json.loads(text)
                    except Exception:
                        parsed = None
                return resp.status, text, parsed
        except Exception as exc:
            _LOGGER.debug("HTTP request error %s %s: %s", method, url, exc)
            return 0, str(exc), None

    # -----------------------
    # Public high-level calls
    # -----------------------
    async def get_poolsync_all(self) -> Dict[str, Any]:
        """GET /api/poolsync?cmd=poolSync&all."""
        status, text, data = await self._request_json(
            "GET",
            "/api/poolsync",
            params={"cmd": "poolSync", "all": ""},
            timeout_total=None,  # use default
        )
        if status != 200 or not isinstance(data, dict):
            raise RuntimeError(f"poolSync all failed: status={status}, body={text}")

        # learn MAC if present
        try:
            mac = data.get("poolSync", {}).get("system", {}).get("macAddr")
            if mac and not self.mac_address:
                self.mac_address = str(mac)
        except Exception:
            pass

        return data

    async def set_chlor_output(self, device_index: int, value: int) -> Dict[str, Any]:
        """PATCH /api/poolsync?cmd=devices&device=<index> with {'chlorOutput': <int>}."""
        return await self._patch_devices(device_index, {"chlorOutput": int(value)})

    async def set_boost_mode(self, device_index: int, on: bool) -> Dict[str, Any]:
        """PATCH /api/poolsync?cmd=devices&device=<index> with {'boostMode': bool}."""
        return await self._patch_devices(device_index, {"boostMode": bool(on)})

    async def _patch_devices(self, device_index: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        status, text, data = await self._request_json(
            "PATCH",
            "/api/poolsync",
            params={"cmd": "devices", "device": str(device_index)},
            headers=headers,
            json_body=payload,
            timeout_total=None,  # use default
        )
        if status != 200:
            raise RuntimeError(f"devices PATCH failed: status={status}, body={text}")
        return {"ok": True, "raw": text} if data is None else data

    # -----------------------
    # Push-link (auto-ephemeral user)
    # -----------------------
    async def async_pushlink_exchange(
        self,
        user_id: Optional[str],
        poll_interval: float = 0.5,
        timeout: float = 60.0,
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Start push-link and poll for {"macAddress": "...", "password": "..."}.
        If user_id is None, generate a fresh ephemeral UUID and send it as the
        lowercase 'user' header for ALL push-link requests.

        Returns: (ok, mac, token, used_user, err)
        """
        base_path = "/api/poolsync"
        debug_full = _LOGGER.isEnabledFor(logging.DEBUG) and UNMASK_LOGS

        # If no user provided, generate one just for this run
        used_user = user_id or str(uuid.uuid4())

        def _push_headers() -> Dict[str, str]:
            return {
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "user": used_user,
            }

        _LOGGER.debug(
            "Starting push-link (base_url=%s, user=%s, poll=%.1fs, timeout=%ds)",
            self._base_url,
            None if user_id is None else "<provided>",
            poll_interval,
            int(timeout),
        )

        # 1) Start the window
        st, text, _ = await self._request_json(
            "PUT",
            base_path,
            params={"cmd": "pushLink", "start": ""},
            headers=_push_headers(),
            timeout_total=self._default_timeout,
        )
        if st != 200:
            return False, None, None, used_user, f"pushLink start failed: status={st}, body={text}"

        # 2) Poll
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        poll = 0

        while True:
            if loop.time() >= deadline:
                _LOGGER.debug("push-link timed out after %.0fs", timeout)
                return False, None, None, used_user, "push-link timed out"

            poll += 1
            st, text, data = await self._request_json(
                "GET",
                base_path,
                params={"cmd": "pushLink", "status": ""},
                headers=_push_headers(),
                timeout_total=self._default_timeout,
            )

            if debug_full:
                _LOGGER.debug("push-link poll #%d RAW: %s", poll, text)
            else:
                # Log response details without exposing tokens/passwords
                redacted = None
                if isinstance(data, dict):
                    redacted = {
                        k: ("<redacted>" if k.lower() in {"password", "pass", "token"} else v)
                        for k, v in data.items()
                    }
                _LOGGER.debug(
                    "push-link poll #%d: status=%s body=%s",
                    poll,
                    st,
                    redacted if redacted is not None else f"<non-json len={len(text)}>",
                )

            if st == 200 and isinstance(data, dict):
                mac = data.get("macAddress") or data.get("mac")
                pw = data.get("password") or data.get("pass") or data.get("token")
                rem = data.get("timeRemaining")

                if pw:
                    self.mac_address = mac or self.mac_address
                    # Also set on this instance so immediate calls work (config flow still stores it)
                    self.user_id = used_user
                    self.token = pw
                    if debug_full:
                        _LOGGER.debug(
                            "push-link SUCCESS: mac=%s password=%s",
                            self.mac_address or "?",
                            pw,
                        )
                    else:
                        _LOGGER.debug(
                            "push-link SUCCESS: mac=%s password_len=%d",
                            self.mac_address or "?",
                            len(pw),
                        )
                    return True, mac, pw, used_user, None

                if isinstance(rem, int) and rem <= 0:
                    _LOGGER.debug(
                        "push-link window ended (timeRemaining=%s) without password in this poll",
                        rem,
                    )
                    return False, None, None, used_user, "push-link ended without password"

            await asyncio.sleep(poll_interval)

