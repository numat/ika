"""Contains mocks for driver objects for offline testing."""

import asyncio
from random import uniform
from typing import Any, Dict, Union
from unittest.mock import MagicMock

from .driver import Hotplate as RealHotplate
from .driver import OverheadStirrer as RealOverheadStirrer
from .driver import Shaker as RealShaker
from .driver import Vacuum as RealVacuum


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
        self.hw = AsyncClientMock()
        self.state: Dict[str, Any] = {
            'name': 'STIRR GO WHIRRR',
            'torque_limit': 60.0,
            'speed_limit': 2000.0,
            'speed': {
                'setpoint': 0.0,
                'actual': 0.0,
                'active': False,
            },
            'torque': 0.0,
            'temp': 0.0,
        }

    async def query(self, command):
        """Return mock requests to queries."""
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
        elif command == self.READ_MOTOR_STATUS:
            return self.state['speed']['active']
        elif command == self.READ_SET_SPEED:
            return self.state['speed']['setpoint']
        elif command == self.START_MOTOR:
            self.state['speed']['active'] = True
            return self.START_MOTOR
        elif command == self.STOP_MOTOR:
            self.state['speed']['active'] = False
            return self.STOP_MOTOR

    async def command(self, command):
        """Update mock state with commands."""
        await asyncio.sleep(uniform(0.0, 0.1))
        command, value = command.split(" ")
        if command == self.SET_SPEED.strip():
            self.state['speed']['setpoint'] = float(value)
        elif command == self.SET_SPEED_LIMIT.strip():
            self.state['speed_limit'] = float(value)
        elif command == self.SET_TORQUE_LIMIT.strip():
            self.state['torque_limit'] = float(value)


class Hotplate(RealHotplate):
    """Mocks the hotplate driver for offline testing."""

    def __init__(self, *args, **kwargs):
        """Set up connection parameters with default port."""
        super().__init__(*args, **kwargs)
        self.hw = AsyncClientMock()
        self.state: Dict[str, Dict[str, Union[bool, float, str]]] = {
            "info": {
                "name": "SPINNY HOT THING",
                "device_type": 1,
                "temp_limit": 150.0,
            },
            "process_temp": {
                "setpoint": 50,
                "active": False,
            },
            "surface_temp": {
                "setpoint": 70,
                "active": False,
            },
            "speed": {
                "setpoint": 300,
                "active": False,
            },
        }

    async def query(self, command):
        """Return mock requests to queries."""
        await asyncio.sleep(uniform(0.0, 0.1))
        if command == self.READ_DEVICE_NAME:
            return self.state["info"]["name"]
        elif command == self.READ_DEVICE_TYPE:
            return self.state["info"]["device_type"]
        elif command == self.READ_TEMP_LIMIT:
            return self.state["info"]["temp_limit"]
        elif command == self.READ_ACTUAL_SPEED:
            return round(uniform(10, 100), 2)
        elif command == self.READ_ACTUAL_PROCESS_TEMP:
            return round(uniform(15, 100), 2)
        elif command == self.READ_ACTUAL_SURFACE_TEMP:
            return round(uniform(80, 120), 2)
        elif command == self.READ_SURFACE_TEMP_SETPOINT:
            return self.state["surface_temp"]["setpoint"]
        elif command == self.READ_PROCESS_TEMP_SETPOINT:
            return self.state["process_temp"]["setpoint"]
        elif command == self.READ_SPEED_SETPOINT:
            return self.state["speed"]["setpoint"]
        elif command == self.READ_SHAKER_STATUS:
            return self.state["speed"]["active"]
        elif command == self.READ_PROCESS_HEATER_STATUS:
            return self.state["process_temp"]["active"]
        elif command == self.READ_SURFACE_HEATER_STATUS:
            return self.state["surface_temp"]["active"]

    async def command(self, command):
        """Update mock state with commands."""
        await asyncio.sleep(uniform(0.0, 0.1))
        if command == self.START_THE_MOTOR:
            self.state["speed"]["active"] = True
        elif command == self.STOP_THE_MOTOR:
            self.state["speed"]["active"] = False
        elif command == self.START_THE_HEATER:
            self.state["process_temp"]["active"] = True
        elif command == self.STOP_THE_HEATER:
            self.state["process_temp"]["active"] = False
        else:
            command, value = command.split(" ")
        if command == self.SET_PROCESS_TEMP_SETPOINT.strip():
            self.state["process_temp"]["setpoint"] = float(value)
        elif command == self.SET_SURFACE_TEMP_SETPOINT.strip():
            self.state["surface_temp"]["setpoint"] = float(value)


class Shaker(RealShaker):
    """Mocks the orbital shaker driver for offline testing."""


class Vacuum(RealVacuum):
    """Mocks the vacuum driver for offline testing."""
