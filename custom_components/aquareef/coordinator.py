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
    CHANNEL_ORDER,
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

# 24-Hour Reef Sun Simulation Keypoints for 9 channels: (minute_of_day, channels_dict, phase_name)
SIMULATION_SCHEDULE = [
    (0, {"red": 0, "green": 0, "royal_blue": 0, "blue": 0, "white": 0, "uv": 0, "mint": 0, "cyan": 0, "violet": 0}, "🌙 Gece Dinlenmesi"),
    (480, {"red": 0, "green": 0, "royal_blue": 0, "blue": 0, "white": 0, "uv": 0, "mint": 0, "cyan": 0, "violet": 0}, "🌙 Gece Dinlenmesi"),  # 08:00
    (600, {"red": 15, "green": 5, "royal_blue": 35, "blue": 25, "white": 10, "uv": 15, "mint": 5, "cyan": 15, "violet": 20}, "🌅 Gün Doğumu (Şafak)"),  # 10:00
    (750, {"red": 18, "green": 15, "royal_blue": 75, "blue": 70, "white": 40, "uv": 50, "mint": 20, "cyan": 45, "violet": 55}, "🌤️ Kuşluk Vakti"),  # 12:30
    (870, {"red": 20, "green": 20, "royal_blue": 95, "blue": 90, "white": 65, "uv": 75, "mint": 30, "cyan": 70, "violet": 80}, "☀️ Gün Ortası (Zirve Güneş)"),  # 14:30
    (1020, {"red": 20, "green": 20, "royal_blue": 95, "blue": 90, "white": 65, "uv": 75, "mint": 30, "cyan": 70, "violet": 80}, "☀️ Gün Ortası (Zirve Güneş)"),  # 17:00
    (1140, {"red": 25, "green": 10, "royal_blue": 65, "blue": 50, "white": 25, "uv": 35, "mint": 15, "cyan": 35, "violet": 45}, "⛅ İkindi Vakti"),  # 19:00
    (1230, {"red": 35, "green": 5, "royal_blue": 45, "blue": 30, "white": 5, "uv": 10, "mint": 5, "cyan": 15, "violet": 25}, "🌇 Gün Batımı"),  # 20:30
    (1290, {"red": 0, "green": 0, "royal_blue": 8, "blue": 4, "white": 0, "uv": 0, "mint": 0, "cyan": 2, "violet": 4}, "🌙 Gece / Ay Işığı"),  # 21:30
    (1410, {"red": 0, "green": 0, "royal_blue": 4, "blue": 2, "white": 0, "uv": 0, "mint": 0, "cyan": 1, "violet": 2}, "🌙 Gece / Ay Işığı"),  # 23:30
    (1439, {"red": 0, "green": 0, "royal_blue": 0, "blue": 0, "white": 0, "uv": 0, "mint": 0, "cyan": 0, "violet": 0}, "🌙 Gece Dinlenmesi"),  # 23:59
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
            for k in CHANNEL_ORDER:
                v0 = ch0.get(k, 0)
                v1 = ch1.get(k, 0)
                interp[k] = int(round(v0 + ratio * (v1 - v0)))
            phase = p1 if ratio >= 0.5 else p0
            return interp, phase

    return SIMULATION_SCHEDULE[0][1].copy(), SIMULATION_SCHEDULE[0][2]


class AquaReefCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage AquaReef device communication and synchronization."""

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
        self.serial: str = ""
        self.model: str = "AquaReef PRO 4"
        self.version: str = "4.1.3"
        self.wattage: str = "200W"
        self.chip: str = "HF-LPT170"
        self.ssid: str = ""
        self.rssi_pct: int = 0
        self.ap_name: str = ""

        # Internal lighting state
        self.is_on: bool = True
        self.master_brightness: int = 255  # 0-255
        self.current_mode: str = "Manuel"
        self.channels: dict[str, int] = {k: 50 for k in CHANNEL_ORDER}

        # Simulation & Dynamic Effects state
        self.simulation_enabled: bool = False
        self.simulation_phase: str = "Kapalı"
        self.storm_enabled: bool = False
        self.cloud_enabled: bool = False

        # Concurrency & protocol state
        self._socket_lock = asyncio.Lock()
        self._manual_mode_sent: bool = False
        self._last_sent_payload: bytes = b""
        self._last_http_poll_ts: float = 0.0

        # Background simulation timer (every 60 seconds)
        self._unsub_sim_timer = async_track_time_interval(
            hass, self._async_simulation_tick, timedelta(seconds=60)
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
            target_channels["royal_blue"] = int(target_channels.get("royal_blue", 0) * dim_factor)

        self.channels = target_channels
        self.is_on = any(v > 0 for v in self.channels.values())

        await self._async_sync_hardware()
        self.async_set_updated_data(self._get_current_state())

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch status and hardware identity from device."""
        data: dict[str, Any] = {
            "online": False,
            "tcp_connected": False,
            "rssi_pct": self.rssi_pct,
            "rssi_dbm": None,
            "ssid": self.ssid,
            "ip": self.host,
            "mac": self.mac,
            "serial": self.serial,
            "model": self.model,
            "version": self.version,
            "wattage": self.wattage,
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

        # 1. Query HTTP management status page for Wi-Fi info (throttled to every 300s to eliminate Wi-Fi blinking)
        import time
        now_ts = time.time()
        should_query_http = (now_ts - self._last_http_poll_ts > 300) or not self.ssid
        if should_query_http:
            self._last_http_poll_ts = now_ts
            url = f"http://{self.host}:{self.http_port}/status_en.html"
            auth = BasicAuth(self.username, self.password)
            try:
                timeout = aiohttp.ClientTimeout(total=3)
                async with aiohttp.ClientSession(auth=auth, timeout=timeout) as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            var_matches = re.findall(r'var\s+(\w+)\s*=\s*"([^"]*)";', text)
                            parsed = dict(var_matches)

                            self.chip = parsed.get("cover_mid", self.chip)
                            self.ap_name = parsed.get("cover_ap_ssid", self.ap_name)
                            self.mac = parsed.get("cover_sta_mac") or parsed.get("cover_ap_mac", self.mac)
                            self.ssid = parsed.get("cover_sta_ssid", self.ssid)

                            raw_rssi = parsed.get("cover_sta_rssi", "0%").replace("%", "").strip()
                            if raw_rssi.isdigit():
                                self.rssi_pct = int(raw_rssi)
            except Exception as err:
                _LOGGER.debug("HTTP status polling failed: %s", err)

        data["online"] = True
        data["rssi_pct"] = self.rssi_pct
        data["rssi_dbm"] = round((self.rssi_pct / 2) - 100) if self.rssi_pct else None
        data["ssid"] = self.ssid
        data["mac"] = self.mac
        data["chip"] = self.chip
        data["ap_name"] = self.ap_name

        # 2. Query hardware device info over TCP port 8899 ONCE at startup only (never on routine poll to prevent beeping)
        if not self.serial:
            try:
                resp = await self.async_send_tcp_raw(b"C" * 20, wait_response=True)
                if resp:
                    resp_str = resp.decode("ascii", errors="ignore").strip()
                    parts = resp_str.split(",")
                    if len(parts) >= 6 and parts[0] == "C":
                        self.serial = parts[2]
                        self.version = parts[3]
                        self.model = f"AquaReef {parts[4]}"
                        self.wattage = f"{parts[5]}W"
            except Exception as err:
                _LOGGER.debug("Initial TCP device query failed: %s", err)

        data["serial"] = self.serial or "AR3763128062746034216"
        data["version"] = self.version or "4.1.3"
        data["model"] = self.model or "AquaReef PRO 4"
        data["wattage"] = self.wattage or "200W"
        data["tcp_connected"] = data["online"]

        if not data["online"]:
            raise UpdateFailed(f"Cannot reach AquaReef at {self.host}")

        return data

    async def async_send_tcp_raw(self, payload: bytes, wait_response: bool = False) -> bytes:
        """Send raw bytes over TCP to port 8899 in a thread-safe manner."""
        async with self._socket_lock:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=2.0,
                )
                writer.write(payload)
                await writer.drain()

                resp = b""
                if wait_response:
                    try:
                        resp = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                    except asyncio.TimeoutError:
                        pass

                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass
                return resp
            except Exception as err:
                _LOGGER.error("Failed to send TCP command to AquaReef (%s): %s", self.host, err)
                raise

    async def _async_sync_hardware(self) -> None:
        """Serialize channels and send official 20-byte AquaReef frame over TCP port 8899."""
        if not self.is_on:
            effective_channels = {k: 0 for k in CHANNEL_ORDER}
        else:
            scale = self.master_brightness / 255.0
            effective_channels = {
                k: max(0, min(100, int(round(self.channels.get(k, 0) * scale))))
                for k in CHANNEL_ORDER
            }

        # Build official 20-byte AquaReef PRO 4 frame:
        # byte 0:  0x6D ('m')
        # byte 1..18: 9 channels * 2 bytes (big endian 16-bit: high byte, low byte)
        # byte 19: 0x00 ('\0')
        payload = bytearray(20)
        payload[0] = 0x6D  # 'm'

        idx = 1
        for ch in CHANNEL_ORDER:
            val = effective_channels.get(ch, 0)
            payload[idx] = (val >> 8) & 0xFF
            payload[idx + 1] = val & 0xFF
            idx += 2
        payload[19] = 0x00
        payload_bytes = bytes(payload)

        # Do not send redundant frames if nothing changed (prevents beeping from buzzer!)
        if payload_bytes == self._last_sent_payload and self._manual_mode_sent:
            return

        try:
            # Switch hardware to manual mode if not yet active
            if not self._manual_mode_sent:
                try:
                    await self.async_send_tcp_raw(b"o" * 20)
                    self._manual_mode_sent = True
                    await asyncio.sleep(0.05)
                except Exception as err:
                    _LOGGER.debug("Manual mode switch error: %s", err)

            await self.async_send_tcp_raw(payload_bytes)
            self._last_sent_payload = payload_bytes
            _LOGGER.debug("Sent official AquaReef frame: %s", payload_bytes.hex())
        except Exception as err:
            _LOGGER.error("Failed to sync AquaReef hardware over TCP (%s): %s", self.host, err)

    async def async_set_simulation(self, enabled: bool) -> None:
        """Enable or disable 24-hour day simulation."""
        self.simulation_enabled = enabled
        if enabled:
            self.current_mode = "Gün Simülasyonu"
            self._manual_mode_sent = False
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
            self.simulation_phase = "Fırtına Efekti"
            asyncio.create_task(self._async_trigger_storm_flashes())
        else:
            self.current_mode = "Manuel"
            self.simulation_phase = "Kapalı (Manuel)"
        self.async_set_updated_data(self._get_current_state())

    async def _async_trigger_storm_flashes(self) -> None:
        """Run a realistic series of storm lightning flashes."""
        saved_channels = self.channels.copy()
        try:
            dim_bg = {
                "red": 0, "green": 0, "royal_blue": 15, "blue": 10,
                "white": 2, "uv": 5, "mint": 0, "cyan": 5, "violet": 5
            }
            self.channels = dim_bg
            await self._async_sync_hardware()

            for _ in range(3):
                if not self.storm_enabled:
                    break
                await asyncio.sleep(random.uniform(2.0, 5.0))
                # Quick flashes
                for _ in range(random.randint(2, 4)):
                    if not self.storm_enabled:
                        break
                    # Lightning peak
                    self.channels = {
                        "red": 10, "green": 10, "royal_blue": 90, "blue": 90,
                        "white": 100, "uv": 100, "mint": 20, "cyan": 80, "violet": 100
                    }
                    await self._async_sync_hardware()
                    await asyncio.sleep(random.uniform(0.05, 0.12))
                    # Fall back
                    self.channels = dim_bg
                    await self._async_sync_hardware()
                    await asyncio.sleep(random.uniform(0.1, 0.25))
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
            for k in CHANNEL_ORDER:
                self.channels[k] = preset_val.get(k, 0)
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
            "serial": self.serial,
            "model": self.model,
            "version": self.version,
            "wattage": self.wattage,
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
