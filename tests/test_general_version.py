"""Tests for PacketGeneralGetExtendedVersionAck"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

from science_mode_4.general.general_types import GeneralHashType
from science_mode_4.general.general_version import PacketGeneralGetExtendedVersionAck
from science_mode_4.protocol.packet import Packet


def test_extended_version_ack_parses_hash_as_hex_string_and_hash_type_as_enum():
    data = bytes([0, 2, 0, 0, 4, 0, 0]) + bytes.fromhex("085510cd") + bytes([GeneralHashType.GIT, 1])
    ack = PacketGeneralGetExtendedVersionAck(data)

    assert ack.firmware_version == "2.0.0"
    assert ack.science_mode_version == "4.0.0"
    assert ack.firmware_hash == "85510cd"
    assert ack.hash_type is GeneralHashType.GIT
    assert ack.is_valid_hash


def test_extended_version_ack_without_data_has_empty_hash_string():
    # firmware_hash is a hex string, the default was int 0 before
    assert PacketGeneralGetExtendedVersionAck(None).firmware_hash == ""


def test_packet_base_get_data_returns_bytes():
    assert Packet().get_data() == b""
