"""Tests for PacketDyscomInit"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

from science_mode_4.dyscom.dyscom_init import PacketDyscomInit, PacketDyscomInitAck
from science_mode_4.dyscom.dyscom_types import DyscomInitParams
from science_mode_4.protocol.commands import Commands
from science_mode_4.protocol.packet_factory import PacketFactory


def test_packets_without_params_do_not_share_params_instance():
    # regression test: the default argument "params = DyscomInitParams()" was evaluated only
    # once, so all packets created without params shared (and mutated) the same instance
    a = PacketDyscomInit()
    b = PacketDyscomInit()

    assert a.params is not b.params

    a.params.proband_name = "changed"
    assert b.params.proband_name == ""


def test_packet_factory_prototype_does_not_share_params_with_created_packets():
    factory = PacketFactory()
    packet = factory.create_packet(Commands.DL_INIT)

    packet.params.proband_name = "changed"

    assert factory.create_packet(Commands.DL_INIT).params.proband_name == ""


def test_packet_uses_given_params_instance():
    params = DyscomInitParams()
    assert PacketDyscomInit(params).params is params


def test_ack_without_data_has_empty_measurement_file_id():
    # regression test: _measurement_file_id was only annotated, not assigned, so accessing
    # measurement_file_id of an ack without data (e.g. packet factory prototype) raised AttributeError
    assert PacketDyscomInitAck(None).measurement_file_id == ""
