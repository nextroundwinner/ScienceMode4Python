"""Tests for Protocol"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

from science_mode_4.protocol.commands import Commands
from science_mode_4.protocol.protocol import Protocol


class _WirePacket:
    """Duck-typed packet with settable command/payload, used to build raw wire bytes"""

    def __init__(self, command: Commands, payload: bytes):
        self.command = command
        self.number = 0
        self._payload = payload

    def get_data(self) -> bytes:
        return self._payload


def test_find_packet_in_buffer_finds_minimal_length_packet():
    # regression test: a packet with an empty payload (just command + number,
    # unstuffed) encodes to exactly 12 bytes: 1 start + 4 length + 4 crc +
    # 2 payload + 1 stop. find_packet_in_buffer used to start searching for
    # the stop byte at "start + 12", one past where it actually sits (relative
    # offset 11), so this minimal packet was never found and callers waiting
    # for e.g. an empty-payload ack would time out even though it arrived.
    packet_bytes = Protocol.packet_to_bytes(_WirePacket(Commands.RESET, b""))
    assert len(packet_bytes) == 12
    assert Protocol.is_valid_packet_data(packet_bytes)

    result = Protocol.find_packet_in_buffer(packet_bytes)

    assert result == (0, len(packet_bytes) - 1)


def test_find_packet_in_buffer_finds_minimal_length_packet_with_leading_garbage():
    packet_bytes = Protocol.packet_to_bytes(_WirePacket(Commands.RESET, b""))
    leading_garbage = bytes([0xAA, 0xBB])
    buffer = leading_garbage + packet_bytes

    result = Protocol.find_packet_in_buffer(buffer)

    assert result == (len(leading_garbage), len(buffer) - 1)


def test_find_packet_in_buffer_finds_non_minimal_packet():
    packet_bytes = Protocol.packet_to_bytes(_WirePacket(Commands.RESET, bytes([0x01, 0x02, 0x03])))

    result = Protocol.find_packet_in_buffer(packet_bytes)

    assert result == (0, len(packet_bytes) - 1)
