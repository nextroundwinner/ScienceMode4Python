"""Tests for PacketBuffer"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

import logging

import pytest

from science_mode_4.device_p24 import DeviceP24
from science_mode_4.dyscom.dyscom_send_file import PacketDyscomSendFileAck
from science_mode_4.protocol.commands import Commands
from science_mode_4.protocol.exceptions import ProtocolError
from science_mode_4.protocol.packet_factory import PacketFactory
from science_mode_4.protocol.protocol import Protocol
from science_mode_4.protocol.types import ResultAndError
from science_mode_4.utils.connection import Connection
from science_mode_4.utils.null_connection import NullConnection
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


def _open_acknowledges(packet_buffer: PacketBuffer) -> dict[tuple[int, int], int]:
    return dict(packet_buffer._open_acknowledges) # pylint: disable=protected-access


def test_low_level_send_functions_register_one_open_acknowledge_per_packet():
    # regression test: send_init/send_channel_config/send_stop called add_open_acknowledge
    # although ProtocolHelper.send_packet already does, so every packet was counted twice
    device = DeviceP24(NullConnection())
    device.get_layer_low_level().send_stop()

    assert _open_acknowledges(device.packet_buffer) == {(Commands.LOW_LEVEL_STOP_ACK, 1): 1}


def test_send_file_ack_registers_no_open_acknowledge():
    # regression test: DL_SEND_FILE_ACK registered an expected acknowledge for command + 1
    # (DL_SYS), which device never sends, so one stale entry piled up per file block
    packet_buffer = PacketBuffer(_FakeConnection(b""), PacketFactory())
    packet_buffer.add_open_acknowledge(PacketDyscomSendFileAck(1))

    assert not _open_acknowledges(packet_buffer)


def test_received_acknowledge_removes_open_entry():
    packet_buffer = PacketBuffer(_FakeConnection(_build_reset_ack_bytes()), PacketFactory())
    packet_buffer.add_open_acknowledge(_WirePacket(Commands.RESET, b""))

    assert packet_buffer.get_packet_from_buffer() is not None
    assert not _open_acknowledges(packet_buffer)


def test_duplicate_acknowledge_is_reported_as_unexpected_and_does_not_go_negative(caplog):
    # regression test: an entry already at 0 is not None, so a duplicate acknowledge
    # decremented it to -1 instead of logging it as unexpected
    packet_bytes = _build_reset_ack_bytes()
    packet_buffer = PacketBuffer(_FakeConnection(packet_bytes + packet_bytes), PacketFactory())
    packet_buffer.add_open_acknowledge(_WirePacket(Commands.RESET, b""))

    packet_buffer.get_packet_from_buffer()
    with caplog.at_level(logging.WARNING, logger="science_mode_4"):
        packet_buffer.get_packet_from_buffer(False)

    assert not _open_acknowledges(packet_buffer)
    assert any("Unexpected acknowledge" in r.getMessage() for r in caplog.records)


def test_remove_open_acknowledge_removes_entry_and_raises_if_not_open():
    packet_buffer = PacketBuffer(_FakeConnection(b""), PacketFactory())
    packet = _WirePacket(Commands.RESET, b"")
    packet_buffer.add_open_acknowledge(packet)
    packet_buffer.add_open_acknowledge(packet)

    packet_buffer.remove_open_acknowledge(packet)
    assert _open_acknowledges(packet_buffer) == {(Commands.RESET_ACK, 0): 1}

    packet_buffer.remove_open_acknowledge(packet)
    assert not _open_acknowledges(packet_buffer)

    with pytest.raises(ProtocolError):
        packet_buffer.remove_open_acknowledge(packet)
