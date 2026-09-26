"""Provides class for ADS129x chip config register 1"""

from dataclasses import dataclass
from enum import IntEnum


class Ads129xPowerMode(IntEnum):
    """Represent ADS129xtype for power mode (configuration register 1, 0x01)"""
    LOW_POWER = 0
    HIGH_RESOLUTION = 1


class Ads129xReadMode(IntEnum):
    """Represent ADS129xtype for read mode (configuration register 1, 0x01)"""
    DAISY_CHAIN = 0
    MULTIPLE_READBACK = 1


class Ads129xClockConnection(IntEnum):
    """Represent ADS129xtype for clock connection (configuration register 1, 0x01)"""
    OSCILLATOR_CLOCK_OUTPUT_DISABLED = 0
    OSCILLATOR_CLOCK_OUTPUT_ENABLED = 1


class Ads129xOutputDataRate(IntEnum):
    """Represent ADS129xtype for output data rate (configuration register 1, 0x01)"""
    HR_MODE_32_KSPS__LP_MODE_16_KSPS = 0
    HR_MODE_16_KSPS__LP_MODE_8_KSPS = 1
    HR_MODE_8_KSPS__LP_MODE_4_KSPS = 2
    HR_MODE_4_KSPS__LP_MODE_2_KSPS = 3
    HR_MODE_2_KSPS__LP_MODE_1_KSPS = 4
    HR_MODE_1_KSPS__LP_MODE_500_SPS = 5
    HR_MODE_500_SPS__LP_MODE_250_SPS = 6


@dataclass
class Ads129xConfigRegister1:
    """Describes config register 1 of ADS129x chip"""

    power_mode: Ads129xPowerMode = Ads129xPowerMode.HIGH_RESOLUTION
    read_mode: Ads129xReadMode = Ads129xReadMode.DAISY_CHAIN
    clock_connection: Ads129xClockConnection = Ads129xClockConnection.OSCILLATOR_CLOCK_OUTPUT_DISABLED
    output_data_rate: Ads129xOutputDataRate = Ads129xOutputDataRate.HR_MODE_4_KSPS__LP_MODE_2_KSPS

    def set_data(self, data: bytes):
        """Convert data to information"""
        tmp = data[0]
        self.power_mode = Ads129xPowerMode((tmp >> 7) & 0x01)
        self.read_mode = Ads129xReadMode((tmp >> 6) & 0x01)
        self.clock_connection = Ads129xClockConnection((tmp >> 5) & 0x01)
        self.output_data_rate = Ads129xOutputDataRate((tmp >> 0) & 0x07)


    def get_data(self) -> bytes:
        """Convert information to bytes"""
        tmp = ((self.power_mode << 7) | (self.read_mode << 6) |
               (self.clock_connection << 5) | (self.output_data_rate << 0))
        return [tmp]
