"""File handling modules for CLI tools."""

from __future__ import annotations

from csv import DictReader, DictWriter
from dataclasses import dataclass, field
from json import dump as json_dump, loads as json_loads
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pathlib import Path

    from network_tools.types import JSON_TYPE


@dataclass(slots=True, frozen=True)
class FileReader:
    """Read hosts from a file."""

    path: Path
    type: Literal["csv", "json"]
    data: JSON_TYPE = field(init=False)

    def __post_init__(self) -> None:
        """Initialise the file reader.

        Raises:
            ValueError: If the file type is invalid.
        """
        match self.type:
            case "csv":
                self.data = list(DictReader(self.path.read_text()))
            case "json":
                self.data = json_loads(self.path.read_text())
            case _:
                msg = f"Invalid file type: {self.type}"
                raise ValueError(msg)


@dataclass(slots=True, frozen=True)
class FileWriter:
    """Read hosts from a CSV file."""

    path: Path
    type: Literal["csv", "json", "plain"] = field(init=False)
    data: JSON_TYPE = field(init=False)

    def __post_init__(self) -> None:
        """Initialise the file writer.

        Raises:
            ValueError: If the file type is invalid.
        """
        match self.type:
            case "csv":
                writer = DictWriter(self.path, fieldnames=self.data[0].keys())
                writer.writeheader()
                [writer.writerow(row) for row in self.data]
            case "json":
                json_dump(self.data, self.path)
            case "plain":
                if isinstance(self.data, list):
                    self.data = "\n".join(self.data)
                # Write text
                self.path.write_text("\n".join(self.data))
            case _:
                msg = f"Invalid file type: {self.type}"
                raise ValueError(msg)
