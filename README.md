# PoolSync – Home Assistant Custom Integration

Local-polling integration for the PoolSync bridge.

- GUI setup (Config Flow)
- Poll interval + HTTP timeout configurable (Options)
- Sensors: Water Temp, Board Temp, Flow Rate, Salt PPM, Chlor Output, Boost Remaining, RSSI, Volume, Polarity Change, Cell Rail Voltage, Cell Raw Salt ADC, Online
- Number: Chlor Output (0–100%)
- Switch: Salt Boost (24h) via `boostMode`

## Manual Install
Copy `custom_components/poolsync/` into `<config>/custom_components/` and restart HA.

## Configure
Settings → Devices & Services → Add Integration → PoolSync.
Options allow changing **scan interval** (default 300s) and **HTTP timeout** (default 30s).
