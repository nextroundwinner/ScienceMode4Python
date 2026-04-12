"""Provides device class representing a science mode device"""

from enum import IntEnum

from .layer import Layer
from .protocol.packet_factory import PacketFactory
from .protocol.packet_number_generator import PacketNumberGenerator
from .general.general_layer import LayerGeneral
from .utils.connection import Connection
from .utils.packet_buffer import PacketBuffer


class DeviceCapability(IntEnum):
    """Represent device capabilities"""
    GENERAL = 0
    LOW_LEVEL = 1
    MID_LEVEL = 2
    DYSCOM = 3


class Device():
    """Base class for a science mode devices"""


    def __init__(self, conn: Connection, capabilities: set[DeviceCapability]):
        self._connection  = conn
        self._packet_factory = PacketFactory()
        self._packet_buffer = PacketBuffer(self._connection, self._packet_factory)
        self._packet_number_generator = PacketNumberGenerator()
        self._capabilities = capabilities + [DeviceCapability.GENERAL]
        self._layer: dict[DeviceCapability, Layer] = {}

        self._layer_general = LayerGeneral(self._packet_buffer, self._packet_factory, self._packet_number_generator)


    @property
    def connection(self) -> Connection:
        """Getter for connection"""
        return self._connection


    @property
    def packet_factory(self) -> PacketFactory:
        """Getter for packet factory"""
        return self._packet_factory


    @property
    def packet_buffer(self) -> PacketBuffer:
        """Getter for packet buffer"""
        return self._packet_buffer


    @property
    def packet_number_generator(self) -> PacketNumberGenerator:
        """Getter for packet number generator"""
        return self._capabilities


    @property
    def capabilities(self) -> set[DeviceCapability]:
        """Getter for capabilities"""
        return self._capabilities


    async def initialize(self):
        """Initialize device to get basic information (serial, versions) and stop any active stimulation/measurement"""
        await self.get_layer_general().initialize()


    def get_layer_general(self) -> LayerGeneral:
        """Helper function to access general layer"""
        return self._layer_general
