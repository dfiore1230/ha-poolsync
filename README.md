
# PoolSync – Home Assistant Custom Integration

A lightweight, local-polling integration for the PoolSync bridge.

- ✅ GUI-based setup (Config Flow)
- ✅ Robust parsing of PoolSync JSON (handles quirk `?cmd=poolSync&all=`)
- ✅ Sensors: Water Temp (°C), Controller Board Temp (°C), Salt PPM, Flow Rate, Chlor Output, Online
- ✅ Converts °F→°C if needed (heuristic or option)
- ✅ Device registry, DataUpdateCoordinator

> Tested against firmware returning `devices{"0":{ status: { waterTemp, ... }}}` when using `.../api/poolsync?cmd=poolSync&all=`.

## Install

### HACS (Custom repo)
1. HACS → Integrations → **Custom repositories**
2. Add: `https://github.com/dfiore1230/ha-poolsync` (Category: Integration)
3. Search **PoolSync** → Install → Restart HA

### Manual
1. Copy `custom_components/poolsync/` to `<config>/custom_components/poolsync/`
2. Restart HA

## Configure (GUI)
- Settings → Devices & Services → **Add Integration** → **PoolSync**
- Base URL: `http://<poolsync-ip>`
- Authorization: your header value (include `Bearer ` prefix if your unit requires it)
- User token: your `user` header value
- Device index: `0` (default)
- Scan interval: 300s (default)
- Assume Fahrenheit: off (enable if your `waterTemp` is °F)

## Sensors
- `sensor.pool_water_temperature` (°C; converts from °F if needed)
- `sensor.controller_board_temperature` (°C)
- `sensor.salt_ppm`
- `sensor.flow_rate`
- `sensor.chlor_output`
- `sensor.device_online`

## Sample Lovelace (Mushroom chips + entity card)

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-chips-card
    chips:
      - type: template
        entity: sensor.pool_water_temperature
        icon: mdi:pool-thermometer
        icon_color: >-
          {% set c = states('sensor.pool_water_temperature')|float(0) %}
          {% if c < 15 %}blue{% elif c < 26 %}teal{% elif c < 31 %}amber{% else %}red{% endif %}
        content: >
          {{ states('sensor.pool_water_temperature') }} °C
      - type: template
        entity: sensor.salt_ppm
        icon: mdi:shaker-outline
        content: "Salt: {{ states('sensor.salt_ppm') }} ppm"
      - type: template
        entity: sensor.flow_rate
        icon: mdi:water-pump
        content: "Flow: {{ states('sensor.flow_rate') }} gpm"
      - type: template
        entity: sensor.chlor_output
        icon: mdi:percent
        content: "Chlor: {{ states('sensor.chlor_output') }}%"
  - type: entities
    title: PoolSync
    entities:
      - sensor.pool_water_temperature
      - sensor.controller_board_temperature
      - sensor.salt_ppm
      - sensor.flow_rate
      - sensor.chlor_output
      - sensor.device_online
```

## Troubleshooting
- Enable debug logging:
  ```yaml
  logger:
    logs:
      custom_components.poolsync: debug
  ```
- Confirm endpoint:
  ```bash
  curl -H "Authorization: <TOKEN>" -H "user: <USER>" "http://<ip>/api/poolsync?cmd=poolSync&all="
  ```

## License
MIT
