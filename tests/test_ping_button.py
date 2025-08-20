import asyncio

from custom_components.poolsync.button import PoolSyncPingButton


class DummyCoordinator:
    def __init__(self):
        self.api = type("api", (), {"mac_address": "00:11"})()
        self.refresh_called = False

    async def async_request_refresh(self):
        self.refresh_called = True


class DummyEntry:
    data: dict = {}


def test_ping_button_requests_refresh():
    coordinator = DummyCoordinator()
    entry = DummyEntry()
    button = PoolSyncPingButton(coordinator, entry)
    asyncio.run(button.async_press())
    assert coordinator.refresh_called
