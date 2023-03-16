"""Test the hotplate driver responds with correct data."""
from random import uniform
from unittest import mock

import pytest

from ika import command_line
from ika.mock import Shaker

ADDRESS = 'fakeip:123'


@pytest.fixture
def driver():
    """Confirm the orbital shaker correctly initializes."""
    return Shaker(ADDRESS)


@pytest.fixture
def expected_info_response():
    """Return mocked data."""
    return {
        "name": "SHAKE AND BAKE",
        'speed': {
            'setpoint': 100,
            'actual': 100,
            'active': True,
        },
        "software_version": 1,
        "software_id": 2,
        "iap_id": 3,
        "pcb_id": 4,
        "flash_size": 1024,
    }


@mock.patch('ika.Shaker', Shaker)
def test_driver_cli_with_info(capsys):
    """Confirm the commandline interface works."""
    command_line([ADDRESS, '--type', 'shaker'])
    captured = capsys.readouterr()
    assert "speed" in captured.out
    assert "name" in captured.out


@mock.patch('ika.Shaker', Shaker)
def test_driver_cli(capsys):
    """Confirm the commandline interface works with --no-info."""
    command_line([ADDRESS, '--type', 'hotplate', '--no-info'])
    captured = capsys.readouterr()
    assert "speed" in captured.out
    assert "name" not in captured.out


async def test_get_response(driver, expected_info_response):
    """Confirm that the driver returns correct values on get_info() calls."""
    assert expected_info_response == await driver.get_info()


async def test_readme_example(expected_info_response):
    """Confirm the readme example using an async context manager works."""
    async def get():
        async with Shaker(ADDRESS) as device:
            response = await device.get()       # Get speed, torque, temp, setpoints
            assert "speed" in response
            assert expected_info_response == await device.get_info()  # Get name
    await get()


async def test_setpoint_roundtrip():
    """Confirm that the setpoint can be updated."""
    async def get():
        async with Shaker(ADDRESS) as device:
            with pytest.raises(ValueError):
                await device.set_speed(setpoint=-1)
            with pytest.raises(ValueError):
                await device.set_speed(setpoint=3001)
            speed_sp = round(uniform(15, 1000), 0)
            await device.set_speed(setpoint=speed_sp)
            assert speed_sp == await device.get_speed()
    await get()


async def test_start_stop():
    """Confirm that the shaker motor can be controlled."""
    async def get():
        async with Shaker(ADDRESS) as device:
            assert await device.get_running() is False
            await device.control(on=True)
            assert await device.get_running() is True
            await device.control(on=False)
            assert await device.get_running() is False
    await get()
