"""Number platform for AquaReef simulation parameters, time-slot intensities, and channels."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
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
    """Set up AquaReef number entities from a config entry."""
    coordinator: AquaReefCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[NumberEntity] = [
        AquaReefSimRampNumber(coordinator),
        AquaReefSimMoonLevelNumber(coordinator),
    ]

    slot_labels = {
        1: "1. Dilim Sabah Parlaklığı",
        2: "2. Dilim Öğle Parlaklığı",
        3: "3. Dilim Akşam Parlaklığı",
        4: "4. Dilim Gece Parlaklığı",
    }
    for slot_id, label in slot_labels.items():
        entities.append(AquaReefSlotIntensityNumber(coordinator, slot_id, label))

    for ch_id, ch_info in CHANNELS.items():
        entities.append(AquaReefChannelNumber(coordinator, ch_id, ch_info["name"], ch_info["icon"]))

    async_add_entities(entities)


class AquaReefBaseNumber(CoordinatorEntity[AquaReefCoordinator], NumberEntity):
    """Base class for AquaReef Number entities."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.SLIDER

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
        )


class AquaReefSimRampNumber(AquaReefBaseNumber):
    """Number entity for Sunrise/Sunset ramp duration in minutes."""

    _attr_icon = "mdi:timer-sand"
    _attr_native_min_value = 15
    _attr_native_max_value = 180
    _attr_native_step = 15
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize ramp duration number."""
        super().__init__(coordinator)
        self._attr_name = "Gün Doğumu/Batımı Geçiş Süresi"
        self._attr_unique_id = f"{coordinator.mac}_sim_ramp_minutes"

    @property
    def native_value(self) -> float:
        """Return current ramp duration."""
        return float(self.coordinator.sim_ramp_minutes)

    async def async_set_native_value(self, value: float) -> None:
        """Update ramp duration."""
        await self.coordinator.async_set_simulation_config(ramp_minutes=int(value))


class AquaReefSimMoonLevelNumber(AquaReefBaseNumber):
    """Number entity for Night Moonlight level percentage (0-30%)."""

    _attr_icon = "mdi:moon-waning-crescent"
    _attr_native_min_value = 0
    _attr_native_max_value = 30
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize moonlight level number."""
        super().__init__(coordinator)
        self._attr_name = "Gece Ay Işığı Seviyesi"
        self._attr_unique_id = f"{coordinator.mac}_sim_moon_level"

    @property
    def native_value(self) -> float:
        """Return current moonlight percentage."""
        return float(self.coordinator.sim_moon_level)

    async def async_set_native_value(self, value: float) -> None:
        """Update moonlight percentage."""
        await self.coordinator.async_set_simulation_config(moon_level=int(value))


class AquaReefSlotIntensityNumber(AquaReefBaseNumber):
    """Number entity for Manual Schedule Time-Slot Intensity (0-100%)."""

    _attr_icon = "mdi:brightness-percent"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: AquaReefCoordinator, slot_id: int, name: str) -> None:
        """Initialize slot intensity slider."""
        super().__init__(coordinator)
        self._slot_id = slot_id
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.mac}_slot_{slot_id}_intensity"

    @property
    def native_value(self) -> float:
        """Return slot intensity percentage."""
        return float(self.coordinator.schedule_slots.get(self._slot_id, {}).get("intensity", 80))

    async def async_set_native_value(self, value: float) -> None:
        """Set slot intensity percentage."""
        await self.coordinator.async_set_schedule_slot(slot=self._slot_id, intensity=int(value))


class AquaReefChannelNumber(AquaReefBaseNumber):
    """Direct 0-100% slider for each of the 9 spectral channels."""

    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self, coordinator: AquaReefCoordinator, channel_id: str, ch_name: str, icon: str
    ) -> None:
        """Initialize channel percentage slider."""
        super().__init__(coordinator)
        self._channel = channel_id
        self._attr_name = f"Seviye {ch_name}"
        self._attr_icon = icon
        self._attr_unique_id = f"{coordinator.mac}_num_channel_{channel_id}"

    @property
    def native_value(self) -> float:
        """Return channel percentage (0-100)."""
        return float(self.coordinator.channels.get(self._channel, 0))

    async def async_set_native_value(self, value: float) -> None:
        """Set channel percentage."""
        await self.coordinator.async_set_channel(self._channel, int(value))
