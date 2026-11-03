"""Select platform for AquaReef Aquarium Lighting modes and presets."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PRESET_MODES
from .coordinator import AquaReefCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AquaReef select entities from a config entry."""
    coordinator: AquaReefCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([AquaReefModeSelect(coordinator)])


class AquaReefModeSelect(CoordinatorEntity[AquaReefCoordinator], SelectEntity):
    """Representation of the AquaReef Mode / Preset selector."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:theme-light-dark"
    _attr_options = PRESET_MODES

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the preset mode selector."""
        super().__init__(coordinator)
        self._attr_name = "Çalışma Modu / Efekt"
        self._attr_unique_id = f"{coordinator.mac}_mode_select"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
        )

    @property
    def current_option(self) -> str | None:
        """Return the current active mode."""
        return self.coordinator.current_mode

    async def async_select_option(self, option: str) -> None:
        """Change the active mode."""
        await self.coordinator.async_set_mode(option)
