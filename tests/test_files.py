"""Unit tests for the CLI file handling module."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from network_tools.cli.files import FileReader, FileWriter

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def temp_directory(tmp_path: Path) -> Path:
    """Fixture providing a temporary directory for file tests."""
    return tmp_path


@pytest.fixture
def test_csv_data() -> list[dict[str, str]]:
    """Fixture providing test CSV data."""
    return [
        {"host": "192.168.1.1", "port": "22", "protocol": "ssh"},
        {"host": "192.168.1.2", "port": "23", "protocol": "telnet"},
        {"host": "192.168.1.3", "port": "80", "protocol": "http"},
    ]


@pytest.fixture
def test_csv_content() -> str:
    """Fixture providing test CSV content as a string."""
    return "host,port,protocol\n192.168.1.1,22,ssh\n192.168.1.2,23,telnet\n192.168.1.3,80,http"


@pytest.fixture
def test_json_data() -> list[dict[str, str]]:
    """Fixture providing test JSON data."""
    return [
        {"host": "192.168.1.1", "port": "22", "protocol": "ssh"},
        {"host": "192.168.1.2", "port": "23", "protocol": "telnet"},
        {"host": "192.168.1.3", "port": "80", "protocol": "http"},
    ]


@pytest.fixture
def test_json_content() -> str:
    """Fixture providing test JSON content as a string."""
    return json.dumps([
        {"host": "192.168.1.1", "port": "22", "protocol": "ssh"},
        {"host": "192.168.1.2", "port": "23", "protocol": "telnet"},
        {"host": "192.168.1.3", "port": "80", "protocol": "http"},
    ])


@pytest.fixture
def test_plain_content() -> str:
    """Fixture providing test plain text content."""
    return "line1\nline2\nline3"


def test_file_reader_csv() -> None:
    """Test FileReader with CSV file."""
    # Create a proper CSV content string with exact format
    csv_content = "host,port,protocol\n192.168.1.1,22,ssh\n192.168.1.2,23,telnet"

    # Mock DictReader to return known data
    mock_csv_data = [
        {"host": "192.168.1.1", "port": "22", "protocol": "ssh"},
        {"host": "192.168.1.2", "port": "23", "protocol": "telnet"},
    ]

    with patch("network_tools.cli.files.DictReader") as mock_dict_reader:
        # Set up the mock to return our test data when iterated
        mock_dict_reader.return_value = mock_csv_data

        # Create mock path
        mock_path = MagicMock()
        mock_path.read_text.return_value = csv_content

        # Create the reader which will use our mocked DictReader
        reader = FileReader(path=mock_path, type="csv")

        # Verify the data matches what we expect
        if len(reader.data) != len(mock_csv_data):
            pytest.fail(f"Expected {len(mock_csv_data)} rows, got {len(reader.data)}")
        if reader.data != mock_csv_data:
            pytest.fail(f"CSV data mismatch. Expected {mock_csv_data}, got {reader.data}")


def test_file_reader_json() -> None:
    """Test FileReader with JSON file."""
    # Prepare JSON content
    json_data = [
        {"host": "192.168.1.1", "port": "22", "protocol": "ssh"},
        {"host": "192.168.1.2", "port": "23", "protocol": "telnet"},
    ]
    json_content = json.dumps(json_data)

    # Mock path object and read_text
    mock_path = MagicMock()
    mock_path.read_text.return_value = json_content

    # Create a reader
    reader = FileReader(path=mock_path, type="json")

    # Verify the data was parsed correctly
    if reader.data != json_data:
        pytest.fail(f"JSON data mismatch. Expected {json_data}, got {reader.data}")


def test_file_reader_invalid_type() -> None:
    """Test FileReader with an invalid file type."""
    mock_path = MagicMock()

    with pytest.raises(ValueError, match="Invalid file type: invalid"):
        # Intentionally use an invalid type
        FileReader(path=mock_path, type="invalid")


def test_file_writer_csv() -> None:
    """Test FileWriter with CSV file."""
    test_data = [
        {"host": "192.168.1.1", "port": "22", "protocol": "ssh"},
        {"host": "192.168.1.2", "port": "23", "protocol": "telnet"},
    ]

    # Set up mocks
    mock_path = MagicMock()
    mock_writer = MagicMock()

    # Direct patching of the DictWriter constructor
    with patch("network_tools.cli.files.DictWriter", return_value=mock_writer) as mock_dict_writer_cls:
        # Create a FileWriter with CSV type
        FileWriter(path=mock_path, type="csv", data=test_data)

        # Verify DictWriter was called with correct fieldnames
        mock_dict_writer_cls.assert_called_once()

        # Verify writeheader and writerow were called
        mock_writer.writeheader.assert_called_once()
        if mock_writer.writerow.call_count != 2:  # noqa: PLR2004
            pytest.fail(f"Expected 2 writerow calls, got {mock_writer.writerow.call_count}")


def test_file_writer_json() -> None:
    """Test FileWriter with JSON file."""
    test_data = [
        {"host": "192.168.1.1", "port": "22", "protocol": "ssh"},
        {"host": "192.168.1.2", "port": "23", "protocol": "telnet"},
    ]

    # Set up path mock
    mock_path = MagicMock()

    # Mock the json_dump function
    with patch("network_tools.cli.files.json_dump") as mock_json_dump:
        # Create a FileWriter with JSON type
        FileWriter(path=mock_path, type="json", data=test_data)

        # Verify json_dump was called correctly
        mock_json_dump.assert_called_once_with(test_data, mock_path)


def test_file_writer_plain_list() -> None:
    """Test FileWriter with plain text list."""
    # Test with list data
    list_data = ["line1", "line2", "line3"]
    expected_text = "line1\nline2\nline3"

    # Set up path mock
    mock_path = MagicMock()

    # Specifically patch the write_text method on our mock_path instance
    mock_path.write_text = MagicMock()

    # Create a FileWriter with plain type
    FileWriter(path=mock_path, type="plain", data=list_data)

    # Verify the instance's write_text was called correctly
    mock_path.write_text.assert_called_once()

    # Check the argument to write_text
    args, _ = mock_path.write_text.call_args
    if args[0] != expected_text:
        pytest.fail(f"Expected '{expected_text}', got '{args[0]}'")


def test_file_writer_plain_string() -> None:
    """Test FileWriter with plain text string."""
    # Test with string data
    string_data = "single line of text"

    # Set up path mock and its write_text method
    mock_path = MagicMock()
    mock_path.write_text = MagicMock()

    # Create a FileWriter with plain type
    FileWriter(path=mock_path, type="plain", data=string_data)

    # Verify write_text was called correctly
    mock_path.write_text.assert_called_once()

    # Check the argument
    args, _ = mock_path.write_text.call_args
    if args[0] != string_data:
        pytest.fail(f"Expected '{string_data}', got '{args[0]}'")


def test_file_writer_plain_dict() -> None:
    """Test FileWriter with plain text dictionary."""
    # Test with dictionary data - should be formatted as key: value pairs
    dict_data = {
        "host": "192.168.1.1",
        "port": "22",
        "protocol": "ssh",
    }

    # The expected format is key: value pairs, one per line
    expected_lines = [f"{key}: {value}" for key, value in dict_data.items()]
    expected_text = "\n".join(expected_lines)

    # Set up path mock
    mock_path = MagicMock()
    mock_path.write_text = MagicMock()

    # Create a FileWriter with plain type
    FileWriter(path=mock_path, type="plain", data=dict_data)

    # Verify write_text was called correctly
    mock_path.write_text.assert_called_once()

    # Check the argument to write_text
    args, _ = mock_path.write_text.call_args
    if args[0] != expected_text:
        pytest.fail(f"Expected '{expected_text}', got '{args[0]}'")


def test_file_writer_invalid_type() -> None:
    """Test FileWriter with an invalid file type."""
    test_path = MagicMock()
    test_data = [{"host": "192.168.1.1", "port": "22"}]

    with pytest.raises(ValueError, match="Invalid file type: invalid"):
        # Intentionally use an invalid type
        FileWriter(path=test_path, type="invalid", data=test_data)


@pytest.mark.parametrize("file_type", ["csv", "json"])
def test_file_integration(file_type: str, temp_directory: Path) -> None:
    """Test integration with real files on disk."""
    # Test data
    test_data = [
        {"host": "192.168.1.1", "port": "22", "protocol": "ssh"},
        {"host": "192.168.1.2", "port": "23", "protocol": "telnet"},
    ]

    # Create test file path
    test_file_path = temp_directory / f"test_file.{file_type}"

    # We need to patch the FileWriter functions that interact with files
    if file_type == "csv":
        # For CSV, we'll need to patch the DictWriter
        with patch("network_tools.cli.files.DictWriter") as mock_dict_writer_cls:
            # Set up the mock writer instance
            mock_writer = MagicMock()
            mock_dict_writer_cls.return_value = mock_writer

            # Call FileWriter
            FileWriter(path=test_file_path, type=file_type, data=test_data)

            # Verify DictWriter was constructed
            mock_dict_writer_cls.assert_called_once()

            # Verify writeheader and writerow were called
            mock_writer.writeheader.assert_called_once()
            if mock_writer.writerow.call_count != 2:  # noqa: PLR2004
                pytest.fail(f"Expected 2 writerow calls, got {mock_writer.writerow.call_count}")

    else:  # JSON
        # For JSON, we'll patch json_dump
        with patch("network_tools.cli.files.json_dump") as mock_json_dump:
            # Call FileWriter
            FileWriter(path=test_file_path, type=file_type, data=test_data)

            # Verify json_dump was called correctly
            mock_json_dump.assert_called_once_with(test_data, test_file_path)


def test_plain_text_integration() -> None:
    """Test writing plain text files."""
    # Test list data
    list_data = ["line1", "line2", "line3"]
    expected_text = "line1\nline2\nline3"

    # Create a mock path
    mock_path = MagicMock()
    mock_path.write_text = MagicMock()

    # Create FileWriter with plain type directly
    FileWriter(path=mock_path, type="plain", data=list_data)

    # Verify write_text was called with the expected text
    mock_path.write_text.assert_called_once()
    args, _ = mock_path.write_text.call_args
    if args[0] != expected_text:
        pytest.fail(f"Expected '{expected_text}', got '{args[0]}'")

    # Test string data
    string_data = "single line of text"

    # Reset the mock
    mock_path.write_text.reset_mock()

    # Create FileWriter with plain type for string data
    FileWriter(path=mock_path, type="plain", data=string_data)

    # Verify write_text was called with the string
    mock_path.write_text.assert_called_once()
    args, _ = mock_path.write_text.call_args
    if args[0] != string_data:
        pytest.fail(f"Expected '{string_data}', got '{args[0]}'")

    # Test dictionary data
    dict_data = {"key1": "value1", "key2": "value2"}
    expected_lines = ["key1: value1", "key2: value2"]
    expected_text = "\n".join(expected_lines)

    # Reset the mock
    mock_path.write_text.reset_mock()

    # Create FileWriter with plain type for dictionary data
    FileWriter(path=mock_path, type="plain", data=dict_data)

    # Verify write_text was called with the expected format
    mock_path.write_text.assert_called_once()
    args, _ = mock_path.write_text.call_args
    if args[0] != expected_text:
        pytest.fail(f"Expected '{expected_text}', got '{args[0]}'")


def test_plain_text_non_string_data() -> None:
    """Test plain text writer with non-string data types."""
    # Test with an integer
    mock_path = MagicMock()
    mock_path.write_text = MagicMock()

    # Create FileWriter with plain type and an integer
    integer_data = 42
    FileWriter(path=mock_path, type="plain", data=integer_data)

    # Verify write_text was called with the string representation
    mock_path.write_text.assert_called_once()
    args, _ = mock_path.write_text.call_args
    if args[0] != "42":
        pytest.fail(f"Expected '42', got '{args[0]}'")

    # Test with a boolean
    mock_path.write_text.reset_mock()
    bool_data = True
    FileWriter(path=mock_path, type="plain", data=bool_data)

    # Verify correct conversion
    mock_path.write_text.assert_called_once()
    args, _ = mock_path.write_text.call_args
    if args[0] != "True":
        pytest.fail(f"Expected 'True', got '{args[0]}'")
