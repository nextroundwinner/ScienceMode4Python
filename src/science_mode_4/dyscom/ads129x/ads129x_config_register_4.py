"""Provides class for ADS129x chip config register 4"""

from dataclasses import dataclass
from enum import IntEnum


class Ads129xRespirationModulationFrequency(IntEnum):
    """Represent ADS129xtype for respiration modulation frequency (configuration register 4, 0x17)"""
    MODULATION_CLOCK_64KHZ = 0
    MODULATION_CLOCK_32KHZ = 1
    SQUARE_WAVE_16KHZ = 2
    SQUARE_WAVE_8KHZ = 3
    SQUARE_WAVE_4KHZ = 4
    SQUARE_WAVE_2KHZ = 5
    SQUARE_WAVE_1KHZ = 6
    SQUARE_WAVE_500HZ = 7


class Ads129xSingleShotConversion(IntEnum):
    """Represent ADS129xtype for single shot mode (configuration register 4, 0x17)"""
    CONTINUOUS_MODE = 0
    SINGLE_SHOT_MODE = 1


class Ads129xWctToRld(IntEnum):
    """Represent ADS129xtype for WCT to RLD (configuration register 4, 0x17)"""
    CONNECTION_OFF = 0
    CONNECTION_ON = 1


class Ads129xLeadOffComparatorPowerDown(IntEnum):
    """Represent ADS129xtype for lead off comparator power down (configuration register 4, 0x17)"""
    LEAD_OFF_COMPARATOR_DISABLED = 0
    LEAD_OFF_COMPARATOR_ENABLED = 1


@dataclass
class Ads129xConfigRegister4:
    """Describes config register 4 of ADS129x chip"""

    respiration_modulation_frequency: Ads129xRespirationModulationFrequency = \
        Ads129xRespirationModulationFrequency.MODULATION_CLOCK_64KHZ
    single_shot_conversion: Ads129xSingleShotConversion = Ads129xSingleShotConversion.CONTINUOUS_MODE
    wct_to_rld: Ads129xWctToRld = Ads129xWctToRld.CONNECTION_OFF
    lead_off_comparator_power_down: Ads129xLeadOffComparatorPowerDown = \
        Ads129xLeadOffComparatorPowerDown.LEAD_OFF_COMPARATOR_DISABLED


    def set_data(self, data: bytes):
        """Convert data to information"""
        tmp = data[0]
        # CONFIG4 (datasheet Table 33): RESP_FREQ[2:0] is a 3 bit field at bits 7:5
        self.respiration_modulation_frequency = Ads129xRespirationModulationFrequency((tmp >> 5) & 0x07)
        self.single_shot_conversion = Ads129xSingleShotConversion((tmp >> 3) & 0x01)
        self.wct_to_rld = Ads129xWctToRld((tmp >> 2) & 0x01)
        self.lead_off_comparator_power_down = Ads129xLeadOffComparatorPowerDown((tmp >> 1) & 0x01)


    def get_data(self) -> bytes:
        """Convert information to bytes"""
        tmp = ((self.respiration_modulation_frequency << 5) | (0 << 4) |
               (self.single_shot_conversion << 3) |(self.wct_to_rld << 2) |
               (self.lead_off_comparator_power_down << 1) | (0 << 0))
        return [tmp]
