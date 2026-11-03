"""Constants for the AquaReef Aquarium Lighting integration."""

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

# 9 Physical Lighting Channels for AquaReef PRO 4 in order of byte array
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
    "red": {"name": "Kırmızı (Red)", "icon": "mdi:palette", "default": 0},
    "green": {"name": "Amber / Yeşil", "icon": "mdi:leaf", "default": 0},
    "royal_blue": {"name": "Royal Blue", "icon": "mdi:wave", "default": 0},
    "blue": {"name": "Mavi (Blue)", "icon": "mdi:water", "default": 0},
    "white": {"name": "Beyaz (White)", "icon": "mdi:white-balance-sunny", "default": 0},
    "uv": {"name": "UV / Mor", "icon": "mdi:weather-sunny-alert", "default": 0},
    "mint": {"name": "Nane (Mint)", "icon": "mdi:clover", "default": 0},
    "cyan": {"name": "Turkuaz (Cyan)", "icon": "mdi:waves", "default": 0},
    "violet": {"name": "Menekşe (Violet)", "icon": "mdi:flower", "default": 0},
}

# Lighting Modes / Presets
PRESETS = {
    "Manuel": None,
    "Gün Simülasyonu": "simulation",
    "Gün Doğumu (Sunrise)": {
        "red": 15, "green": 5, "royal_blue": 35, "blue": 25, "white": 10, "uv": 15, "mint": 5, "cyan": 15, "violet": 20
    },
    "Gün Ortası (Midday)": {
        "red": 20, "green": 20, "royal_blue": 95, "blue": 90, "white": 65, "uv": 75, "mint": 30, "cyan": 70, "violet": 80
    },
    "Gün Batımı (Sunset)": {
        "red": 35, "green": 10, "royal_blue": 45, "blue": 30, "white": 5, "uv": 10, "mint": 5, "cyan": 15, "violet": 25
    },
    "Ay Işığı / Gece (Moonlight)": {
        "red": 0, "green": 0, "royal_blue": 8, "blue": 4, "white": 0, "uv": 0, "mint": 0, "cyan": 2, "violet": 4
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
SERVICE_REBOOT = "reboot"
