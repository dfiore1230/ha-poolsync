from __future__ import annotations

import voluptuous as vol
from typing import Any, Optional

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN, CONF_BASE_URL, CONF_AUTH, CONF_USER,
    CONF_DEVICE_INDEX, CONF_SCAN_INTERVAL, CONF_ASSUME_FAHRENHEIT,
    DEFAULT_DEVICE_INDEX, DEFAULT_SCAN_INTERVAL, DEFAULT_ASSUME_FAHRENHEIT
)

STEP_USER = vol.Schema({
    vol.Required(CONF_BASE_URL): str,       # e.g. http://172.16.42.218
    vol.Required(CONF_AUTH): str,           # token or "Bearer <token>"
    vol.Required(CONF_USER): str,           # user token/ID
    vol.Optional(CONF_DEVICE_INDEX, default=DEFAULT_DEVICE_INDEX): str,
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    vol.Optional(CONF_ASSUME_FAHRENHEIT, default=DEFAULT_ASSUME_FAHRENHEIT): bool,
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER)

        await self.async_set_unique_id(f"{user_input[CONF_BASE_URL]}_{user_input.get(CONF_DEVICE_INDEX, DEFAULT_DEVICE_INDEX)}")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="PoolSync", data=user_input)

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        return await self.async_step_user(user_input)
