"""Command line argument parser for network tools.

This module provides a configurable and extensible argument parser for
command line interfaces built with the network tools package. It includes
common network-related arguments and allows for command-specific subparsers.
"""

from __future__ import annotations

from argparse import (
    ArgumentParser,
    Namespace as Arguments,
    RawDescriptionHelpFormatter as Formatter,
)
from sys import argv as sys_argv, exit as sys_exit

from network_tools.constants import (
    CLI_ARGUMENTS,
    CLI_HELP_DESCRIPTION,
    CLI_HELP_EPILOGUE,
    CLI_HELP_NAME,
)

from .console import log


def parse_args() -> Arguments:
    """Create a standard argument parser with common network tool arguments.

    Args:
        description: Description of the tool
        epilog: Text to display after the argument help
        prog: The name of the program

    Returns:
        Configured ArgumentParser instance
    """
    # Create the parser
    parser = ArgumentParser(
        description=CLI_HELP_DESCRIPTION,
        epilog=CLI_HELP_EPILOGUE,
        prog=CLI_HELP_NAME,
        formatter_class=Formatter,
    )
    # Add groups and arguments
    for category_name, args in CLI_ARGUMENTS.items():
        category = parser.add_argument_group(category_name)
        [category.add_argument(*flags, **kwargs) for flags, kwargs in args]

    # Check if no arguments are provided
    if len(sys_argv) == 1:
        parser.print_help()
        sys_exit(0)

    # Run the parser
    parsed_args = parser.parse_args(sys_argv[1:])

    # Handle verbosity
    if parsed_args.verbose >= 2:  # noqa: PLR2004
        log.setLevel("DEBUG")
    elif parsed_args.verbose == 1:
        log.setLevel("INFO")
    else:
        log.setLevel("WARNING")

    # Return the parsed arguments
    return parsed_args
