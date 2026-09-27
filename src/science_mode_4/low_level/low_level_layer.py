"""Provides low level layer"""

from science_mode_4.protocol.channel_point import ChannelPoint
from science_mode_4.protocol.types import Channel, Connector
from science_mode_4.utils.logger import logger
from science_mode_4.layer import Layer
from .low_level_channel_config import PacketLowLevelChannelConfig
from .low_level_init import PacketLowLevelInit, PacketLowLevelInitAck
from .low_level_stop import PacketLowLevelStop, PacketLowLevelStopAck
from .low_level_types import LowLevelHighVoltageSource, LowLevelMode


class LayerLowLevel(Layer):
    """
    Class for low level layer, uses internally a PacketBuffer to keep track of responses because
    no command waits for response
    """


    async def init(self, mode: LowLevelMode, high_voltage_source: LowLevelHighVoltageSource):
        """Send low level init command and waits for response"""
        p = PacketLowLevelInit()
        p.mode = mode
        p.high_voltage_source = high_voltage_source
        ack: PacketLowLevelInitAck = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "LowLevelInit")
        logger().info("Low level init")


    async def stop(self):
        """Send low level stop command and waits for response"""
        p = PacketLowLevelStop()
        ack: PacketLowLevelStopAck = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "LowLevelStop")
        logger().info("Low level stop")


    def send_init(self, mode: LowLevelMode, high_voltage_source: LowLevelHighVoltageSource):
        """Send low level init command"""
        p = PacketLowLevelInit()
        p.mode = mode
        p.high_voltage_source = high_voltage_source
        self.send_packet(p)
        logger().info("Low level send init")


    def send_channel_config(self, execute_stimulation: bool, channel: Channel,
                            connector: Connector, points: list[ChannelPoint]):
        """Send low level channel config command"""
        p = PacketLowLevelChannelConfig()
        p.execute_stimulation = execute_stimulation
        p.channel = channel
        p.connector = connector
        p.points = points
        self.send_packet(p)
        logger().info("Low level send channel config")


    def send_stop(self):
        """Send low level stop command"""
        p = PacketLowLevelStop()
        self.send_packet(p)
        logger().info("Low level send stop")
