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

QUICK_PRESETS = [
    ("gun_simulasyonu", "Gün Simülasyonunu Başlat", "mdi:weather-sunset-up", "Gün Simülasyonu"),
    ("gun_dogumu", "Gün Doğumu Modu (Sunrise)", "mdi:weather-sunset-up", "Gün Doğumu (Sunrise)"),
    ("gun_ortasi", "Gün Ortası Modu (Midday)", "mdi:weather-sunny", "Gün Ortası (Midday)"),
    ("gun_batimi", "Gün Batımı Modu (Sunset)", "mdi:weather-sunset-down", "Gün Batımı (Sunset)"),
    ("ay_isigi", "Ay Işığı / Gece Modu (Moonlight)", "mdi:weather-night", "Ay Işığı / Gece (Moonlight)"),
    ("derin_deniz", "Derin Deniz Modu (Deep Blue)", "mdi:waves", "Derin Deniz (Deep Blue)"),
    ("mercan_alistirma", "Mercan Alıştırma Modu (Acclimation)", "mdi:shield-sun", "Mercan Alıştırma (Acclimation)"),
    ("fotograf_modu", "Mercan Fotoğraf Çekim Modu", "mdi:camera-iris", "Mercan Fotoğraf Çekim"),
    ("bitkili_akvaryum", "Bitkili / Tatlı Su Modu", "mdi:sprout", "Bitkili / Tatlı Su"),
    ("firtina_simsek", "Fırtına & Şimşek Efekti Başlat", "mdi:weather-lightning", "Fırtına & Şimşek"),
    ("bulut_efekti", "Bulut Efekti Başlat", "mdi:weather-partly-cloudy", "Bulut Efekti"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AquaReef buttons from a config entry."""
    coordinator: AquaReefCoordinator = hass.data[DOMAIN][entry.entry_id]

    buttons: list[ButtonEntity] = [
        AquaReefRestartButton(coordinator),
        AquaReefRefreshButton(coordinator),
    ]

    for key, name, icon, mode in QUICK_PRESETS:
        buttons.append(AquaReefPresetButton(coordinator, key, name, icon, mode))

    async_add_entities(buttons)


class AquaReefBaseButton(CoordinatorEntity[AquaReefCoordinator], ButtonEntity):
    """Base class for AquaReef buttons."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
        )


class AquaReefPresetButton(AquaReefBaseButton):
    """Button to apply a quick preset or mode."""

    def __init__(
        self, coordinator: AquaReefCoordinator, key: str, name: str, icon: str, mode: str
    ) -> None:
        """Initialize the preset button."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_icon = icon
        self._mode = mode
        self._attr_unique_id = f"{coordinator.mac}_btn_{key}"

    async def async_press(self) -> None:
        """Trigger preset action."""
        await self.coordinator.async_set_mode(self._mode)


class AquaReefRestartButton(AquaReefBaseButton):
    """Button to restart AquaReef Wi-Fi controller."""

    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the restart button."""
        super().__init__(coordinator)
        self._attr_name = "Cihazı Yeniden Başlat (Reboot)"
        self._attr_unique_id = f"{coordinator.mac}_reboot_button"

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.async_reboot()


class AquaReefRefreshButton(AquaReefBaseButton):
    """Button to manually poll AquaReef status."""

    _attr_icon = "mdi:sync"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the refresh button."""
        super().__init__(coordinator)
        self._attr_name = "Durumu Yenile"
        self._attr_unique_id = f"{coordinator.mac}_refresh_button"

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.async_request_refresh()
