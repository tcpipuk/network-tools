"""Asynchronous Telnet client implementation module.

This module provides a modern asynchronous Telnet client implementation as a
replacement for the deprecated telnetlib standard library module.

The AsyncTelnetClient class offers a simple interface for connecting to Telnet
services, reading and writing data, and properly closing connections. It is built
using Python's asyncio framework for efficient I/O operations.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from network_tools.cli import log


@dataclass(slots=True)
class AsyncTelnetClient:
    """Simple async Telnet client as replacement for deprecated telnetlib."""

    host: str
    port: int
    timeout: float = field(default=5.0)
    reader: asyncio.StreamReader | None = field(default=None)
    writer: asyncio.StreamWriter | None = field(default=None)

    async def connect(self) -> bool:
        """Establish telnet connection.

        Returns:
            True if connection was successful, False otherwise.
        """
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port, timeout=self.timeout
            )
        except (TimeoutError, ConnectionRefusedError, OSError):
            log.exception("Telnet connection error")
            return False
        else:
            return True

    async def read(self, time_limit: float | None = None) -> bytes:
        """Read data from telnet connection.

        Returns:
            The data read from the telnet connection.
        """
        if not self.reader:
            return b""
        if time_limit is None:
            time_limit = self.timeout

        try:
            return await asyncio.wait_for(self.reader.read(1024), timeout=time_limit)
        except TimeoutError:
            return b""

    async def write(self, data: bytes) -> None:
        """Write data to telnet connection."""
        if not self.writer:
            return

        self.writer.write(data)
        await self.writer.drain()

    async def close(self) -> None:
        """Close telnet connection."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self.writer = None
            self.reader = None
