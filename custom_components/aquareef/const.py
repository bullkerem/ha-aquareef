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
PRESETS = {
    "Manuel": None,
    "Gün Simülasyonu": "simulation",
    "Gün Doğumu (Sunrise)": {"uv": 15, "royal_blue": 35, "blue": 25, "white": 10, "red": 15, "green": 5},
    "Gün Ortası (Midday)": {"uv": 75, "royal_blue": 95, "blue": 90, "white": 60, "red": 20, "green": 20},
    "Gün Batımı (Sunset)": {"uv": 10, "royal_blue": 45, "blue": 30, "white": 5, "red": 35, "green": 5},
    "Ay Işığı / Gece (Moonlight)": {"uv": 0, "royal_blue": 6, "blue": 2, "white": 0, "red": 0, "green": 0},
    "Derin Deniz (Deep Blue)": {"uv": 85, "royal_blue": 100, "blue": 100, "white": 15, "red": 0, "green": 5},
    "Mercan Alıştırma (Acclimation)": {"uv": 25, "royal_blue": 40, "blue": 40, "white": 25, "red": 10, "green": 10},
    "Mercan Fotoğraf Çekim": {"uv": 20, "royal_blue": 50, "blue": 50, "white": 50, "red": 20, "green": 20},
    "Bitkili / Tatlı Su": {"uv": 10, "royal_blue": 30, "blue": 40, "white": 85, "red": 75, "green": 60},
    "Fırtına & Şimşek": "storm",
    "Bulut Efekti": "cloud",
    "Tam Güç (%100 Test)": {"uv": 100, "royal_blue": 100, "blue": 100, "white": 100, "red": 100, "green": 100},
}

PRESET_MODES = list(PRESETS.keys())

# Service Names
SERVICE_SEND_RAW = "send_raw_command"
SERVICE_SET_CHANNELS = "set_channels"
SERVICE_APPLY_PRESET = "apply_preset"
SERVICE_SET_SIMULATION = "set_simulation"
SERVICE_REBOOT = "reboot"
