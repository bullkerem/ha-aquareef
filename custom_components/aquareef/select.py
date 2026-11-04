"""Select platform for AquaReef Aquarium Lighting modes, simulation presets, and schedules."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    PRESET_MODES,
    SCHEDULE_LIGHT_OPTIONS,
    SIM_END_TIME_OPTIONS,
    SIM_MOON_END_OPTIONS,
    SIM_START_TIME_OPTIONS,
    SIMULATION_PROFILE_NAMES,
    SLOT_1_TIME_OPTIONS,
    SLOT_2_TIME_OPTIONS,
    SLOT_3_TIME_OPTIONS,
    SLOT_4_TIME_OPTIONS,
)
from .coordinator import AquaReefCoordinator

_LOGGER = logging.getLogger(__name__)

SLOT_TIME_MAP = {
    1: ("1. Dilim Sabah Saat Aralığı", "mdi:clock-start", SLOT_1_TIME_OPTIONS),
    2: ("2. Dilim Öğle Saat Aralığı", "mdi:clock-time-twelve-outline", SLOT_2_TIME_OPTIONS),
    3: ("3. Dilim Akşam Saat Aralığı", "mdi:clock-time-six-outline", SLOT_3_TIME_OPTIONS),
    4: ("4. Dilim Gece Saat Aralığı", "mdi:clock-end", SLOT_4_TIME_OPTIONS),
}

SLOT_LIGHT_MAP = {
    1: ("1. Dilim Sabah Yanan Işık", "mdi:weather-sunset-up"),
    2: ("2. Dilim Öğle Yanan Işık", "mdi:weather-sunny"),
    3: ("3. Dilim Akşam Yanan Işık", "mdi:weather-sunset-down"),
    4: ("4. Dilim Gece Yanan Işık", "mdi:weather-night"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AquaReef select entities from a config entry."""
    coordinator: AquaReefCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SelectEntity] = [
        AquaReefModeSelect(coordinator),
        AquaReefSimulationProfileSelect(coordinator),
        AquaReefSimStartSelect(coordinator),
        AquaReefSimEndSelect(coordinator),
        AquaReefSimMoonEndSelect(coordinator),
    ]

    for slot_id in (1, 2, 3, 4):
        t_name, t_icon, t_opts = SLOT_TIME_MAP[slot_id]
        l_name, l_icon = SLOT_LIGHT_MAP[slot_id]
        entities.append(AquaReefSlotTimeSelect(coordinator, slot_id, t_name, t_icon, t_opts))
        entities.append(AquaReefSlotLightSelect(coordinator, slot_id, l_name, l_icon))

    async_add_entities(entities)


class AquaReefBaseSelect(CoordinatorEntity[AquaReefCoordinator], SelectEntity):
    """Base class for AquaReef Select entities."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
        )


class AquaReefModeSelect(AquaReefBaseSelect):
    """Representation of the AquaReef Mode / Preset selector."""

    _attr_icon = "mdi:theme-light-dark"
    _attr_options = PRESET_MODES

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the preset mode selector."""
        super().__init__(coordinator)
        self._attr_name = "Çalışma Modu / Efekt"
        self._attr_unique_id = f"{coordinator.mac}_mode_select"

    @property
    def current_option(self) -> str | None:
        """Return the current active mode."""
        return self.coordinator.current_mode

    async def async_select_option(self, option: str) -> None:
        """Change the active mode."""
        await self.coordinator.async_set_mode(option)


class AquaReefSimulationProfileSelect(AquaReefBaseSelect):
    """Select entity for the 4 Ready-Made Day Simulation Options."""

    _attr_icon = "mdi:weather-sunny-alert"
    _attr_options = SIMULATION_PROFILE_NAMES

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the simulation profile selector."""
        super().__init__(coordinator)
        self._attr_name = "Gün Simülasyonu Profili"
        self._attr_unique_id = f"{coordinator.mac}_sim_profile_select"

    @property
    def current_option(self) -> str | None:
        """Return current simulation profile."""
        return self.coordinator.simulation_profile

    async def async_select_option(self, option: str) -> None:
        """Select simulation profile and enable simulation."""
        await self.coordinator.async_set_simulation_profile(option)


class AquaReefSimStartSelect(AquaReefBaseSelect):
    """Select entity for Day Simulation Start (Sunrise) Time."""

    _attr_icon = "mdi:weather-sunset-up"
    _attr_options = SIM_START_TIME_OPTIONS

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize simulation start time selector."""
        super().__init__(coordinator)
        self._attr_name = "Gün Simülasyonu Başlangıç Saati"
        self._attr_unique_id = f"{coordinator.mac}_sim_start_time"

    @property
    def current_option(self) -> str | None:
        """Return start time."""
        return self.coordinator.sim_start_time

    async def async_select_option(self, option: str) -> None:
        """Update start time."""
        await self.coordinator.async_set_simulation_config(start_time=option)


class AquaReefSimEndSelect(AquaReefBaseSelect):
    """Select entity for Day Simulation End (Sunset) Time."""

    _attr_icon = "mdi:weather-sunset-down"
    _attr_options = SIM_END_TIME_OPTIONS

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize simulation end time selector."""
        super().__init__(coordinator)
        self._attr_name = "Gün Simülasyonu Kapanış Saati"
        self._attr_unique_id = f"{coordinator.mac}_sim_end_time"

    @property
    def current_option(self) -> str | None:
        """Return end time."""
        return self.coordinator.sim_end_time

    async def async_select_option(self, option: str) -> None:
        """Update end time."""
        await self.coordinator.async_set_simulation_config(end_time=option)


class AquaReefSimMoonEndSelect(AquaReefBaseSelect):
    """Select entity for Night Moonlight Turn-Off Time."""

    _attr_icon = "mdi:weather-night"
    _attr_options = SIM_MOON_END_OPTIONS

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize moonlight end time selector."""
        super().__init__(coordinator)
        self._attr_name = "Gece Ay Işığı Bitiş Saati"
        self._attr_unique_id = f"{coordinator.mac}_sim_moon_end_time"

    @property
    def current_option(self) -> str | None:
        """Return moonlight end time."""
        return self.coordinator.sim_moon_end_time

    async def async_select_option(self, option: str) -> None:
        """Update moonlight end time."""
        await self.coordinator.async_set_simulation_config(moon_end_time=option)


class AquaReefSlotTimeSelect(AquaReefBaseSelect):
    """Select entity for Manual Schedule Time Slot Range."""

    def __init__(
        self,
        coordinator: AquaReefCoordinator,
        slot_id: int,
        name: str,
        icon: str,
        options: list[str],
    ) -> None:
        """Initialize time slot range selector."""
        super().__init__(coordinator)
        self._slot_id = slot_id
        self._attr_name = name
        self._attr_icon = icon
        self._attr_options = options
        self._attr_unique_id = f"{coordinator.mac}_slot_{slot_id}_time"

    @property
    def current_option(self) -> str | None:
        """Return current time range for slot."""
        val = self.coordinator.schedule_slots.get(self._slot_id, {}).get("time_range")
        if val in self._attr_options:
            return val
        return self._attr_options[0]

    async def async_select_option(self, option: str) -> None:
        """Set time range for slot."""
        await self.coordinator.async_set_schedule_slot(slot=self._slot_id, time_range=option)


class AquaReefSlotLightSelect(AquaReefBaseSelect):
    """Select entity for Manual Schedule Time Slot Light Spectrum."""

    _attr_options = SCHEDULE_LIGHT_OPTIONS

    def __init__(
        self,
        coordinator: AquaReefCoordinator,
        slot_id: int,
        name: str,
        icon: str,
    ) -> None:
        """Initialize time slot light spectrum selector."""
        super().__init__(coordinator)
        self._slot_id = slot_id
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{coordinator.mac}_slot_{slot_id}_light"

    @property
    def current_option(self) -> str | None:
        """Return current light spectrum for slot."""
        val = self.coordinator.schedule_slots.get(self._slot_id, {}).get("light_preset")
        if val in self._attr_options:
            return val
        return self._attr_options[0]

    async def async_select_option(self, option: str) -> None:
        """Set light spectrum for slot."""
        await self.coordinator.async_set_schedule_slot(slot=self._slot_id, light_preset=option)
