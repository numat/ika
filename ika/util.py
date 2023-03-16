"""Base functionality for async TCP communication.

Distributed under the GNU General Public License v3
Copyright (C) 2022 NuMat Technologies
"""
try:
    import asyncio
except ImportError:
    raise ImportError("TCP connections require python >=3.5.")
import logging

logger = logging.getLogger('ika')


class TcpClient():
    """A generic reconnecting asyncio TCP client.

    This base functionality can be used by any industrial control device
    communicating over TCP.
    """

    def __init__(self, address, eol='\r\n'):
        """Set connection parameters.

        Connection is handled asynchronously, either using `async with` or
        behind the scenes on the first `await` call.
        """
        try:
            self.address, port = address.split(':')
        except ValueError:
            raise ValueError('address must be hostname:port')
        self.port = int(port)
        self.eol = eol.encode()
        self.open = False
        self.reconnecting = False
        self.timeouts = 0
        self.max_timeouts = 10
        self.connection = {}
        self.lock = None

    async def __aenter__(self):
        """Provide async entrance to context manager.

        Contrasting synchronous access, this will connect on initialization.
        """
        await self._handle_connection()
        return self

    def __exit__(self, *args):
        """Provide exit to context manager."""
        self.close()

    async def __aexit__(self, *args):
        """Provide async exit to context manager."""
        self.close()

    def close(self):
        """Close the TCP connection."""
        if self.open:
            self.connection['writer'].close()
        self.open = False

    async def _connect(self):
        """Asynchronously open a TCP connection with the server."""
        self.close()
        reader, writer = await asyncio.open_connection(self.address, self.port)
        self.connection = {'reader': reader, 'writer': writer}
        self.open = True

    async def _write_and_read(self, command):
        """Write a command and read a response.

        As industrial devices are commonly unplugged, this has been expanded to
        handle recovering from disconnects.  A lock is used to queue multiple requests.
        """
        if not self.lock:
            # lock initialized here so the loop exists.
            self.lock = asyncio.Lock()
        async with self.lock:  # lock releases on CancelledError
            await self._handle_connection()
            if self.open:
                try:
                    response = await self._handle_communication(command)
                    if response is None:
                        return None
                    elif 'IN_NAME' in command or 'TYPE' in command:
                        return response
                    elif 'IN_PV_4' in response:
                        raise ConnectionError(
                            'Hotplate configured to communciate with a Eurostar overhead stirrer. '
                            'This must be turned off in the hotplate settings.'
                        )
                    elif command[-1] != response[-1]:
                        logger.error(f'Invalid response {response} to command {command}.')
                        await self._clear()
                        return None
                    elif 'STATUS_2' in command:
                        raise NotImplementedError  # not sure how to interpret response of '-90 2'
                    elif 'STATUS_4' in command:  # overhead stirrer
                        return response[0] == '1'
                    elif 'STATUS' in command:  # hotplate
                        return response[0:2] == '11'  # undocumented, 11 = active, 12 = inactive
                    return float(response[:-2])  # strip response command readback
                except asyncio.exceptions.IncompleteReadError:
                    logger.error('IncompleteReadError.  Are there multiple connections?')
                    return None
            else:
                return None

    async def _write(self, command):
        """Write a command and do not expect a response.

        As industrial devices are commonly unplugged, this has been expanded to
        handle recovering from disconnects.  A lock is used to queue multiple requests.
        """
        if not self.lock:
            # lock initialized here so the loop exists.
            self.lock = asyncio.Lock()
        async with self.lock:  # lock releases on CancelledError
            await self._handle_connection()
            await self._handle_communication(command)

    async def _clear(self):
        """Clear the reader stream when it has been corrupted from multiple connections."""
        logger.warning("Multiple connections detected; clearing reader stream.")
        try:
            junk = await asyncio.wait_for(self.connection['reader'].read(100), timeout=0.5)
            logger.warning(junk)
        except TimeoutError:
            pass

    async def _handle_connection(self):
        """Automatically maintain TCP connection."""
        try:
            if not self.open:
                await asyncio.wait_for(self._connect(), timeout=0.5)
            self.reconnecting = False
        except (asyncio.TimeoutError, OSError):
            if not self.reconnecting:
                logger.error(f'Connecting to {self.address} timed out.')
            self.reconnecting = True

    async def _handle_communication(self, command):
        """Manage communication, including timeouts and logging."""
        try:
            self.connection['writer'].write(command.encode() + self.eol)
            future = self.connection['reader'].readuntil(self.eol)
            line = await asyncio.wait_for(future, timeout=0.5)
            result = line.decode().strip()
            self.timeouts = 0
            return result
        except (asyncio.TimeoutError, TypeError, OSError):
            self.timeouts += 1
            if self.timeouts == self.max_timeouts:
                logger.error(f'Reading from {self.address} timed out '
                             f'{self.timeouts} times.')
                self.close()
            return None
