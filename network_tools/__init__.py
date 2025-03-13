"""Network protocol detection and interaction package.

This package provides tools for detecting and interacting with network management
protocols on remote devices. It includes automatic protocol detection capabilities
for SSH, HTTP(S), Telnet, and FTP, along with appropriate client interfaces for
each protocol.

The package is designed for network automation tasks, diagnostics, and programmatic
interaction with network devices. It uses modern asynchronous Python patterns for
efficient network operations.
"""

from __future__ import annotations

from importlib.metadata import version

from .cli import (
    complete_progress,
    console,
    create_progress,
    log,
    parse_args,
    update_progress,
)
from .clients.telnet import AsyncTelnetClient

__all__ = [
    "AsyncTelnetClient",
    "complete_progress",
    "console",
    "create_progress",
    "log",
    "parse_args",
    "update_progress",
]

__version__ = version(__name__)
