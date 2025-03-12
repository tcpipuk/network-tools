"""JSON input class."""

from __future__ import annotations

from dataclasses import dataclass, field
from json import loads as json_loads
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from network_tools.types import JSON_TYPE


@dataclass(slots=True, frozen=True)
class JSONInput:
    """JSON input class."""

    path: Path
    data: JSON_TYPE = field(init=False)

    def __post_init__(self) -> None:
        """Post-initialization method."""
        json_text = self.path.read_text()
        self.data = json_loads(json_text)
