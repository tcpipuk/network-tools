"""Type definitions module for network protocol detection.

This module contains dataclass definitions and type hints used throughout the
network tools package. It provides standardised data structures for representing
protocol detection results and other network-related information.

The primary class is DetectionResult, which encapsulates the outcome of protocol
detection attempts, including the identified protocol, any received banner data,
and additional protocol-specific information.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

type JSON_TYPE = bool | dict[str, JSON_TYPE] | float | int | list[JSON_TYPE] | str | None


@dataclass(slots=True)
class DetectionResult:
    """Container for protocol detection results."""

    protocol: str
    banner: bytes | None = field(default=None)
    extra_info: dict[str, Any] | None = field(default=None)
