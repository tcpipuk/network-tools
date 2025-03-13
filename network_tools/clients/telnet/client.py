"""Asynchronous Telnet client implementation module.

This module provides a modern asynchronous Telnet client implementation as a
replacement for the deprecated telnetlib standard library module.

The AsyncTelnetClient class offers a simple interface for connecting to Telnet
services, reading and writing data, and properly closing connections. It is built
using Python's asyncio framework for efficient I/O operations.
"""

from __future__ import annotations

import asyncio
import contextlib
from asyncio import StreamReader, StreamWriter, open_connection
from dataclasses import dataclass, field
from typing import Any, ClassVar, Self

from network_tools.cli import log

from .negotiate import TelnetNegotiator
from .types import IAC_BYTE


@dataclass(slots=True)
class AsyncTelnetClient:
    """Modern async Telnet client as replacement for deprecated telnetlib.

    This class implements the async context manager protocol for easy use in
    async with statements.

    Examples:
        Basic usage with context manager:

        ```python
        async with AsyncTelnetClient.connect_to("device.example.com", 23) as client:
            await client.send_command("show version")
            response = await client.read_until_prompt()
            print(response.decode())
        ```

        Manual connection management:

        ```python
        client = AsyncTelnetClient("device.example.com", 23)
        try:
            await client.connect()
            await client.send_command("show version")
            response = await client.read_until_prompt()
        finally:
            await client.close()
        ```
    """

    host: str
    port: int
    timeout: float = field(default=5.0)
    reader: StreamReader | None = field(default=None)
    writer: StreamWriter | None = field(default=None)

    # Telnet options
    terminal_type: str = field(default="VT100")
    window_width: int = field(default=132)  # Wide terminal to avoid pagination
    window_height: int = field(default=100)  # Tall terminal to avoid pagination

    # Negotiation handler
    negotiator: TelnetNegotiator = field(init=False)

    # Common prompt patterns for telnet devices - users can override
    DEFAULT_PROMPT: ClassVar[bytes] = b"[>#$] $"

    def __post_init__(self) -> None:
        """Initialise negotiator with our settings."""
        self.negotiator = TelnetNegotiator(
            terminal_type=self.terminal_type,
            window_width=self.window_width,
            window_height=self.window_height,
        )

    @classmethod
    async def connect_to(cls, host: str, port: int, time_limit: float = 5.0, **kwargs: Any) -> Self:
        """Create and connect to a telnet server in one step.

        This factory method creates a client instance and establishes a connection
        in a single operation.

        Args:
            host: The hostname or IP address of the telnet server
            port: The port number of the telnet server
            time_limit: Connection timeout in seconds
            **kwargs: Additional parameters to pass to the AsyncTelnetClient constructor

        Returns:
            A connected AsyncTelnetClient instance

        Raises:
            ConnectionError: If the connection attempt fails
        """
        client = cls(host=host, port=port, timeout=time_limit, **kwargs)
        if not await client.connect():
            msg = f"Failed to connect to {host}:{port}"
            raise ConnectionError(msg)
        return client

    async def __aenter__(self) -> Self:
        """Enter the async context manager.

        This method is called when entering an async with statement.
        It establishes the telnet connection if not already connected.

        Returns:
            The connected client instance

        Raises:
            ConnectionError: If the connection attempt fails
        """
        if not self.is_connected and not await self.connect():
            msg = f"Failed to connect to {self.host}:{self.port}"
            raise ConnectionError(msg)
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Exit the async context manager, closing the connection.

        This method is called when exiting an async with statement.
        It ensures the telnet connection is properly closed.
        """
        await self.close()

    @property
    def is_connected(self) -> bool:
        """Check if the client is currently connected."""
        return self.reader is not None and self.writer is not None

    async def connect(self) -> bool:
        """Establish telnet connection.

        This method opens a connection to the telnet server and performs
        the initial telnet protocol negotiation.

        Returns:
            True if connection was successful, False otherwise.
        """
        if self.is_connected:
            return True

        try:
            async with asyncio.timeout(self.timeout):
                log.info("Connecting with telnet to %s:%d", self.host, self.port)
                self.reader, self.writer = await open_connection(self.host, self.port)

                # Send initial negotiation options
                initial_negotiation = self.negotiator.get_initial_negotiation()
                self.writer.write(initial_negotiation)
                await self.writer.drain()

                # Handle any immediate negotiation responses
                await self._complete_negotiation()
        except (TimeoutError, ConnectionRefusedError, OSError):
            log.exception("Telnet connection error")
            return False
        else:
            log.debug("Connected with telnet to %s:%d", self.host, self.port)
            return True

    async def _complete_negotiation(self) -> None:
        """Handle telnet protocol negotiation after connection."""
        if not self.reader or not self.writer:
            return

        # Give the server a moment to send initial negotiations
        await asyncio.sleep(0.1)

        # Try to read initial negotiation data
        try:
            data = await asyncio.wait_for(self.reader.read(1024), timeout=1.0)
            if data:
                log.debug("Received %d bytes during initial negotiation", len(data))
                self._process_negotiation(data)
        except TimeoutError:
            # No initial negotiation data, that's okay
            pass

    def _process_negotiation(self, data: bytes) -> bytes:
        """Process any telnet negotiation commands in the data.

        Args:
            data: Raw data that may contain IAC sequences

        Returns:
            Processed data with IAC sequences removed
        """
        if not data:
            return b""

        processed_data, responses = self.negotiator.handle_command(data)

        # Send responses in single write operation if any exist
        if responses and self.writer:
            # Combine all responses into single bytes object
            combined_response = b"".join(responses)
            self.writer.write(combined_response)
            self.writer.drain()

        return processed_data

    async def read(self, size: int = 1024, time_limit: float | None = None) -> bytes:
        """Read data from telnet connection.

        Args:
            size: Maximum number of bytes to read
            time_limit: Maximum time to wait for data, defaults to self.timeout

        Returns:
            The data read from the telnet connection or empty bytes on timeout.
        """
        if not self.reader:
            return b""
        if time_limit is None:
            time_limit = self.timeout

        try:
            raw_data = await asyncio.wait_for(self.reader.read(size), timeout=time_limit)

            # Process any telnet commands
            return self._process_negotiation(raw_data)
        except TimeoutError:
            return b""

    async def read_until(self, expected: bytes, time_limit: float | None = None) -> bytes:
        """Read data until a specific pattern is found.

        Returns:
            All data read including the expected pattern

        Raises:
            TimeoutError: If the pattern is not found within the timeout
        """
        if not self.reader:
            return b""

        if time_limit is None:
            time_limit = self.timeout

        # Pre-allocate buffer with reasonable size to reduce reallocations
        buffer = bytearray(4096)
        view = memoryview(buffer)
        pos = 0

        start_time = asyncio.get_event_loop().time()
        end_time = start_time + time_limit

        while asyncio.get_event_loop().time() < end_time:
            remaining = end_time - asyncio.get_event_loop().time()
            chunk = await self.read(timeout=min(1.0, remaining))

            if not chunk:
                await asyncio.sleep(0.01)
                continue

            # Ensure buffer has enough space
            if pos + len(chunk) > len(buffer):
                # Double buffer size when needed
                new_buffer = bytearray(len(buffer) * 2)
                new_buffer[:pos] = buffer[:pos]
                buffer = new_buffer
                view = memoryview(buffer)

            view[pos : pos + len(chunk)] = chunk
            pos += len(chunk)

            # Check if pattern exists in the new data plus a small overlap
            if expected in buffer[max(0, pos - len(expected) - len(chunk)) : pos]:
                return bytes(buffer[:pos])

        msg = f"Timeout waiting for {expected!r}"
        raise TimeoutError(msg)

    async def read_until_prompt(self, prompt: bytes | None = None, time_limit: float | None = None) -> bytes:
        """Read data until a command prompt is detected.

        Args:
            prompt: The prompt pattern to look for, defaults to DEFAULT_PROMPT
            time_limit: Maximum time to wait for the prompt

        Returns:
            All data read including the prompt
        """
        if prompt is None:
            prompt = self.DEFAULT_PROMPT

        return await self.read_until(prompt, time_limit)

    async def write(self, data: bytes) -> None:
        """Write data to telnet connection with optimised IAC escaping."""
        if not self.writer:
            return

        # Fast path for common case - no IAC bytes
        if IAC_BYTE not in data:
            self.writer.write(data)
            await self.writer.drain()
            return

        # Pre-calculate exact size needed
        iac_count = data.count(IAC_BYTE)
        escaped_data = bytearray(len(data) + iac_count)

        # Use memoryview for more efficient buffer manipulation
        view = memoryview(escaped_data)
        i = j = 0

        # Single-pass escape using memoryview
        while i < len(data):
            b = data[i]
            view[j] = b
            if b == IAC_BYTE:
                j += 1
                view[j] = IAC_BYTE
            i += 1
            j += 1

        self.writer.write(escaped_data)
        await self.writer.drain()

    async def send_command(self, command: str, newline: str = "\r\n") -> None:
        """Send a command to the telnet device.

        Args:
            command: The command string to send
            newline: The newline character(s) to append
        """
        await self.write(command.encode() + newline.encode())

    async def interact(self) -> None:
        """Start an interactive session with the telnet device.

        This method creates a two-way communication channel between
        the terminal and the telnet device. It's similar to what you'd
        experience with a direct telnet connection.

        The session continues until Ctrl+C is pressed.
        """
        if not self.is_connected and not await self.connect():
            return

        log.info(f"Connected to {self.host}:{self.port}")
        log.info("Press Ctrl+C to exit")

        # Set up a task to read from the telnet connection
        read_task = asyncio.create_task(self._interactive_reader())

        try:
            # Read from stdin and send to telnet
            while True:
                line = await asyncio.get_event_loop().run_in_executor(None, input, "")
                await self.send_command(line)
        except (KeyboardInterrupt, EOFError):
            log.info("\nExiting interactive session")
        finally:
            read_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await read_task

    async def _interactive_reader(self) -> None:
        """Background task that reads from telnet with adaptive sleep."""
        idle_count = 0
        try:
            while True:
                data = await self.read(timeout=0.1)
                if data:
                    log.info(data.decode(errors="replace"), end="", flush=True)
                    idle_count = 0
                else:
                    # Adaptive sleep - increase sleep time when idle
                    idle_count = min(idle_count + 1, 10)
                    await asyncio.sleep(0.05 * idle_count)
        except Exception:
            log.exception("Error in telnet reader")

    async def close(self) -> None:
        """Close telnet connection."""
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                log.exception("Error closing telnet connection")
            finally:
                self.writer = None
                self.reader = None
                log.debug("Closed telnet connection to %s:%d", self.host, self.port)
