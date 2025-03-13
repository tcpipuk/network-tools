# Network Tools

A set of async network tools for Python that help you identify protocols and interact with network devices.

## What it does

This package helps you:

- detect what protocols are running on network devices (like SSH, HTTP, Telnet and FTP)
- connect to network devices using these protocols
- display progress and logs in your terminal

It's built with modern async Python to make your network operations more efficient.

## Core components

- `AsyncTelnetClient`: modern replacement for the deprecated telnetlib
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

   # On macOS and Linux
   source .venv/bin/activate

   # On Windows:
   .venv\Scripts\activate
   ```

## How to use it

After installation, you can run the tool from the command line when this Python environment is active:

```bash
network-tools --help
```

This will display the available options:

```plaintext
usage: network_tools [-h] [-V] [-v] [-c <50>] -m banner|connect|fingerprint|probe|scan
                     [-p <auto>|http|https|ssh|telnet] [-t <10>] -i INPUT
                     [-if <csv>|json] [-o OUTPUT] [-of csv|json|<plain>]

Network tools: detect, analyse and interact with network services.

This tool helps you identify protocols running on network devices,
test connectivity, scan for services, and retrieve information
from compatible network endpoints. Use different modes to perform
specific operations, with customisable input and output options.

options:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -v, --verbose         show extra logging during run

operations:
  -c, --concurrency <50>
  -m, --mode banner|connect|fingerprint|probe|scan
  -p, --protocol <auto>|http|https|ssh|telnet
  -t, --timeout <10>

files:
  -i, --input INPUT     Input file path
  -if, --input-format <csv>|json
  -o, --output OUTPUT   Output file path (default: stdout)
  -of, --output-format csv|json|<plain>
```

### Example usage

Probe a list of devices for open TCP ports:

```bash
network-tools -m connect -p 22 2222 -i hosts.json -if json
```

## Licence

This project is licensed under the GNU General Public License v3.0 (GPLv3).
See the [LICENCE](LICENCE) file for details.
