"""DataUpdateCoordinator for AquaReef Aquarium Lighting."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
import re
from typing import Any

import aiohttp
from aiohttp import BasicAuth

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CHANNELS,
    DEFAULT_HTTP_PORT,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DOMAIN,
    PRESET_MODES,
    SCAN_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)


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
                            # Approximate dBm from percentage
                            data["rssi_dbm"] = round((self.rssi_pct / 2) - 100)

                        data["online"] = True
                        data["rssi_pct"] = self.rssi_pct
                        data["ssid"] = self.ssid
                        data["mac"] = self.mac
                        data["model"] = self.model
                        data["version"] = self.version
                        data["chip"] = self.chip
                        data["ap_name"] = self.ap_name
                    else:
                        _LOGGER.warning("HTTP status returned code %s", resp.status)
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

    async def async_set_channel(self, channel: str, level_pct: int) -> None:
        """Set individual channel brightness percentage (0-100)."""
        level_pct = max(0, min(100, int(level_pct)))
        self.channels[channel] = level_pct

        # If any channel is > 0, light is considered ON
        if any(v > 0 for v in self.channels.values()):
            self.is_on = True

        await self._async_sync_hardware()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_all_channels(self, levels: dict[str, int]) -> None:
        """Set all channel percentages at once."""
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
        if mode in PRESET_MODES:
            self.current_mode = mode
            if mode == "Ay Işığı / Gece":
                self.channels = {"uv": 0, "royal_blue": 5, "blue": 10, "white": 0, "red": 0, "green": 0}
                self.is_on = True
            elif mode == "Gün Simülasyonu":
                # In simulation mode, app runs schedule
                self.is_on = True
            elif mode == "Mercan Alıştırma":
                # Soft 50% levels
                self.channels = {k: 40 for k in CHANNELS}
                self.is_on = True
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

        # Build packet frame: standard AquaReef packet or ASCII frame:
        # "AR:CH1,CH2,CH3,CH4,CH5,CH6\r\n"
        uv = effective_channels.get("uv", 0)
        rb = effective_channels.get("royal_blue", 0)
        b = effective_channels.get("blue", 0)
        w = effective_channels.get("white", 0)
        r = effective_channels.get("red", 0)
        g = effective_channels.get("green", 0)

        # Send structured text frame
        ascii_frame = f"AQUAREEF:{uv},{rb},{b},{w},{r},{g}\r\n".encode("ascii")
        # Also binary frame [0xAA, 0x55, 6 channels, checksum]
        checksum = (uv + rb + b + w + r + g) & 0xFF
        binary_frame = bytes([0xAA, 0x55, uv, rb, b, w, r, g, checksum])

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
        }
