"""Telnet protocol types module."""

from __future__ import annotations

from enum import IntEnum
from typing import NamedTuple

IAC_BYTE = 0xFF  # Interpret As Command byte


class ParserState(IntEnum):
    """States for the telnet parser state machine."""

    DATA = 0
    IAC = 1
    COMMAND = 2
    SUBNEG = 3
    SUBNEG_IAC = 4


class TelnetCommand(IntEnum):
    """Telnet protocol commands."""

    IAC = 255  # Interpret As Command
    DONT = 254
    DO = 253
    WONT = 252
    WILL = 251
    SB = 250  # Subnegotiation Begin
    SE = 240  # Subnegotiation End

    @classmethod
    def is_negotiation(cls, cmd: int) -> bool:
        """Check if a command byte is a negotiation command.

        Returns:
            True if the command is a negotiation command, False otherwise
        """
        return cmd in {cls.DO, cls.DONT, cls.WILL, cls.WONT}

    @classmethod
    def get_response_command(cls, cmd: int) -> int:
        """Get the appropriate response command for a negotiation request.

        Returns:
            The appropriate response command
        """
        return {
            cls.DO: cls.WILL,  # Respond to DO with WILL
            cls.DONT: cls.WONT,  # Respond to DONT with WONT
            cls.WILL: cls.DO,  # Respond to WILL with DO
            cls.WONT: cls.DONT,  # Respond to WONT with DONT
        }.get(cmd, 0)


class TelnetOption(IntEnum):
    """Telnet protocol options."""

    BINARY = 0
    ECHO = 1
    SGA = 3  # Suppress Go Ahead
    STATUS = 5
    TIMING_MARK = 6
    TERMINAL_TYPE = 24
    NAWS = 31  # Negotiate About Window Size
    TERMINAL_SPEED = 32
    LINEMODE = 34
    NEW_ENVIRON = 39

    @classmethod
    def is_supported(cls, option: int) -> bool:
        """Check if an option is supported by our implementation.

        Returns:
            True if the option is supported, False otherwise
        """
        return option in {
            cls.BINARY,
            cls.ECHO,
            cls.SGA,
            cls.TERMINAL_TYPE,
            cls.NAWS,
        }

    @classmethod
    def get_common_options(cls) -> list[int]:
        """Get list of commonly supported options.

        Returns:
            List of commonly supported options
        """
        return [cls.SGA, cls.ECHO, cls.BINARY]

    @classmethod
    def get_advanced_options(cls) -> list[int]:
        """Get list of advanced options we support.

        Returns:
            List of advanced options
        """
        return [cls.TERMINAL_TYPE, cls.NAWS]


class TelnetSequence(NamedTuple):
    """Represents a complete telnet command sequence."""

    command: int
    option: int = 0
    data: bytes = b""

    @classmethod
    def create_command(cls, command: int, option: int) -> bytes:
        """Create a simple telnet command sequence.

        Returns:
            The created command sequence
        """
        return bytes([TelnetCommand.IAC, command, option])

    @classmethod
    def create_subnegotiation(cls, option: int, data: bytes) -> bytes:
        """Create a telnet subnegotiation sequence.

        Returns:
            The created subnegotiation sequence
        """
        result = bytearray([TelnetCommand.IAC, TelnetCommand.SB, option])
        result.extend(data)
        result.extend([TelnetCommand.IAC, TelnetCommand.SE])
        return bytes(result)


class NegotiationResponse:
    """Helper class for building negotiation responses."""

    @staticmethod
    def accept(command: int, option: int) -> bytes:
        """Accept a negotiation by responding positively.

        This follows the telnet protocol standard by responding with:
        - WILL in response to DO
        - DO in response to WILL
        - WONT in response to DONT
        - DONT in response to WONT

        Args:
            command: The received command (DO, DONT, WILL, WONT)
            option: The option being negotiated

        Returns:
            The appropriate acceptance response
        """
        resp_cmd = TelnetCommand.get_response_command(command)
        return TelnetSequence.create_command(resp_cmd, option)

    @staticmethod
    def reject(command: int, option: int) -> bytes:
        """Reject a negotiation by responding negatively.

        This follows the telnet protocol standard by responding with:
        - WONT in response to DO
        - DONT in response to WILL

        Args:
            command: The received command (DO, DONT, WILL, WONT)
            option: The option being negotiated

        Returns:
            The appropriate rejection response
        """
        if command == TelnetCommand.DO:
            return TelnetSequence.create_command(TelnetCommand.WONT, option)
        if command == TelnetCommand.WILL:
            return TelnetSequence.create_command(TelnetCommand.DONT, option)
        # For DONT and WONT, we agree (standard protocol behavior)
        return NegotiationResponse.accept(command, option)
