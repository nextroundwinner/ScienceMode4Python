"""Provices general layer"""

from ..protocol.packet_number_generator import PacketNumberGenerator
from .general_reset import PacketGeneralReset, PacketGeneralResetAck
from .general_stim_status import GetStimStatusResult, PacketGeneralGetStimStatus, PacketGeneralGetStimStatusAck
from .general_device_id import PacketGeneralGetDeviceId, PacketGeneralGetDeviceIdAck
from .general_version import PacketGeneralGetExtendedVersion, PacketGeneralGetExtendedVersionAck, GetExtendedVersionResult
from ..protocol.packet_factory import PacketFactory
from ..utils.connection import Connection
from ..layer import Layer
from ..protocol.protocol import Protocol


class LayerGeneral(Layer):
    """Class for general layer"""


    def __init__(self, conn: Connection, packet_factory: PacketFactory, packet_number_generator: PacketNumberGenerator):
        super().__init__(conn, packet_factory, packet_number_generator)
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
        """Calls initialze commands"""
        await self.get_device_id()
        await self.get_version()


    async def get_device_id(self) -> str:
        """Send get device id command and waits for response"""
        p = PacketGeneralGetDeviceId()
        ack: PacketGeneralGetDeviceIdAck = await self._send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "GetDeviceId")
        self._device_id = ack.device_id
        return self._device_id


    async def reset(self):
        """Sends reset command and waits for response"""
        p = PacketGeneralReset()
        # maybe we get no ack because the device resets before sending ack
        ack: PacketGeneralResetAck = await self._send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "Reset")


    async def get_stim_status(self) -> GetStimStatusResult:
        """Sends get stim status and waits for response"""
        p = PacketGeneralGetStimStatus()
        ack: PacketGeneralGetStimStatusAck = await self._send_packet_and_wait(p)
        if not ack.successful:
            raise ValueError("Error get stim status")
        return GetStimStatusResult(ack.stim_status, ack.high_voltage_on)


    async def get_version(self) -> GetExtendedVersionResult:
        """Sends get extended version and waits for response, returns firmware and science mode version"""      
        p = PacketGeneralGetExtendedVersion()
        ack: PacketGeneralGetExtendedVersionAck = await self._send_packet_and_wait(p)
        if not ack.successful:
            raise ValueError("Error get extended version")
        self._firmware_version = ack.firmware_version
        self._science_mode_version = ack.science_mode_version
        return GetExtendedVersionResult(self._firmware_version, self._science_mode_version)
