"""Telnet protocol negotiation helper class."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .types import NegotiationResponse, ParserState, TelnetCommand, TelnetOption, TelnetSequence

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(slots=True)
class TelnetNegotiator:
    """Helper class to handle telnet protocol negotiations."""

    # Default terminal settings
    terminal_type: str = field(default="VT100")
    window_width: int = field(default=132)  # Wide terminal to avoid pagination
    window_height: int = field(default=100)  # Tall terminal to avoid pagination

    # Tracking negotiated options
    our_options: dict[int, bool] = field(default_factory=dict)
    their_options: dict[int, bool] = field(default_factory=dict)

    # Option handlers by option code
    _option_handlers: dict[int, Callable] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        """Initialise option handlers and default settings."""
        # Setup special option handlers
        self._option_handlers[TelnetOption.TERMINAL_TYPE] = self._handle_terminal_type
        self._option_handlers[TelnetOption.NAWS] = self._handle_window_size

    def handle_command(self, data: bytes) -> tuple[bytes, list[bytes]]:
        """Process telnet commands from received data.

        Args:
            data: Raw bytes received from the telnet server

        Returns:
            Tuple containing (processed_data, responses_to_send)
        """
        if not data:
            return b"", []

        processed = bytearray()
        responses = []

        # Use a state machine to parse the data
        state = ParserState.DATA
        cmd = 0
        opt = 0
        subneg_option = 0
        subneg_data = bytearray()

        for byte in data:
            match state:
                case ParserState.DATA:
                    # Processing regular data
                    if byte == TelnetCommand.IAC:
                        state = ParserState.IAC
                    else:
                        processed.append(byte)

                case ParserState.IAC:
                    # Received IAC, expecting a command
                    match byte:
                        case TelnetCommand.IAC:
                            # Escaped IAC - literal 255
                            processed.append(byte)
                            state = ParserState.DATA
                        case TelnetCommand.SB:
                            state = ParserState.SUBNEG
                            subneg_data = bytearray()
                            # Next byte will be the option
                        case _ if TelnetCommand.is_negotiation(byte):
                            # Negotiation command (DO/DONT/WILL/WONT)
                            cmd = byte
                            state = ParserState.COMMAND
                        case _:
                            # Unknown command, ignore
                            state = ParserState.DATA

                case ParserState.COMMAND:
                    # Got the option for a command
                    opt = byte
                    responses.append(self._handle_negotiation(cmd, opt))
                    state = ParserState.DATA

                case ParserState.SUBNEG:
                    # Inside subnegotiation
                    if byte == TelnetCommand.IAC:
                        state = ParserState.SUBNEG_IAC
                    elif not subneg_data:
                        # First byte is the option
                        subneg_option = byte
                    else:
                        # Data part of subnegotiation
                        subneg_data.append(byte)

                case ParserState.SUBNEG_IAC:
                    match byte:
                        case TelnetCommand.SE:
                            # End of subnegotiation
                            subneg_response = self._handle_subnegotiation(subneg_option, bytes(subneg_data))
                            if subneg_response:
                                responses.append(subneg_response)
                            state = ParserState.DATA
                        case _:
                            # Escaped IAC within subnegotiation
                            subneg_data.append(TelnetCommand.IAC)
                            subneg_data.append(byte)
                            state = ParserState.SUBNEG

        return bytes(processed), responses

    def _handle_negotiation(self, cmd: int, option: int) -> bytes:
        """Process a single telnet negotiation command.

        This consolidated method handles all negotiation commands (DO/DONT/WILL/WONT)
        and updates the appropriate option tracking.

        Args:
            cmd: The telnet command (DO/DONT/WILL/WONT)
            option: The option being negotiated

        Returns:
            The response to send to the server
        """
        # Check if we have a special handler for this option
        if option in self._option_handlers:
            return self._option_handlers[option](option, cmd)

        # Handle based on command type and option
        match cmd:
            case TelnetCommand.DO | TelnetCommand.WILL:
                # Server is asking us to enable an option (DO)
                # or announcing it will enable an option (WILL)
                if self._should_accept_option(option, cmd):
                    # We'll accept this option
                    self._update_option_state(option, cmd, True)
                    return NegotiationResponse.accept(cmd, option)
                # We'll reject this option
                self._update_option_state(option, cmd, False)
                return NegotiationResponse.reject(cmd, option)
            case _:  # DONT or WONT
                # Server is asking us to disable an option (DONT)
                # or announcing it won't enable an option (WONT)
                self._update_option_state(option, cmd, False)
                return NegotiationResponse.accept(cmd, option)

    def _should_accept_option(self, option: int, cmd: int) -> bool:
        """Determine if we should accept an option.

        Args:
            option: The option being negotiated
            cmd: The command (DO/WILL)

        Returns:
            True if we should accept the option, False otherwise
        """
        # We accept common options
        if option in TelnetOption.get_common_options():
            return True

        # We accept advanced options we specifically support
        return bool(option in TelnetOption.get_advanced_options())

    def _update_option_state(self, option: int, cmd: int, enabled: bool) -> None:
        """Update the option state based on the command.

        Args:
            option: The option being negotiated
            cmd: The command (DO/DONT/WILL/WONT)
            enabled: Whether the option should be enabled or disabled
        """
        match cmd:
            case TelnetCommand.DO | TelnetCommand.DONT:
                # These affect our options (what we do)
                self.our_options[option] = enabled
            case _:  # WILL or WONT
                # These affect their options (what they do)
                self.their_options[option] = enabled

    def _handle_subnegotiation(self, option: int, data: bytes) -> bytes:
        """Handle subnegotiation request.

        Args:
            option: The option being negotiated
            data: The subnegotiation data

        Returns:
            The response to send to the server
        """
        # Check if we have a special handler for this option
        if option in self._option_handlers and data:
            return self._option_handlers[option](option, TelnetCommand.SB, data)
        return b""

    def _handle_terminal_type(self, option: int, cmd: int, data: bytes = b"") -> bytes:
        """Handle terminal type option negotiation.

        Args:
            option: The option being negotiated
            cmd: The command (DO/WILL/SB)
            data: The subnegotiation data (for SB)

        Returns:
            The response to send to the server
        """
        match cmd:
            case TelnetCommand.DO:
                # Server is asking if we can send terminal type
                self.our_options[option] = True
                return TelnetSequence.create_command(TelnetCommand.WILL, option)
            case TelnetCommand.SB if data and data[0] == 1:
                # Server is asking for terminal type (SEND)
                response = bytearray([0])  # IS
                response.extend(self.terminal_type.encode("ascii"))
                return TelnetSequence.create_subnegotiation(option, bytes(response))
        return b""

    def _handle_window_size(self, option: int, cmd: int, data: bytes = b"") -> bytes:
        """Handle window size option negotiation.

        Args:
            option: The option being negotiated
            cmd: The command (DO/WILL/SB)
            data: The subnegotiation data (for SB)

        Returns:
            The response to send to the server
        """
        if cmd == TelnetCommand.DO:
            # Server is asking if we can send window size
            self.our_options[option] = True

            # Send WILL followed by the actual window size
            will_resp = TelnetSequence.create_command(TelnetCommand.WILL, option)
            naws_resp = self._send_window_size()
            return will_resp + naws_resp
        return b""

    def _send_window_size(self) -> bytes:
        """Send window size information.

        Returns:
            The response to send to the server
        """
        # Pack width and height into 4 bytes
        window_data = bytes([
            (self.window_width >> 8) & 0xFF,
            self.window_width & 0xFF,
            (self.window_height >> 8) & 0xFF,
            self.window_height & 0xFF,
        ])
        return TelnetSequence.create_subnegotiation(TelnetOption.NAWS, window_data)

    @staticmethod
    def get_initial_negotiation() -> bytes:
        """Return the initial negotiation sequence to send when connecting."""
        # We request these options by default
        negotiations = bytearray()
        # Suppress Go Ahead - we'll always do this
        negotiations.extend(TelnetSequence.create_command(TelnetCommand.WILL, TelnetOption.SGA))
        negotiations.extend(TelnetSequence.create_command(TelnetCommand.DO, TelnetOption.SGA))
        # We'll handle echo based on server preference - most telnet servers do echo
        negotiations.extend(TelnetSequence.create_command(TelnetCommand.WONT, TelnetOption.ECHO))
        # Announce we're willing to negotiate terminal type
        negotiations.extend(TelnetSequence.create_command(TelnetCommand.WILL, TelnetOption.TERMINAL_TYPE))
        # Announce we're willing to negotiate window size
        negotiations.extend(TelnetSequence.create_command(TelnetCommand.WILL, TelnetOption.NAWS))
        # Return the initial negotiation sequence
        return bytes(negotiations)
