"""Command line interface components for network tools.

This module provides CLI-related functionality including console output,
logging, progress tracking for command line applications built with
the network tools package.

Core components:
- Console: Rich-based console for formatted output
- Logger: Standardised logging configuration
- Progress tracking: Thread-safe progress bars
- Argument parsing: Standard CLI argument parser with network-specific options
"""

from __future__ import annotations

from .args import parse_args
from .console import complete_progress, console, create_progress, log, update_progress
from .main import main

__all__ = [
    "complete_progress",
    "console",
    "create_progress",
    "log",
    "main",
    "parse_args",
    "update_progress",
]
