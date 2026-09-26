"""Tests for Device capabilities handling"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

from science_mode_4.device import Device, DeviceCapability
from science_mode_4.utils.null_connection import NullConnection


def test_capabilities_accepts_a_real_set():
    # regression test: capabilities was type-hinted as set[DeviceCapability] but the
    # constructor did "capabilities + [DeviceCapability.GENERAL]", which raises
    # TypeError for an actual set ("unsupported operand type(s) for +: 'set' and
    # 'list'") and only worked because every caller happened to pass a list instead
    device = Device(NullConnection(), {DeviceCapability.LOW_LEVEL, DeviceCapability.MID_LEVEL})

    assert isinstance(device.capabilities, set)
    assert device.capabilities == {DeviceCapability.GENERAL, DeviceCapability.LOW_LEVEL, DeviceCapability.MID_LEVEL}


def test_capabilities_always_returns_a_real_set_even_from_list_input():
    device = Device(NullConnection(), [DeviceCapability.DYSCOM])

    assert isinstance(device.capabilities, set)
    assert device.capabilities == {DeviceCapability.GENERAL, DeviceCapability.DYSCOM}


def test_capabilities_deduplicates_general_if_passed_explicitly():
    device = Device(NullConnection(), {DeviceCapability.GENERAL, DeviceCapability.DYSCOM})

    assert device.capabilities == {DeviceCapability.GENERAL, DeviceCapability.DYSCOM}
