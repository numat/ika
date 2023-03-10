"""Test the overhead stirrer driver responds with correct data."""
from unittest import mock

import pytest

from ika import command_line
from ika.mock import OverheadStirrer

ADDRESS = '192.168.10.12'
PORT = 26


@pytest.fixture
def driver():
    """Confirm the overhead stirrer correctly initializes."""
    return OverheadStirrer(ADDRESS, PORT)


@pytest.fixture
def expected_response():
    """Return mocked overhead stirrer data."""
    return {
        "name": "STIRR GO WHIRRR",
        "torque_limit": 60.0,
        "speed_limit": 2000.0,
    }


@mock.patch('ika.OverheadStirrer', OverheadStirrer)
def test_driver_cli_with_info(capsys):
    """Confirm the commandline interface works."""
    command_line([ADDRESS, '-p', str(PORT), '-t', 'overhead'])
    captured = capsys.readouterr()
    assert "torque" in captured.out
    assert "name" in captured.out


@mock.patch('ika.OverheadStirrer', OverheadStirrer)
def test_driver_cli(capsys):
    """Confirm the commandline interface works with --no-info."""
    command_line([ADDRESS, '-p', str(PORT), '-t', 'overhead', '--no-info'])
    captured = capsys.readouterr()
    assert "torque" in captured.out
    assert "name" not in captured.out


async def test_get_response(driver, expected_response):
    """Confirm that the driver returns correct values on get_info() calls."""
    assert expected_response == await driver.get_info()


async def test_readme_example(expected_response):
    """Confirm the readme example using an async context manager works."""
    async def get():
        async with OverheadStirrer(ADDRESS, PORT) as device:
            await device.get()       # Get speed, torque, temp
            assert expected_response == await device.get_info()  # Get name
    await get()
