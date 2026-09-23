"""Example how to use dyscom and write values to a .csv file.
Because writing takes time, we handle it in a
background thread and synchronize measurement data vie Queue from main thread"""

import asyncio
from timeit import default_timer as timer

from science_mode_4 import DeviceI24
from science_mode_4 import Commands
from science_mode_4 import SerialPortConnection
from science_mode_4.dyscom.ads129x.ads129x_config_register_1 import Ads129xOutputDataRate, Ads129xPowerMode
from science_mode_4.dyscom.dyscom_get_operation_mode import PacketDyscomGetAckOperationMode
from science_mode_4.dyscom.dyscom_send_live_data import PacketDyscomSendLiveData
from science_mode_4.dyscom.dyscom_types import DyscomGetType, DyscomInitParams, DyscomPowerModulePowerType,\
    DyscomPowerModuleType, DyscomSignalType
from science_mode_4.protocol.types import ResultAndError
from science_mode_4.utils.logger import logger
from examples.utils.example_utils import ExampleUtils
from examples.utils.csv_utils import CsvHelper


def main():
    """Main function"""

    csv_helper = CsvHelper("values.csv", ["package_nr", "Channel 1", "Channel 2", "Channel 3", "Channel 4", "Channel 5", "time_delta"])
    csv_helper.start()

    async def device_communication() -> int:
        """Communication with science mode device"""

        # disable logger to increase performance
        logger().disabled = True

        # get comport from command line argument
        com_port = ExampleUtils.get_comport_from_commandline_argument()
        # create serial port connection
        connection = SerialPortConnection(com_port)
        # open connection, now we can read and write data
        connection.open()

        # create science mode device
        device = DeviceI24(connection)
        # call initialize to get basic information (serial, versions) and stop any active stimulation/measurement
        # to have a defined state
        await device.initialize()

        # get dyscom layer to call dyscom level commands
        dyscom = device.get_layer_dyscom()

        # call enable measurement power module for measurement
        await dyscom.power_module(DyscomPowerModuleType.MEASUREMENT, DyscomPowerModulePowerType.SWITCH_ON)
        # call init with 4k sample rate and enable signal types
        init_params = DyscomInitParams()
        init_params.signal_type = [DyscomSignalType.BI, DyscomSignalType.EMG_1,\
                                DyscomSignalType.EMG_2, DyscomSignalType.BREATHING]
        init_params.register_map_ads129x.config_register_1.output_data_rate = Ads129xOutputDataRate.HR_MODE_4_KSPS__LP_MODE_2_KSPS
        init_params.register_map_ads129x.config_register_1.power_mode = Ads129xPowerMode.HIGH_RESOLUTION
        await dyscom.init(init_params)

        # start dyscom measurement
        await dyscom.start()

        start_time = timer()
        total_count = 0

        # loop for some time
        update_buffer = True
        next_operation_mode_check = 0
        stop_sent = False
        while True:
            # check operation mode from time to time, this function is not waiting for response
            # so we have to handle it by ourself later
            if total_count >= next_operation_mode_check:
                dyscom.send_get_operation_mode()
                next_operation_mode_check = total_count + 4000
            if total_count >= 40000 and not stop_sent:
                # stop measurement after 40000 samples
                # send it here to avoid mix with live data packages
                dyscom.send_stop()
                stop_sent = True

            # process all available packages
            ack = dyscom.packet_buffer.get_packet_from_buffer(update_buffer)
            if ack:
                update_buffer = False
                # because there are multiple get commands, we need to additionally check kind,
                # which is always associated DyscomGetType
                if ack.command == Commands.DL_GET_ACK and ack.kind == DyscomGetType.OPERATION_MODE:
                    om_ack: PacketDyscomGetAckOperationMode = ack
                    print(f"Operation mode {om_ack.operation_mode.name}")
                    # check if measurement is still active
                    if om_ack.result_error != ResultAndError.NO_ERROR:
                        break
                elif ack.command == Commands.DL_SEND_LIVE_DATA:
                    total_count += 1

                    sld: PacketDyscomSendLiveData = ack
                    if sld.status_error:
                        print(f"SendLiveData status error {sld.samples}")
                        break

                    csv_helper.append_values(ack.number, [sld.samples[0].value, sld.samples[1].value,\
                                                            sld.samples[2].value, sld.samples[3].value,\
                                                            sld.samples[4].value], sld.time_offset)
                elif ack.command == Commands.DL_STOP_ACK:
                    break
            else:
                update_buffer = True

        # print stats
        end_time = timer()
        print(f"Samples: {total_count}, duration: {end_time - start_time}, sample rate: {total_count / (end_time - start_time)}")

        await asyncio.sleep(1)

        # turn power module off
        await dyscom.power_module(DyscomPowerModuleType.MEASUREMENT, DyscomPowerModulePowerType.SWITCH_OFF)

        # close serial port connection
        connection.close()

        # stop writing file
        csv_helper.stop()

        return 0


    # start device communication
    asyncio.run(device_communication())


if __name__ == "__main__":
    main()
