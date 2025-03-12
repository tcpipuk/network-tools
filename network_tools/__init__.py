"""Network protocol detection and interaction package.

This package provides tools for detecting and interacting with network management protocols
on remote devices. It includes automatic protocol detection capabilities for SSH, HTTP(S),
Telnet, and FTP, along with appropriate client interfaces for each protocol.

The package is designed for network automation tasks, diagnostics, and programmatic
interaction with network devices. It uses modern asynchronous Python patterns for
efficient network operations.

Core components:
- AsyncProtocolDetector: Auto-detects protocols running on network devices
- AsyncTelnetClient: Modern async replacement for the deprecated telnetlib
- DetectionResult: Structured container for protocol detection results
- Console: Rich-based console with integrated logging and progress bars

See example.py for a thorough usage example.
"""

from __future__ import annotations

from .cli import (
    complete_progress,
    console,
    create_progress,
    logger,
    update_progress,
)
from .detector import AsyncProtocolDetector
from .telnet import AsyncTelnetClient
from .types import DetectionResult

__all__ = [
    "AsyncProtocolDetector",
    "AsyncTelnetClient",
    "DetectionResult",
    "complete_progress",
    "console",
    "create_progress",
    "logger",
    "update_progress",
]
