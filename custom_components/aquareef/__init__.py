"""The AquaReef Aquarium Lighting integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_HOST,
    CONF_HTTP_PORT,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    DEFAULT_HTTP_PORT,
    DEFAULT_NAME,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DOMAIN,
    SERVICE_REBOOT,
    SERVICE_SEND_RAW,
    SERVICE_SET_CHANNELS,
)
from .coordinator import AquaReefCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.BUTTON,
]

# Service Schemas
SERVICE_SEND_RAW_SCHEMA = vol.Schema(
    {
        vol.Required("command"): cv.string,
        vol.Optional("is_hex", default=True): cv.boolean,
    }
)

SERVICE_SET_CHANNELS_SCHEMA = vol.Schema(
    {
        vol.Optional("uv"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("royal_blue"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("blue"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("white"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("red"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("green"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AquaReef from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = AquaReefCoordinator(
        hass=hass,
        host=entry.data[CONF_HOST],
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
        http_port=entry.data.get(CONF_HTTP_PORT, DEFAULT_HTTP_PORT),
        username=entry.data.get(CONF_USERNAME, DEFAULT_USERNAME),
        password=entry.data.get(CONF_PASSWORD, DEFAULT_PASSWORD),
        name=entry.data.get(CONF_NAME, DEFAULT_NAME),
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register integration services
    async def handle_send_raw(call: ServiceCall) -> None:
        cmd_str = call.data["command"]
        is_hex = call.data.get("is_hex", True)
        if is_hex:
            clean = "".join(cmd_str.split()).replace("0x", "")
            payload = bytes.fromhex(clean)
        else:
            payload = cmd_str.encode("utf-8")
        _LOGGER.info("Sending raw AquaReef payload: %s", payload)
        await coordinator.async_send_tcp_raw(payload)

    async def handle_set_channels(call: ServiceCall) -> None:
        levels = {k: v for k, v in call.data.items() if v is not None}
        _LOGGER.info("Setting AquaReef channels: %s", levels)
        await coordinator.async_set_all_channels(levels)

    async def handle_reboot(call: ServiceCall) -> None:
        _LOGGER.info("Rebooting AquaReef device")
        await coordinator.async_reboot()

    hass.services.async_register(
        DOMAIN, SERVICE_SEND_RAW, handle_send_raw, schema=SERVICE_SEND_RAW_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_CHANNELS, handle_set_channels, schema=SERVICE_SET_CHANNELS_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REBOOT, handle_reboot
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
