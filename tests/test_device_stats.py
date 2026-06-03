from homeassistant.const import UnitOfTemperature

from custom_components.poolsync.sensor import SENSORS


def _device_stats_attr_fn():
    for desc in SENSORS:
        if desc.key == "device_stats":
            return desc.attr_fn
    raise AssertionError("device_stats descriptor not found")


def _sensor_desc(key):
    for desc in SENSORS:
        if desc.key == key:
            return desc
    raise AssertionError(f"{key} descriptor not found")


def test_device_stats_values():
    attr_fn = _device_stats_attr_fn()
    data = {"devices": {"0": {"stats": list(range(10))}}}
    attrs = attr_fn(data)
    for i in range(10):
        assert attrs[f"stat{i}"] == i


def test_water_temperature_is_reported_as_fahrenheit():
    desc = _sensor_desc("water_temp_c")

    assert desc.native_unit_of_measurement == UnitOfTemperature.FAHRENHEIT
    assert desc.value_fn({"devices": {"0": {"status": {"waterTemp": 66}}}}) == 66
