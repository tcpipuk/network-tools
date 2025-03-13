"""Main entry point for network tools."""

from __future__ import annotations

from asyncio import run as asyncio_run

from .cli import main


def launch() -> None:
    """Launch the network tools application."""
    asyncio_run(main())


if __name__ == "__main__":
    launch()
