"""Network device protocol scanning and interaction example module.

This module demonstrates how to use the AsyncProtocolDetector to scan network devices,
identify running services, and interact with them using appropriate clients.

It provides a practical implementation that scans a device on multiple ports,
logs the results, and shows how to interact with detected services like SSH, HTTP/HTTPS,
and Telnet.

Example:
    To scan a network device:

    ```python
    from asyncio import run
    from network_tools.example import scan_device

    results = run(scan_device("192.168.1.1", [22, 80, 443]))
    print(results)
    ```
"""

from __future__ import annotations

from asyncio import run as asyncio_run
from typing import Any, TypeVar

from .cli import logger
from .detector import AsyncProtocolDetector
from .types import DetectionResult

# Define generic client type for type hints
ClientT = TypeVar("ClientT")


async def _handle_ssh_client(client: Any) -> None:
    """Handle SSH protocol client interaction."""
    async with client.start_session() as session:
        result = await session.run("show version", check=False)
        logger.info("SSH command result: %s", result.stdout)
    client.close()


async def _handle_http_client(client: Any) -> None:
    """Handle HTTP/HTTPS protocol client interaction."""
    async with client.get("/") as response:
        logger.info("HTTP status: %s", response.status)
    await client.close()


async def _handle_telnet_client(client: Any) -> None:
    """Handle Telnet protocol client interaction."""
    data = await client.read(timeout=1.0)
    logger.info("Telnet received: %s", data[:100])
    await client.close()


async def _handle_protocol_client(client: Any | None, result: DetectionResult) -> None:
    """Handle client interaction based on detected protocol."""
    if not client:
        return

    protocol = result.protocol
    if protocol == "SSH":
        await _handle_ssh_client(client)
    elif protocol in {"HTTP", "HTTPS"}:
        await _handle_http_client(client)
    elif protocol == "TELNET":
        await _handle_telnet_client(client)


async def _scan_single_port(detector: AsyncProtocolDetector, host: str, port: int) -> DetectionResult:
    """Scan a single port and handle the result.

    Returns:
        DetectionResult with protocol information.
    """
    logger.info("Scanning %s:%s", host, port)
    try:
        # Detect protocol
        result = await detector.detect(host, port)

        # If protocol detected, try to get client
        if result.protocol not in {"UNKNOWN", "ERROR"}:
            logger.info("Protocol %s detected on %s:%s", result.protocol, host, port)
            client = await detector.get_client(result, host, port)
            await _handle_protocol_client(client, result, host, port)
        else:
            logger.info("No protocol detected on %s:%s", host, port)
            return result
    except Exception as e:
        logger.exception("Error scanning %s:%s: %s", host, port)
        return DetectionResult(protocol="ERROR", extra_info={"error": str(e)})


async def scan_device(host: str, ports: list[int]) -> dict[int, DetectionResult]:
    """Scan a device on specified ports and identify protocols.

    Returns:
        A dictionary of port to DetectionResult.
    """
    detector = AsyncProtocolDetector()
    results = {}

    for port in ports:
        results[port] = await _scan_single_port(detector, host, port)

    return results


# Example usage
async def main() -> None:
    """Example usage of the AsyncProtocolDetector."""
    # Sample network device
    host = "192.168.1.1"
    ports = [22, 23, 80, 443, 8080]

    results = await scan_device(host, ports)

    logger.info("Scan Results:")
    for port, result in results.items():
        logger.info("Port %s: %s", port, result.protocol)
        if result.extra_info:
            logger.info("  Info: %s", result.extra_info)


if __name__ == "__main__":
    asyncio_run(main())
