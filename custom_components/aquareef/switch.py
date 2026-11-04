"""Switch platform for AquaReef day simulation, manual schedule, and dynamic effects."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AquaReefCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AquaReef switch entities from a config entry."""
    coordinator: AquaReefCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            AquaReefSimulationSwitch(coordinator),
            AquaReefScheduleSwitch(coordinator),
            AquaReefStormSwitch(coordinator),
            AquaReefCloudSwitch(coordinator),
            AquaReefSettingsPanelSwitch(coordinator),
        ]
    )


class AquaReefSimulationSwitch(CoordinatorEntity[AquaReefCoordinator], SwitchEntity):
    """Switch to toggle 24-hour day simulation."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:weather-sunset-up"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = "Gün Simülasyonu"
        self._attr_unique_id = f"{coordinator.mac}_day_simulation_switch"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
        )

    @property
    def is_on(self) -> bool:
        """Return True if day simulation is active."""
        return self.coordinator.simulation_enabled

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return simulation configuration details."""
        return {
            "profile": self.coordinator.simulation_profile,
            "start_time": self.coordinator.sim_start_time,
            "end_time": self.coordinator.sim_end_time,
            "moon_end_time": self.coordinator.sim_moon_end_time,
            "ramp_minutes": self.coordinator.sim_ramp_minutes,
            "moon_level": self.coordinator.sim_moon_level,
            "phase": self.coordinator.simulation_phase,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable simulation."""
        await self.coordinator.async_set_simulation(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable simulation."""
        await self.coordinator.async_set_simulation(False)


class AquaReefScheduleSwitch(CoordinatorEntity[AquaReefCoordinator], SwitchEntity):
    """Switch to toggle Manual Time-Slot Schedule ('Hangi Saat Hangi Işık Yansın')."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the manual schedule switch."""
        super().__init__(coordinator)
        self._attr_name = "Manuel Saat Programı"
        self._attr_unique_id = f"{coordinator.mac}_manual_schedule_switch"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
        )

    @property
    def is_on(self) -> bool:
        """Return True if manual schedule is active."""
        return self.coordinator.schedule_enabled

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return schedule slots configuration."""
        return {
            "slot_1": self.coordinator.schedule_slots.get(1),
            "slot_2": self.coordinator.schedule_slots.get(2),
            "slot_3": self.coordinator.schedule_slots.get(3),
            "slot_4": self.coordinator.schedule_slots.get(4),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable manual time-slot schedule."""
        await self.coordinator.async_set_schedule_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable manual time-slot schedule."""
        await self.coordinator.async_set_schedule_enabled(False)


class AquaReefStormSwitch(CoordinatorEntity[AquaReefCoordinator], SwitchEntity):
    """Switch to toggle storm & lightning effect."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:weather-lightning"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = "Fırtına Efekti"
        self._attr_unique_id = f"{coordinator.mac}_storm_effect_switch"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
        )

    @property
    def is_on(self) -> bool:
        """Return True if storm effect is active."""
        return self.coordinator.storm_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable storm effect."""
        await self.coordinator.async_set_storm(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable storm effect."""
        await self.coordinator.async_set_storm(False)


class AquaReefCloudSwitch(CoordinatorEntity[AquaReefCoordinator], SwitchEntity):
    """Switch to toggle passing cloud effect."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = "Bulut Efekti"
        self._attr_unique_id = f"{coordinator.mac}_cloud_effect_switch"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
        )

    @property
    def is_on(self) -> bool:
        """Return True if cloud effect is active."""
        return self.coordinator.cloud_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable cloud effect."""
        await self.coordinator.async_set_cloud(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable cloud effect."""
        await self.coordinator.async_set_cloud(False)


class AquaReefSettingsPanelSwitch(CoordinatorEntity[AquaReefCoordinator], SwitchEntity):
    """Switch to toggle the inline detailed settings panel on the Lovelace dashboard."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:tune-variant"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = "Ayarlar Paneli"
        self._attr_unique_id = f"{coordinator.mac}_settings_panel_switch"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
        )

    @property
    def is_on(self) -> bool:
        """Return True if the settings panel is expanded."""
        return self.coordinator.settings_panel_open

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Expand the inline settings panel."""
        await self.coordinator.async_set_settings_panel(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Collapse the inline settings panel."""
        await self.coordinator.async_set_settings_panel(False)

