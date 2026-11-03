"""Sensor platform for AquaReef Aquarium Lighting diagnostics and status."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
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
    """Set up AquaReef sensors from a config entry."""
    coordinator: AquaReefCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors: list[SensorEntity] = [
        AquaReefSignalPctSensor(coordinator),
        AquaReefSignalDbmSensor(coordinator),
        AquaReefIpSensor(coordinator),
        AquaReefMacSensor(coordinator),
        AquaReefSsidSensor(coordinator),
        AquaReefApSensor(coordinator),
        AquaReefFirmwareSensor(coordinator),
        AquaReefTcpStatusSensor(coordinator),
        AquaReefSimulationPhaseSensor(coordinator),
        AquaReefActivePresetSensor(coordinator),
    ]

    async_add_entities(sensors)


class AquaReefBaseSensor(CoordinatorEntity[AquaReefCoordinator], SensorEntity):
    """Base class for AquaReef sensors."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.mac)},
        )


class AquaReefSimulationPhaseSensor(AquaReefBaseSensor):
    """Current phase of 24h Day Simulation."""

    _attr_icon = "mdi:weather-sunset-up"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Gün Simülasyonu Fazı"
        self._attr_unique_id = f"{coordinator.mac}_simulation_phase"

    @property
    def native_value(self) -> str:
        """Return simulation phase."""
        return self.coordinator.simulation_phase


class AquaReefActivePresetSensor(AquaReefBaseSensor):
    """Current active preset or lighting mode."""

    _attr_icon = "mdi:palette-swatch-outline"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Aktif Efekt / Profil"
        self._attr_unique_id = f"{coordinator.mac}_active_preset"

    @property
    def native_value(self) -> str:
        """Return current mode."""
        return self.coordinator.current_mode


class AquaReefSignalPctSensor(AquaReefBaseSensor):
    """Wi-Fi Signal Strength in Percentage."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:wifi"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Wi-Fi Sinyal Gücü"
        self._attr_unique_id = f"{coordinator.mac}_wifi_signal_pct"

    @property
    def native_value(self) -> int | None:
        """Return signal percentage."""
        return self.coordinator.data.get("rssi_pct") if self.coordinator.data else None


class AquaReefSignalDbmSensor(AquaReefBaseSensor):
    """Wi-Fi Signal Strength in dBm."""

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Wi-Fi Sinyal (dBm)"
        self._attr_unique_id = f"{coordinator.mac}_wifi_signal_dbm"

    @property
    def native_value(self) -> int | None:
        """Return signal dBm."""
        return self.coordinator.data.get("rssi_dbm") if self.coordinator.data else None


class AquaReefIpSensor(AquaReefBaseSensor):
    """IP Address Sensor."""

    _attr_icon = "mdi:ip-network"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "IP Adresi"
        self._attr_unique_id = f"{coordinator.mac}_ip_address"

    @property
    def native_value(self) -> str | None:
        """Return IP."""
        return self.coordinator.host


class AquaReefMacSensor(AquaReefBaseSensor):
    """MAC Address Sensor."""

    _attr_icon = "mdi:network"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "MAC Adresi"
        self._attr_unique_id = f"{coordinator.mac}_mac_address"

    @property
    def native_value(self) -> str | None:
        """Return MAC."""
        return self.coordinator.mac


class AquaReefSsidSensor(AquaReefBaseSensor):
    """Wi-Fi SSID Sensor."""

    _attr_icon = "mdi:access-point"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Bağlı Wi-Fi Ağı"
        self._attr_unique_id = f"{coordinator.mac}_wifi_ssid"

    @property
    def native_value(self) -> str | None:
        """Return SSID."""
        return self.coordinator.data.get("ssid") if self.coordinator.data else self.coordinator.ssid


class AquaReefApSensor(AquaReefBaseSensor):
    """Device AP SSID Sensor."""

    _attr_icon = "mdi:router-wireless"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Cihaz AP Adı"
        self._attr_unique_id = f"{coordinator.mac}_device_ap"

    @property
    def native_value(self) -> str | None:
        """Return device AP name."""
        return self.coordinator.data.get("ap_name") if self.coordinator.data else self.coordinator.ap_name


class AquaReefFirmwareSensor(AquaReefBaseSensor):
    """Firmware & Chip Sensor."""

    _attr_icon = "mdi:chip"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Donanım / Firmware"
        self._attr_unique_id = f"{coordinator.mac}_firmware_info"

    @property
    def native_value(self) -> str | None:
        """Return chip and version."""
        chip = self.coordinator.data.get("chip", self.coordinator.chip) if self.coordinator.data else self.coordinator.chip
        ver = self.coordinator.data.get("version", self.coordinator.version) if self.coordinator.data else self.coordinator.version
        return f"{chip} {ver}"


class AquaReefTcpStatusSensor(AquaReefBaseSensor):
    """TCP Port 8899 Status Sensor."""

    _attr_icon = "mdi:transit-connection-variant"

    def __init__(self, coordinator: AquaReefCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "TCP Kontrol Bağlantısı"
        self._attr_unique_id = f"{coordinator.mac}_tcp_status"

    @property
    def native_value(self) -> str:
        """Return socket status."""
        if self.coordinator.data and self.coordinator.data.get("tcp_connected"):
            return "Aktif (Port 8899 Dinliyor)"
        return "Bağlantı Yok"
