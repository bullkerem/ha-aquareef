"""Switch platform for AquaReef day simulation and dynamic effects."""

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
            AquaReefStormSwitch(coordinator),
            AquaReefCloudSwitch(coordinator),
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

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable simulation."""
        await self.coordinator.async_set_simulation(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable simulation."""
        await self.coordinator.async_set_simulation(False)


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
