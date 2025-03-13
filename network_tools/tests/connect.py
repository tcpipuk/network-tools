"""TCP connection testing module.

This module provides functionality to test TCP connectivity to multiple hosts and ports
concurrently, with configurable timeouts and concurrency limits.
"""

from __future__ import annotations

from asyncio import (
    Semaphore,
    gather as asyncio_gather,
    get_event_loop as asyncio_get_event_loop,
    open_connection as asyncio_open_connection,
    wait_for as asyncio_wait_for,
)
from dataclasses import dataclass
from socket import gaierror as socket_gaierror
from typing import Any

from network_tools.cli.console import complete_progress, create_progress, log, update_progress


@dataclass
class ConnectionResult:
    """Result of a TCP connection attempt."""

    host: str
    port: int
    success: bool
    time_ms: float
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Convert the result to a dictionary.

        Returns:
            Dictionary representation of the result
        """
        return {
            "host": self.host,
            "port": self.port,
            "success": self.success,
            "time_ms": self.time_ms,
            "error": self.error,
        }


async def try_connect(host: str, port: int, time_limit: float) -> ConnectionResult:
    """Attempt to connect to a single host and port.

    Args:
        host: The hostname or IP address to connect to
        port: The TCP port to connect to
        time_limit: Connection timeout in seconds

    Returns:
        ConnectionResult with connection details
    """
    start_time = asyncio_get_event_loop().time()

    try:
        # Create socket object
        _reader, writer = await asyncio_wait_for(asyncio_open_connection(host, port), timeout=time_limit)

        # If we get here, connection was successful
        elapsed_ms = (asyncio_get_event_loop().time() - start_time) * 1000

        # Properly close the connection
        writer.close()
        await writer.wait_closed()

        return ConnectionResult(host=host, port=port, success=True, time_ms=round(elapsed_ms, 2))

    except TimeoutError:
        elapsed_ms = (asyncio_get_event_loop().time() - start_time) * 1000
        return ConnectionResult(
            host=host, port=port, success=False, time_ms=round(elapsed_ms, 2), error="Connection timed out"
        )

    except socket_gaierror as e:
        elapsed_ms = (asyncio_get_event_loop().time() - start_time) * 1000
        return ConnectionResult(
            host=host,
            port=port,
            success=False,
            time_ms=round(elapsed_ms, 2),
            error=f"DNS resolution error: {e!s}",
        )

    except OSError as e:
        elapsed_ms = (asyncio_get_event_loop().time() - start_time) * 1000
        return ConnectionResult(
            host=host, port=port, success=False, time_ms=round(elapsed_ms, 2), error=str(e)
        )

    except Exception as e:
        elapsed_ms = (asyncio_get_event_loop().time() - start_time) * 1000
        return ConnectionResult(
            host=host,
            port=port,
            success=False,
            time_ms=round(elapsed_ms, 2),
            error=f"Unexpected error: {e!s}",
        )


async def test_connections(
    hosts: list[str], ports: list[int], time_limit: float, max_concurrency: int
) -> list[ConnectionResult]:
    """Test TCP connectivity to multiple hosts and ports concurrently.

    Args:
        hosts: List of hostnames or IP addresses to test
        ports: List of TCP ports to test on each host
        time_limit: Connection timeout in seconds (default: 10.0)
        max_concurrency: Maximum number of concurrent connections (default: 50)

    Returns:
        List of ConnectionResult objects for each connection attempt
    """
    # Create a semaphore to limit concurrency
    semaphore = Semaphore(max_concurrency)

    # Calculate total number of connection attempts
    total_tests = len(hosts) * len(ports)

    # Create a progress bar
    task_id = create_progress(f"Testing {total_tests} connections", total=total_tests)

    # Create tasks for each host/port combination
    async def connection_task(host: str, port: int) -> ConnectionResult:
        async with semaphore:
            log.debug(f"Testing connection to {host}:{port}")
            result = await try_connect(host, port, time_limit)

            # Update progress bar
            status = "✓" if result.success else "✗"
            update_progress(task_id, advance=1, description=f"Testing connections: {host}:{port} {status}")

            return result

    tasks = [connection_task(host, port) for host in hosts for port in ports]

    try:
        # Run all tasks concurrently and collect results
        results = await asyncio_gather(*tasks)
        # Complete the progress bar
        complete_progress(task_id, f"Completed {total_tests} connection tests")
    except Exception as e:
        log.error(f"Error testing connections: {e!s}")
        complete_progress(task_id, "Connection testing failed")
        raise
    else:
        return results
