"""Provides a packet buffer functionality for more async handling of packets and acknowledges"""

from science_mode_4.protocol.exceptions import ProtocolError
from science_mode_4.protocol.packet import Packet
from science_mode_4.protocol.packet_factory import PacketFactory
from science_mode_4.protocol.protocol import Protocol
from science_mode_4.protocol.commands import Commands
from science_mode_4.utils.logger import logger
from .connection import Connection


class PacketBuffer():
    """Class for handling a buffer and provides methods to take care of arriving acknowledges"""

    def __init__(self, conn: Connection, packet_factory: PacketFactory):
        self._buffer: bytes = b""
        # dict with command and packet number as key and open count as value
        self._open_acknowledges: dict[tuple[int, int], int] = {}
        self._connection = conn
        self._packet_factory = packet_factory


    @property
    def connection(self) -> Connection:
        """Getter for connection"""
        return self._connection


    @property
    def buffer(self) -> bytes:
        """Getter for buffer"""
        return self._buffer


    def update_buffer(self):
        """Reads all data from connection and appends to internal buffer"""
        self._buffer += self._connection.read()


    def add_open_acknowledge(self, packet: Packet):
        """Adds packet to list of packets, that are waiting for a acknowledge"""
        key = packet.command + 1, packet.number
        if key in self._open_acknowledges:
            self._open_acknowledges[key] += 1
        else:
            self._open_acknowledges[key] = 1


    def remove_open_acknowledge(self, packet: Packet):
        """Remove packet from list of packets, that are waiting for a acknowledge"""
        key = packet.command + 1, packet.number
        if key in self._open_acknowledges:
            self._open_acknowledges[key] -= 1
        else:
            raise ProtocolError(f"Remove non existing acknowledge from packet buffer, command {packet.command}, number {packet.number}")


    def print_open_acknowledge(self):
        """Print open acknowledges"""
        logger().info("Open acknowledges")
        for key, value in self._open_acknowledges.items():
            if value != 0:
                logger().info("Command: %s, number: %d, value: %d", Commands(key[0]).name, key[1], value)


    def get_packet_from_buffer(self, do_update_buffer = True) -> Packet | None:
        """Search for a valid packet in buffer and returns found packet. Does adjust internal buffer accordingly.
        Returns None if no valid packet was found
        """
        if do_update_buffer:
            self.update_buffer()

        start_stop = Protocol.find_packet_in_buffer(self._buffer)
        if start_stop is None:
            return None

        packet_data = self._buffer[start_stop[0]: start_stop[1] + 1]
        ack_data = Protocol.extract_packet_data(packet_data)
        # check if we wait for this acknowledge
        key = ack_data[0], ack_data[1]
        wait_ack = self._open_acknowledges.get(key)
        if wait_ack is None:
            if ack_data[0] not in [Commands.DL_SEND_LIVE_DATA, Commands.DL_SEND_FILE]:
                logger().warning("Unexpected acknowledge command: %s, number: %d", Commands(ack_data[0]).name, ack_data[1])
        else:
            self._open_acknowledges[ack_data[0], ack_data[1]] -= 1

        # remove from buffer
        self._buffer = self._buffer[start_stop[0] + start_stop[1] + 1:]
        ack = self._packet_factory.create_packet_with_data(ack_data[0], ack_data[1], ack_data[2])
        return ack


    def clear_buffer(self):
        """Clear internal buffer and buffer from connection"""
        self._connection.clear_buffer()
        self._buffer = b""
