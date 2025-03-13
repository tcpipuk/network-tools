"""Unit tests for the console and logging implementation."""

from __future__ import annotations

import threading
from logging import getLogger
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, call, patch

import pytest

from network_tools.cli.console import (
    LiveDisplayHandler,
    _active_tasks,  # noqa: PLC2701
    complete_progress,
    create_progress,
    live_display,
    progress_lock,
    start_live_display,
    stop_live_display,
    update_progress,
)

if TYPE_CHECKING:
    from collections.abc import Generator

log = getLogger(__name__)


@pytest.fixture(autouse=True)
def reset_progress_state() -> Generator[None]:
    """Reset progress-related global state between tests."""
    original_active_tasks = _active_tasks.copy()

    # Clear active tasks before test
    _active_tasks.clear()

    # Ensure live display is stopped
    if live_display.is_started:
        live_display.stop()

    yield

    # Clean up after test
    if live_display.is_started:
        live_display.stop()

    # Restore original tasks
    _active_tasks.clear()
    _active_tasks.update(original_active_tasks)


@pytest.fixture
def mock_console() -> Generator[MagicMock]:
    """Fixture providing a mock console for testing."""
    with patch("network_tools.cli.console.console") as mock:
        yield mock


@pytest.fixture
def mock_live() -> Generator[MagicMock]:
    """Fixture providing a mock live display for testing."""
    with patch("network_tools.cli.console.live_display") as mock:
        # Set up mock properties that tests will check
        mock.is_started = False
        yield mock


@pytest.fixture
def mock_log() -> Generator[MagicMock]:
    """Fixture providing a mock logger for testing."""
    with patch("network_tools.cli.console.log") as mock:
        yield mock


@pytest.fixture
def mock_progress() -> Generator[MagicMock]:
    """Fixture providing a mock progress bar for testing."""
    with patch("network_tools.cli.console.progress") as mock:
        # Set up mock tasks dictionary
        mock.tasks = {}
        yield mock


def test_progress_lock_is_rlock() -> None:
    """Test that progress_lock is an RLock instance."""
    if not isinstance(progress_lock, type(threading.RLock())):
        pytest.fail(f"Expected progress_lock to be threading.RLock, got {type(progress_lock)}")


def test_live_display_handler_emit_display_not_started(mock_console: MagicMock) -> None:
    """Test LiveDisplayHandler.emit when live display is not started."""
    with patch("network_tools.cli.console.live_display") as mock_live:
        mock_live.is_started = False

        handler = LiveDisplayHandler(console=mock_console)
        record = MagicMock()
        rendered = MagicMock()

        with patch.object(handler, "render", return_value=rendered) as mock_render:
            handler.emit(record)

            mock_render.assert_called_once_with(record)
            mock_console.print.assert_called_once_with(rendered)
            mock_live.refresh.assert_not_called()


def test_live_display_handler_emit_display_started(mock_console: MagicMock) -> None:
    """Test LiveDisplayHandler.emit when live display is started."""
    with patch("network_tools.cli.console.live_display") as mock_live:
        mock_live.is_started = True

        handler = LiveDisplayHandler(console=mock_console)
        record = MagicMock()
        rendered = MagicMock()

        with patch.object(handler, "render", return_value=rendered) as mock_render:
            handler.emit(record)

            mock_render.assert_called_once_with(record)
            mock_console.print.assert_called_once_with(rendered)
            if mock_live.refresh.call_count != 2:  # noqa: PLR2004
                pytest.fail(f"Expected 2 refresh calls, got {mock_live.refresh.call_count}")


def test_start_live_display_not_started(mock_live: MagicMock) -> None:
    """Test start_live_display when display is not already started."""
    mock_live.is_started = False

    start_live_display()

    mock_live.start.assert_called_once()


def test_start_live_display_already_started(mock_live: MagicMock) -> None:
    """Test start_live_display when display is already started."""
    mock_live.is_started = True

    start_live_display()

    mock_live.start.assert_not_called()


def test_stop_live_display_started_no_tasks(mock_live: MagicMock) -> None:
    """Test stop_live_display when display is started and no active tasks."""
    mock_live.is_started = True

    # Ensure _active_tasks is empty (handled by fixture)

    stop_live_display()

    mock_live.stop.assert_called_once()


def test_stop_live_display_started_with_tasks(mock_live: MagicMock) -> None:
    """Test stop_live_display when display is started but has active tasks."""
    mock_live.is_started = True

    # Add a mock task
    _active_tasks["test_task"] = 1

    stop_live_display()

    mock_live.stop.assert_not_called()

    # Clean up
    _active_tasks.clear()


def test_stop_live_display_not_started(mock_live: MagicMock) -> None:
    """Test stop_live_display when display is not started."""
    mock_live.is_started = False

    stop_live_display()

    mock_live.stop.assert_not_called()


def test_create_progress_new_task(mock_progress: MagicMock, mock_live: MagicMock) -> None:
    """Test create_progress with auto-generated task ID."""
    mock_progress.add_task.return_value = 123
    mock_live.is_started = True

    description = "Test Task"
    total = 50

    # Patch time.time() to return a predictable value
    with patch("time.time", return_value=1000.0):
        task_id = create_progress(description, total)

    mock_progress.add_task.assert_called_once_with(description, total=total)
    if task_id != "task_1000.0":
        pytest.fail(f"Expected task ID 'task_1000.0', got {task_id}")
    if _active_tasks[task_id] != 123:  # noqa: PLR2004
        pytest.fail(f"Expected task ID {task_id} to have value 123, got {_active_tasks[task_id]}")
    mock_live.refresh.assert_called_once()


def test_create_progress_custom_task_id(mock_progress: MagicMock, mock_live: MagicMock) -> None:
    """Test create_progress with custom task ID."""
    mock_progress.add_task.return_value = 123
    mock_live.is_started = True

    description = "Test Task"
    total = 50
    task_id = "custom_task_id"

    returned_task_id = create_progress(description, total, task_id)

    mock_progress.add_task.assert_called_once_with(description, total=total)
    if returned_task_id != task_id:
        pytest.fail(f"Expected task ID {task_id}, got {returned_task_id}")
    if _active_tasks[task_id] != 123:  # noqa: PLR2004
        pytest.fail(f"Expected task ID {task_id} to have value 123, got {_active_tasks[task_id]}")
    mock_live.refresh.assert_called_once()


def test_create_progress_starts_display(mock_progress: MagicMock, mock_live: MagicMock) -> None:
    """Test create_progress starts live display if not already started."""
    mock_progress.add_task.return_value = 123
    mock_live.is_started = False

    description = "Test Task"

    task_id = create_progress(description)

    mock_live.start.assert_called_once()
    if task_id not in _active_tasks:
        pytest.fail(f"Task {task_id} should be in _active_tasks")
    mock_live.refresh.assert_called_once()


def test_update_progress_advance(mock_progress: MagicMock, mock_live: MagicMock) -> None:
    """Test update_progress with advance parameter."""
    mock_live.is_started = True
    task_id = "test_task"
    progress_task_id = 123
    _active_tasks[task_id] = progress_task_id

    update_progress(task_id, advance=10)

    mock_progress.update.assert_called_once_with(progress_task_id, advance=10)
    mock_live.refresh.assert_called_once()


def test_update_progress_completed(mock_progress: MagicMock, mock_live: MagicMock) -> None:
    """Test update_progress with completed parameter."""
    mock_live.is_started = True
    task_id = "test_task"
    progress_task_id = 123
    _active_tasks[task_id] = progress_task_id

    update_progress(task_id, completed=50)

    mock_progress.update.assert_called_once_with(progress_task_id, completed=50)
    mock_live.refresh.assert_called_once()


def test_update_progress_description(mock_progress: MagicMock, mock_live: MagicMock) -> None:
    """Test update_progress with description parameter."""
    mock_live.is_started = True
    task_id = "test_task"
    progress_task_id = 123
    description = "Updated description"
    _active_tasks[task_id] = progress_task_id

    update_progress(task_id, description=description)

    mock_progress.update.assert_called_once_with(progress_task_id, description=description)
    mock_live.refresh.assert_called_once()


def test_update_progress_multiple_params(mock_progress: MagicMock, mock_live: MagicMock) -> None:
    """Test update_progress with multiple parameters."""
    mock_live.is_started = True
    task_id = "test_task"
    progress_task_id = 123
    description = "Updated description"
    _active_tasks[task_id] = progress_task_id

    update_progress(task_id, advance=10, description=description, visible=True)

    mock_progress.update.assert_called_once_with(
        progress_task_id, advance=10, description=description, visible=True
    )
    mock_live.refresh.assert_called_once()


def test_update_progress_nonexistent_task(mock_progress: MagicMock, mock_log: MagicMock) -> None:
    """Test update_progress with non-existent task ID."""
    task_id = "nonexistent_task"

    update_progress(task_id, advance=10)

    mock_progress.update.assert_not_called()
    mock_log.warning.assert_called_once()
    # Check that warning was called with the right format
    # Format should be: "Attempted to update non-existent progress task: %s"
    mock_log.warning.assert_called_with("Attempted to update non-existent progress task: %s", task_id)


def test_update_progress_display_not_started(mock_progress: MagicMock, mock_live: MagicMock) -> None:
    """Test update_progress when live display is not started."""
    mock_live.is_started = False
    task_id = "test_task"
    progress_task_id = 123
    _active_tasks[task_id] = progress_task_id

    update_progress(task_id, advance=10)

    mock_progress.update.assert_called_once()
    mock_live.refresh.assert_not_called()


def test_complete_progress(mock_progress: MagicMock, mock_live: MagicMock) -> None:
    """Test complete_progress basic functionality."""
    mock_live.is_started = True
    task_id = "test_task"
    progress_task_id = 123
    _active_tasks[task_id] = progress_task_id

    # Mock the task object
    task = MagicMock()
    task.total = 100
    mock_progress.tasks = {progress_task_id: task}

    complete_progress(task_id)

    # Should update to mark as completed
    mock_progress.update.assert_called_once_with(progress_task_id, completed=100)

    # Should be removed from active tasks
    if task_id in _active_tasks:
        pytest.fail(f"Task {task_id} should not be in _active_tasks")

    # Should stop display if no active tasks
    mock_live.stop.assert_called_once()


def test_complete_progress_with_description(mock_progress: MagicMock, mock_live: MagicMock) -> None:
    """Test complete_progress with description parameter."""
    mock_live.is_started = True
    task_id = "test_task"
    progress_task_id = 123
    description = "Completed!"
    _active_tasks[task_id] = progress_task_id

    # Mock the task object
    task = MagicMock()
    task.total = 100
    mock_progress.tasks = {progress_task_id: task}

    complete_progress(task_id, description=description)

    # Should update description first, then mark as completed
    calls = [
        call(progress_task_id, description=description),
        call(progress_task_id, completed=100),
    ]
    mock_progress.update.assert_has_calls(calls)

    # Should be removed from active tasks
    if task_id in _active_tasks:
        pytest.fail(f"Task {task_id} should not be in _active_tasks")


def test_complete_progress_nonexistent_task(mock_progress: MagicMock, mock_log: MagicMock) -> None:
    """Test complete_progress with non-existent task ID."""
    task_id = "nonexistent_task"

    complete_progress(task_id)

    mock_progress.update.assert_not_called()
    mock_log.warning.assert_called_once()
    # Check that warning was called with the right format
    # Format should be: "Attempted to complete non-existent progress task: %s"
    mock_log.warning.assert_called_with("Attempted to complete non-existent progress task: %s", task_id)


def test_complete_progress_with_other_tasks(mock_progress: MagicMock, mock_live: MagicMock) -> None:
    """Test complete_progress when other tasks are still active."""
    mock_live.is_started = True
    task_id1 = "test_task_1"
    task_id2 = "test_task_2"
    progress_task_id1 = 123
    progress_task_id2 = 456
    _active_tasks[task_id1] = progress_task_id1
    _active_tasks[task_id2] = progress_task_id2

    # Mock the task object
    task = MagicMock()
    task.total = 100
    mock_progress.tasks = {progress_task_id1: task}

    complete_progress(task_id1)

    # Should not stop display when other tasks exist
    mock_live.stop.assert_not_called()

    # Only task_id1 should be removed
    if task_id1 in _active_tasks:
        pytest.fail(f"Task {task_id1} should not be in _active_tasks")
    if task_id2 not in _active_tasks:
        pytest.fail(f"Task {task_id2} should be in _active_tasks")


def test_integration_progress_workflow(mock_progress: MagicMock, mock_live: MagicMock) -> None:
    """Test an integration of the full progress workflow."""
    # Setup
    mock_live.is_started = False
    mock_progress.add_task.return_value = 123
    task = MagicMock()
    task.total = 100
    mock_progress.tasks = {123: task}

    # Patch stop_live_display to directly call mock_live.stop
    with patch("network_tools.cli.console.stop_live_display", side_effect=mock_live.stop):
        # 1. Create a progress task
        task_id = create_progress("Starting task", total=100)

        # Verify live display started
        mock_live.start.assert_called_once()

        # Set live display as started for the rest of the test
        mock_live.is_started = True

        # 2. Update progress multiple times
        update_progress(task_id, advance=25)
        update_progress(task_id, advance=25, description="Halfway there")
        update_progress(task_id, advance=25)

        # Verify updates
        if mock_progress.update.call_count != 3:  # noqa: PLR2004
            pytest.fail(f"Expected 3 update calls, got {mock_progress.update.call_count}")

        # 3. Complete the task
        complete_progress(task_id, description="Task completed!")

        # Verify task completed and removed
        if mock_progress.update.call_count != 5:  # noqa: PLR2004
            pytest.fail(f"Expected 5 update calls, got {mock_progress.update.call_count}")
        if task_id in _active_tasks:
            pytest.fail(f"Task {task_id} should not be in _active_tasks")

        # 4. Live display should be stopped
        mock_live.stop.assert_called_once()
