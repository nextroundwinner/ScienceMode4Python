"""Provides class for ADS129x chip"""

from dataclasses import dataclass, field

from science_mode_4.utils.byte_builder import ByteBuilder
from .ads129x_config_register_1 import Ads129xConfigRegister1
from .ads129x_config_register_2 import Ads129xConfigRegister2
from .ads129x_config_register_3 import Ads129xConfigRegister3
from .ads129x_config_register_4 import Ads129xConfigRegister4
from .ads129x_respiration_control_register import Ads129xRespirationControlRegister
from .ads129x_channel_settings_register import Ads129xChannelSettingsRegister


@dataclass
class Ads129x: # pylint:disable=too-many-instance-attributes
    """Describes register map of ADS129x chip, one field per physical chip register"""

    # control register
    device_id: int = 0

    config_register_1: Ads129xConfigRegister1 = field(default_factory=Ads129xConfigRegister1) # CONFIG1
    config_register_2: Ads129xConfigRegister2 = field(default_factory=Ads129xConfigRegister2) # CONFIG2
    config_register_3: Ads129xConfigRegister3 = field(default_factory=Ads129xConfigRegister3) # CONFIG3
    config_register_4: Ads129xConfigRegister4 = field(default_factory=Ads129xConfigRegister4) # CONFIG4

    lead_off_control_register: int = 0 # LOFF

    channel_1_setting_register: Ads129xChannelSettingsRegister = field(default_factory=Ads129xChannelSettingsRegister) # CH1SET
    channel_2_setting_register: Ads129xChannelSettingsRegister = field(default_factory=Ads129xChannelSettingsRegister) # CH2SET
    channel_3_setting_register: Ads129xChannelSettingsRegister = field(default_factory=Ads129xChannelSettingsRegister) # CH3SET
    channel_4_setting_register: Ads129xChannelSettingsRegister = field(default_factory=Ads129xChannelSettingsRegister) # CH4SET

    positive_signal_derivation_register: int = 0x02 # RLD_SENSP
    negative_signal_derivation_register: int = 0x02 # RLD_SENSN
    positive_signal_lead_off_detection_register: int = 0 # LOFF_SENSP
    negative_signal_lead_off_detection_register: int = 0 # LOFF_SENSN

    lead_off_flip_register: int = 0 # LOFF_FLIP
    lead_off_positive_signal_status_register: int = 0 # LOFF_STATP
    lead_off_negative_signal_status_register: int = 0 # LOFF_STATN
    gpio_register: int = 0 # GPIO
    pace_detect_register: int = 0 # PACE

    respiration_control_register: Ads129xRespirationControlRegister = field(default_factory=Ads129xRespirationControlRegister) # RESP

    wilson_central_terminal_and_augmented_lead_control_register: int = 0 # WCT1
    wilson_central_terminal_control_register: int = 0 # WCT2



    def set_data(self, data: bytes):
        """Convert data to information"""

        self.channel_1_setting_register.set_data([data[0]])
        self.channel_2_setting_register.set_data([data[1]])
        self.channel_3_setting_register.set_data([data[2]])
        self.channel_4_setting_register.set_data([data[3]])

        self.config_register_1.set_data([data[8]])
        self.config_register_2.set_data([data[9]])
        self.config_register_3.set_data([data[10]])
        self.config_register_4.set_data([data[11]])

        self.gpio_register = data[12]
        self.device_id = data[13]
        self.lead_off_control_register = data[14]
        self.lead_off_flip_register = data[15]
        self.negative_signal_lead_off_detection_register = data[16]
        self.positive_signal_lead_off_detection_register = data[17]
        self.lead_off_negative_signal_status_register = data[18]
        self.lead_off_positive_signal_status_register = data[19]

        self.pace_detect_register = data[20]
        self.respiration_control_register.set_data([data[21]])
        self.negative_signal_derivation_register = data[22]
        self.positive_signal_derivation_register = data[23]

        self.wilson_central_terminal_and_augmented_lead_control_register = data[24]
        self.wilson_central_terminal_control_register = data[25]



    def get_data(self) -> bytes:
        """Convert information to bytes"""

        bb = ByteBuilder(0, 26)
        bb.set_bytes_to_position(self.channel_1_setting_register.get_data(), 0, 1)
        bb.set_bytes_to_position(self.channel_2_setting_register.get_data(), 1, 1)
        bb.set_bytes_to_position(self.channel_3_setting_register.get_data(), 2, 1)
        bb.set_bytes_to_position(self.channel_4_setting_register.get_data(), 3, 1)

        bb.set_bytes_to_position(self.config_register_1.get_data(), 8, 1)
        bb.set_bytes_to_position(self.config_register_2.get_data(), 9, 1)
        bb.set_bytes_to_position(self.config_register_3.get_data(), 10, 1)
        bb.set_bytes_to_position(self.config_register_4.get_data(), 11, 1)

        bb.set_bytes_to_position([self.gpio_register], 12, 1)
        bb.set_bytes_to_position([self.device_id], 13, 1)
        bb.set_bytes_to_position([self.lead_off_control_register], 14, 1)
        bb.set_bytes_to_position([self.lead_off_flip_register], 15, 1)
        bb.set_bytes_to_position([self.negative_signal_lead_off_detection_register], 16, 1)
        bb.set_bytes_to_position([self.positive_signal_lead_off_detection_register], 17, 1)
        bb.set_bytes_to_position([self.lead_off_negative_signal_status_register], 18, 1)
        bb.set_bytes_to_position([self.lead_off_positive_signal_status_register], 19, 1)

        bb.set_bytes_to_position([self.pace_detect_register], 20, 1)
        bb.set_bytes_to_position(self.respiration_control_register.get_data(), 21, 1)
        bb.set_bytes_to_position([self.negative_signal_derivation_register], 22, 1)
        bb.set_bytes_to_position([self.positive_signal_derivation_register], 23, 1)

        bb.set_bytes_to_position([self.wilson_central_terminal_and_augmented_lead_control_register], 24, 1)
        bb.set_bytes_to_position([self.wilson_central_terminal_control_register], 25, 1)

        return bb.get_bytes()
