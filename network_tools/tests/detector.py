"""Protocol detection and client creation module for network management interfaces.

This module provides functionality to automatically detect the protocol being used on a
network device's management interface. It supports detection of common protocols such as
SSH, HTTP(S), Telnet, and FTP.

The main class, AsyncProtocolDetector, attempts to identify protocols through both passive
and active detection methods, and can provide appropriate clients for interacting with
detected services.

Example:
    detector = AsyncProtocolDetector()
    result = await detector.detect("192.168.1.1", 22)
    if result.protocol == "SSH":
        client = await detector.get_client(result, "192.168.1.1", 22)
"""

from __future__ import annotations

import asyncio
import ssl
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from aiohttp import ClientSession
from asyncssh import Error as SSHError, connect as ssh_connect

from network_tools.cli import log
from network_tools.clients.telnet import AsyncTelnetClient
from network_tools.types import DetectionResult

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from asyncssh import SSHClientConnection

# Telnet protocol constants
IAC_BYTE = 0xFF  # Interpret As Command byte


@dataclass(slots=True)
class AsyncProtocolDetector:
    """Asynchronous protocol detector for network management interfaces.

    Detects common management protocols and prepares connections for handoff
    to appropriate client libraries.
    """

    timeout: float = field(default=3.0)
    _current_reader: asyncio.StreamReader | None = field(default=None)
    _current_writer: asyncio.StreamWriter | None = field(default=None)

    async def detect(self, host: str, port: int) -> DetectionResult:
        """Connect to host:port and detect protocol.

        Returns:
            DetectionResult with protocol information.
        """
        try:
            # First try passive detection
            result = await self._passive_detection(host, port)
            if result.protocol != "UNKNOWN":
                return result

            # If passive detection fails, try active probing
            return await self._active_detection(host, port)
        except Exception as e:
            log.exception("Detection error on %s:%s", host, port)
            # Close connection if open
            await self._close_connection()
            return DetectionResult(protocol="ERROR", extra_info={"error": str(e)})

    async def _passive_detection(self, host: str, port: int) -> DetectionResult:
        """Detect protocols that send data immediately on connection.

        Returns:
            DetectionResult with protocol information.
        """
        reader, writer = await asyncio.open_connection(host, port)
        self._current_reader, self._current_writer = reader, writer

        # Wait for initial data with timeout
        try:
            initial_data = await asyncio.wait_for(reader.read(1024), timeout=1.0)

            # Check for SSH
            if initial_data.startswith(b"SSH-"):
                ssh_version = initial_data.decode("ascii", errors="ignore").strip()
                return DetectionResult(
                    protocol="SSH", banner=initial_data, extra_info={"version": ssh_version}
                )

            # Check for FTP
            if initial_data.startswith(b"220 "):
                return DetectionResult(protocol="FTP", banner=initial_data)

            # Check for Telnet option negotiation
            if (
                initial_data
                and all(b in range(256) for b in initial_data)
                and any(b == IAC_BYTE for b in initial_data)
            ):
                return DetectionResult(protocol="TELNET", banner=initial_data)
            # Unknown protocol that sends data
            return DetectionResult(protocol="UNKNOWN_BANNER", banner=initial_data)
        except TimeoutError:
            # No immediate data - silent protocol
            return DetectionResult(protocol="UNKNOWN")

    async def _active_detection(self, host: str, port: int) -> DetectionResult:
        """Probe protocols that don't send data immediately.

        Returns:
            DetectionResult with protocol information.
        """
        # If we already have an open connection, close it
        await self._close_connection()
        # Try HTTPS detection
        if await self._is_tls(host, port):
            return DetectionResult(protocol="HTTPS")
        # Try HTTP detection
        result = await self._is_http(host, port)
        if result.protocol == "HTTP":
            return result
        # Default to unknown
        return DetectionResult(protocol="UNKNOWN")

    async def _is_tls(self, host: str, port: int) -> bool:
        """Check if the service speaks TLS.

        Returns:
            True if the service speaks TLS, False otherwise.
        """
        # Create SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            reader, writer = await asyncio.open_connection(host, port, ssl=ssl_context, server_hostname=host)
            self._current_reader, self._current_writer = reader, writer
        except (ssl.SSLError, ConnectionRefusedError, OSError):
            return False
        else:
            return True

    async def _is_http(self, host: str, port: int) -> DetectionResult:
        """Check if the service speaks HTTP.

        Returns:
            DetectionResult with protocol information.
        """
        reader, writer = await asyncio.open_connection(host, port)
        self._current_reader, self._current_writer = reader, writer

        try:
            # Send HTTP HEAD request
            writer.write(b"HEAD / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
            await writer.drain()

            # Wait for response
            response = await asyncio.wait_for(reader.read(1024), timeout=2.0)

            if b"HTTP/" in response:
                version = "1.1"
                if b"HTTP/1.0" in response:
                    version = "1.0"
                elif b"HTTP/2" in response:
                    version = "2"

                return DetectionResult(protocol="HTTP", banner=response, extra_info={"version": version})
            return DetectionResult(protocol="UNKNOWN")
        except (TimeoutError, ConnectionRefusedError, OSError):
            return DetectionResult(protocol="UNKNOWN")

    async def _close_connection(self) -> None:
        """Close current connection if open."""
        if self._current_writer:
            try:
                self._current_writer.close()
                await self._current_writer.wait_closed()
            except Exception:
                pass
            self._current_writer = None
            self._current_reader = None

    async def get_client(
        self, detection_result: DetectionResult, host: str, port: int
    ) -> AsyncGenerator[Any]:
        """Return appropriate client for the detected protocol.

        Reuses the existing connection if possible.

        Yields:
            Appropriate client for the detected protocol, or None if the protocol is not supported.
        """
        match detection_result.protocol:
            case "HTTP":
                yield await self._get_http_client(host, port, False)
            case "HTTPS":
                yield await self._get_http_client(host, port, True)
            case "SSH":
                yield await self._get_ssh_client(host, port)
            case "TELNET":
                yield await self._get_telnet_client(host, port)
            case _:
                log.error("Unsupported protocol: %s", detection_result.protocol)

    async def _get_ssh_client(self, host: str, port: int) -> AsyncGenerator[SSHClientConnection]:
        """Get SSH client, closing the detection connection first.

        Yields:
            SSH client, or None if the connection fails.

        Raises:
            asyncssh.Error: If the connection fails.
            OSError: If the connection fails.
        """
        await self._close_connection()
        # Create an asyncssh client
        try:
            client = await ssh_connect(host=host, port=port, known_hosts=None)
            yield client
            # Close the client if it's not already closed
            if not client.is_closed():
                await client.close()
        except (SSHError, OSError):
            log.exception("SSH connection error")
            raise

    async def _get_http_client(self, host: str, port: int, is_https: bool) -> AsyncGenerator[ClientSession]:
        """Get HTTP/HTTPS client session.

        Yields:
            HTTP/HTTPS client session, or None if the connection fails.
        """
        # We need to close our detection connection as aiohttp will create its own
        await self._close_connection()

        # Create scheme URL
        scheme = "https" if is_https else "http"
        base_url = f"{scheme}://{host}:{port}"

        # Create aiohttp session
        client = ClientSession(base_url=base_url)
        yield client
        await client.close()

    async def _get_telnet_client(self, host: str, port: int) -> AsyncGenerator[AsyncTelnetClient]:
        """Get telnet client, potentially reusing the connection.

        Yields:
            Telnet client, or None if the connection fails.
        """
        # Close existing connection as we'll create a new one for the client
        await self._close_connection()

        # Create a simple async telnet client
        # Since telnetlib is deprecated, we implement a basic one
        client = AsyncTelnetClient(host, port)

        await client.connect()
        yield client
        await client.close()
