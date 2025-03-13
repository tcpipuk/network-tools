"""Main entry point for network tools CLI."""

from __future__ import annotations

from .args import parse_args
from .console import log


async def main() -> None:
    """Main entry point for network tools CLI."""
    args = parse_args()
    log.info(args)
