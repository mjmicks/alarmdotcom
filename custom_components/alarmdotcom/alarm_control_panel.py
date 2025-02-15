"""Interfaces with Alarm.com alarm control panels."""
from __future__ import annotations

import logging
import re

from homeassistant.components import alarm_control_panel

from custom_components.alarmdotcom.const import ADCIPartitionData
from pyalarmdotcomajax.entities import ADCPartition, ADCPartitionCommand

# Needed for backward compatibility because of https://github.com/home-assistant/core/commit/6f7f5b4034bc55246a8fa170dd330b1edec9ea57.
# AlarmControlPanel renamed AlarmControlPanelEntity in April 2020.
try:
    from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
except ImportError:
    from homeassistant.components.alarm_control_panel import (
        AlarmControlPanel as AlarmControlPanelEntity,
    )

from homeassistant import config_entries, core
from homeassistant.components import persistent_notification
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
    SUPPORT_ALARM_ARM_NIGHT,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback, DiscoveryInfoType
from homeassistant.helpers.typing import ConfigType

from . import ADCIEntity, const as adci
from .controller import ADCIController

log = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the legacy platform."""
    log.warning(
        "Configuration of Alarm.com via configuration.yaml is deprecated and will be"
        " removed in a future release. Your existing configuration has been migrated to"
        " the integrations page successfully and can be removed from your"
        " configuration.yaml file."
    )

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            adci.DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=config
        )
    )

    error_msg = (
        "The Alarm.com custom integration can now only be configured via Home"
        " Assistant's integration's page. Please delete the Alarm.com entry from"
        " configuration.yaml. Your settings have already been migrated. "
    )

    persistent_notification.async_create(
        hass,
        error_msg,
        title="Alarm.com Updated",
        notification_id="alarmdotcom_migration",
    )


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform and create a master device."""

    controller: ADCIController = hass.data[adci.DOMAIN][config_entry.entry_id]

    async_add_entities(
        ADCIControlPanel(
            controller, controller.devices.get("entity_data", {}).get(partition_id)
        )
        for partition_id in controller.devices.get("partition_ids", [])
    )


class ADCIControlPanel(ADCIEntity, AlarmControlPanelEntity):  # type: ignore
    """Alarm.com Alarm Control Panel entity."""

    def __init__(self, controller: ADCIController, device_data: ADCIPartitionData):
        """Pass coordinator to CoordinatorEntity."""
        log.debug("%s: Initializing Alarm.com control panel entity.", __name__)
        super().__init__(controller, device_data)

        self._arm_code: str | None = self._controller.config_entry.options.get(
            "arm_code"
        )
        self._device: ADCIPartitionData = device_data

    @property
    def code_format(
        self,
    ) -> alarm_control_panel.FORMAT_NUMBER | alarm_control_panel.FORMAT_TEXT | None:
        """Return one or more digits/characters."""
        if self._arm_code is None:
            return None
        if isinstance(self._arm_code, str) and re.search("^\\d+$", self._arm_code):
            return alarm_control_panel.FORMAT_NUMBER
        return alarm_control_panel.FORMAT_TEXT

    @property
    def state(self) -> str:
        """Return the state of the device."""

        if self._device.get("state") is None or self._device.get("mismatched_states"):
            return adci.STATE_MALFUNCTION

        if self._device.get("state") == ADCPartition.DeviceState.DISARMED:
            return str(STATE_ALARM_DISARMED)
        elif self._device["state"] == ADCPartition.DeviceState.ARMED_STAY:
            return str(STATE_ALARM_ARMED_HOME)
        elif self._device["state"] == ADCPartition.DeviceState.ARMED_AWAY:
            return str(STATE_ALARM_ARMED_AWAY)
        elif self._device["state"] == ADCPartition.DeviceState.ARMED_NIGHT:
            return str(STATE_ALARM_ARMED_NIGHT)
        else:
            return str(adci.STATE_MALFUNCTION)

    @property
    def extra_state_attributes(self) -> dict:
        """Return entity specific state attributes."""

        return dict(
            (super().extra_state_attributes or {})
            | {
                "mismatched_states": self._device.get("mismatched_states"),
                "desired_state": self._device.get("desired_state").name.title(),
                "uncleared_issues": self._device.get("uncleared_issues"),
            }
        )

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return (
            int(SUPPORT_ALARM_ARM_HOME)
            | int(SUPPORT_ALARM_ARM_AWAY)
            | int(SUPPORT_ALARM_ARM_NIGHT)
        )

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send disarm command."""
        if self._validate_code(code):
            await self._controller.async_partition_action(
                self.unique_id, ADCPartitionCommand.ARM_NIGHT
            )

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        if self._validate_code(code):
            await self._controller.async_partition_action(
                self.unique_id, ADCPartitionCommand.DISARM
            )

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home (alarm stay in adc) command."""
        if self._validate_code(code):
            await self._controller.async_partition_action(
                self.unique_id, ADCPartitionCommand.ARM_STAY
            )

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        if self._validate_code(code):
            await self._controller.async_partition_action(
                self.unique_id, ADCPartitionCommand.ARM_AWAY
            )

    def _validate_code(self, code: str | None) -> bool | str:
        """Validate given code."""
        check: bool | str = self._arm_code is None or code == self._arm_code
        if not check:
            log.warning("Wrong code entered")
        return check
