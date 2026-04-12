"""Helper class for sending packets to connection"""

import asyncio

from science_mode_4.general.general_error import PacketGeneralError
from science_mode_4.general.general_unknown_command import PacketGeneralUnknownCommand
from science_mode_4.utils.packet_buffer import PacketBuffer
from .exceptions import ProtocolError
from .protocol import Protocol
from .commands import Commands
from .packet import Packet, PacketAck


class ProtocolHelper:
    """Helper class for Protocol"""


    @staticmethod
    def send_packet(packet: Packet, packet_number: int, packet_buffer: PacketBuffer) -> PacketAck:
        """Send a packet and returns immediately"""
        packet.number = packet_number
        packet_buffer.add_open_acknowledge(packet)

        packet_buffer.connection.write(Protocol.packet_to_bytes(packet))


    @staticmethod
    async def send_packet_and_wait(packet: Packet, packet_number: int, packet_buffer: PacketBuffer, timeout_in_seconds = 5) -> PacketAck:
        """Send a packet and wait for response, if no response arrives raise an exception,
        this function assumes that the response has the same packet number and ack command must be command+1
        
        Clears all incoming data from connection and packet buffer"""

        # discard all packets because we don"t need them anymore
        packet_buffer.clear_buffer()
        ProtocolHelper.send_packet(packet, packet_number, packet_buffer)

        # calculate number of loops to reach timeout
        sleep_duration = 0.01
        counter = timeout_in_seconds / sleep_duration
        while counter > 0:
            while True:
                ack = packet_buffer.get_packet_from_buffer()
                if ack:
                    if (ack.command == packet.command + 1) and (ack.number == packet.number):
                        return ack

                    # check if we got an error
                    if ack.command == Commands.GENERAL_ERROR:
                        ge: PacketGeneralError = ack
                        raise ProtocolError(f"General error packet {ge.result_error.name}")
                    if ack.command == Commands.UNKNOWN_COMMAND:
                        uc: PacketGeneralUnknownCommand = ack
                        raise ProtocolError(f"Unknown command packet {uc.result_error.name}")

                    # discard acknowledge and continue

                # no acknowledge arrived, sleep and check again
                break

            await asyncio.sleep(sleep_duration)
            counter -= 1

        # we got no response in time, so remove open acknowledges
        packet_buffer.remove_open_acknowledge(packet)
        raise ProtocolError(f"No valid answer for packet {packet.command}")
