"""Test the overhead stirrer driver responds with correct data."""
from random import randint
from unittest import mock

import pytest

from ika import command_line
from ika.mock import OverheadStirrer

ADDRESS = '192.168.10.12:23'


@pytest.fixture
def driver():
    """Confirm the overhead stirrer correctly initializes."""
    return OverheadStirrer(ADDRESS)


@mock.patch('ika.OverheadStirrer', OverheadStirrer)
def test_driver_cli_with_info(capsys):
    """Confirm the commandline interface works."""
    command_line([ADDRESS, '-t', 'overhead'])
    captured = capsys.readouterr()
    assert "torque" in captured.out
    assert "name" in captured.out
    assert "null" not in captured.out


@mock.patch('ika.OverheadStirrer', OverheadStirrer)
def test_driver_cli(capsys):
    """Confirm the commandline interface works with --no-info."""
    command_line([ADDRESS, '-t', 'overhead', '--no-info'])
    captured = capsys.readouterr()
    assert "torque" in captured.out
    assert "name" not in captured.out
    assert "null" not in captured.out


async def test_get_response(driver):
    """Confirm that the driver returns correct values on get_info() calls."""
    info = await driver.get_info()
    assert 'IKA ES 60' in info['name'] or 'STIRR GO WHIRRR' in info['name']
    assert (isinstance(info['torque_limit'], float)
            and info['torque_limit'] <= 60.0 and info['torque_limit'] > 0.0)
    assert (isinstance(info['speed_limit'], float)
            and info['speed_limit'] <= 2000.0 and info['speed_limit'] > 30.0)


async def test_readme_example():
    """Confirm the readme example using an async context manager works."""
    async def get():
        async with OverheadStirrer(ADDRESS) as device:
            await device.get()       # Get speed, torque, temp
            info = await device.get_info()  # get name
            assert 'IKA ES 60' in info['name'] or 'STIRR GO WHIRRR' in info['name']
            assert (isinstance(info['torque_limit'], float)
                    and info['torque_limit'] <= 60.0 and info['torque_limit'] > 0.0)
            assert (isinstance(info['speed_limit'], float)
                    and info['speed_limit'] <= 2000.0 and info['speed_limit'] > 30.0)

    await get()


async def test_setpoint_roundtrip():
    """Confirm that setpoints can be updated."""
    async def get():
        async with OverheadStirrer(ADDRESS) as device:
            speed_limit = randint(50, 2000)
            speed_sp = randint(30, speed_limit)
            torque_limit = randint(5, 60)
            await device.control(on=True)
            await device.set(equipment='speed_limit', setpoint=speed_limit)
            await device.set(equipment='speed', setpoint=speed_sp)
            await device.set(equipment='torque_limit', setpoint=torque_limit)
            await device.control(on=False)
            response = await device.get()
            response.update(await device.get_info())
            assert speed_limit == response['speed_limit']
            assert speed_sp == response['speed']['setpoint']
            assert torque_limit == response['torque_limit']
    await get()


async def test_start_stop():
    """Confirm that the stirrer motor can be controlled."""
    async def get():
        async with OverheadStirrer(ADDRESS) as device:
            await device.control(on=True)
            response = await device.get()
            assert response['speed']['active'] is True

            await device.control(on=False)
            response = await device.get()
            assert response['speed']['active'] is False
    await get()


@pytest.mark.skip
async def test_reset():
    """Confirm that the reset functionality works."""
    async def get():
        async with OverheadStirrer(ADDRESS) as device:
            await device.reset()
            raise NotImplementedError
    await get()
