"""Tests for bit-flag decoding in dyscom battery status and live data packets"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

import struct

from science_mode_4.dyscom.dyscom_get_battery_status import PacketDyscomGetAckBatteryStatus
from science_mode_4.dyscom.dyscom_send_live_data import PacketDyscomSendLiveData
from science_mode_4.dyscom.dyscom_types import DyscomEnergyFlag, DyscomPowerLiveDataStatusFlag, DyscomSignalType


def _build_battery_status_data(energy_state: int) -> bytes:
    return bytes([0, 0]) + struct.pack("<BBbiI", energy_state, 50, 20, 100, 3700)


def test_battery_status_decodes_no_flags():
    # regression test: "energy_state & (1 << f) == 1" used to never match any
    # flag except by coincidence, since it shifted by the flag's own value
    # instead of testing the flag's bits directly
    packet = PacketDyscomGetAckBatteryStatus(_build_battery_status_data(0))
    assert packet.energy_state == set()


def test_battery_status_decodes_single_flag():
    packet = PacketDyscomGetAckBatteryStatus(_build_battery_status_data(int(DyscomEnergyFlag.CABLE_CONNECTED)))
    assert packet.energy_state == {DyscomEnergyFlag.CABLE_CONNECTED}


def test_battery_status_decodes_combined_flags():
    combined = int(DyscomEnergyFlag.CABLE_CONNECTED) | int(DyscomEnergyFlag.DEVICE_IS_LOADING)
    packet = PacketDyscomGetAckBatteryStatus(_build_battery_status_data(combined))
    assert packet.energy_state == {DyscomEnergyFlag.CABLE_CONNECTED, DyscomEnergyFlag.DEVICE_IS_LOADING}


def _build_live_data(status: int) -> bytes:
    data = bytes([1]) + (0).to_bytes(4, "big")
    data += struct.pack(">f", 1.23) + bytes([int(DyscomSignalType.EMG_1), status])
    return data


def test_live_data_decodes_no_status_flags():
    packet = PacketDyscomSendLiveData(_build_live_data(0))
    assert packet.samples[0].status == set()


def test_live_data_decodes_single_status_flag():
    packet = PacketDyscomSendLiveData(_build_live_data(int(DyscomPowerLiveDataStatusFlag.POSITIVE_ELECTRODE_ADHESIVE)))
    assert packet.samples[0].status == {DyscomPowerLiveDataStatusFlag.POSITIVE_ELECTRODE_ADHESIVE}


def test_live_data_decodes_both_electrodes_status():
    packet = PacketDyscomSendLiveData(_build_live_data(int(DyscomPowerLiveDataStatusFlag.BOTH_ELECTRODES_ADHESIVE)))
    assert packet.samples[0].status == {
        DyscomPowerLiveDataStatusFlag.POSITIVE_ELECTRODE_ADHESIVE,
        DyscomPowerLiveDataStatusFlag.NEGATIVE_ELECTRODE_ADHESIVE,
        DyscomPowerLiveDataStatusFlag.BOTH_ELECTRODES_ADHESIVE,
    }
