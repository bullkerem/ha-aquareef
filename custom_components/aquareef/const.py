"""Constants for the AquaReef Aquarium Lighting integration."""

from __future__ import annotations

DOMAIN = "aquareef"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_NAME = "name"
CONF_HTTP_PORT = "http_port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

DEFAULT_PORT = 8899
DEFAULT_HTTP_PORT = 80
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"
DEFAULT_NAME = "AquaReef PRO 4"

SCAN_INTERVAL_SECONDS = 60

# 9 Physical Lighting Channels for AquaReef PRO 4 in order of 20-byte 'm' frame
CHANNEL_ORDER = [
    "red",
    "green",
    "royal_blue",
    "blue",
    "white",
    "uv",
    "mint",
    "cyan",
    "violet",
]

CHANNELS = {
    "red": {"name": "Kırmızı (Red)", "icon": "mdi:palette", "default": 15},
    "green": {"name": "Amber / Yeşil", "icon": "mdi:leaf", "default": 15},
    "royal_blue": {"name": "Royal Blue", "icon": "mdi:wave", "default": 85},
    "blue": {"name": "Mavi (Blue)", "icon": "mdi:water", "default": 80},
    "white": {"name": "Beyaz (White)", "icon": "mdi:white-balance-sunny", "default": 45},
    "uv": {"name": "UV / Mor", "icon": "mdi:weather-sunny-alert", "default": 60},
    "mint": {"name": "Nane (Mint)", "icon": "mdi:clover", "default": 25},
    "cyan": {"name": "Turkuaz (Cyan)", "icon": "mdi:waves", "default": 55},
    "violet": {"name": "Menekşe (Violet)", "icon": "mdi:flower", "default": 70},
}

# 4 Ready-Made Day Simulation Profiles (Hazır 4 Gün Simülasyonu Seçeneği)
SIMULATION_PROFILES: dict[str, dict[str, int]] = {
    "1. Karışık Resif (Mixed Reef)": {
        "red": 20,
        "green": 20,
        "royal_blue": 90,
        "blue": 85,
        "white": 55,
        "uv": 65,
        "mint": 25,
        "cyan": 60,
        "violet": 75,
    },
    "2. SPS Mercan (Yüksek PAR & UV)": {
        "red": 25,
        "green": 25,
        "royal_blue": 100,
        "blue": 95,
        "white": 75,
        "uv": 90,
        "mint": 35,
        "cyan": 80,
        "violet": 90,
    },
    "3. LPS & Soft (Derin Mavi Floresan)": {
        "red": 10,
        "green": 10,
        "royal_blue": 100,
        "blue": 90,
        "white": 20,
        "uv": 85,
        "mint": 12,
        "cyan": 55,
        "violet": 95,
    },
    "4. Doğal Gün Işığı (Balık & Bitki)": {
        "red": 45,
        "green": 40,
        "royal_blue": 60,
        "blue": 70,
        "white": 85,
        "uv": 20,
        "mint": 45,
        "cyan": 50,
        "violet": 30,
    },
}

SIMULATION_PROFILE_NAMES = list(SIMULATION_PROFILES.keys())

# Simulation Time Options
SIM_START_TIME_OPTIONS = [
    "06:00",
    "06:30",
    "07:00",
    "07:30",
    "08:00",
    "08:30",
    "09:00",
    "09:30",
    "10:00",
    "10:30",
    "11:00",
    "11:30",
    "12:00",
    "13:00",
    "14:00",
]

SIM_END_TIME_OPTIONS = [
    "17:00",
    "17:30",
    "18:00",
    "18:30",
    "19:00",
    "19:30",
    "20:00",
    "20:30",
    "21:00",
    "21:30",
    "22:00",
    "22:30",
    "23:00",
    "23:30",
    "23:59",
]

SIM_MOON_END_OPTIONS = [
    "Kapalı (Hemen Sönsün)",
    "21:30",
    "22:00",
    "22:30",
    "23:00",
    "23:30",
    "23:59",
    "00:30",
    "01:00",
    "02:00",
    "Sabaha Kadar Açık",
]

# Manual Time-Slot Schedule Options ("Hangi Saat Hangi Işık Yansın")
SLOT_1_TIME_OPTIONS = [
    "Kapalı",
    "06:00 - 09:00",
    "07:00 - 10:00",
    "07:00 - 11:00",
    "08:00 - 11:00",
    "08:00 - 12:00",
    "08:30 - 12:00",
    "09:00 - 12:00",
    "09:00 - 13:00",
    "10:00 - 13:00",
]

SLOT_2_TIME_OPTIONS = [
    "Kapalı",
    "11:00 - 16:00",
    "11:00 - 17:00",
    "12:00 - 16:00",
    "12:00 - 17:00",
    "12:00 - 18:00",
    "13:00 - 17:00",
    "13:00 - 18:00",
    "13:00 - 19:00",
    "14:00 - 19:00",
]

SLOT_3_TIME_OPTIONS = [
    "Kapalı",
    "16:00 - 20:00",
    "17:00 - 20:00",
    "17:00 - 21:00",
    "17:00 - 22:00",
    "18:00 - 21:00",
    "18:00 - 22:00",
    "18:00 - 23:00",
    "19:00 - 22:00",
    "19:00 - 23:00",
]

SLOT_4_TIME_OPTIONS = [
    "Kapalı",
    "20:00 - 23:00",
    "21:00 - 23:00",
    "21:00 - 23:30",
    "21:00 - 23:59",
    "22:00 - 23:30",
    "22:00 - 23:59",
    "22:00 - 01:00",
    "22:00 - 02:00",
    "23:00 - 02:00",
]

# Light spectrum choices for each manual time slot
SCHEDULE_LIGHT_PRESETS: dict[str, dict[str, int] | str] = {
    "🔵 Sadece Mavi (Royal Blue + Mavi)": {
        "red": 0, "green": 0, "royal_blue": 100, "blue": 95, "white": 0, "uv": 30, "mint": 0, "cyan": 40, "violet": 45
    },
    "🟣 Floresan Mor & Mavi (UV + Menekşe + Royal)": {
        "red": 0, "green": 0, "royal_blue": 95, "blue": 80, "white": 5, "uv": 95, "mint": 0, "cyan": 45, "violet": 100
    },
    "🌅 Gün Doğumu (Mavi + Hafif Beyaz & Kırmızı)": {
        "red": 20, "green": 10, "royal_blue": 60, "blue": 50, "white": 20, "uv": 25, "mint": 10, "cyan": 30, "violet": 35
    },
    "☀️ Tam Spektrum Gün Ortası (Tüm Işıklar Dengeli)": {
        "red": 20, "green": 20, "royal_blue": 95, "blue": 90, "white": 65, "uv": 75, "mint": 30, "cyan": 70, "violet": 80
    },
    "⚪ Beyaz + Mavi (Berrak Akvaryum Işığı)": {
        "red": 15, "green": 15, "royal_blue": 80, "blue": 85, "white": 85, "uv": 30, "mint": 35, "cyan": 60, "violet": 35
    },
    "🌊 Derin Deniz (Deep Blue Aktinik)": {
        "red": 0, "green": 5, "royal_blue": 100, "blue": 100, "white": 15, "uv": 85, "mint": 10, "cyan": 50, "violet": 90
    },
    "🌇 Gün Batımı (Kırmızı + Amber + Mavi)": {
        "red": 45, "green": 15, "royal_blue": 55, "blue": 40, "white": 10, "uv": 20, "mint": 10, "cyan": 20, "violet": 35
    },
    "🌙 Gece Ay Işığı (Loş Royal Blue & Menekşe)": {
        "red": 0, "green": 0, "royal_blue": 55, "blue": 45, "white": 0, "uv": 20, "mint": 0, "cyan": 15, "violet": 35
    },
    "🌱 Bitkili / Gün Işığı (Beyaz + Kırmızı + Yeşil)": {
        "red": 75, "green": 60, "royal_blue": 30, "blue": 40, "white": 85, "uv": 10, "mint": 40, "cyan": 20, "violet": 15
    },
    "🎛️ Özel Manuel Spektrum (Kaydettiğim Ayar)": "custom",
    "⚫ Işıklar Kapalı (%0)": {
        "red": 0, "green": 0, "royal_blue": 0, "blue": 0, "white": 0, "uv": 0, "mint": 0, "cyan": 0, "violet": 0
    },
}

SCHEDULE_LIGHT_OPTIONS = list(SCHEDULE_LIGHT_PRESETS.keys())

# Lighting Modes / Presets
PRESETS = {
    "Manuel": None,
    "Gün Simülasyonu": "simulation",
    "Manuel Saat Programı": "schedule",
    "Gün Doğumu (Sunrise)": {
        "red": 20, "green": 10, "royal_blue": 50, "blue": 40, "white": 15, "uv": 25, "mint": 10, "cyan": 25, "violet": 35
    },
    "Gün Ortası (Midday)": {
        "red": 20, "green": 20, "royal_blue": 95, "blue": 90, "white": 65, "uv": 75, "mint": 30, "cyan": 70, "violet": 80
    },
    "Gün Batımı (Sunset)": {
        "red": 45, "green": 15, "royal_blue": 55, "blue": 40, "white": 10, "uv": 25, "mint": 10, "cyan": 25, "violet": 40
    },
    "Ay Işığı / Gece (Moonlight)": {
        "red": 0, "green": 0, "royal_blue": 55, "blue": 45, "white": 0, "uv": 20, "mint": 0, "cyan": 15, "violet": 35
    },
    "Derin Deniz (Deep Blue)": {
        "red": 0, "green": 5, "royal_blue": 100, "blue": 100, "white": 15, "uv": 85, "mint": 10, "cyan": 50, "violet": 90
    },
    "Mercan Alıştırma (Acclimation)": {
        "red": 10, "green": 10, "royal_blue": 40, "blue": 40, "white": 25, "uv": 25, "mint": 15, "cyan": 25, "violet": 30
    },
    "Mercan Fotoğraf Çekim": {
        "red": 20, "green": 20, "royal_blue": 50, "blue": 50, "white": 50, "uv": 20, "mint": 20, "cyan": 35, "violet": 30
    },
    "Bitkili / Tatlı Su": {
        "red": 75, "green": 60, "royal_blue": 30, "blue": 40, "white": 85, "uv": 10, "mint": 40, "cyan": 20, "violet": 15
    },
    "Fırtına & Şimşek": "storm",
    "Bulut Efekti": "cloud",
    "Tam Güç (%100 Test)": {
        "red": 100, "green": 100, "royal_blue": 100, "blue": 100, "white": 100, "uv": 100, "mint": 100, "cyan": 100, "violet": 100
    },
}

PRESET_MODES = list(PRESETS.keys())

# Service Names
SERVICE_SEND_RAW = "send_raw_command"
SERVICE_SET_CHANNELS = "set_channels"
SERVICE_APPLY_PRESET = "apply_preset"
SERVICE_SET_SIMULATION = "set_simulation"
SERVICE_SET_SIMULATION_CONFIG = "set_simulation_config"
SERVICE_SET_SCHEDULE_SLOT = "set_schedule_slot"
SERVICE_REBOOT = "reboot"
