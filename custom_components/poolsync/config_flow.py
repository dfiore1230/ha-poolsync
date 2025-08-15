# custom_components/poolsync/config_flow.py
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PoolSyncApi
from .const import (
    CONF_POLL_SECONDS,
    CONF_REQUEST_TIMEOUT,
    DEFAULT_POLL_SECONDS,
    DEFAULT_REQUEST_TIMEOUT,
)

DOMAIN = "poolsync"
_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required("base_url"): str,
        # No user_id requested up front; we auto-generate an ephemeral one for push-link
        vol.Optional("poll_interval", default=0.5): vol.All(
            vol.Coerce(float), vol.Range(min=0.1)
        ),
        vol.Optional("timeout", default=60): vol.All(
            vol.Coerce(int), vol.Range(min=1)
        ),
    }
)


class PoolSyncConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PoolSync."""

    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA)

        base_url: str = user_input["base_url"].strip().rstrip("/")
        poll_interval: float = user_input["poll_interval"]
        timeout: int = user_input["timeout"]

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
            base_url, poll_interval, timeout,
        )

        ok, mac, token, used_user, err = await api.async_pushlink_exchange(
            user_id=None,
            poll_interval=poll_interval,
            timeout=timeout,
        )
        if not ok or not token:
            _LOGGER.debug("Link mode failed: %s", err or "unknown error")
            return self.async_abort(reason="pushlink_failed")

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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "PoolSyncOptionsFlow":
        """Return the options flow for this handler."""
        return PoolSyncOptionsFlow(config_entry)


class PoolSyncOptionsFlow(config_entries.OptionsFlow):
    """Handle PoolSync options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize PoolSync options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage PoolSync options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_POLL_SECONDS,
                        default=self.config_entry.options.get(
                            CONF_POLL_SECONDS,
                            self.config_entry.data.get(
                                CONF_POLL_SECONDS, DEFAULT_POLL_SECONDS
                            ),
                        ),
                    ): int,
                    vol.Required(
                        CONF_REQUEST_TIMEOUT,
                        default=self.config_entry.options.get(
                            CONF_REQUEST_TIMEOUT,
                            self.config_entry.data.get(
                                CONF_REQUEST_TIMEOUT,
                                DEFAULT_REQUEST_TIMEOUT,
                            ),
                        ),
                    ): int,
                }
            ),
        )



