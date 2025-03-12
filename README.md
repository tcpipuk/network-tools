# Network Tools

A set of async network tools for Python that help you identify protocols and interact with network devices.

## What it does

This package helps you:

- detect what protocols are running on network devices (like SSH, HTTP, Telnet and FTP)
- connect to network devices using these protocols
- display progress and logs in your terminal

It's built with modern async Python to make your network operations more efficient.

## Core components

- `AsyncProtocolDetector`: identifies protocols on network devices
- `AsyncTelnetClient`: modern replacement for the deprecated telnetlib
- `DetectionResult`: stores protocol detection results
- `Console`: shows logs and progress bars using Rich

## How to install

1. Clone the repository:

   ```bash
   git clone https://github.com/tcpipuk/network-tools.git
   cd network-tools
   ```

2. Install `uv` (if not already installed):

   ```bash
   # On macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   Or update your existing install:

   ```bash
   uv self update
   ```

3. Install dependencies and activate the Python environment:

   ```bash
   uv sync
   source .venv/bin/activate  # On Linux/macOS
   # Or on Windows:
   # .venv\Scripts\activate
   ```

> **Note:** If/when this package is published to PyPI, you'll be able to install it with:
> `pip install network-tools`

## How to use it

```python
from asyncio import run
from network_tools import AsyncProtocolDetector
from network_tools.console import log

async def main():
    # Create detector
    detector = AsyncProtocolDetector()

    # Detect protocol on a network device
    host = "192.168.1.1"
    port = 22

    log.info("Scanning %s:%s", host, port)
    result = await detector.detect(host, port)

    # Handle detected protocol
    if result.protocol != "UNKNOWN":
        log.info("Detected protocol: %s", result.protocol)

        # Get appropriate client
        client = await detector.get_client(result, host, port)

        # Use the client based on protocol type
        if result.protocol == "SSH":
            async with client.start_session() as session:
                output = await session.run("show version")
                log.info("Command output: %s", output.stdout)

        # Close client connection
        client.close()
    else:
        log.info("No protocol detected on %s:%s", host, port)

if __name__ == "__main__":
    run(main())
```

See `network_tools/example.py` for a more detailed example.

## Licence

This project is licensed under the GNU General Public License v3.0 (GPLv3).
See the [LICENCE](LICENCE) file for details.
