# PoolSync – Home Assistant Custom Integration

## Thanks to u/SOCBRIAN as some of the onboarding work inspired ChatGPT/Codex in helping that function
#### https://github.com/socbrian/AP_PoolSync

Local-polling integration for the PoolSync bridge.

### Features

- GUI setup (Config Flow)
- Poll interval + HTTP timeout configurable via Options (defaults: 300s / 30s)
- Stable MAC-address fallback for entity IDs
- Validation for poll-link numeric fields
- Masked logging for push-link tokens
- API failure handling in the coordinator
- Dynamic device index and list-aware path helper
- Sensors: Water Temp, Board Temp, Flow Rate, Salt PPM, Chlor Output, Boost Remaining, RSSI, Volume, Polarity Change, Cell Rail Voltage, Cell Raw Salt ADC, Online
- Number: Chlor Output (0–100%)
- Switch: Salt Boost (24h) via `boostMode`

## Manual Install
Copy `custom_components/poolsync/` into `<config>/custom_components/` and restart HA.

## Configure
Settings → Devices & Services → Add Integration → PoolSync.
After setup, use **Options** on the integration to adjust the **poll interval** (default 300s) and **HTTP request timeout** (default 30s).

## Releases

| Version | Highlights |
|---------|------------|
| 0.4.4 | Current sensors, number & switch entities, config flow, etc. |
| 0.4.5 (upcoming) | MAC fallback, poll-link validation, masked logging, coordinator error handling, dynamic device index, list-aware helper, get_running_loop, test fixes, manifest/translation newlines. |

