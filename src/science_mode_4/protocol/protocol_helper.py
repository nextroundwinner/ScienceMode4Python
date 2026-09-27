"""Helper class for sending packets to connection"""

import asyncio
import time

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
    def send_packet(packet: Packet, packet_number: int, packet_buffer: PacketBuffer) -> None:
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

        # use a deadline instead of counting sleep cycles, because asyncio.sleep() usually
        # sleeps longer than requested (e.g. ~15.6 ms timer resolution on Windows)
        sleep_duration = 0.01
        deadline = time.monotonic() + timeout_in_seconds
        while True:
            while True:
                ack = packet_buffer.get_packet_from_buffer()
                if ack is None:
                    # no acknowledge arrived, sleep and check again
                    break

                if (ack.command == packet.command + 1) and (ack.number == packet.number):
                    return ack

                # check if we got an error, we stop waiting then, so the acknowledge
                # for packet is no longer expected
                if ack.command == Commands.GENERAL_ERROR:
                    ge: PacketGeneralError = ack
                    packet_buffer.remove_open_acknowledge(packet)
                    raise ProtocolError(f"General error packet {ge.result_error.name}")
                if ack.command == Commands.UNKNOWN_COMMAND:
                    uc: PacketGeneralUnknownCommand = ack
                    packet_buffer.remove_open_acknowledge(packet)
                    raise ProtocolError(f"Unknown command packet {uc.result_error.name}")

                # discard this stale/mismatched acknowledge and check the buffer again immediately

            # check deadline after buffer was processed, so an acknowledge that arrived
            # during the last sleep is still accepted
            if time.monotonic() >= deadline:
                break
            await asyncio.sleep(sleep_duration)

        # we got no response in time, so remove open acknowledges
        packet_buffer.remove_open_acknowledge(packet)
        raise ProtocolError(f"No valid answer for packet {ProtocolHelper._command_name(packet.command)} "
                            f"within {timeout_in_seconds}s")


    @staticmethod
    def _command_name(command: int) -> str:
        """Returns name of command, or the number if it is no known command"""
        try:
            return Commands(command).name
        except ValueError:
            return str(command)
