"""Provides general layer"""

from science_mode_4.protocol.exceptions import ProtocolError
from science_mode_4.protocol.packet_number_generator import PacketNumberGenerator
from science_mode_4.protocol.packet_factory import PacketFactory
from science_mode_4.layer import Layer
from science_mode_4.utils import logger
from science_mode_4.utils.packet_buffer import PacketBuffer
from .general_reset import PacketGeneralReset, PacketGeneralResetAck
from .general_stim_status import GetStimStatusResult, PacketGeneralGetStimStatus, PacketGeneralGetStimStatusAck
from .general_device_id import PacketGeneralGetDeviceId, PacketGeneralGetDeviceIdAck
from .general_version import PacketGeneralGetExtendedVersion, PacketGeneralGetExtendedVersionAck, GetExtendedVersionResult


class LayerGeneral(Layer):
    """Class for general layer"""


    def __init__(self, packet_buffer: PacketBuffer, packet_factory: PacketFactory, packet_number_generator: PacketNumberGenerator):
        super().__init__(packet_buffer, packet_factory, packet_number_generator)
        self._device_id: str | None = None
        self._firmware_version: str | None = None
        self._science_mode_version: str | None = None


    @property
    def device_id(self) -> str | None:
        """Getter for device id"""
        return self._device_id


    @property
    def firmware_version(self) -> str | None:
        """Getter for firmware version"""
        return self._firmware_version


    @property
    def science_mode_version(self) -> str | None:
        """Getter for science mode version"""
        return self._science_mode_version


    async def initialize(self):
        """Calls initialize commands"""
        await self.get_device_id()
        await self.get_version()


    async def get_device_id(self) -> str:
        """Send get device id command and waits for response"""
        p = PacketGeneralGetDeviceId()
        ack: PacketGeneralGetDeviceIdAck = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "GetDeviceId")
        self._device_id = ack.device_id
        logger().info("Get device id: %s", ack.device_id)
        return self._device_id


    async def reset(self):
        """Sends reset command and waits for response"""
        logger().info("Reset",)
        p = PacketGeneralReset()
        # maybe we get no ack because the device resets before sending ack
        ack: PacketGeneralResetAck = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "Reset")


    async def get_stim_status(self) -> GetStimStatusResult:
        """Sends get stim status and waits for response"""
        p = PacketGeneralGetStimStatus()
        ack: PacketGeneralGetStimStatusAck = await self.send_packet_and_wait(p)
        if not ack.successful:
            raise ProtocolError("Error get stim status")
        logger().info("Get stim status: %s, active: %r", ack.stim_status.name, ack.high_voltage_on)
        return GetStimStatusResult(ack.stim_status, ack.high_voltage_on)


    async def get_version(self) -> GetExtendedVersionResult:
        """Sends get extended version and waits for response, returns firmware and science mode version"""      
        p = PacketGeneralGetExtendedVersion()
        ack: PacketGeneralGetExtendedVersionAck = await self.send_packet_and_wait(p)
        if not ack.successful:
            raise ProtocolError("Error get extended version")
        self._firmware_version = ack.firmware_version
        self._science_mode_version = ack.science_mode_version
        logger().info("Get version, firmware version: %s science mode version: %s, firmware hash: %s, hash type: %s, is valid hash: %r",\
                      ack.firmware_version, ack.science_mode_version, ack.firmware_hash, ack.hash_type.name, ack.is_valid_hash)
        return GetExtendedVersionResult(self._firmware_version, self._science_mode_version, ack.firmware_hash,\
                                        ack.hash_type, ack.is_valid_hash)
