"""Constants for network tools."""

from __future__ import annotations

from typing import Any

# Network protocol constants

IAC_BYTE = 0xFF  # Interpret As Command byte
MIN_PORT = 1
MAX_PORT = 65535

# CLI constants

CLI_ARGUMENTS: dict[str, list[tuple[Any]]] = {
    # Common networking arguments
    "common": [
        (["target"], {"help": "Target hostname or IP address", "nargs": "?"}),
        (
            ["-p", "--port"],
            {"choices": range(1, 65536), "help": "Target port number", "metavar": "[1-65535]"},
        ),
        (
            ["-t", "--timeout"],
            {"type": float, "default": 10.0, "help": "Connection timeout in seconds (default: %(default)s)"},
        ),
        (
            ["-v", "--verbose"],
            {"action": "count", "default": 0, "help": "Increase verbosity (can be used multiple times)"},
        ),
        (["-q", "--quiet"], {"action": "store_true", "help": "Suppress non-error output"}),
    ],
    # Protocol options
    "protocols": [
        (["--ssh"], {"action": "store_true", "help": "Force SSH protocol detection"}),
        (["--http"], {"action": "store_true", "help": "Force HTTP protocol detection"}),
        (["--https"], {"action": "store_true", "help": "Force HTTPS protocol detection"}),
        (["--telnet"], {"action": "store_true", "help": "Force Telnet protocol detection"}),
        (["--ftp"], {"action": "store_true", "help": "Force FTP protocol detection"}),
    ],
    # Output options
    "output": [
        (["--json"], {"action": "store_true", "help": "Output results in JSON format"}),
        (["--csv"], {"action": "store_true", "help": "Output results in CSV format"}),
        (["-o", "--output"], {"help": "Save output to file"}),
    ],
}
CLI_HELP_DESCRIPTION: str = """Command line interface for network tools.

This module provides a configurable and extensible argument parser for
command line interfaces built with the network tools package. It includes
common network-related arguments and allows for command-specific subparsers.
"""
CLI_HELP_EPILOGUE: str | None = None
CLI_HELP_NAME: str = "Network tools"
