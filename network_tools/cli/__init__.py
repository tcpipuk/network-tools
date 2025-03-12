"""Command line interface components for network tools.

This module provides CLI-related functionality including console output,
logging, and progress tracking for command line applications built with
the network tools package.

Core components:
- Console: Rich-based console for formatted output
- Logger: Standardised logging configuration
- Progress tracking: Thread-safe progress bars
"""

from __future__ import annotations

from .console import (
    complete_progress,
    console,
    create_progress,
    logger,
    update_progress,
)

__all__ = [
    "complete_progress",
    "console",
    "create_progress",
    "logger",
    "update_progress",
]
