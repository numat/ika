"""Contains mocks for driver objects for offline testing."""

import asyncio
from random import uniform
from unittest.mock import MagicMock

from .driver import Hotplate as RealHotplate
from .driver import OverheadStirrer as RealOverheadStirrer


class OverheadStirrer(MagicMock, RealOverheadStirrer):
    """Mocks the overhead stirrer driver for offline testing."""

    def __init__(self, *args, **kwargs):
        """Set up connection parameters with default port."""
        super().__init__(*args, **kwargs)
        self.info = {
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
        if self.READ_DEVICE_NAME == command:
            return self.info['name']
        elif self.READ_TORQUE_LIMIT == command:
            return self.info['torque_limit']
        elif self.READ_SPEED_LIMIT == command:
            return self.info['speed_limit']
        elif self.READ_ACTUAL_SPEED == command:
            return round(uniform(30, 120), 2)
        elif self.READ_ACTUAL_TORQUE == command:
            return round(uniform(0, 10), 2)
        elif self.READ_PT1000 == command:
            return round(uniform(15, 60), 2)


class Hotplate(MagicMock, RealHotplate):
    """Mocks the hotplate driver for offline testing."""

    def __init__(self, *args, **kwargs):
        """Set up connection parameters with default port."""
        super().__init__(*args, **kwargs)
        self.info = {
            "name": "SPINNY HOT THING",
            "temp_limit": 150.0,
        }

    async def __aenter__(self, *args):
        """Set up connection."""
        return self

    async def __aexit__(self, *args):
        """Close connection."""
        pass

    async def _write_and_read(self, command):
        await asyncio.sleep(uniform(0.1, 0.2))
        if self.READ_DEVICE_NAME == command:
            return self.info['name']
        elif self.READ_TEMP_LIMIT == command:
            return self.info['temp_limit']
        elif self.READ_ACTUAL_SPEED == command:
            return round(uniform(10, 100), 2)
        elif self.READ_ACTUAL_PROCESS_TEMP == command:
            return round(uniform(15, 100), 2)
        elif self.READ_ACTUAL_SURFACE_TEMP == command:
            return round(uniform(80, 120), 2)
