"""Contains mocks for driver objects for offline testing."""

import asyncio
from random import uniform
from unittest.mock import MagicMock

from .driver import Hotplate as RealHotplate
from .driver import OverheadStirrer as RealOverheadStirrer


class AsyncClientMock(MagicMock):
    """Magic mock that works with async methods."""

    async def __call__(self, *args, **kwargs):
        """Convert regular mocks into into an async coroutine."""
        return super().__call__(*args, **kwargs)


class OverheadStirrer(RealOverheadStirrer):
    """Mocks the overhead stirrer driver for offline testing."""

    def __init__(self, *args, **kwargs):
        """Set up connection parameters with default port."""
        super().__init__(*args, **kwargs)
        self.client = AsyncClientMock()
        self.state = {
            "name": "STIRR GO WHIRRR",
            "torque_limit": 15.0,
            "speed_limit": 150.0,
        }

    async def __aenter__(self, *args):
        """Set up connection."""
        return self

    async def __aexit__(self, *args):
        """Close connection."""
        pass

    async def _write_and_read(self, command):
        if command == self.READ_DEVICE_NAME:
            return self.state['name']
        elif command == self.READ_TORQUE_LIMIT:
            return self.state['torque_limit']
        elif command == self.READ_SPEED_LIMIT:
            return self.state['speed_limit']
        elif command == self.READ_ACTUAL_SPEED:
            return round(uniform(30, 120), 2)
        elif command == self.READ_ACTUAL_TORQUE:
            return round(uniform(0, 10), 2)
        elif command == self.READ_PT1000:
            return round(uniform(15, 60), 2)


class Hotplate(RealHotplate):
    """Mocks the hotplate driver for offline testing."""

    def __init__(self, *args, **kwargs):
        """Set up connection parameters with default port."""
        super().__init__(*args, **kwargs)
        self.client = AsyncClientMock()
        self.state = {
            "name": "SPINNY HOT THING",
            "temp_limit": 150.0,
            "process_temp_sp": 50,
            "surface_temp_sp": 70,
            "device_type": 1,
        }

    async def __aenter__(self, *args):
        """Set up connection."""
        return self

    async def __aexit__(self, *args):
        """Close connection."""
        pass

    async def _write_and_read(self, command):
        await asyncio.sleep(uniform(0.0, 0.1))
        if command == self.READ_DEVICE_NAME:
            return self.state['name']
        elif command == self.READ_TEMP_LIMIT:
            return self.state['temp_limit']
        elif command == self.READ_ACTUAL_SPEED:
            return round(uniform(10, 100), 2)
        elif command == self.READ_ACTUAL_PROCESS_TEMP:
            return round(uniform(15, 100), 2)
        elif command == self.READ_ACTUAL_SURFACE_TEMP:
            return round(uniform(80, 120), 2)
        elif command == self.READ_SURFACE_TEMP_SETPOINT:
            return self.state["surface_temp_sp"]
        elif command == self.READ_PROCESS_TEMP_SETPOINT:
            return self.state["process_temp_sp"]
        elif command == self.READ_DEVICE_TYPE:
            return self.state["device_type"]

    async def _write(self, command):
        await asyncio.sleep(uniform(0.0, 0.1))
        command, value = command.split(" ")
        if command == self.SET_PROCESS_TEMP_SETPOINT.strip():
            self.state["process_temp_sp"] = float(value)
        elif command == self.SET_SURFACE_TEMP_SETPOINT.strip():
            self.state["surface_temp_sp"] = float(value)
