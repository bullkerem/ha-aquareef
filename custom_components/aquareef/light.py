"""Light platform for AquaReef Aquarium Lighting."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CHANNELS, DOMAIN
from .coordinator import AquaReefCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AquaReef lights from a config entry."""
    coordinator: AquaReefCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[LightEntity] = [
        AquaReefMasterLight(coordinator),
    ]

    for ch_id, ch_info in CHANNELS.items():
        entities.append(AquaReefChannelLight(coordinator, ch_id, ch_info))

    async_add_entities(entities)


class AquaReefMasterLight(CoordinatorEntity[AquaReefCoordinator], LightEntity):
    """Representation of the AquaReef Master Light fixture."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_has_entity_name = True

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the master light."""
        super().__init__(coordinator)
        self._attr_name = "Ana Aydınlatma (Master)"
        self._attr_unique_id = f"{coordinator.mac}_master_light"
        self._attr_icon = "mdi:aquarium"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
            name=self.coordinator.device_name,
            manufacturer="AquaReef (Alstek Elektronik)",
            model=self.coordinator.model or "AquaReef PRO 4",
            sw_version=self.coordinator.version or "4.1.3",
            configuration_url=f"http://{self.coordinator.host}",
        )

    @property
    def is_on(self) -> bool:
        """Return true if master light is on."""
        return self.coordinator.is_on and self.coordinator.master_brightness > 0

    @property
    def brightness(self) -> int:
        """Return the master brightness (0-255)."""
        return self.coordinator.master_brightness

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "mode": self.coordinator.current_mode,
            "simulation_enabled": self.coordinator.simulation_enabled,
            "simulation_profile": self.coordinator.simulation_profile,
            "sim_start_time": self.coordinator.sim_start_time,
            "sim_end_time": self.coordinator.sim_end_time,
            "sim_moon_end_time": self.coordinator.sim_moon_end_time,
            "schedule_enabled": self.coordinator.schedule_enabled,
            "channels": self.coordinator.channels,
            "ip_address": self.coordinator.host,
            "mac_address": self.coordinator.mac,
            "serial_number": self.coordinator.serial,
            "wattage": self.coordinator.wattage,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        if ATTR_BRIGHTNESS in kwargs:
            await self.coordinator.async_set_master_brightness(kwargs[ATTR_BRIGHTNESS])
        else:
            await self.coordinator.async_set_power(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self.coordinator.async_set_power(False)


class AquaReefChannelLight(CoordinatorEntity[AquaReefCoordinator], LightEntity):
    """Representation of an individual AquaReef spectral channel."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AquaReefCoordinator, channel_id: str, channel_info: dict[str, Any]
    ) -> None:
        """Initialize the channel light."""
        super().__init__(coordinator)
        self._channel = channel_id
        self._attr_name = f"Kanal {channel_info['name']}"
        self._attr_unique_id = f"{coordinator.mac}_channel_{channel_id}"
        self._attr_icon = channel_info.get("icon", "mdi:led-strip-variant")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
        )

    @property
    def is_on(self) -> bool:
        """Return true if this channel is on."""
        return self.coordinator.is_on and (self.coordinator.channels.get(self._channel, 0) > 0)

    @property
    def brightness(self) -> int:
        """Return the channel brightness mapped from 0-100% to 0-255."""
        pct = self.coordinator.channels.get(self._channel, 0)
        return int(round(pct * 2.55))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "channel_id": self._channel,
            "percentage": self.coordinator.channels.get(self._channel, 0),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the channel."""
        if ATTR_BRIGHTNESS in kwargs:
            pct = int(round(kwargs[ATTR_BRIGHTNESS] / 2.55))
        else:
            pct = self.coordinator.channels.get(self._channel, 75)
            if pct <= 0:
                pct = CHANNELS.get(self._channel, {}).get("default", 75) or 75
        await self.coordinator.async_set_channel(self._channel, pct)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the channel."""
        await self.coordinator.async_set_channel(self._channel, 0)
