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

SCAN_INTERVAL_SECONDS = 15

# Lighting Channels
CHANNELS = {
    "uv": {"name": "UV / Mor", "icon": "mdi:weather-sunny-alert", "default": 0},
    "royal_blue": {"name": "Royal Blue", "icon": "mdi:wave", "default": 0},
    "blue": {"name": "Mavi (Blue)", "icon": "mdi:water", "default": 0},
    "white": {"name": "Beyaz (White)", "icon": "mdi:white-balance-sunny", "default": 0},
    "red": {"name": "Kırmızı (Red)", "icon": "mdi:weather-sunset", "default": 0},
    "green": {"name": "Yeşil (Green)", "icon": "mdi:sprout", "default": 0},
}

# Lighting Modes / Presets
PRESET_MODES = [
    "Manuel",
    "Gün Simülasyonu",
    "Ay Işığı / Gece",
    "Bulut Efekti",
    "Fırtına & Şimşek",
    "Mercan Alıştırma",
]

# Service Names
SERVICE_SEND_RAW = "send_raw_command"
SERVICE_SET_CHANNELS = "set_channels"
SERVICE_REBOOT = "reboot"
