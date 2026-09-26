"""Tests for PacketGeneralGetDeviceIdAck"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

from science_mode_4.general.general_device_id import PacketGeneralGetDeviceIdAck
from science_mode_4.protocol.types import ResultAndError


def _build_data(result_error: int, device_id: str) -> bytes:
    return bytes([result_error]) + device_id.encode().ljust(10, b"\x00")


def test_device_id_strips_null_padding():
    # regression test: data[1:11].decode() used to include the null padding bytes
    # verbatim, so a device id shorter than 10 chars came back with a trailing "\x00"
    ack = PacketGeneralGetDeviceIdAck(_build_data(0, "220824001"))
    assert ack.device_id == "220824001"
    assert "\x00" not in ack.device_id


def test_device_id_uses_full_field_when_not_null_terminated():
    ack = PacketGeneralGetDeviceIdAck(_build_data(0, "1234567890"))
    assert ack.device_id == "1234567890"


def test_result_error_is_parsed():
    ack = PacketGeneralGetDeviceIdAck(_build_data(1, "220824001"))
    assert ack.result_error == ResultAndError.TRANSFER_ERROR


def test_device_id_defaults_to_empty_string_without_data():
    ack = PacketGeneralGetDeviceIdAck(None)
    assert ack.device_id == ""
    assert ack.result_error == ResultAndError.NO_ERROR
