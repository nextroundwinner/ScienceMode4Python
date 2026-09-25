"""Tests for PacketBuffer"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

from science_mode_4.protocol.commands import Commands
from science_mode_4.protocol.packet_factory import PacketFactory
from science_mode_4.protocol.protocol import Protocol
from science_mode_4.protocol.types import ResultAndError
from science_mode_4.utils.connection import Connection
from science_mode_4.utils.packet_buffer import PacketBuffer


class _WirePacket:
    """Duck-typed packet with settable command/payload, used to build raw wire bytes.
    Deliberately does NOT subclass Packet: PacketFactory auto-registers every
    Packet subclass that exists in the process (via __subclasses__()), so a real
    subclass here would need to be instantiable with no args and would pollute
    the shared (command, kind) registry used by other tests."""

    def __init__(self, command: Commands, payload: bytes):
        self.command = command
        self.number = 0
        self._payload = payload

    def get_data(self) -> bytes:
        return self._payload


class _FakeConnection(Connection):
    """Connection that returns a fixed buffer once and stays empty afterwards"""

    def __init__(self, data: bytes):
        self._data = data

    def open(self):
        pass

    def close(self):
        pass

    def is_open(self) -> bool:
        return True

    def clear_buffer(self):
        self._data = b""

    def _read_intern(self) -> bytes:
        result, self._data = self._data, b""
        return result


def _build_reset_ack_bytes() -> bytes:
    # payload of 1 byte -> encoded packet is longer than the minimal 12 byte packet,
    # so this test only exercises the buffer trimming, not the (separate) minimal
    # packet length handling in Protocol.find_packet_in_buffer
    packet = _WirePacket(Commands.RESET_ACK, bytes([ResultAndError.NO_ERROR.value]))
    return Protocol.packet_to_bytes(packet)


def test_get_packet_from_buffer_keeps_bytes_after_packet_with_leading_garbage():
    # regression test for a bug where PacketBuffer._buffer was trimmed by
    # "start + stop + 1" instead of "stop + 1" (start/stop are already absolute
    # indices into the buffer), which drops bytes belonging to the next packet
    # whenever the found packet does not start at index 0
    packet_bytes = _build_reset_ack_bytes()
    leading_garbage = bytes([0xAA, 0xBB, 0xCC])
    trailing_bytes = bytes([0xDD, 0xEE])

    buffer = leading_garbage + packet_bytes + trailing_bytes
    connection = _FakeConnection(buffer)
    packet_buffer = PacketBuffer(connection, PacketFactory())

    ack = packet_buffer.get_packet_from_buffer()

    assert ack is not None
    assert ack.command == Commands.RESET_ACK
    assert ack.result_error == ResultAndError.NO_ERROR
    # bytes belonging to the *next* packet must be preserved, not swallowed
    assert packet_buffer.buffer == trailing_bytes


def test_get_packet_from_buffer_without_leading_garbage_still_works():
    # the previous (buggy) offset happened to be correct when start == 0,
    # make sure the fix keeps that case working
    packet_bytes = _build_reset_ack_bytes()
    trailing_bytes = bytes([0x11, 0x22, 0x33])

    buffer = packet_bytes + trailing_bytes
    connection = _FakeConnection(buffer)
    packet_buffer = PacketBuffer(connection, PacketFactory())

    ack = packet_buffer.get_packet_from_buffer()

    assert ack is not None
    assert packet_buffer.buffer == trailing_bytes
