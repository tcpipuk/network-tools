# Console output

A simple but powerful way to display logs and progress bars in your terminal.

- [What it does](#what-it-does)
- [How to use it](#how-to-use-it)
  - [Show log messages](#show-log-messages)
  - [Show progress bars](#show-progress-bars)
  - [Track multiple tasks at once](#track-multiple-tasks-at-once)
- [Available functions](#available-functions)
  - [Core components](#core-components)
  - [Progress tracking](#progress-tracking)
- [Technical details](#technical-details)

## What it does

This module helps you:

- show log messages above progress bars
- keep progress bars at the bottom of the screen
- format text with colours and styles
- track multiple tasks at once

It's built on [Rich](https://github.com/Textualize/rich), which provides text formatting in the terminal.

## How to use it

### Show log messages

```python
from network_tools.console import log

# Use standard logging levels
log.debug("Technical details for troubleshooting")
log.info("General information")
log.warning("Something needs attention")
log.error("Something went wrong")
log.critical("Urgent problem")
```

You can create your own logger too:

```python
from logging import getLogger
from network_tools.console import console

my_logger = getLogger("my_module")
my_logger.info("This will appear with Rich formatting")
```

For direct output with formatting:

```python
from network_tools.console import console

console.print("[bold]Note:[/bold] This uses Rich formatting")
console.print("Status: [green]OK[/green]")
```

### Show progress bars

```python
from network_tools.console import create_progress, update_progress, complete_progress
import time

# Start tracking progress
task_id = create_progress("Processing network devices", total=10)

# Update as you go
for i in range(10):
    # Do some work
    time.sleep(0.5)

    # Log information during progress
    log.info("Processing device %d/10", i+1)

    # Update the progress bar
    update_progress(task_id, advance=1, description=f"Processing device {i+1}/10")

# Mark as finished
complete_progress(task_id, description="All devices processed")
```

### Track multiple tasks at once

```python
import asyncio
from network_tools.console import create_progress, update_progress, complete_progress
from network_tools.console import log

async def process_device(device_id, total_steps):
    # Create a progress bar for this device
    task_id = create_progress(f"Device {device_id}", total=total_steps)

    for step in range(total_steps):
        # Do some work
        await asyncio.sleep(0.2)

        # Log occasionally
        if step % 3 == 0:
            log.info("Device %d: Processing step %d/%d", device_id, step+1, total_steps)

        # Update progress
        update_progress(task_id, advance=1,
                       description=f"Device {device_id}: Step {step+1}/{total_steps}")

    # Mark as complete
    complete_progress(task_id, description=f"Device {device_id}: Complete")

async def main():
    # Process multiple devices at the same time
    await asyncio.gather(
        process_device(1, 5),
        process_device(2, 8),
        process_device(3, 3)
    )

# Run the async main function
asyncio.run(main())
```

## Available functions

### Core components

- `console`: for direct output
- `log`: for log messages
- `progress`: for creating progress bars
- `live_display`: manages both logs and progress bars

### Progress tracking

- `create_progress(description, total=100, task_id=None)`: starts a new progress bar
- `update_progress(task_id, advance=None, completed=None, description=None, **kwargs)`: updates progress
- `complete_progress(task_id, description=None)`: marks a task as finished
- `start_live_display()`: starts the display (called automatically)
- `stop_live_display()`: stops the display (called automatically)

## Technical details

The module:

- works safely with multiple threads
- makes sure logs appear above progress bars
- prevents issues when multiple things update at once
- uses Rich's `Live` display and a custom `LiveDisplayHandler`

You can customise the appearance by modifying the `Progress` instance. The current setup shows:

- a spinner for active tasks
- description text in blue
- a progress bar
- percentage complete
- time elapsed and remaining

For more options, see the [Rich documentation](https://rich.readthedocs.io/en/latest/progress.html).
