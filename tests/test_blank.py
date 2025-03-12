"""Test to ensure pytest passes when no other tests are present."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_blank() -> None:
    """Blank placeholder test."""
