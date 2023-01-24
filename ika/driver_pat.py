"""IKA TCP adapter, built around open-source serial project.

Then, we hack into the repo to change the transport from serial to TCP.

See the base class implementation for documentation:
https://gitlab.com/heingroup/ika/-/blob/master/ika/magnetic_stirrer.py
"""
import asyncio
import atexit
import logging

from ika import magnetic_stirrer

logger = logging.getLogger()


class Transport():
    """Override transport to allow TCP."""

    def __init__(self, address):
        """Initialize the class."""
        self.ip, self.port = address.split(':')
        self.loop = asyncio.get_event_loop()
        self.lock = asyncio.Lock()
        self.connection = None
        self.connected = False
        self.timeouts = 0
        self.max_timeouts = 10

    def __enter__(self):
        """Provide entrance to context manager."""
        return self

    async def __aenter__(self):
        """Provide async entrance to context manager.

        Contrasting synchronous access, this will connect on
        initialization.
        """
        await self._connect()
        return self

    def __exit__(self, *args):
        """Provide exit to context manager."""
        self.close()

    def request(self, data, *args, **kwargs):
        """Override sync serial request method with matching args.

        This converts an async driver into a sync call to match the
        parent class architecture. A PR on the ika repo could
        propagate async and eliminate the need for this class.
        """
        return self.loop.run_until_complete(self._write_and_read(data))

    def write(self, data, *args, **kwargs):
        """Another method called by the current driver."""
        return self.request(data, *args, **kwargs)

    def disconnect(self):
        """Close the TCP connection."""
        if self.connected:
            self.connection['writer'].close()
        self.connected = False

    async def __aexit__(self, *args):
        """Provide async exit to context manager."""
        self.close()

    async def _write_and_read(self, command):
        """Write a command and reads a response from the bath.

        As lab equipment is commonly moved around, this has been
        expanded to handle recovering from disconnects. A lock is used
        to queue multiple requests.
        """
        async with self.lock:
            await self._handle_connection()
            response = await self._handle_communication(command)
        return response

    async def _connect(self):
        """Asynchronously open a TCP connection with the server."""
        self.connected = False
        reader, writer = await asyncio.open_connection(self.ip, self.port)
        self.connection = {'reader': reader, 'writer': writer}
        self.connected = True

    async def _handle_connection(self):
        """Automatically maintain TCP connection."""
        try:
            if not self.connected:
                await asyncio.wait_for(self._connect(), timeout=0.25)
            self.reconnecting = False
        except (asyncio.TimeoutError, OSError):
            if not self.reconnecting:
                logger.error(f'Connecting to {self.ip} timed out.')
            self.reconnecting = True

    async def _handle_communication(self, command):
        """Manage communication, including timeouts and logging."""
        try:
            self.connection['writer'].write(command)
            future = self.connection['reader'].readuntil(b'\r\n')
            line = await asyncio.wait_for(future, timeout=0.95)
            result = line.strip()
            self.timeouts = 0
        except (asyncio.TimeoutError, TypeError, OSError):
            self.timeouts += 1
            if self.timeouts == self.max_timeouts:
                logger.error(f'Reading from {self.address} timed out '
                             f'{self.timeouts} times.')
            result = None
        return result


class TcpOverheadStirrer(magnetic_stirrer.OverheadStirrer):
    """Extension to use this driver over TCP."""

    def connect(self):
        """Connect."""
        self.ser = Transport(address=self._device_port)
        atexit.register(self.disconnect)


# ms = TcpMagneticStirrer(device_port='192.168.0.7:23')
# print(ms.read_actual_hotplate_sensor_value())
# print(ms.read_stirring_speed_value())
# print(ms.read_viscosity_trend_value())
# print(ms.read_rated_set_safety_temperature_value())
# print(ms.read_device_name())  # Bug in parent driver
