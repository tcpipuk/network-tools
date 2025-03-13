"""Constants for network tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Network protocol constants

IAC_BYTE = 0xFF  # Interpret As Command byte
MIN_PORT = 1
MAX_PORT = 65535

# CLI constants

CLI_ARGUMENTS: dict[str, list[tuple[Any]]] = {
    "operations": [
        (["-c", "--concurrency"], {"type": int, "default": 50, "metavar": "<50>"}),
        (
            ["-m", "--mode"],
            {
                "choices": ["banner", "connect", "fingerprint", "probe", "scan"],
                "metavar": "banner|connect|fingerprint|probe|scan",
                "required": True,
            },
        ),
        (
            ["-p", "--protocol"],
            {
                "choices": ["auto", "http", "https", "ssh", "telnet"],
                "default": "auto",
                "metavar": "<auto>|http|https|ssh|telnet",
            },
        ),
        (["-t", "--timeout"], {"type": float, "default": 10.0, "metavar": "<10>"}),
    ],
    "files": [
        (["-i", "--input"], {"help": "Input file path", "required": True, "type": Path}),
        (
            ["-if", "--input-format"],
            {"choices": ["csv", "json"], "default": "csv", "metavar": "<csv>|json"},
        ),
        (["-o", "--output"], {"help": "Output file path (default: stdout)", "type": Path}),
        (
            ["-of", "--output-format"],
            {"choices": ["csv", "json", "plain"], "default": "plain", "metavar": "csv|json|<plain>"},
        ),
    ],
}
CLI_HELP_DESCRIPTION: str = """Network tools: detect, analyse and interact with network services.

This tool helps you identify protocols running on network devices,
test connectivity, scan for services, and retrieve information
from compatible network endpoints. Use different modes to perform
specific operations, with customisable input and output options.
"""
CLI_HELP_EPILOGUE: str | None = "If an argument has a default, it's shown in <parentheses>."
CLI_HELP_NAME: str = "network_tools"
