"""CSV input class."""

from __future__ import annotations

from csv import DictReader
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(slots=True, frozen=True)
class CSVInput:
    """CSV input class."""

    path: Path
    data: tuple[dict[str, str], ...] = field(init=False)

    def __post_init__(self) -> None:
        """Load data from file."""
        csv_text = self.path.read_text()
        self.data = tuple(DictReader(csv_text))
