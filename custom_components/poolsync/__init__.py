
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_USER_ID,
    CONF_TOKEN,
    CONF_POLL_SECONDS,
    CONF_REQUEST_TIMEOUT,
    DEFAULT_POLL_SECONDS,
    DEFAULT_REQUEST_TIMEOUT,
)
from .api import PoolSyncApi
from .coordinator import PoolSyncCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = [
    "sensor",
    "switch",
    "number",
    "binary_sensor",
    "climate",
    "button",
]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    # Merge data and options for runtime values
    data = {**entry.data, **entry.options}

    # Normalize / defaults
    poll_seconds = int(data.get(CONF_POLL_SECONDS, DEFAULT_POLL_SECONDS))
    request_timeout = int(data.get(CONF_REQUEST_TIMEOUT, DEFAULT_REQUEST_TIMEOUT))

    api = PoolSyncApi(
        hass=hass,
        base_url=data[CONF_BASE_URL],
        token=data.get(CONF_TOKEN),
        user_id=data.get(CONF_USER_ID),
        request_timeout=request_timeout,
    )

    coordinator = PoolSyncCoordinator(
        hass=hass,
        api=api,
        scan_interval=timedelta(seconds=poll_seconds),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {"api": api, "coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.debug(
        "PoolSync setup complete: base_url=%s, user_id=%s, poll=%ss, timeout=%ss",
        data[CONF_BASE_URL],
        data.get(CONF_USER_ID),
        poll_seconds,
        request_timeout,
    )

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
