# custom_components/poolsync/config_flow.py
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PoolSyncApi

DOMAIN = "poolsync"
_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required("base_url"): str,
        # No user_id requested up front; we auto-generate an ephemeral one for push-link
        vol.Optional("poll_interval", default=0.5): float,
        vol.Optional("timeout", default=60): int,
    }
)


class PoolSyncConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PoolSync."""

    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA)

        base_url: str = user_input["base_url"].strip().rstrip("/")
        poll_interval: float = float(user_input.get("poll_interval", 0.5))
        timeout: float = float(user_input.get("timeout", 60))

        # Create a temporary API client (no token, no user)
        session = async_get_clientsession(self.hass)
        api = PoolSyncApi(
            hass=self.hass,
            base_url=base_url,
            token=None,
            user_id=None,  # force ephemeral user for push-link
            session=session,
            request_timeout=30.0,
        )

        _LOGGER.debug(
            "Starting push-link (base_url=%s, user=None, poll=%.1fs, timeout=%ds)",
            base_url, poll_interval, int(timeout),
        )

        ok, mac, token, used_user, err = await api.async_pushlink_exchange(
            user_id=None,
            poll_interval=poll_interval,
            timeout=timeout,
        )
        if not ok or not token:
            _LOGGER.debug("Link mode failed: %s", err or "unknown error")
            return self.async_abort(reason="cannot_connect")

        # Create the entry and persist the token + the SAME ephemeral user used
        title = f"PoolSync ({mac})" if mac else "PoolSync"
        data = {
            "base_url": base_url,
            "token": token,
            "user_id": used_user,  # critical: keep this for all subsequent calls
            "mac": mac or "",
            # Coordinator defaults; can be made options later
            "poll_seconds": 300.0,
            "request_timeout": 30.0,
        }

        await self.async_set_unique_id(mac or base_url)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=title, data=data)

