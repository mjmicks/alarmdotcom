"""Alarmdotcom implementation of an HA lock."""
from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant import core
from homeassistant.components import lock
from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_JAMMED, STATE_LOCKED, STATE_UNLOCKED
from homeassistant.helpers.entity_platform import AddEntitiesCallback, DiscoveryInfoType

from pyalarmdotcomajax.const import ADCLockCommand
from pyalarmdotcomajax.entities import ADCLock

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
        ADCILock(controller, controller.devices.get("entity_data", {}).get(lock_id))  # type: ignore
        for lock_id in controller.devices.get("lock_ids", [])
    )


class ADCILock(ADCIEntity, LockEntity):  # type: ignore
    """Integration Lock Entity."""

    def __init__(self, controller: ADCIController, device_data: adci.ADCILockData):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(controller, device_data)

        self._device: adci.ADCILockData = device_data
        self._arm_code: str | None = self._controller.config_entry.options.get(
            "lock_code"
        )

    @property
    def code_format(self) -> str | None:
        """Return one or more digits/characters."""
        if self._arm_code is None:
            return None
        if isinstance(self._arm_code, str) and re.search("^\\d+$", self._arm_code):
            return str(lock.ATTR_CODE_FORMAT)
        return str(lock.ATTR_CODE_FORMAT)

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return entity specific state attributes."""

        return (super().extra_state_attributes or {}) | {
            "mismatched_states": self._device.get("mismatched_states"),
            "desired_state": self._device.get("desired_state"),
        }

    @property
    def state(self) -> str | STATE_LOCKED | STATE_UNLOCKED | STATE_JAMMED | None:
        """Return the state of the sensor."""

        if self.is_locked is not None:
            return self.is_locked

        return str(adci.STATE_MALFUNCTION)

    @property
    def is_locked(self) -> STATE_LOCKED | STATE_UNLOCKED | STATE_JAMMED | None:
        """Return true if the lock is locked."""

        if not self._device.get("malfunction"):
            if self._device.get("state") == ADCLock.DeviceState.LOCKED:
                return STATE_LOCKED

            if self._device.get("state") == ADCLock.DeviceState.UNLOCKED:
                return STATE_UNLOCKED

            if self._device.get("state") == ADCLock.DeviceState.FAILED:
                return STATE_JAMMED

        return None

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        if self._validate_code(kwargs.get("code")):
            await self._controller.async_lock_action(
                self.unique_id, ADCLockCommand.LOCK
            )

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        if self._validate_code(kwargs.get("code")):
            await self._controller.async_lock_action(
                self.unique_id, ADCLockCommand.UNLOCK
            )

    def _validate_code(self, code: str | None) -> bool:
        """Validate given code."""
        check: bool = self._arm_code is None or code == self._arm_code
        if not check:
            log.warning("Wrong code entered")
        return check
