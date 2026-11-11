"""The AquaReef Aquarium Lighting integration."""

from __future__ import annotations

import logging

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
    PRESET_MODES,
    SERVICE_APPLY_PRESET,
    SERVICE_REBOOT,
    SERVICE_SEND_RAW,
    SERVICE_SET_CHANNELS,
    SERVICE_SET_SCHEDULE_SLOT,
    SERVICE_SET_SIMULATION,
    SERVICE_SET_SIMULATION_CONFIG,
)
from .coordinator import AquaReefCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.BUTTON,
    Platform.SWITCH,
]

SERVICE_SEND_RAW_SCHEMA = vol.Schema(
    {
        vol.Required("command"): cv.string,
        vol.Optional("is_hex", default=True): cv.boolean,
    }
)

SERVICE_SET_CHANNELS_SCHEMA = vol.Schema(
    {
        vol.Optional("red"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("green"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("royal_blue"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("blue"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("white"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("uv"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("mint"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("cyan"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Optional("violet"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    }
)

SERVICE_APPLY_PRESET_SCHEMA = vol.Schema(
    {
        vol.Required("preset"): vol.In(PRESET_MODES),
    }
)

SERVICE_SET_SIMULATION_SCHEMA = vol.Schema(
    {
        vol.Required("enabled"): cv.boolean,
    }
)

SERVICE_SET_SIMULATION_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional("profile"): cv.string,
        vol.Optional("start_time"): cv.string,
        vol.Optional("end_time"): cv.string,
        vol.Optional("moon_end_time"): cv.string,
        vol.Optional("ramp_minutes"): vol.All(vol.Coerce(int), vol.Range(min=15, max=180)),
        vol.Optional("moon_level"): vol.All(vol.Coerce(int), vol.Range(min=0, max=30)),
    }
)

SERVICE_SET_SCHEDULE_SLOT_SCHEMA = vol.Schema(
    {
        vol.Required("slot"): vol.All(vol.Coerce(int), vol.Range(min=1, max=4)),
        vol.Optional("time_range"): cv.string,
        vol.Optional("light_preset"): cv.string,
        vol.Optional("intensity"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AquaReef from a config entry."""
    import importlib
    import sys

    for mod_name in (
        "custom_components.aquareef.const",
        "custom_components.aquareef.coordinator",
        "custom_components.aquareef.select",
        "custom_components.aquareef.button",
    ):
        if mod_name in sys.modules:
            importlib.reload(sys.modules[mod_name])

    from .coordinator import AquaReefCoordinator as ReloadedCoordinator

    hass.data.setdefault(DOMAIN, {})

    coordinator = ReloadedCoordinator(
        hass=hass,
        host=entry.data[CONF_HOST],
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
        http_port=entry.data.get(CONF_HTTP_PORT, DEFAULT_HTTP_PORT),
        username=entry.data.get(CONF_USERNAME, DEFAULT_USERNAME),
        password=entry.data.get(CONF_PASSWORD, DEFAULT_PASSWORD),
        name=entry.data.get(CONF_NAME, DEFAULT_NAME),
    )

    await coordinator.async_load_stored_settings()
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_send_raw(call: ServiceCall) -> None:
        cmd_str = call.data["command"]
        is_hex = call.data.get("is_hex", True)
        if is_hex:
            clean = "".join(cmd_str.split()).replace("0x", "")
            payload = bytes.fromhex(clean)
        else:
            payload = cmd_str.encode("utf-8")
        await coordinator.async_send_tcp_raw(payload)

    async def handle_set_channels(call: ServiceCall) -> None:
        levels = {k: v for k, v in call.data.items() if v is not None}
        await coordinator.async_set_all_channels(levels)

    async def handle_apply_preset(call: ServiceCall) -> None:
        preset = call.data["preset"]
        await coordinator.async_set_mode(preset)

    async def handle_set_simulation(call: ServiceCall) -> None:
        enabled = call.data["enabled"]
        await coordinator.async_set_simulation(enabled)

    async def handle_set_simulation_config(call: ServiceCall) -> None:
        if "profile" in call.data and len(call.data) == 1:
            await coordinator.async_set_simulation_profile(call.data["profile"])
        else:
            await coordinator.async_set_simulation_config(
                profile=call.data.get("profile"),
                start_time=call.data.get("start_time"),
                end_time=call.data.get("end_time"),
                moon_end_time=call.data.get("moon_end_time"),
                ramp_minutes=call.data.get("ramp_minutes"),
                moon_level=call.data.get("moon_level"),
            )

    async def handle_set_schedule_slot(call: ServiceCall) -> None:
        await coordinator.async_set_schedule_slot(
            slot=call.data["slot"],
            time_range=call.data.get("time_range"),
            light_preset=call.data.get("light_preset"),
            intensity=call.data.get("intensity"),
        )

    async def handle_reboot(call: ServiceCall) -> None:
        await coordinator.async_reboot()

    hass.services.async_register(
        DOMAIN, SERVICE_SEND_RAW, handle_send_raw, schema=SERVICE_SEND_RAW_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_CHANNELS, handle_set_channels, schema=SERVICE_SET_CHANNELS_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_APPLY_PRESET, handle_apply_preset, schema=SERVICE_APPLY_PRESET_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_SIMULATION, handle_set_simulation, schema=SERVICE_SET_SIMULATION_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SIMULATION_CONFIG,
        handle_set_simulation_config,
        schema=SERVICE_SET_SIMULATION_CONFIG_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SCHEDULE_SLOT,
        handle_set_schedule_slot,
        schema=SERVICE_SET_SCHEDULE_SLOT_SCHEMA,
    )
    hass.services.async_register(DOMAIN, SERVICE_REBOOT, handle_reboot)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: AquaReefCoordinator | None = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator is not None:
        await coordinator.async_shutdown()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
