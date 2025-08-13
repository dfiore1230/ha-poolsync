from __future__ import annotations

import logging
from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PoolSyncApi
from .const import (
    DOMAIN, CONF_BASE_URL, CONF_AUTH, CONF_USER,
    CONF_SCAN_INTERVAL, COORDINATOR_NAME, CONF_TIMEOUT
)
from .coordinator import PoolSyncCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[str] = ["sensor", "number", "switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session: ClientSession = async_get_clientsession(hass)

    scan = entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL))
    timeout = entry.options.get(CONF_TIMEOUT, entry.data.get(CONF_TIMEOUT, 30))

    api = PoolSyncApi(
        session,
        base_url=entry.data[CONF_BASE_URL],
        auth=entry.data[CONF_AUTH],
        user=entry.data[CONF_USER],
        timeout=timeout,
    )

    coordinator = PoolSyncCoordinator(hass, api, scan_interval=scan)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {COORDINATOR_NAME: coordinator, "api": api}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
