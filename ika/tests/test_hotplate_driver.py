"""Test the hotplate driver responds with correct data."""
from unittest import mock

import pytest

from ika import command_line
from ika.mock import Hotplate


@pytest.fixture
def driver():
    """Confirm the hotplate correctly initializes."""
    return Hotplate('fakeip')


@pytest.fixture
def expected_response():
    """Return mocked hotplate data."""
    return {
        "name": "SPINNY HOT THING",
        "temp_limit": 150.0,
    }


@mock.patch('ika.Hotplate', Hotplate)
def test_driver_cli_with_info(capsys):
    """Confirm the commandline interface works."""
    command_line(['fakeip', '--type', 'hotplate'])
    captured = capsys.readouterr()
    assert "temp_limit" in captured.out
    assert "name" in captured.out


@mock.patch('ika.Hotplate', Hotplate)
def test_driver_cli(capsys):
    """Confirm the commandline interface works with --no-info."""
    command_line(['fakeip', '--type', 'hotplate', '--no-info'])
    captured = capsys.readouterr()
    assert "temp" in captured.out
    assert "name" not in captured.out


async def test_get_response(driver, expected_response):
    """Confirm that the driver returns correct values on get_info() calls."""
    assert expected_response == await driver.get_info()


async def test_readme_example(expected_response):
    """Confirm the readme example using an async context manager works."""
    async def get():
        async with Hotplate('hotplate-ip.local') as device:
            await device.get()       # Get speed, torque, temp
            assert expected_response == await device.get_info()  # Get name
    await get()
