"""Type definitions module for network protocol detection.

This module contains dataclass definitions and type hints used throughout the
network tools package. It provides standardised data structures for representing
protocol detection results and other network-related information.

The primary class is DetectionResult, which encapsulates the outcome of protocol
detection attempts, including the identified protocol, any received banner data,
and additional protocol-specific information.

Example:
    Creating and using a detection result:

    ```python
    from network_tools.types import DetectionResult

    # Create a result for an SSH detection
    result = DetectionResult(
        protocol="SSH",
        banner=b"SSH-2.0-OpenSSH_8.2p1",
        extra_info={"version": "OpenSSH_8.2p1"}
    )

    # Use the result
    if result.protocol == "SSH":
        print(f"SSH detected: {result.extra_info.get('version')}")
    ```
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DetectionResult:
    """Container for protocol detection results."""

    protocol: str
    banner: bytes | None = field(default=None)
    extra_info: dict[str, Any] | None = field(default=None)
