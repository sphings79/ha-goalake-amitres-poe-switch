"""Constants for the Goalake / Amitres PoE switch integration."""

DOMAIN = "goalake_poe_switch"

CONF_HOST = "host"  # same key as homeassistant.const.CONF_HOST

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 30  # seconds; the device is slow and allows one session only
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 3600

MANUFACTURER = "Goalake / Amitres"
