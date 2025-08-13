DOMAIN = "poolsync"

CONF_BASE_URL = "base_url"            # e.g. http://172.16.42.218
CONF_AUTH = "authorization"           # full header value (raw token or 'Bearer ...')
CONF_USER = "user_token"
CONF_DEVICE_INDEX = "device_index"    # "0" for first device
CONF_SCAN_INTERVAL = "scan_interval"  # seconds
CONF_ASSUME_FAHRENHEIT = "assume_fahrenheit"

DEFAULT_SCAN_INTERVAL = 300
DEFAULT_DEVICE_INDEX = "0"
DEFAULT_ASSUME_FAHRENHEIT = False

COORDINATOR_NAME = "poolsync_coordinator"
