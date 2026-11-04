"""DataUpdateCoordinator for AquaReef Aquarium Lighting."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
import random
import re
import time
from typing import Any

import aiohttp
from aiohttp import BasicAuth

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
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
    SCHEDULE_LIGHT_OPTIONS,
    SCHEDULE_LIGHT_PRESETS,
    SIM_END_TIME_OPTIONS,
    SIM_MOON_END_OPTIONS,
    SIM_START_TIME_OPTIONS,
    SIMULATION_PROFILE_NAMES,
    SIMULATION_PROFILES,
    SLOT_1_TIME_OPTIONS,
    SLOT_2_TIME_OPTIONS,
    SLOT_3_TIME_OPTIONS,
    SLOT_4_TIME_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_settings"


def parse_hhmm_to_minutes(hhmm: str, default_min: int = 480) -> int:
    """Convert 'HH:MM' string to minute of day (0..1439)."""
    try:
        clean = hhmm.strip()
        if ":" not in clean:
            return default_min
        parts = clean.split(":")
        h = max(0, min(23, int(parts[0])))
        m = max(0, min(59, int(parts[1])))
        return h * 60 + m
    except Exception:
        return default_min


def is_minute_in_window(minute_now: int, start_min: int, end_min: int) -> bool:
    """Return True if minute_now is inside [start_min, end_min), supporting midnight wrap."""
    if start_min == end_min:
        return False
    if start_min < end_min:
        return start_min <= minute_now < end_min
    # Crosses midnight (e.g. 22:00 to 01:00)
    return minute_now >= start_min or minute_now < end_min


class AquaReefCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage AquaReef device communication, simulation, and schedules."""

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

        self._store = Store[dict[str, Any]](hass, STORAGE_VERSION, f"{STORAGE_KEY}_{host}")
        self._storage_loaded = False

        # Hardware identity (pre-populated to avoid any background TCP 8899 polling beeps)
        self.mac: str = "34:EA:E7:48:C6:21"
        self.serial: str = "AR3763128062746034216"
        self.model: str = "AquaReef PRO 4"
        self.version: str = "4.1.3"
        self.wattage: str = "200W"
        self.chip: str = "HF-LPT170"
        self.ssid: str = "homeguneri"
        self.rssi_pct: int = 80
        self.ap_name: str = "AquaReefPRO4:424"

        # Master & Channel state
        self.is_on: bool = True
        self.master_brightness: int = 255  # 0-255
        self.current_mode: str = "Gün Simülasyonu"
        self.channels: dict[str, int] = {
            k: CHANNELS[k]["default"] for k in CHANNEL_ORDER
        }
        self._last_active_channels: dict[str, int] = self.channels.copy()
        self.custom_saved_channels: dict[str, int] = self.channels.copy()

        # Day Simulation Settings (Gün Simülasyonu & Hazır 4 Seçenek & Saatler)
        self.simulation_enabled: bool = True
        self.simulation_profile: str = SIMULATION_PROFILE_NAMES[0]
        self.sim_start_time: str = "08:30"
        self.sim_end_time: str = "21:30"
        self.sim_moon_end_time: str = "23:30"
        self.sim_ramp_minutes: int = 60
        self.sim_moon_level: int = 15
        self.simulation_phase: str = "☀️ Gün Simülasyonu"

        # Manual Time-Slot Schedule ("Hangi Saat Hangi Işık Yansın")
        self.schedule_enabled: bool = False
        self.schedule_slots: dict[int, dict[str, Any]] = {
            1: {
                "name": "1. Dilim (Sabah)",
                "time_range": "08:30 - 12:00",
                "light_preset": "🌅 Gün Doğumu (Mavi + Hafif Beyaz & Kırmızı)",
                "intensity": 65,
            },
            2: {
                "name": "2. Dilim (Öğle)",
                "time_range": "12:00 - 17:00",
                "light_preset": "☀️ Tam Spektrum Gün Ortası (Tüm Işıklar Dengeli)",
                "intensity": 95,
            },
            3: {
                "name": "3. Dilim (Akşam)",
                "time_range": "17:00 - 21:00",
                "light_preset": "🟣 Floresan Mor & Mavi (UV + Menekşe + Royal)",
                "intensity": 70,
            },
            4: {
                "name": "4. Dilim (Gece)",
                "time_range": "21:00 - 23:30",
                "light_preset": "🌙 Gece Ay Işığı (Loş Royal Blue & Menekşe)",
                "intensity": 30,
            },
        }

        # Dynamic Effects state
        self.storm_enabled: bool = False
        self.cloud_enabled: bool = False
        self.settings_panel_open: bool = False

        # Concurrency & TCP protocol state
        self._socket_lock = asyncio.Lock()
        self._manual_mode_sent: bool = False
        self._last_sent_payload: bytes = b""
        self._last_tcp_close_ts: float = 0.0
        self._last_http_poll_ts: float = 0.0
        self._last_sim_hw_sync_ts: float = 0.0
        self._last_sim_synced_phase: str = ""
        self._sim_preview_until_ts: float = 0.0

        # Periodic 60s timer for Day Simulation and Manual Time Schedule
        self._unsub_sim_timer = async_track_time_interval(
            hass, self._async_periodic_tick, timedelta(seconds=60)
        )

    async def async_shutdown(self) -> None:
        """Clean up timers when unloading integration."""
        if self._unsub_sim_timer is not None:
            self._unsub_sim_timer()
            self._unsub_sim_timer = None

    async def async_load_stored_settings(self) -> None:
        """Load persisted simulation, schedule, and channel settings from disk."""
        if self._storage_loaded:
            return
        self._storage_loaded = True
        try:
            stored = await self._store.async_load()
            if not stored or not isinstance(stored, dict):
                return

            self.is_on = bool(stored.get("is_on", self.is_on))
            self.master_brightness = int(stored.get("master_brightness", self.master_brightness))
            self.current_mode = str(stored.get("current_mode", self.current_mode))

            if isinstance(stored.get("channels"), dict):
                for k in CHANNEL_ORDER:
                    if k in stored["channels"]:
                        self.channels[k] = max(0, min(100, int(stored["channels"][k])))

            if isinstance(stored.get("last_active_channels"), dict):
                for k in CHANNEL_ORDER:
                    if k in stored["last_active_channels"]:
                        self._last_active_channels[k] = max(
                            0, min(100, int(stored["last_active_channels"][k]))
                        )

            if isinstance(stored.get("custom_saved_channels"), dict):
                for k in CHANNEL_ORDER:
                    if k in stored["custom_saved_channels"]:
                        self.custom_saved_channels[k] = max(
                            0, min(100, int(stored["custom_saved_channels"][k]))
                        )

            self.simulation_enabled = bool(stored.get("simulation_enabled", self.simulation_enabled))
            prof = stored.get("simulation_profile")
            if prof in SIMULATION_PROFILES:
                self.simulation_profile = prof

            if stored.get("sim_start_time") in SIM_START_TIME_OPTIONS:
                self.sim_start_time = stored["sim_start_time"]
            if stored.get("sim_end_time") in SIM_END_TIME_OPTIONS:
                self.sim_end_time = stored["sim_end_time"]
            if stored.get("sim_moon_end_time") in SIM_MOON_END_OPTIONS:
                self.sim_moon_end_time = stored["sim_moon_end_time"]

            self.sim_ramp_minutes = max(
                15, min(180, int(stored.get("sim_ramp_minutes", self.sim_ramp_minutes)))
            )
            self.sim_moon_level = max(
                0, min(30, int(stored.get("sim_moon_level", self.sim_moon_level)))
            )

            self.schedule_enabled = bool(stored.get("schedule_enabled", self.schedule_enabled))
            raw_slots = stored.get("schedule_slots")
            if isinstance(raw_slots, dict):
                for s_idx in (1, 2, 3, 4):
                    s_data = raw_slots.get(str(s_idx)) or raw_slots.get(s_idx)
                    if isinstance(s_data, dict):
                        if "time_range" in s_data:
                            self.schedule_slots[s_idx]["time_range"] = str(s_data["time_range"])
                        if s_data.get("light_preset") in SCHEDULE_LIGHT_PRESETS:
                            self.schedule_slots[s_idx]["light_preset"] = s_data["light_preset"]
                        if "intensity" in s_data:
                            self.schedule_slots[s_idx]["intensity"] = max(
                                0, min(100, int(s_data["intensity"]))
                            )
        except Exception as err:
            _LOGGER.warning("Could not load stored AquaReef settings: %s", err)

    async def _async_save_settings(self) -> None:
        """Persist current settings to Home Assistant storage."""
        try:
            payload = {
                "is_on": self.is_on,
                "master_brightness": self.master_brightness,
                "current_mode": self.current_mode,
                "channels": self.channels,
                "last_active_channels": self._last_active_channels,
                "custom_saved_channels": self.custom_saved_channels,
                "simulation_enabled": self.simulation_enabled,
                "simulation_profile": self.simulation_profile,
                "sim_start_time": self.sim_start_time,
                "sim_end_time": self.sim_end_time,
                "sim_moon_end_time": self.sim_moon_end_time,
                "sim_ramp_minutes": self.sim_ramp_minutes,
                "sim_moon_level": self.sim_moon_level,
                "schedule_enabled": self.schedule_enabled,
                "schedule_slots": {str(k): v for k, v in self.schedule_slots.items()},
            }
            await self._store.async_save(payload)
        except Exception as err:
            _LOGGER.debug("Failed to save AquaReef settings: %s", err)

    def compute_simulation_channels(self, minute_now: int) -> tuple[dict[str, int], str]:
        """Compute interpolated 9-channel values for Day Simulation based on user settings."""
        peak = SIMULATION_PROFILES.get(
            self.simulation_profile, SIMULATION_PROFILES[SIMULATION_PROFILE_NAMES[0]]
        )
        start_min = parse_hhmm_to_minutes(self.sim_start_time, 510)  # default 08:30
        end_min = parse_hhmm_to_minutes(self.sim_end_time, 1290)  # default 21:30
        if end_min <= start_min + 60:
            end_min = min(1439, start_min + 120)

        ramp = max(15, min(180, self.sim_ramp_minutes))
        total_day = end_min - start_min
        if ramp * 4 > total_day:
            ramp = max(10, total_day // 4)

        # Build key spectra from the selected profile's peak
        zero_ch = {k: 0 for k in CHANNEL_ORDER}
        dawn_ch = {
            "red": int(round(peak["red"] * 0.35)),
            "green": int(round(peak["green"] * 0.20)),
            "royal_blue": int(round(peak["royal_blue"] * 0.45)),
            "blue": int(round(peak["blue"] * 0.35)),
            "white": int(round(peak["white"] * 0.15)),
            "uv": int(round(peak["uv"] * 0.30)),
            "mint": int(round(peak["mint"] * 0.15)),
            "cyan": int(round(peak["cyan"] * 0.25)),
            "violet": int(round(peak["violet"] * 0.35)),
        }
        morning_ch = {k: int(round(peak[k] * 0.78)) for k in CHANNEL_ORDER}
        peak_ch = peak.copy()
        afternoon_ch = {
            "red": int(round(peak["red"] * 0.80)),
            "green": int(round(peak["green"] * 0.55)),
            "royal_blue": int(round(peak["royal_blue"] * 0.80)),
            "blue": int(round(peak["blue"] * 0.70)),
            "white": int(round(peak["white"] * 0.45)),
            "uv": int(round(peak["uv"] * 0.65)),
            "mint": int(round(peak["mint"] * 0.45)),
            "cyan": int(round(peak["cyan"] * 0.60)),
            "violet": int(round(peak["violet"] * 0.75)),
        }
        sunset_ch = {
            "red": max(10, int(round(peak["red"] * 0.70))),
            "green": int(round(peak["green"] * 0.25)),
            "royal_blue": int(round(peak["royal_blue"] * 0.45)),
            "blue": int(round(peak["blue"] * 0.35)),
            "white": int(round(peak["white"] * 0.08)),
            "uv": int(round(peak["uv"] * 0.25)),
            "mint": int(round(peak["mint"] * 0.10)),
            "cyan": int(round(peak["cyan"] * 0.20)),
            "violet": int(round(peak["violet"] * 0.40)),
        }

        moon_lvl = max(0, min(30, self.sim_moon_level))
        if self.sim_moon_end_time == "Kapalı (Hemen Sönsün)" or moon_lvl == 0:
            moon_ch = zero_ch.copy()
            has_moon = False
        else:
            has_moon = True
            moon_ch = {
                "red": 0,
                "green": 0,
                "royal_blue": max(5, int(round(moon_lvl * (peak["royal_blue"] / 100.0)))),
                "blue": max(4, int(round(moon_lvl * 0.75 * (peak["blue"] / 100.0)))),
                "white": 0,
                "uv": max(2, int(round(moon_lvl * 0.4 * (peak["uv"] / 100.0)))),
                "mint": 0,
                "cyan": max(2, int(round(moon_lvl * 0.35 * (peak["cyan"] / 100.0)))),
                "violet": max(4, int(round(moon_lvl * 0.8 * (peak["violet"] / 100.0)))),
            }

        t0 = start_min
        t1 = start_min + ramp
        t2 = start_min + 2 * ramp
        t3 = end_min - 2 * ramp
        t4 = end_min - ramp
        t5 = end_min

        def lerp_dict(c0: dict[str, int], c1: dict[str, int], ratio: float) -> dict[str, int]:
            r = max(0.0, min(1.0, ratio))
            return {
                k: max(0, min(100, int(round(c0.get(k, 0) + r * (c1.get(k, 0) - c0.get(k, 0))))))
                for k in CHANNEL_ORDER
            }

        # Check daytime phases [t0 .. t5]
        if t0 <= minute_now < t1:
            return lerp_dict(zero_ch, dawn_ch, (minute_now - t0) / float(max(1, t1 - t0))), "🌅 Gün Doğumu (Şafak)"
        if t1 <= minute_now < t2:
            return lerp_dict(dawn_ch, morning_ch, (minute_now - t1) / float(max(1, t2 - t1))), "🌤️ Kuşluk Vakti"
        if t2 <= minute_now < t3:
            # Smooth rise to peak in first 20% of midday
            mid_span = max(1, t3 - t2)
            if minute_now - t2 < mid_span * 0.25:
                return lerp_dict(morning_ch, peak_ch, (minute_now - t2) / float(mid_span * 0.25)), "☀️ Gün Ortası (Zirve)"
            return peak_ch.copy(), "☀️ Gün Ortası (Zirve)"
        if t3 <= minute_now < t4:
            return lerp_dict(peak_ch, afternoon_ch, (minute_now - t3) / float(max(1, t4 - t3))), "⛅ İkindi Vakti"
        if t4 <= minute_now < t5:
            return lerp_dict(afternoon_ch, sunset_ch, (minute_now - t4) / float(max(1, t5 - t4))), "🌇 Gün Batımı"

        # Night / Moonlight check outside [t0 .. t5)
        if has_moon:
            if self.sim_moon_end_time == "Sabaha Kadar Açık":
                return moon_ch, "🌙 Gece / Ay Işığı"
            moon_end_min = parse_hhmm_to_minutes(self.sim_moon_end_time, 1410)
            if is_minute_in_window(minute_now, t5, moon_end_min):
                return moon_ch, "🌙 Gece / Ay Işığı"

        return zero_ch, "🌙 Gece Dinlenmesi (Kapalı)"

    def compute_schedule_channels(self, minute_now: int) -> tuple[dict[str, int], str, int | None]:
        """Compute 9-channel values for Manual Time-Slot Schedule ('Hangi Saat Hangi Işık Yansın')."""
        for slot_id in (1, 2, 3, 4):
            slot = self.schedule_slots.get(slot_id, {})
            t_range = str(slot.get("time_range", "Kapalı")).strip()
            if t_range == "Kapalı" or "-" not in t_range:
                continue
            parts = t_range.split("-")
            if len(parts) != 2:
                continue
            s_min = parse_hhmm_to_minutes(parts[0].strip(), -1)
            e_min = parse_hhmm_to_minutes(parts[1].strip(), -1)
            if s_min < 0 or e_min < 0:
                continue

            if is_minute_in_window(minute_now, s_min, e_min):
                preset_name = slot.get("light_preset", SCHEDULE_LIGHT_OPTIONS[0])
                intensity = max(0, min(100, int(slot.get("intensity", 80))))
                raw_spec = SCHEDULE_LIGHT_PRESETS.get(preset_name)
                if raw_spec == "custom":
                    base_ch = self.custom_saved_channels.copy()
                elif isinstance(raw_spec, dict):
                    base_ch = raw_spec.copy()
                else:
                    base_ch = {k: CHANNELS[k]["default"] for k in CHANNEL_ORDER}

                scale = intensity / 100.0
                scaled = {
                    k: max(0, min(100, int(round(base_ch.get(k, 0) * scale))))
                    for k in CHANNEL_ORDER
                }
                short_light = preset_name.split("(")[0].strip()
                phase_str = f"🕒 {slot_id}. Dilim ({t_range}) • {short_light} %{intensity}"
                return scaled, phase_str, slot_id

        return {k: 0 for k in CHANNEL_ORDER}, "🌙 Program Dışı (Kapalı)", None

    async def _async_periodic_tick(self, _now: datetime) -> None:
        """Periodic 60-second tick for Day Simulation and Manual Time-Slot Schedule."""
        if not self.simulation_enabled and not self.schedule_enabled:
            return

        now_ts = time.time()
        # Hold nighttime preview when user manually clicks one of the 4 simulation profiles
        if self.simulation_enabled and now_ts < self._sim_preview_until_ts:
            return

        local_now = dt_util.now()
        minute_of_day = local_now.hour * 60 + local_now.minute

        if self.schedule_enabled:
            target_channels, phase, _ = self.compute_schedule_channels(minute_of_day)
            self.current_mode = "Manuel Saat Programı"
        else:
            target_channels, phase = self.compute_simulation_channels(minute_of_day)
            self.current_mode = "Gün Simülasyonu"

        # Apply cloud effect if enabled
        if self.cloud_enabled and any(v > 0 for v in target_channels.values()):
            dim_factor = random.uniform(0.55, 0.80)
            target_channels["white"] = int(target_channels.get("white", 0) * dim_factor)
            target_channels["blue"] = int(target_channels.get("blue", 0) * dim_factor)
            target_channels["royal_blue"] = int(target_channels.get("royal_blue", 0) * dim_factor)

        old_is_on = self.is_on
        new_is_on = any(v > 0 for v in target_channels.values())
        max_channel_diff = max(
            abs(target_channels.get(k, 0) - self.channels.get(k, 0)) for k in CHANNEL_ORDER
        )

        self.channels = target_channels
        self.simulation_phase = phase
        self.is_on = new_is_on
        if new_is_on and sum(target_channels.values()) >= 25:
            self._last_active_channels = target_channels.copy()

        phase_changed = phase != self._last_sim_synced_phase
        power_changed = new_is_on != old_is_on
        periodic_due = (now_ts - self._last_sim_hw_sync_ts >= 600) and (max_channel_diff >= 3)

        if phase_changed or power_changed or periodic_due:
            self._last_sim_synced_phase = phase
            self._last_sim_hw_sync_ts = now_ts
            await self._async_sync_hardware(force_send=power_changed)

        self.async_set_updated_data(self._get_current_state())

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch status from HTTP management page (never sends TCP packets on poll to prevent beeps)."""
        if not self._storage_loaded:
            await self.async_load_stored_settings()

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
                _LOGGER.debug("HTTP status polling skipped/failed: %s", err)

        return self._get_current_state()

    async def async_send_tcp_raw(self, payload: bytes, wait_response: bool = False) -> bytes:
        """Send raw bytes over TCP to port 8899 in a thread-safe manner."""
        async with self._socket_lock:
            elapsed = time.time() - self._last_tcp_close_ts
            if elapsed < 0.30:
                await asyncio.sleep(0.30 - elapsed)

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
                        resp = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                    except asyncio.TimeoutError:
                        pass
                else:
                    await asyncio.sleep(0.06)

                writer.close()
                try:
                    await asyncio.wait_for(writer.wait_closed(), timeout=1.0)
                except Exception:
                    pass
                self._last_tcp_close_ts = time.time()
                return resp
            except Exception as err:
                self._last_tcp_close_ts = time.time()
                _LOGGER.error("Failed to send TCP command to AquaReef (%s): %s", self.host, err)
                raise

    async def _async_sync_hardware(
        self, force_send: bool = False, ensure_manual_mode: bool = False
    ) -> None:
        """Serialize 9 channels and send official 20-byte AquaReef PRO 4 'm' frame over TCP port 8899."""
        if not self.is_on:
            effective_channels = {k: 0 for k in CHANNEL_ORDER}
        else:
            scale = self.master_brightness / 255.0
            effective_channels = {
                k: max(0, min(100, int(round(self.channels.get(k, 0) * scale))))
                for k in CHANNEL_ORDER
            }

        # Official 20-byte AquaReef PRO 4 frame (Pro4DataAdapter.prepareManualData + DataHelper):
        # byte 0: 0x6D ('m' - Manual control frame)
        # byte 1..18: 9 channels * 2 bytes, where each channel level (0..100) is scaled by 40 (0..4000):
        #   ByteTranslateFirst(val)  = (val * 40) // 256
        #   ByteTranslateSecond(val) = (val * 40) % 256
        # byte 19: 0x00
        payload = bytearray(20)
        payload[0] = 0x6D  # 'm'

        idx = 1
        for ch in CHANNEL_ORDER:
            val = max(0, min(100, int(effective_channels.get(ch, 0))))
            pwm_val = val * 40
            payload[idx] = (pwm_val // 256) & 0xFF
            payload[idx + 1] = (pwm_val % 256) & 0xFF
            idx += 2
        payload[19] = 0x00
        payload_bytes = bytes(payload)

        if not force_send and payload_bytes == self._last_sent_payload and self._manual_mode_sent:
            return

        async with self._socket_lock:
            for attempt in range(2):
                elapsed = time.time() - self._last_tcp_close_ts
                if elapsed < 0.25:
                    await asyncio.sleep(0.25 - elapsed)

                try:
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(self.host, self.port),
                        timeout=3.0,
                    )
                    writer.write(payload_bytes)
                    await writer.drain()
                    await asyncio.sleep(0.08)

                    writer.close()
                    try:
                        await asyncio.wait_for(writer.wait_closed(), timeout=1.0)
                    except Exception:
                        pass

                    self._last_tcp_close_ts = time.time()
                    self._last_sent_payload = payload_bytes
                    self._manual_mode_sent = True
                    _LOGGER.debug("Synced AquaReef PRO 4 hardware frame: %s", payload_bytes.hex())
                    return
                except Exception as err:
                    self._last_tcp_close_ts = time.time()
                    if attempt == 0:
                        _LOGGER.debug("Retrying AquaReef TCP sync after error: %s", err)
                        await asyncio.sleep(0.35)
                    else:
                        _LOGGER.error(
                            "Failed to sync AquaReef hardware over TCP (%s): %s", self.host, err
                        )

    async def async_set_simulation(self, enabled: bool) -> None:
        """Enable or disable 24-hour day simulation."""
        self.simulation_enabled = enabled
        self._sim_preview_until_ts = 0.0
        if enabled:
            self.schedule_enabled = False
            self.storm_enabled = False
            self.current_mode = "Gün Simülasyonu"
            local_now = dt_util.now()
            minute_of_day = local_now.hour * 60 + local_now.minute
            calc_ch, phase = self.compute_simulation_channels(minute_of_day)
            self.channels = calc_ch
            self.simulation_phase = phase
            self.is_on = any(v > 0 for v in self.channels.values())
            self._last_sim_synced_phase = phase
            self._last_sim_hw_sync_ts = time.time()
        else:
            self.simulation_phase = "Kapalı (Manuel)"
            self.current_mode = "Manuel"
            if not any(v > 0 for v in self.channels.values()):
                self.channels = self._last_active_channels.copy()
            self.is_on = any(v > 0 for v in self.channels.values())

        await self._async_sync_hardware(force_send=True)
        await self._async_save_settings()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_simulation_profile(self, profile: str) -> None:
        """Select one of the 4 Ready-Made Day Simulation profiles and apply immediately."""
        if profile not in SIMULATION_PROFILES:
            return
        self.simulation_profile = profile
        self.simulation_enabled = True
        self.schedule_enabled = False
        self.storm_enabled = False
        self.current_mode = "Gün Simülasyonu"

        local_now = dt_util.now()
        minute_of_day = local_now.hour * 60 + local_now.minute
        calc_ch, phase = self.compute_simulation_channels(minute_of_day)

        # If selected during night/low-light hours, apply a visible 50% preview of the profile
        # and hold it for 10 minutes so the 60s timer does not immediately overwrite it!
        if sum(calc_ch.values()) < 45:
            peak = SIMULATION_PROFILES[profile]
            calc_ch = {k: max(0, min(100, int(round(peak[k] * 0.50)))) for k in CHANNEL_ORDER}
            short_p = profile.split("(")[0].strip()
            phase = f"✨ {short_p} (Aktif Önizleme)"
            self._sim_preview_until_ts = time.time() + 600
        else:
            self._sim_preview_until_ts = 0.0

        self.channels = calc_ch
        self.simulation_phase = phase
        self.is_on = True
        if self.master_brightness == 0:
            self.master_brightness = 255
        self._last_active_channels = calc_ch.copy()
        self._last_sim_synced_phase = phase
        self._last_sim_hw_sync_ts = time.time()

        await self._async_sync_hardware(force_send=True)
        await self._async_save_settings()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_simulation_config(
        self,
        profile: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        moon_end_time: str | None = None,
        ramp_minutes: int | None = None,
        moon_level: int | None = None,
    ) -> None:
        """Update Day Simulation schedule times and parameters."""
        if profile and profile in SIMULATION_PROFILES:
            self.simulation_profile = profile
        if start_time and start_time in SIM_START_TIME_OPTIONS:
            self.sim_start_time = start_time
        if end_time and end_time in SIM_END_TIME_OPTIONS:
            self.sim_end_time = end_time
        if moon_end_time and moon_end_time in SIM_MOON_END_OPTIONS:
            self.sim_moon_end_time = moon_end_time
        if ramp_minutes is not None:
            self.sim_ramp_minutes = max(15, min(180, int(ramp_minutes)))
        if moon_level is not None:
            self.sim_moon_level = max(0, min(30, int(moon_level)))

        if self.simulation_enabled:
            local_now = dt_util.now()
            minute_of_day = local_now.hour * 60 + local_now.minute
            self.channels, self.simulation_phase = self.compute_simulation_channels(minute_of_day)
            self.is_on = any(v > 0 for v in self.channels.values())
            await self._async_sync_hardware(force_send=True)

        await self._async_save_settings()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_schedule_enabled(self, enabled: bool) -> None:
        """Enable or disable Manual Time-Slot Schedule ('Hangi Saat Hangi Işık Yansın')."""
        self.schedule_enabled = enabled
        if enabled:
            self.simulation_enabled = False
            self.storm_enabled = False
            self.current_mode = "Manuel Saat Programı"
            local_now = dt_util.now()
            minute_of_day = local_now.hour * 60 + local_now.minute
            calc_ch, phase, _ = self.compute_schedule_channels(minute_of_day)
            self.channels = calc_ch
            self.simulation_phase = phase
            self.is_on = any(v > 0 for v in self.channels.values())
            if self.is_on and self.master_brightness == 0:
                self.master_brightness = 255
        else:
            self.current_mode = "Manuel"
            self.simulation_phase = "Kapalı (Manuel)"
            if not any(v > 0 for v in self.channels.values()):
                self.channels = self._last_active_channels.copy()
            self.is_on = any(v > 0 for v in self.channels.values())

        await self._async_sync_hardware(force_send=True)
        await self._async_save_settings()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_schedule_slot(
        self,
        slot: int,
        time_range: str | None = None,
        light_preset: str | None = None,
        intensity: int | None = None,
        apply_preview: bool = True,
    ) -> None:
        """Configure a Manual Time-Slot (1..4) and optionally preview/apply."""
        if slot not in (1, 2, 3, 4):
            return
        if time_range is not None:
            self.schedule_slots[slot]["time_range"] = str(time_range)
        if light_preset is not None and light_preset in SCHEDULE_LIGHT_PRESETS:
            self.schedule_slots[slot]["light_preset"] = light_preset
        if intensity is not None:
            self.schedule_slots[slot]["intensity"] = max(0, min(100, int(intensity)))

        # If schedule mode is active, or if user changed light_preset/intensity, sync hardware
        local_now = dt_util.now()
        minute_of_day = local_now.hour * 60 + local_now.minute
        calc_ch, phase, active_slot = self.compute_schedule_channels(minute_of_day)

        if self.schedule_enabled:
            if active_slot == slot or active_slot is not None:
                self.channels = calc_ch
                self.simulation_phase = phase
                self.is_on = any(v > 0 for v in self.channels.values())
                await self._async_sync_hardware(force_send=True)
            elif apply_preview and (light_preset is not None or intensity is not None):
                # Preview the edited slot immediately so user sees the light they picked
                p_name = self.schedule_slots[slot]["light_preset"]
                p_int = self.schedule_slots[slot]["intensity"]
                raw_spec = SCHEDULE_LIGHT_PRESETS.get(p_name)
                base_ch = (
                    self.custom_saved_channels.copy()
                    if raw_spec == "custom"
                    else (raw_spec.copy() if isinstance(raw_spec, dict) else self.channels.copy())
                )
                self.channels = {
                    k: max(0, min(100, int(round(base_ch.get(k, 0) * (p_int / 100.0)))))
                    for k in CHANNEL_ORDER
                }
                self.is_on = any(v > 0 for v in self.channels.values())
                await self._async_sync_hardware(force_send=True)

        await self._async_save_settings()
        self.async_set_updated_data(self._get_current_state())

    async def async_save_current_as_custom_spectrum(self) -> None:
        """Save current 9-channel manual sliders as the user's custom spectrum preset."""
        self.custom_saved_channels = self.channels.copy()
        await self._async_save_settings()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_storm(self, enabled: bool) -> None:
        """Enable or disable storm & lightning effect."""
        self.storm_enabled = enabled
        if enabled:
            self.current_mode = "Fırtına & Şimşek"
            self.simulation_enabled = False
            self.schedule_enabled = False
            self.simulation_phase = "⚡ Fırtına Efekti"
            self.is_on = True
            asyncio.create_task(self._async_trigger_storm_flashes())
        else:
            self.current_mode = "Manuel"
            self.simulation_phase = "Kapalı (Manuel)"
            await self._async_sync_hardware(force_send=True)
        self.async_set_updated_data(self._get_current_state())

    async def _async_trigger_storm_flashes(self) -> None:
        """Run a realistic series of storm lightning flashes."""
        saved_channels = self.channels.copy()
        try:
            dim_bg = {
                "red": 0, "green": 0, "royal_blue": 15, "blue": 10,
                "white": 2, "uv": 5, "mint": 0, "cyan": 5, "violet": 5,
            }
            self.channels = dim_bg
            await self._async_sync_hardware(force_send=True)

            for _ in range(3):
                if not self.storm_enabled:
                    break
                await asyncio.sleep(random.uniform(2.0, 4.0))
                for _ in range(random.randint(2, 3)):
                    if not self.storm_enabled:
                        break
                    self.channels = {
                        "red": 10, "green": 10, "royal_blue": 90, "blue": 90,
                        "white": 100, "uv": 100, "mint": 20, "cyan": 80, "violet": 100,
                    }
                    await self._async_sync_hardware(force_send=True)
                    await asyncio.sleep(random.uniform(0.35, 0.50))
                    self.channels = dim_bg
                    await self._async_sync_hardware(force_send=True)
                    await asyncio.sleep(random.uniform(0.35, 0.55))
        finally:
            if self.storm_enabled:
                self.storm_enabled = False
                self.channels = saved_channels
                self.current_mode = "Manuel"
                self.simulation_phase = "Manuel"
                await self._async_sync_hardware(force_send=True)
                self.async_set_updated_data(self._get_current_state())

    async def async_set_settings_panel(self, enabled: bool) -> None:
        """Toggle the inline dashboard settings panel visibility."""
        self.settings_panel_open = bool(enabled)
        self.async_set_updated_data(self._get_current_state())

    async def async_set_cloud(self, enabled: bool) -> None:
        """Enable or disable cloud passing effect."""
        self.cloud_enabled = enabled
        if enabled:
            self.current_mode = "Bulut Efekti"
            dim_factor = 0.65
            base = self._last_active_channels.copy()
            base["white"] = int(base.get("white", 40) * dim_factor)
            base["blue"] = int(base.get("blue", 70) * dim_factor)
            self.channels = base
            self.is_on = True
        else:
            self.channels = self._last_active_channels.copy()
        await self._async_sync_hardware(force_send=True)
        await self._async_save_settings()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_channel(self, channel: str, level_pct: int) -> None:
        """Set individual channel brightness percentage (0-100)."""
        self.simulation_enabled = False
        self.schedule_enabled = False
        self._sim_preview_until_ts = 0.0
        self.simulation_phase = "🎛️ Manuel Spektrum"
        self.current_mode = "Manuel"
        level_pct = max(0, min(100, int(level_pct)))
        self.channels[channel] = level_pct

        if any(v > 0 for v in self.channels.values()):
            self.is_on = True
            if self.master_brightness == 0:
                self.master_brightness = 255
            if sum(self.channels.values()) >= 20:
                self._last_active_channels = self.channels.copy()
        else:
            self.is_on = False

        await self._async_sync_hardware(force_send=True)
        await self._async_save_settings()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_all_channels(self, levels: dict[str, int]) -> None:
        """Set multiple or all channel percentages at once."""
        self.simulation_enabled = False
        self.schedule_enabled = False
        self._sim_preview_until_ts = 0.0
        self.simulation_phase = "🎛️ Manuel Spektrum"
        self.current_mode = "Manuel"
        for ch, val in levels.items():
            if ch in self.channels:
                self.channels[ch] = max(0, min(100, int(val)))

        if any(v > 0 for v in self.channels.values()):
            self.is_on = True
            if self.master_brightness == 0:
                self.master_brightness = 255
            if sum(self.channels.values()) >= 20:
                self._last_active_channels = self.channels.copy()
        else:
            self.is_on = False

        await self._async_sync_hardware(force_send=True)
        await self._async_save_settings()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_power(self, power: bool) -> None:
        """Turn overall light on or off reliably."""
        self.is_on = power
        self._sim_preview_until_ts = 0.0
        if not power:
            if sum(self.channels.values()) >= 20:
                self._last_active_channels = self.channels.copy()
            self.simulation_enabled = False
            self.schedule_enabled = False
            self.storm_enabled = False
            self.cloud_enabled = False
            self.simulation_phase = "⚫ Kapalı"
        else:
            if self.master_brightness == 0:
                self.master_brightness = 255
            # Ensure channels are visibly lit when turning on
            if sum(self.channels.values()) < 20:
                if sum(self._last_active_channels.values()) >= 20:
                    self.channels = self._last_active_channels.copy()
                else:
                    self.channels = {k: CHANNELS[k]["default"] for k in CHANNEL_ORDER}
                    self._last_active_channels = self.channels.copy()
            if self.simulation_phase == "⚫ Kapalı" or self.simulation_phase.endswith("(Kapalı)"):
                self.simulation_phase = "💡 Açık (Manuel)"
                self.current_mode = "Manuel"

        await self._async_sync_hardware(force_send=True, ensure_manual_mode=True)
        await self._async_save_settings()
        self.async_set_updated_data(self._get_current_state())

    async def async_set_master_brightness(self, brightness: int) -> None:
        """Set overall master brightness (0-255)."""
        self.master_brightness = max(0, min(255, int(brightness)))
        self.is_on = self.master_brightness > 0
        if self.is_on and sum(self.channels.values()) < 20:
            self.channels = self._last_active_channels.copy()
        await self._async_sync_hardware(force_send=True)
        await self._async_save_settings()
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

        if preset_val == "schedule":
            await self.async_set_schedule_enabled(True)
            return

        if preset_val == "storm":
            await self.async_set_storm(True)
            return

        if preset_val == "cloud":
            await self.async_set_cloud(True)
            return

        self.simulation_enabled = False
        self.schedule_enabled = False
        self.storm_enabled = False
        self._sim_preview_until_ts = 0.0
        self.simulation_phase = f"🎨 {mode}"

        if isinstance(preset_val, dict):
            for k in CHANNEL_ORDER:
                self.channels[k] = preset_val.get(k, 0)
            self.is_on = any(v > 0 for v in self.channels.values())
            if self.is_on:
                self.master_brightness = 255
                if sum(self.channels.values()) >= 20:
                    self._last_active_channels = self.channels.copy()
        elif mode == "Manuel":
            self.simulation_phase = "🎛️ Manuel Spektrum"
            self.is_on = True
            self.master_brightness = 255
            if sum(self.channels.values()) < 50:
                if sum(self.custom_saved_channels.values()) >= 50:
                    self.channels = self.custom_saved_channels.copy()
                elif sum(self._last_active_channels.values()) >= 50:
                    self.channels = self._last_active_channels.copy()
                else:
                    self.channels = {k: CHANNELS[k]["default"] for k in CHANNEL_ORDER}

        await self._async_sync_hardware(force_send=True, ensure_manual_mode=True)
        await self._async_save_settings()
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
                    _LOGGER.info("AquaReef reboot requested, status: %s", resp.status)
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
            "custom_saved_channels": self.custom_saved_channels.copy(),
            "simulation_enabled": self.simulation_enabled,
            "simulation_profile": self.simulation_profile,
            "sim_start_time": self.sim_start_time,
            "sim_end_time": self.sim_end_time,
            "sim_moon_end_time": self.sim_moon_end_time,
            "sim_ramp_minutes": self.sim_ramp_minutes,
            "sim_moon_level": self.sim_moon_level,
            "simulation_phase": self.simulation_phase,
            "schedule_enabled": self.schedule_enabled,
            "schedule_slots": {k: v.copy() for k, v in self.schedule_slots.items()},
            "storm_enabled": self.storm_enabled,
            "cloud_enabled": self.cloud_enabled,
        }
