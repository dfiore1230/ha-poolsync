# PoolSync – Home Assistant Custom Integration

## Thanks to u/SOCBRIAN as some of the onboarding work inspired ChatGPT/Codex in helping that function
#### https://github.com/socbrian/AP_PoolSync

Local-polling integration for the PoolSync bridge.

- GUI setup (Config Flow)
- Poll interval + HTTP timeout configurable via Options (defaults: 300s / 30s)
- Sensors: Water Temp, Board Temp, Flow Rate, Salt PPM, Chlor Output, Boost Remaining, RSSI, Volume, Polarity Change, Cell Rail Voltage, Cell Raw Salt ADC, Online
- Number: Chlor Output (0–100%)
- Switch: Salt Boost (24h) via `boostMode`

## Manual Install
Copy `custom_components/poolsync/` into `<config>/custom_components/` and restart HA.

## Configure
Settings → Devices & Services → Add Integration → PoolSync.
After setup, use **Options** on the integration to adjust the **poll interval** (default 300s) and **HTTP request timeout** (default 30s).
