from custom_components.poolsync.sensor import SENSORS


def _device_stats_attr_fn():
    for desc in SENSORS:
        if desc.key == "device_stats":
            return desc.attr_fn
    raise AssertionError("device_stats descriptor not found")


def test_device_stats_values():
    attr_fn = _device_stats_attr_fn()
    data = {"devices": {"0": {"stats": list(range(10))}}}
    attrs = attr_fn(data)
    for i in range(10):
        assert attrs[f"stat{i}"] == i
