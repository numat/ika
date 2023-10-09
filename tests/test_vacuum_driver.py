"""Test the vacuum driver responds with correct data."""
from random import randint
from unittest import mock

import pytest

from ika import command_line
from ika.driver import VacuumProtocol
from ika.mock import Vacuum

ADDRESS = 'fakeip:123'


@pytest.fixture
def driver():
    """Confirm the vacuum correctly initializes."""
    return Vacuum(ADDRESS)


@pytest.fixture
def expected_response():
    """Return mocked vacuum data."""
    return {
        'name': "THIS SUCKS",
        'version': '1.3.001',
    }


@mock.patch('ika.Vacuum', Vacuum)
def test_driver_cli_with_info(capsys):
    """Confirm the commandline interface works."""
    command_line([ADDRESS, '--type', 'vacuum'])
    captured = capsys.readouterr()
    assert 'pressure' in captured.out
    assert 'name' in captured.out


@mock.patch('ika.Vacuum', Vacuum)
def test_driver_cli(capsys):
    """Confirm the commandline interface works with --no-info."""
    command_line([ADDRESS, '--type', 'vacuum', '--no-info'])
    captured = capsys.readouterr()
    assert 'pressure' in captured.out
    assert 'name' not in captured.out


async def test_get_response(driver, expected_response):
    """Confirm that the driver returns correct values on get_info() calls."""
    assert expected_response == await driver.get_info()


async def test_readme_example(expected_response):
    """Confirm the readme example using an async context manager works."""
    async def get():
        async with Vacuum(ADDRESS) as device:
            await device.get()
            assert expected_response == await device.get_info()  # Get name
    await get()


async def test_start_stop():
    """Confirm that the vacuum motor can be controlled."""
    async def get():
        async with Vacuum(ADDRESS) as device:
            await device.control(on=True)
            response = await device.get()
            assert response['active'] is True

            await device.control(on=False)
            response = await device.get()
            assert response['active'] is False
    await get()


async def test_setpoint_roundtrip():
    """Confirm that the pressure setpoint can be updated."""
    async def get():
        async with Vacuum(ADDRESS) as device:
            await device.control(on=True)
            pressure_sp = randint(0, 760)
            await device.set(setpoint=pressure_sp)
            response = await device.get()
            assert pressure_sp == pytest.approx(response['pressure']['setpoint'], 2)
            await device.control(on=False)
    await get()


@pytest.mark.parametrize('mode', list(VacuumProtocol.Mode))
async def test_mode_roundtrip(mode):
    """Confirm that the various vacuum modes can be updated."""
    async def get():
        async with Vacuum(ADDRESS) as device:
            await device.set_mode(mode)
            response = await device.get()
            assert mode.name == response['mode']
    await get()


async def test_name_roundtrip():
    """Confirm that the device name can be updated."""
    async def get():
        async with Vacuum(ADDRESS) as device:
            await device.set_name('THIS SUCKS')
            name = (await device.get_info())['name']
            assert name == 'THIS SUCKS'
            await device.set_name('VACSTAR control')
            name = (await device.get_info())['name']
            assert name == 'VACSTAR control'
    await get()
