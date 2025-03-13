"""Type definitions module for network protocol detection.

This module contains dataclass definitions and type hints used throughout the
network tools package. It provides standardised data structures for representing
protocol detection results and other network-related information.
"""

from __future__ import annotations

type JSON_TYPE = bool | dict[str, JSON_TYPE] | float | int | list[JSON_TYPE] | str | None
