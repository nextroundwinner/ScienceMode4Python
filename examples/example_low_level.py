"""Provides an example how to use low level layer"""

import asyncio
import sys

from example_utils import ExampleUtils, KeyboardInputThread
from science_mode_4 import DeviceP24
from science_mode_4 import ChannelPoint
from science_mode_4 import SerialPortConnection
from science_mode_4 import LayerLowLevel
from science_mode_4 import Connector, Channel
from science_mode_4 import LowLevelHighVoltageSource, LowLevelMode


def send_channel_config(low_level_layer: LayerLowLevel, connector: Connector):
    """Sends channel update"""
    # device can store up to 10 channel config commands
    for channel in Channel:
        # send_channel_config does not wait for an acknowledge
        low_level_layer.send_channel_config(True, channel, connector,
                                            [ChannelPoint(4000, 20), ChannelPoint(4000, -20),
                                            ChannelPoint(4000, 0)])


async def main() -> int:
    """Main function"""

    # keyboard is our trigger to start specific stimulation
    def input_callback(input_value: str) -> bool:
        """Callback call from keyboard input thread"""
        print(f"Input value {input_value}")

        if input_value == "1":
            send_channel_config(low_level_layer, Connector.GREEN)
        elif input_value == "2":
            send_channel_config(low_level_layer, Connector.YELLOW)
        elif input_value == "q":
            # end keyboard input thread
            return True

        return False

    print("Usage: press 1 or 2 to stimulate green or yellow connector or press q to quit")
    # create keyboard input thread for non blocking console input
    keyboard_input_thread = KeyboardInputThread(input_callback)

    # get comport from command line argument
    com_port = ExampleUtils.get_comport_from_commandline_argument()
    # create serial port connection
    connection = SerialPortConnection(com_port)
    # open connection, now we can read and write data
    connection.open()

    # create science mode device
    device = DeviceP24(connection)
    # call initialize to get basic information (serial, versions) and stop any active stimulation/measurement
    # to have a defined state
    await device.initialize()

    # get low level layer to call low level commands
    low_level_layer = device.get_layer_low_level()

    # call init low level
    await low_level_layer.init(LowLevelMode.NO_MEASUREMENT, LowLevelHighVoltageSource.STANDARD)

    # now we can start stimulation
    while keyboard_input_thread.is_alive():
        # get new data from connection
        # both append_bytes_to_buffer and get_packet_from_buffer should be called regulary
        new_buffer_data = device.connection.read()
        if len(new_buffer_data) > 0:
            low_level_layer.packet_buffer.append_bytes_to_buffer(new_buffer_data)
            # we added new data to buffer, so there may be new valid acknowledges
            packet_ack = low_level_layer.packet_buffer.get_packet_from_buffer()
            # do something with packet ack
            # here we print that an acknowledge arrived
            print(packet_ack)

        await asyncio.sleep(0.1)

    # call stop low level
    await low_level_layer.stop()

    # close serial port connection
    connection.close()
    return 0


if __name__ == '__main__':
    res = asyncio.run(main())
    sys.exit(res)
