"""Alarmdotcom implementation of an HA cover (garage door)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant import core
from homeassistant.components.cover import (
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    CoverDeviceClass,
    CoverEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback, DiscoveryInfoType

from pyalarmdotcomajax.const import ADCGarageDoorCommand
from pyalarmdotcomajax.entities import ADCGarageDoor

from . import ADCIEntity, const as adci
from .controller import ADCIController

log = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""

    controller: ADCIController = hass.data[adci.DOMAIN][config_entry.entry_id]

    async_add_entities(
        ADCICover(controller, controller.devices.get("entity_data", {}).get(garage_id))  # type: ignore
        for garage_id in controller.devices.get("garage_door_ids", [])
    )


class ADCICover(ADCIEntity, CoverEntity):  # type: ignore
    """Integration Cover Entity."""

    def __init__(
        self, controller: ADCIController, device_data: adci.ADCIGarageDoorData
    ):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(controller, device_data)

        self._device: adci.ADCIGarageDoorData = device_data
        self._attr_device_class: CoverDeviceClass = CoverDeviceClass.GARAGE
        self._last_reported_state: ADCGarageDoor.DeviceState = None

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return entity specific state attributes."""

        return (super().extra_state_attributes or {}) | {
            "mismatched_states": self._device.get("mismatched_states"),
            "desired_state": self._device.get("desired_state"),
        }

    @property
    def supported_features(self) -> int:
        """Flag supported features."""

        return int(SUPPORT_OPEN) | int(SUPPORT_CLOSE)

    @property
    def is_opening(self) -> bool | None:
        """Return if the cover is opening or not."""
        if (
            self._device.get("state") == ADCGarageDoor.DeviceState.TRANSITIONING
            and self._last_reported_state == ADCGarageDoor.DeviceState.CLOSED
        ):
            return True

        return None

    @property
    def is_closing(self) -> bool | None:
        """Return if the cover is closing or not."""
        if (
            self._device.get("state") == ADCGarageDoor.DeviceState.TRANSITIONING
            and self._last_reported_state == ADCGarageDoor.DeviceState.OPEN
        ):
            return True

        return None

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed or not."""

        if (
            reported_state := self._device.get("state")
        ) == ADCGarageDoor.DeviceState.OPEN:
            self._last_reported_state = ADCGarageDoor.DeviceState.OPEN
            return False
        elif reported_state == ADCGarageDoor.DeviceState.CLOSED:
            self._last_reported_state = ADCGarageDoor.DeviceState.CLOSED
            return True

        return None

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._controller.async_garage_door_action(
            self.unique_id, ADCGarageDoorCommand.OPEN
        )

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        await self._controller.async_garage_door_action(
            self.unique_id, ADCGarageDoorCommand.CLOSE
        )
