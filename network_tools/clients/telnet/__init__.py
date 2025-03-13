"""Telnet Client Module.

This module provides a modern, asyncio-based implementation of the Telnet protocol
for communicating with legacy devices that still use telnet.

Example usage:
    ```python
    import asyncio
    from network_tools.clients.telnet import AsyncTelnetClient

    async def main():
        async with AsyncTelnetClient.connect_to('device.example.com', 23) as client:
            await client.send_command('show version')
            response = await client.read_until_prompt()
            print(response.decode())

    asyncio.run(main())
    ```
"""

from __future__ import annotations

from .client import AsyncTelnetClient

__all__ = ["AsyncTelnetClient"]
