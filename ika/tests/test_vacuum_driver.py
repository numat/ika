"""Test the vacuum driver responds with correct data."""
from unittest import mock

import pytest

from ika import command_line
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
        "name": "THIS SUCKS",
        "pressure": 0.01,
    }


@mock.patch('ika.Vacuum', Vacuum)
def test_driver_cli_with_info(capsys):
    """Confirm the commandline interface works."""
    command_line([ADDRESS])
    captured = capsys.readouterr()
    assert "pressure" in captured.out
    assert "name" in captured.out


@mock.patch('ika.Vacuum', Vacuum)
def test_driver_cli(capsys):
    """Confirm the commandline interface works with --no-info."""
    command_line([ADDRESS])
    captured = capsys.readouterr()
    assert "pressure" in captured.out
    assert "name" not in captured.out


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
