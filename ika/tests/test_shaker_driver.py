"""Test the shaker driver responds with correct data."""
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
            'name': "SHAKE AND BAKE",
            'version': 1,
            'software_ID': 2,
    }


@mock.patch('ika.Shaker', Shaker)
def test_driver_cli_with_info(capsys):
    """Confirm the commandline interface works."""
    command_line([ADDRESS, '--type', 'shaker'])
    captured = capsys.readouterr()
    assert 'speed' in captured.out
    assert 'name' in captured.out


@mock.patch('ika.Shaker', Shaker)
def test_driver_cli(capsys):
    """Confirm the commandline interface works with --no-info."""
    command_line([ADDRESS, '--type', 'shaker', '--no-info'])
    captured = capsys.readouterr()
    assert 'speed' in captured.out
    assert 'name' not in captured.out


async def test_get_response(driver, expected_info_response):
    """Confirm that the driver returns correct values on get_info() calls."""
    assert expected_info_response == await driver.get_info()


async def test_readme_example(expected_info_response):
    """Confirm the readme example using an async context manager works."""
    async def get():
        async with Shaker(ADDRESS) as device:
            response = await device.get()       # Get speed, torque, temp, setpoints
            assert 'speed' in response
            assert expected_info_response == await device.get_info()  # Get name
    await get()


async def test_setpoint_roundtrip():
    """Confirm that the setpoint can be updated."""
    async def get():
        async with Shaker(ADDRESS) as device:
            with pytest.raises(ValueError, match="Setpoint invalid"):
                await device.set(equipment='shaker', setpoint=299)
            with pytest.raises(ValueError, match="Setpoint invalid"):
                await device.set(equipment='shaker', setpoint=3001)
            with pytest.raises(ValueError, match="Setpoint invalid"):
                await device.set(equipment='heater', setpoint=0)
            with pytest.raises(ValueError, match="Setpoint invalid"):
                await device.set(equipment='heater', setpoint=101)
            speed_sp = round(uniform(300, 1000), 0)
            temp_sp = round(uniform(30, 100), 2)
            await device.set(equipment='shaker', setpoint=speed_sp)
            await device.set(equipment='heater', setpoint=temp_sp)
            response = await device.get()
            assert speed_sp == response['speed']['setpoint']
            assert temp_sp == response['temp']['setpoint']
    await get()


async def test_start_stop():
    """Confirm that the shaker motor can be controlled."""
    async def get():
        async with Shaker(ADDRESS) as device:
            response = await device.get()
            assert response['temp']['active'] is False
            assert response['speed']['active']

            await device.control(equipment='heater', on=True)
            response = await device.get()
            assert response['temp']['active']
            assert response['speed']['active']

            await device.control(equipment='shaker', on=False)
            response = await device.get()
            assert response['temp']['active']
            assert response['speed']['active'] is False

            await device.control(equipment='heater', on=False)
            await device.control(equipment='shaker', on=True)
            response = await device.get()
            assert response['temp']['active'] is False
            assert response['speed']['active']
    await get()
