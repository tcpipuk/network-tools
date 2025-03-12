"""Console and logging configuration module for network tools.

This module provides a standardised console setup for the network tools package,
configuring a Rich-based console with integrated logging and progress bars.

Key features:
1. Rich-formatted logging that appears above any progress bars
2. Progress bars that stay pinned to the bottom of the screen
3. Thread-safe operations for concurrent updates

For detailed documentation and examples, see docs/console.md
"""

from __future__ import annotations

import logging
import threading
import time
from logging import INFO, getLogger
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

# Create a Rich console for output
console = Console()

# Create a progress instance that can be shared across the application
progress_lock = threading.RLock()
progress = Progress(
    SpinnerColumn(),
    TextColumn("[bold blue]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    TimeElapsedColumn(),
    TimeRemainingColumn(),
    console=console,
    expand=True,  # Expand to fill available width
)

# Create a Live display that will manage both logs and progress
live_display = Live(
    progress,
    console=console,
    refresh_per_second=10,
    transient=False,  # Keep progress bars visible
    auto_refresh=False,  # We'll handle refreshing manually
)

# Dictionary to track active progress tasks
_active_tasks: dict[str, TaskID] = {}


# Configure logging with Rich handler that works with our Live display
class LiveDisplayHandler(RichHandler):
    """A custom Rich handler that works with our Live display.

    This handler ensures logs appear above the progress bars when they're active.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record that works with our Live display."""
        with progress_lock:
            # When live display is active, print above the progress bar
            if live_display.is_started:
                # Refresh to ensure latest progress is shown
                live_display.refresh()
                # Use console directly to print above the progress bar
                console.print(self.render(record))
                # Refresh again to ensure progress bar is shown
                live_display.refresh()
            else:
                # If live display isn't started, just use normal console output
                console.print(self.render(record))


# Configure logging with our custom handler
logging.basicConfig(
    level=INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[LiveDisplayHandler(console=console, rich_tracebacks=True, show_time=True)],
    force=True,
)

# Get the logger for this module
logger = getLogger("network_tools")


def start_live_display() -> None:
    """Start the live display for logs and progress bars.

    This should be called once at the beginning of operations that use progress bars.
    It's automatically called by create_progress if needed.
    """
    with progress_lock:
        if not live_display.is_started:
            live_display.start()


def stop_live_display() -> None:
    """Stop the live display.

    This should be called when all operations using progress bars are complete.
    It's automatically called by complete_progress when all tasks are done.
    """
    with progress_lock:
        if live_display.is_started and not _active_tasks:
            live_display.stop()


def create_progress(description: str, total: int = 100, task_id: str | None = None) -> str:
    """Create a new progress bar task.

    Args:
        description: Description of the task
        total: Total number of steps
        task_id: Optional identifier for the task (generated if not provided)

    Returns:
        String identifier for the task
    """
    with progress_lock:
        if not live_display.is_started:
            start_live_display()

        # Generate a task ID if not provided
        if task_id is None:
            task_id = f"task_{time.time()}"

        # Create the progress task
        progress_task_id = progress.add_task(description, total=total)
        _active_tasks[task_id] = progress_task_id

        # Refresh the display to show the new task
        live_display.refresh()

        return task_id


def update_progress(
    task_id: str,
    advance: float | None = None,
    completed: float | None = None,
    description: str | None = None,
    **kwargs: Any,
) -> None:
    """Update a progress bar task.

    Args:
        task_id: Identifier for the task
        advance: Number of steps to advance
        completed: Set the absolute completed value
        description: Update the task description
        **kwargs: Additional arguments to pass to progress.update
    """
    with progress_lock:
        if task_id not in _active_tasks:
            logger.warning("Attempted to update non-existent progress task: %s", task_id)
            return

        progress_task_id = _active_tasks[task_id]
        update_kwargs: dict[str, Any] = {}

        if advance is not None:
            update_kwargs["advance"] = advance
        if completed is not None:
            update_kwargs["completed"] = completed
        if description is not None:
            update_kwargs["description"] = description

        update_kwargs.update(kwargs)
        progress.update(progress_task_id, **update_kwargs)

        # Refresh the display to show the updated progress
        if live_display.is_started:
            live_display.refresh()


def complete_progress(task_id: str, description: str | None = None) -> None:
    """Mark a progress bar task as complete.

    Args:
        task_id: Identifier for the task
        description: Final description for the completed task
    """
    with progress_lock:
        if task_id not in _active_tasks:
            logger.warning("Attempted to complete non-existent progress task: %s", task_id)
            return

        progress_task_id = _active_tasks[task_id]

        # Update description if provided
        if description is not None:
            progress.update(progress_task_id, description=description)

        # Mark as completed
        progress.update(progress_task_id, completed=progress.tasks[progress_task_id].total)

        # Refresh the display to show the completed task
        if live_display.is_started:
            live_display.refresh()

        # Remove from active tasks
        del _active_tasks[task_id]

        # Stop live display if no active tasks
        if not _active_tasks and live_display.is_started:
            stop_live_display()
