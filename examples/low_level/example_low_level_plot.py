"""Provides an example how to use low level layer to measure current and plot values"""

import asyncio
import sys

from science_mode_4 import DeviceP24
from science_mode_4 import ChannelPoint, Commands
from science_mode_4 import SerialPortConnection
from science_mode_4 import PacketLowLevelChannelConfigAck
from science_mode_4 import Connector, Channel
from science_mode_4 import LowLevelHighVoltageSource, LowLevelMode
from science_mode_4 import LayerLowLevel
from examples.utils.example_utils import ExampleUtils
from examples.utils.pyplot_utils import PyPlotHelper


def send_channel_config(low_level_layer: LayerLowLevel):
    """Sends channel update"""
    # device can store up to 10 channel config commands
    for connector in Connector:
        for channel in Channel:
            factor = channel + 1
            # send_channel_config does not wait for an acknowledge
            low_level_layer.send_channel_config(True, channel, connector,
                                                [ChannelPoint(500 * factor, 10 * factor),
                                                 ChannelPoint(500 * factor, 0),
                                                 ChannelPoint(500 * factor, -10 * factor),
                                                 ChannelPoint(500 * factor, 0)])


def calc_plot_index(connector: Connector, channel: Channel) -> int:
    """Calculates index for plot from connector and channel"""
    return connector * len(Channel) + channel


def get_channel_color(channel: Channel) -> str:
    """Retrieves color from channel"""
    color = channel.name
    if color == "WHITE":
        color = "PURPLE"
    return color


async def main() -> int:
    """Main function"""

    plots_info: dict[int, tuple[str, str]] =  {}
    for connector in Connector:
        for channel in Channel:
            plots_info[calc_plot_index(connector, channel)] = f"Connector {connector.name}, channel {channel.name}", get_channel_color(channel)
    plot_helper = PyPlotHelper(plots_info, 500)

    # get comport from command line argument
    com_port = ExampleUtils.get_comport_from_commandline_argument()

    connection = None
    try:
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

        # call init low level and enable measurement
        await low_level_layer.init(LowLevelMode.STIM_CURRENT, LowLevelHighVoltageSource.STANDARD)

        for _ in range(3):
            # send 8 channel config so we get only 8 acknowledges
            send_channel_config(low_level_layer)

            # wait for stimulation to happen
            await asyncio.sleep(1.0)

            # process all acknowledges and append values to plot data
            while True:
                ack = low_level_layer.packet_buffer.get_packet_from_buffer()
                if ack:
                    if ack.command == Commands.LOW_LEVEL_CHANNEL_CONFIG_ACK:
                        ll_config_ack: PacketLowLevelChannelConfigAck = ack
                        # update plot with measured values
                        plot_helper.append_values(calc_plot_index(ll_config_ack.connector, ll_config_ack.channel),
                                                  ll_config_ack.measurement_samples)
                        plot_helper.update()
                else:
                    break

            await asyncio.sleep(0.1)

        # call stop low level
        await low_level_layer.stop()
    finally:
        # always close the serial port connection, even if an exception occurred above,
        # otherwise the COM port stays locked for subsequent runs
        if connection is not None:
            connection.close()

    print("Close plot window to quit")
    plot_helper.loop()
    return 0


if __name__ == "__main__":
    res = asyncio.run(main())
    sys.exit(res)
