from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PoolSyncCoordinator
from .util import _g


@dataclass(frozen=True)
class PoolSyncBinarySensorDesc(BinarySensorEntityDescription):
    """Descriptor with a value extractor."""

    value_fn: Callable[[dict[str, Any]], Any] | None = None


class PoolSyncBinarySensor(CoordinatorEntity[PoolSyncCoordinator], BinarySensorEntity):
    """Generic PoolSync binary sensor."""

    entity_description: PoolSyncBinarySensorDesc

    def __init__(
        self,
        coordinator: PoolSyncCoordinator,
        entry: ConfigEntry,
        description: PoolSyncBinarySensorDesc,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description

        mac = coordinator.api.mac_address or entry.data.get("mac") or "poolsync"
        self._attr_unique_id = f"{mac}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_name = description.name

        self._attr_device_info = {
            "identifiers": {(DOMAIN, mac)},
            "manufacturer": "AquaCal",
            "name": "PoolSync",
            "model": "PoolSync",
        }

    @property
    def is_on(self) -> Optional[bool]:
        data = self.coordinator.data or {}
        if self.entity_description.value_fn is None:
            return None
        try:
            val = self.entity_description.value_fn(data)
        except Exception:
            return None
        if val is None:
            return None
        if isinstance(val, bool):
            return val
        if isinstance(val, int):
            return val != 0
        return bool(val)

    @property
    def available(self) -> bool:
        return self.is_on is not None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator: PoolSyncCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[PoolSyncBinarySensor] = []

    data = coordinator.data or {}
    device_types = _g(data, "deviceType", default={}) or {}
    heatpump_idx = next(
        (idx for idx, dev in device_types.items() if dev == "heatPump"),
        None,
    )

    if heatpump_idx is not None:
        hp_idx = str(heatpump_idx)
        sensors = [
            PoolSyncBinarySensorDesc(
                key="heatpump_online",
                name="Heat Pump Online",
                device_class=BinarySensorDeviceClass.CONNECTIVITY,
                value_fn=lambda d, i=hp_idx: _g(d, "devices", i, "nodeAttr", "online"),
            ),
            PoolSyncBinarySensorDesc(
                key="heatpump_fault",
                name="Heat Pump Fault",
                device_class=BinarySensorDeviceClass.PROBLEM,
                value_fn=lambda d, i=hp_idx: (
                    any(f != 0 for f in (_g(d, "devices", i, "faults") or []))
                ),
            ),
            PoolSyncBinarySensorDesc(
                key="heatpump_flow",
                name="Heat Pump Flow",
                value_fn=lambda d, i=hp_idx: (
                    (_g(d, "devices", i, "status", "ctrlFlags") or 0) >= 1
                ),
            ),
            PoolSyncBinarySensorDesc(
                key="heatpump_compressor",
                name="Heat Pump Compressor",
                value_fn=lambda d, i=hp_idx: (
                    (_g(d, "devices", i, "status", "stateFlags") or 0) == 8
                ),
            ),
            PoolSyncBinarySensorDesc(
                key="heatpump_fan",
                name="Heat Pump Fan",
                value_fn=lambda d, i=hp_idx: (
                    (_g(d, "devices", i, "status", "stateFlags") or 0) in (8, 520)
                ),
            ),
        ]
        for desc in sensors:
            entities.append(PoolSyncBinarySensor(coordinator, entry, desc))

    if entities:
        async_add_entities(entities, update_before_add=True)
