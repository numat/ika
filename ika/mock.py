"""Contains mocks for driver objects for offline testing."""
from __future__ import annotations

import asyncio
from random import uniform
from typing import Any
from unittest.mock import MagicMock

from .driver import Hotplate as RealHotplate
from .driver import OverheadStirrer as RealOverheadStirrer
from .driver import Shaker as RealShaker
from .driver import Vacuum as RealVacuum
from .driver import VacuumProtocol


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
        self.state: dict[str, Any] = {
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
        if not self.lock:
            self.lock = asyncio.Lock()
        async with self.lock:  # lock releases on CancelledError
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
        if not self.lock:
            self.lock = asyncio.Lock()
        async with self.lock:  # lock releases on CancelledError
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
        self.state: dict[str, dict[str, bool | float | str]] = {
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
            "fluid_temp": {
                "actual": 100,
            }
        }

    async def query(self, command):
        """Return mock requests to queries."""
        await asyncio.sleep(uniform(0.0, 0.05))
        if not self.lock:
            self.lock = asyncio.Lock()
        async with self.lock:  # lock releases on CancelledError
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
            elif command == self.READ_ACTUAL_FLUID_TEMP:
                return round(uniform(20, 110), 2)
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
        if not self.lock:
            self.lock = asyncio.Lock()
        async with self.lock:  # lock releases on CancelledError
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

    def __init__(self, *args, **kwargs):
        """Set up connection parameters with default port."""
        super().__init__(*args, **kwargs)
        self.hw = AsyncClientMock()
        self.state: dict[str, Any] = {
            'name': "SHAKE AND BAKE",
            'temp': {
                'setpoint': 50,
                'actual': 25,
                'active': False,
            },
            'speed': {
                'setpoint': 100,
                'actual': 100,
                'active': True,
            },
            'version': 1,
            'software_ID': 2,
        }

    async def query(self, command):
        """Return mock requests to queries."""
        if not self.lock:
            self.lock = asyncio.Lock()
        async with self.lock:  # lock releases on CancelledError
            if command == self.READ_DEVICE_NAME:
                return self.state['name']
            elif command == self.READ_SET_TEMPERATURE:
                return self.state['temp']['setpoint']
            elif command == self.READ_ACTUAL_TEMPERATURE:
                return self.state['temp']['actual']
            elif command == self.READ_HEATER_STATUS:
                return self.state['temp']['active']
            elif command == self.READ_SET_SPEED:
                return self.state['speed']['setpoint']
            elif command == self.READ_ACTUAL_SPEED:
                return self.state['speed']['actual']
            elif command == self.READ_MOTOR_STATUS:
                return self.state['speed']['active']
            elif command == self.READ_SOFTWARE_VERSION:
                return self.state['version']
            elif command == self.READ_SOFTWARE_ID:
                return self.state['software_ID']

    async def command(self, command):
        """Update mock state with commands."""
        if not self.lock:
            self.lock = asyncio.Lock()
        async with self.lock:  # lock releases on CancelledError
            if command == self.START_MOTOR:
                self.state['speed']['active'] = True
            elif command == self.STOP_MOTOR:
                self.state['speed']['active'] = False
            elif command == self.START_HEATER:
                self.state['temp']['active'] = True
            elif command == self.STOP_HEATER:
                self.state['temp']['active'] = False
            else:
                command, value = command.split(" ")
            if command == self.SET_TEMP.strip():
                self.state['temp']['setpoint'] = float(value)
            elif command == self.SET_SPEED.strip():
                self.state['speed']['setpoint'] = float(value)


class Vacuum(RealVacuum):
    """Mocks the vacuum driver for offline testing."""

    def __init__(self, *args, **kwargs):
        """Set up connection parameters with default port."""
        super().__init__(*args, **kwargs)
        self.hw = AsyncClientMock()
        self.state: dict[str, Any] = {
            'name': 'THIS SUCKS',
            'active': False,
            'mode': VacuumProtocol.Mode.AUTOMATIC.name,
            'version': '1.3.001',
            'pressure': {
                'setpoint': 0.0,
                'actual': 0.0,
            }
        }

    async def query(self, command) -> str:
        """Return mock requests to queries."""
        if not self.lock:
            self.lock = asyncio.Lock()
        async with self.lock:  # lock releases on CancelledError
            if command == self.READ_DEVICE_NAME:
                return self.state['name']
            elif command == self.READ_SET_PRESSURE:
                return str(self.state['pressure']['setpoint'])
            elif command == self.READ_ACTUAL_PRESSURE:
                return str(self.state['pressure']['actual'])
            elif command == self.READ_VAC_STATUS:
                return '75' if not self.state['active'] else '12345'
            elif command == self.READ_SOFTWARE_VERSION:
                return self.state['version']
            elif command == self.READ_VAC_MODE:
                return VacuumProtocol.Mode[self.state['mode']].value
            elif command == self.START_MEASUREMENT:
                self.state['active'] = True
            elif command == self.STOP_MEASUREMENT:
                self.state['active'] = False
            else:
                command, value = command.split(" ", 1)
            if command == self.SET_PRESSURE.strip():
                self.state['pressure']['setpoint'] = float(value)
            elif command == self.SET_DEVICE_NAME.strip():
                self.state['name'] = value
                return ""
            elif command == self.SET_VAC_MODE.strip():
                self.state['mode'] = VacuumProtocol.Mode(value).name
            return command
