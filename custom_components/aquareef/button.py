"""Button platform for AquaReef Aquarium Lighting."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
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
    """Set up AquaReef buttons from a config entry."""
    coordinator: AquaReefCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            AquaReefRestartButton(coordinator),
            AquaReefRefreshButton(coordinator),
        ]
    )


class AquaReefRestartButton(CoordinatorEntity[AquaReefCoordinator], ButtonEntity):
    """Button to restart AquaReef Wi-Fi controller."""

    _attr_has_entity_name = True
    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the restart button."""
        super().__init__(coordinator)
        self._attr_name = "Cihazı Yeniden Başlat (Reboot)"
        self._attr_unique_id = f"{coordinator.mac}_reboot_button"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
        )

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.async_reboot()


class AquaReefRefreshButton(CoordinatorEntity[AquaReefCoordinator], ButtonEntity):
    """Button to manually poll AquaReef status."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:sync"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the refresh button."""
        super().__init__(coordinator)
        self._attr_name = "Durumu Yenile"
        self._attr_unique_id = f"{coordinator.mac}_refresh_button"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
        )

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.async_request_refresh()
