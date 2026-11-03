"""DataUpdateCoordinator for AquaReef Aquarium Lighting."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
import random
import re
from typing import Any

import aiohttp
from aiohttp import BasicAuth

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .const import (
    CHANNELS,
    DEFAULT_HTTP_PORT,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DOMAIN,
    PRESET_MODES,
    PRESETS,
    SCAN_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

# 24-Hour Reef Sun Simulation Keypoints: (minute_of_day, channels_dict, phase_name)
SIMULATION_SCHEDULE = [
    (0, {"uv": 0, "royal_blue": 0, "blue": 0, "white": 0, "red": 0, "green": 0}, "🌑 Gece Dinlenmesi"),
    (480, {"uv": 0, "royal_blue": 0, "blue": 0, "white": 0, "red": 0, "green": 0}, "🌑 Gece Dinlenmesi"),  # 08:00
    (600, {"uv": 15, "royal_blue": 35, "blue": 25, "white": 10, "red": 15, "green": 5}, "🌅 Gün Doğumu (Şafak)"),  # 10:00
    (750, {"uv": 50, "royal_blue": 75, "blue": 70, "white": 40, "red": 18, "green": 15}, "🌤️ Kuşluk Vakti"),  # 12:30
    (870, {"uv": 75, "royal_blue": 95, "blue": 90, "white": 60, "red": 20, "green": 20}, "☀️ Gün Ortası (Zirve Güneş)"),  # 14:30
    (1020, {"uv": 75, "royal_blue": 95, "blue": 90, "white": 60, "red": 20, "green": 20}, "☀️ Gün Ortası (Zirve Güneş)"),  # 17:00
    (1140, {"uv": 35, "royal_blue": 65, "blue": 50, "white": 25, "red": 25, "green": 10}, "⛅ İkindi Vakti"),  # 19:00
    (1230, {"uv": 10, "royal_blue": 45, "blue": 30, "white": 5, "red": 35, "green": 5}, "🌇 Gün Batımı"),  # 20:30
    (1290, {"uv": 0, "royal_blue": 6, "blue": 2, "white": 0, "red": 0, "green": 0}, "🌙 Gece / Ay Işığı"),  # 21:30
    (1410, {"uv": 0, "royal_blue": 4, "blue": 1, "white": 0, "red": 0, "green": 0}, "🌙 Gece / Ay Işığı"),  # 23:30
    (1439, {"uv": 0, "royal_blue": 0, "blue": 0, "white": 0, "red": 0, "green": 0}, "🌑 Gece Dinlenmesi"),  # 23:59
]


def interpolate_channels(minute_now: int) -> tuple[dict[str, int], str]:
    """Calculate interpolated channel values for the current minute of the day."""
    if minute_now <= SIMULATION_SCHEDULE[0][0]:
        return SIMULATION_SCHEDULE[0][1].copy(), SIMULATION_SCHEDULE[0][2]
    if minute_now >= SIMULATION_SCHEDULE[-1][0]:
        return SIMULATION_SCHEDULE[-1][1].copy(), SIMULATION_SCHEDULE[-1][2]

    for i in range(len(SIMULATION_SCHEDULE) - 1):
        m0, ch0, p0 = SIMULATION_SCHEDULE[i]
        m1, ch1, p1 = SIMULATION_SCHEDULE[i + 1]

        if m0 <= minute_now <= m1:
            ratio = 0.0 if m1 == m0 else (minute_now - m0) / float(m1 - m0)
            interp = {}
            for k in CHANNELS:
                v0 = ch0.get(k, 0)
                v1 = ch1.get(k, 0)
                interp[k] = int(round(v0 + ratio * (v1 - v0)))
            phase = p1 if ratio >= 0.5 else p0
            return interp, phase

    return SIMULATION_SCHEDULE[0][1].copy(), SIMULATION_SCHEDULE[0][2]


class AquaReefCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage AquaReef device polling and communication."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int = DEFAULT_PORT,
        http_port: int = DEFAULT_HTTP_PORT,
        username: str = DEFAULT_USERNAME,
        password: str = DEFAULT_PASSWORD,
        name: str = "AquaReef PRO 4",
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{host}",
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.host = host
        self.port = port
        self.http_port = http_port
        self.username = username
        self.password = password
        self.device_name = name

        # Discovered hardware attributes
        self.mac: str = "34:EA:E7:48:C6:21"
        self.model: str = "AquaReef PRO 4"
        self.version: str = "V1.00"
        self.chip: str = "HF-LPT170"
        self.ssid: str = ""
        self.rssi_pct: int = 0
        self.ap_name: str = ""

        # Internal lighting state
        self.is_on: bool = True
        self.master_brightness: int = 255  # 0-255
        self.current_mode: str = "Manuel"
        self.channels: dict[str, int] = {k: 100 for k in CHANNELS}

        # Simulation & Dynamic Effects state
        self.simulation_enabled: bool = False
        self.simulation_phase: str = "Kapalı"
        self.storm_enabled: bool = False
        self.cloud_enabled: bool = False

        # Fast background simulation timer (every 30 seconds)
        self._unsub_sim_timer = async_track_time_interval(
            hass, self._async_simulation_tick, timedelta(seconds=30)
        )

    async def _async_simulation_tick(self, _now: datetime) -> None:
        """Periodic background tick for smooth 24-hour day simulation and effects."""
        if not self.simulation_enabled:
            return

        local_now = dt_util.now()
        minute_of_day = local_now.hour * 60 + local_now.minute
        target_channels, phase = interpolate_channels(minute_of_day)

        self.simulation_phase = phase
        self.current_mode = "Gün Simülasyonu"

        # Apply cloud effect if enabled (temporarily dim white & blues)
        if self.cloud_enabled:
            dim_factor = random.uniform(0.5, 0.75)
            target_channels["white"] = int(target_channels.get("white", 0) * dim_factor)
            target_channels["blue"] = int(target_channels.get("blue", 0) * dim_factor)

        self.channels = target_channels
        self.is_on = any(v > 0 for v in self.channels.values())

        await self._async_sync_hardware()
        self.async_set_updated_data(self._get_current_state())

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch status from device."""
        data: dict[str, Any] = {
            "online": False,
            "tcp_connected": False,
            "rssi_pct": self.rssi_pct,
            "rssi_dbm": None,
            "ssid": self.ssid,
            "ip": self.host,
            "mac": self.mac,
            "model": self.model,
            "version": self.version,
            "chip": self.chip,
            "ap_name": self.ap_name,
            "is_on": self.is_on,
            "master_brightness": self.master_brightness,
            "current_mode": self.current_mode,
            "channels": self.channels.copy(),
            "simulation_enabled": self.simulation_enabled,
            "simulation_phase": self.simulation_phase,
            "storm_enabled": self.storm_enabled,
            "cloud_enabled": self.cloud_enabled,
        }

        # 1. Query HTTP management status page
        url = f"http://{self.host}:{self.http_port}/status_en.html"
        auth = BasicAuth(self.username, self.password)
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(auth=auth, timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        var_matches = re.findall(r'var\s+(\w+)\s*=\s*"([^"]*)";', text)
                        parsed = dict(var_matches)

                        self.chip = parsed.get("cover_mid", self.chip)
                        self.version = parsed.get("cover_ver", self.version)
                        self.ap_name = parsed.get("cover_ap_ssid", self.ap_name)
                        if self.ap_name and "AquaReef" in self.ap_name:
                            self.model = self.ap_name.split(":")[0]

                        self.mac = parsed.get("cover_sta_mac") or parsed.get("cover_ap_mac", self.mac)
                        self.ssid = parsed.get("cover_sta_ssid", self.ssid)

                        raw_rssi = parsed.get("cover_sta_rssi", "0%").replace("%", "").strip()
                        if raw_rssi.isdigit():
                            self.rssi_pct = int(raw_rssi)
                            data["rssi_dbm"] = round((self.rssi_pct / 2) - 100)

                        data["online"] = True
                        data["rssi_pct"] = self.rssi_pct
                        data["ssid"] = self.ssid
                        data["mac"] = self.mac
                        data["model"] = self.model
                        data["version"] = self.version
                        data["chip"] = self.chip
                        data["ap_name"] = self.ap_name
        except Exception as err:
            _LOGGER.debug("HTTP status polling failed: %s", err)

        # 2. Check TCP Socket connection on port 8899
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=2.0,
            )
            data["tcp_connected"] = True
            writer.close()
            await writer.wait_closed()
        except Exception as err:
            _LOGGER.debug("TCP socket check failed: %s", err)
            data["tcp_connected"] = False

        if not data["online"] and not data["tcp_connected"]:
            raise UpdateFailed(f"Cannot reach AquaReef at {self.host}")

        return data

    async def async_send_tcp_raw(self, payload: bytes, wait_response: bool = False) -> bytes:
        """Send raw bytes over TCP to port 8899."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=3.0,
            )
            writer.write(payload)
            await writer.drain()

            resp = b""
            if wait_response:
                try:
                    resp = await asyncio.wait_for(reader.read(1024), timeout=1.5)
                except asyncio.TimeoutError:
                    pass

            writer.close()
            await writer.wait_closed()
            return resp
        except Exception as err:
            _LOGGER.error("Failed to send TCP command to AquaReef (%s): %s", self.host, err)
            raise

    async def async_set_simulation(self, enabled: bool) -> None:
        """Enable or disable 24-hour day simulation."""
        self.simulation_enabled = enabled
        if enabled:
            self.current_mode = "Gün Simülasyonu"
            local_now = dt_util.now()
            minute_of_day = local_now.hour * 60 + local_now.minute
            self.channels, self.simulation_phase = interpolate_channels(minute_of_day)
            self.is_on = any(v > 0 for v in self.channels.values())
        else:
            self.simulation_phase = "Kapalı (Manuel)"
            self.current_mode = "Manuel"

        await self._async_sync_hardware()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_storm(self, enabled: bool) -> None:
        """Enable or disable storm & lightning effect."""
        self.storm_enabled = enabled
        if enabled:
            self.current_mode = "Fırtına & Şimşek"
            self.simulation_enabled = False
            # Start lightning flashes
            asyncio.create_task(self._async_trigger_storm_flashes())
        else:
            self.current_mode = "Manuel"
        self.async_set_updated_data(self._get_current_state())

    async def _async_trigger_storm_flashes(self) -> None:
        """Run a realistic series of storm lightning flashes."""
        saved_channels = self.channels.copy()
        try:
            # Dim base background
            dim_bg = {"uv": 5, "royal_blue": 15, "blue": 10, "white": 2, "red": 0, "green": 0}
            self.channels = dim_bg
            await self._async_sync_hardware()

            for _ in range(3):
                if not self.storm_enabled:
                    break
                await asyncio.sleep(random.uniform(2.0, 5.0))
                # Double/triple quick flashes
                for _ in range(random.randint(2, 4)):
                    if not self.storm_enabled:
                        break
                    # Lightning peak
                    self.channels = {"uv": 100, "royal_blue": 80, "blue": 80, "white": 100, "red": 10, "green": 10}
                    await self._async_sync_hardware()
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                    # Fall back to dark
                    self.channels = dim_bg
                    await self._async_sync_hardware()
                    await asyncio.sleep(random.uniform(0.1, 0.3))
        finally:
            if not self.storm_enabled:
                self.channels = saved_channels
                await self._async_sync_hardware()
                self.async_set_updated_data(self._get_current_state())

    async def async_set_cloud(self, enabled: bool) -> None:
        """Enable or disable cloud passing effect."""
        self.cloud_enabled = enabled
        if enabled:
            self.current_mode = "Bulut Efekti"
        self.async_set_updated_data(self._get_current_state())

    async def async_set_channel(self, channel: str, level_pct: int) -> None:
        """Set individual channel brightness percentage (0-100)."""
        self.simulation_enabled = False
        self.simulation_phase = "Manuel"
        self.current_mode = "Manuel"
        level_pct = max(0, min(100, int(level_pct)))
        self.channels[channel] = level_pct

        if any(v > 0 for v in self.channels.values()):
            self.is_on = True

        await self._async_sync_hardware()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_all_channels(self, levels: dict[str, int]) -> None:
        """Set all channel percentages at once."""
        self.simulation_enabled = False
        self.simulation_phase = "Manuel"
        self.current_mode = "Manuel"
        for ch, val in levels.items():
            if ch in self.channels:
                self.channels[ch] = max(0, min(100, int(val)))

        if any(v > 0 for v in self.channels.values()):
            self.is_on = True

        await self._async_sync_hardware()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_power(self, power: bool) -> None:
        """Turn overall light on or off."""
        self.is_on = power
        if not power:
            self.simulation_enabled = False
            self.storm_enabled = False
            self.cloud_enabled = False

        await self._async_sync_hardware()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_master_brightness(self, brightness: int) -> None:
        """Set overall master brightness (0-255)."""
        self.master_brightness = max(0, min(255, brightness))
        self.is_on = self.master_brightness > 0
        await self._async_sync_hardware()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_mode(self, mode: str) -> None:
        """Set lighting mode/preset."""
        if mode not in PRESETS:
            return

        self.current_mode = mode
        preset_val = PRESETS[mode]

        if preset_val == "simulation":
            await self.async_set_simulation(True)
            return

        if preset_val == "storm":
            await self.async_set_storm(True)
            return

        if preset_val == "cloud":
            await self.async_set_cloud(True)
            return

        # Static preset dict
        self.simulation_enabled = False
        self.storm_enabled = False
        self.simulation_phase = f"Sabit Mod ({mode})"

        if isinstance(preset_val, dict):
            self.channels = preset_val.copy()
            self.is_on = any(v > 0 for v in self.channels.values())
        elif mode == "Manuel":
            self.is_on = True

        await self._async_sync_hardware()
        self.async_set_updated_data(self._get_current_state())

    async def async_reboot(self) -> None:
        """Reboot AquaReef Wi-Fi controller via HTTP API."""
        url = f"http://{self.host}:{self.http_port}/success_en.html"
        auth = BasicAuth(self.username, self.password)
        data = {"HF_PROCESS_CMD": "RESTART"}
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(auth=auth, timeout=timeout) as session:
                async with session.post(url, data=data) as resp:
                    _LOGGER.info("AquaReef reboot requested, response code: %s", resp.status)
        except Exception as err:
            _LOGGER.error("Failed to request AquaReef reboot: %s", err)
            raise

    async def _async_sync_hardware(self) -> None:
        """Serialize channels and send frame over TCP port 8899."""
        if not self.is_on:
            effective_channels = {k: 0 for k in self.channels}
        else:
            scale = self.master_brightness / 255.0
            effective_channels = {k: int(round(v * scale)) for k, v in self.channels.items()}

        uv = effective_channels.get("uv", 0)
        rb = effective_channels.get("royal_blue", 0)
        b = effective_channels.get("blue", 0)
        w = effective_channels.get("white", 0)
        r = effective_channels.get("red", 0)
        g = effective_channels.get("green", 0)

        # Build binary frame [0xAA, 0x55, 6 channels, checksum]
        checksum = (uv + rb + b + w + r + g) & 0xFF
        binary_frame = bytes([0xAA, 0x55, uv, rb, b, w, r, g, checksum])

        # Also send structured ASCII frame
        ascii_frame = f"AQUAREEF:{uv},{rb},{b},{w},{r},{g}\r\n".encode("ascii")

        try:
            await self.async_send_tcp_raw(binary_frame)
        except Exception as err:
            _LOGGER.debug("Binary sync frame send error: %s", err)

    def _get_current_state(self) -> dict[str, Any]:
        """Return dict representing current state for coordinator listeners."""
        return {
            "online": True,
            "tcp_connected": True,
            "rssi_pct": self.rssi_pct,
            "rssi_dbm": round((self.rssi_pct / 2) - 100) if self.rssi_pct else None,
            "ssid": self.ssid,
            "ip": self.host,
            "mac": self.mac,
            "model": self.model,
            "version": self.version,
            "chip": self.chip,
            "ap_name": self.ap_name,
            "is_on": self.is_on,
            "master_brightness": self.master_brightness,
            "current_mode": self.current_mode,
            "channels": self.channels.copy(),
            "simulation_enabled": self.simulation_enabled,
            "simulation_phase": self.simulation_phase,
            "storm_enabled": self.storm_enabled,
            "cloud_enabled": self.cloud_enabled,
        }
