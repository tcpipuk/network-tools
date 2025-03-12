"""Main entry point for network tools."""

from __future__ import annotations

from asyncio import run as asyncio_run

from .cli import main

if __name__ == "__main__":
    asyncio_run(main())
