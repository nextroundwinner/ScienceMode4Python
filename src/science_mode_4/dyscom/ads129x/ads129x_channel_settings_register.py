"""Provides class for ADS129x chip channel settings register"""

from dataclasses import dataclass
from enum import IntEnum


class Ads129xChannelPowerMode(IntEnum):
    """Represent ADS129xtype for power mode (channel settings register, 0x05 to 0x0C)"""
    NORMAL_OPERATION = 0
    CHANNEL_POWER_DOWN = 1


class Ads129xChannelGain(IntEnum):
    """Represent ADS129xtype for channel gain (channel settings register, 0x05 to 0x0C)"""
    GAIN_1 = 1
    GAIN_2 = 2
    GAIN_3 = 3
    GAIN_4 = 4
    GAIN_6 = 0
    GAIN_8 = 5
    GAIN_12 = 6


class Ads129xChannelInput(IntEnum):
    """Represent ADS129xtype for channel input (channel settings register, 0x05 to 0x0C)"""
    NORMAL_ELECTRODE_INPUT = 0
    INPUT_SHORTED = 1
    CONJUNCTION_WITH_RLD_MEAS = 2 # Used in conjunction with RLD_MEAS bit for RLD measurements
    MVDD_FOR_SUPPLY_MEASUREMENT = 3
    TEMPERATURE_SENSOR = 4
    TEST_SIGNAL = 5
    RLD_DRP = 6 # RLD_DRP (positive electrode is the driver)
    RLD_DRN = 7 # RLD_DRN (negative electrode is the driver)


@dataclass
class Ads129xChannelSettingsRegister:
    """Describes a channel settings register of ADS129x chip"""

    power_mode: Ads129xChannelPowerMode = Ads129xChannelPowerMode.NORMAL_OPERATION
    gain: Ads129xChannelGain = Ads129xChannelGain.GAIN_6
    input: Ads129xChannelInput = Ads129xChannelInput.NORMAL_ELECTRODE_INPUT

    def set_data(self, data: bytes):
        """Convert data to information"""
        tmp = data[0]
        self.power_mode = Ads129xChannelPowerMode((tmp >> 7) & 0x01)
        self.gain = Ads129xChannelGain((tmp >> 4) & 0x07)
        self.input = Ads129xChannelInput((tmp >> 0) & 0x07)


    def get_data(self) -> bytes:
        """Convert information to bytes"""
        tmp = ((self.power_mode << 7) | (self.gain << 4) | (self.input << 0))
        return [tmp]
