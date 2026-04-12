"""Provides low level layer"""

import asyncio
import struct

from science_mode_4.layer import Layer
from science_mode_4.protocol.commands import Commands
from science_mode_4.protocol.exceptions import ProtocolError
from science_mode_4.utils.logger import logger
from .dyscom_types import DyscomFrequencyOut, DyscomGetOperationModeType, DyscomInitState, DyscomPowerModuleType,\
    DyscomPowerModulePowerType, DyscomSignalType, DyscomSysState, DyscomSysType
from .dyscom_init import DyscomInitResult, PacketDyscomInit, PacketDyscomInitAck, DyscomInitParams
from .dyscom_get_file_system_status import PacketDyscomGetFileSystemStatus, PacketDyscomGetAckFileSystemStatus,\
    DyscomGetFileSystemStatusResult
from .dyscom_get_file_by_name import PacketDyscomGetFileByName, PacketDyscomGetAckFileByName, DyscomGetFileByNameResult
from .dyscom_get_firmware_version import PacketDyscomGetFirmwareVersion, PacketDyscomGetAckFirmwareVersion
from .dyscom_get_operation_mode import PacketDyscomGetOperationMode, PacketDyscomGetAckOperationMode
from .dyscom_start import PacketDyscomStart, PacketDyscomStartAck
from .dyscom_stop import PacketDyscomStop, PacketDyscomStopAck
from .dyscom_power_module import PacketDyscomPowerModule, PacketDyscomPowerModuleAck, DyscomPowerModuleResult
from .dyscom_get_list_of_measurement_meta_info import PacketDyscomGetAckListOfMeasurementMetaInfo, PacketDyscomGetListOfMeasurementMetaInfo
from .dyscom_get_device_id import PacketDyscomGetAckDeviceId, PacketDyscomGetDeviceId
from .dyscom_get_file_info import DyscomGetFileInfoResult, PacketDyscomGetAckFileInfo, PacketDyscomGetFileInfo
from .dyscom_get_battery_status import DyscomGetBatteryResult, PacketDyscomGetAckBatteryStatus, PacketDyscomGetBatteryStatus
from .dyscom_sys import DyscomSysResult, PacketDyscomSys, PacketDyscomSysAck
from .dyscom_send_file import PacketDyscomSendFile, PacketDyscomSendFileAck


class LayerDyscom(Layer):
    """
    Class for dyscom layer
    """


    async def init(self, params: DyscomInitParams) -> DyscomInitResult:
        """Send dyscom init command and waits for response"""
        p = PacketDyscomInit(params)
        ack: PacketDyscomInitAck = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "DyscomInit")
        if ack.init_state not in [DyscomInitState.UNUSED, DyscomInitState.SUCCESS]:
            raise ProtocolError(f"Dyscom error init {ack.init_state.name}")

        logger().info("Dyscom init, measurement_file_id: %s, state: %s, frequency: %s",\
                      ack.measurement_file_id, ack.init_state.name, ack.frequency_out.name)
        return DyscomInitResult(ack.register_map_ads129x, ack.measurement_file_id, ack.init_state, ack.frequency_out)


    async def get_file_system_status(self) -> DyscomGetFileSystemStatusResult:
        """Sends dyscom get type file system status and waits for response, returns file system ready, used size and free size"""
        p = PacketDyscomGetFileSystemStatus()
        ack: PacketDyscomGetAckFileSystemStatus = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "DyscomGetFileSystemStatus")
        logger().info("Dyscom get file system status, ready: %s, used size: %d, free size: %s",\
                      ack.file_system_ready, ack.used_size, ack.free_size)
        return DyscomGetFileSystemStatusResult(ack.file_system_ready, ack.used_size, ack.free_size)


    async def get_list_of_measurement_meta_info(self) -> int:
        """Sends dyscom get type list of measurement meta info and waits for response, returns number of measurements"""
        p = PacketDyscomGetListOfMeasurementMetaInfo()
        ack: PacketDyscomGetAckListOfMeasurementMetaInfo = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "DyscomGetListOfMeasurementMetaInfo")
        logger().info("Dyscom get list of mmi, number of measurements: %d", ack.number_of_measurements)
        return ack.number_of_measurements


    async def get_file_by_name(self, filename: str) -> DyscomGetFileByNameResult:
        """Sends dyscom get type file by name and waits for response, returns filename, block offset,
        filesize, number of blocks and mode"""
        p = PacketDyscomGetFileByName(filename)
        ack: PacketDyscomGetAckFileByName = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "DyscomGetFileByName")
        logger().info("Dyscom get file by name, filename: %s, block offset: %d, filesize: %d, number of blocks: %d, mode: %s",\
                      ack.filename, ack.block_offset, ack.filesize, ack.number_of_blocks, ack.mode.name)
        return DyscomGetFileByNameResult(ack.filename, ack.block_offset, ack.filesize, ack.number_of_blocks, ack.mode)


    async def get_device_id(self) -> str:
        """Sends dyscom get type device id and waits for response, returns device id"""
        p = PacketDyscomGetDeviceId()
        ack: PacketDyscomGetAckDeviceId = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "DyscomGetDeviceId")
        logger().info("Dyscom get device id: %s", ack.device_id)
        return ack.device_id


    async def get_firmware_version(self) -> str:
        """Sends dyscom get type firmware version and waits for response, returns firmware version"""
        p = PacketDyscomGetFirmwareVersion()
        ack: PacketDyscomGetAckFirmwareVersion = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "DyscomGetFirmwareVersion")
        logger().info("Dyscom get firmware version: %s", ack.firmware_version)
        return ack.firmware_version


    async def get_file_info(self, filename: str) -> DyscomGetFileInfoResult:
        """Sends dyscom get type file by name and waits for response, returns filename, block offset, filesize and number of blocks"""
        p = PacketDyscomGetFileInfo(filename)
        ack: PacketDyscomGetAckFileInfo = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "DyscomGetFileInfo")
        logger().info("Dyscom get file info, filename: %s, filesize: %d, checksum: %d",\
                      ack.filename, ack.filesize, ack.checksum)
        return DyscomGetFileInfoResult(ack.filename, ack.filesize, ack.checksum)


    async def get_battery(self) -> DyscomGetBatteryResult:
        """Sends dyscom get type batter and waits for response, returns voltage, current, percentage, temperature and energy state"""
        p = PacketDyscomGetBatteryStatus()
        ack: PacketDyscomGetAckBatteryStatus = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "DyscomGetBatteryStatus")
        logger().info("Dyscom get battery, voltage: %d, current: %d, percentage: %d, temperature: %d, energy state: %s",\
                      ack.voltage, ack.current, ack.percentage, ack.temperature, ack.energy_state)
        return DyscomGetBatteryResult(ack.voltage, ack.current, ack.percentage, ack.temperature, ack.energy_state)


    async def get_operation_mode(self) -> DyscomGetOperationModeType:
        """Sends dyscom get type operation mode and waits for response, returns operation mode"""
        p = PacketDyscomGetOperationMode()
        ack: PacketDyscomGetAckOperationMode = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "DyscomGetFirmwareVersion")
        logger().info("Dyscom get operation mode: %s", ack.operation_mode.name)
        return ack.operation_mode


    def send_get_operation_mode(self):
        """Sends dyscom get type operation mode and returns immediately without waiting for response"""
        p = PacketDyscomGetOperationMode()
        logger().info("Dyscom send get operation mode")
        self.send_packet(p)


    async def power_module(self, module: DyscomPowerModuleType, power: DyscomPowerModulePowerType) -> DyscomPowerModuleResult:
        """Sends dyscom power module and waits for response, returns module and power"""
        p = PacketDyscomPowerModule(module, power)
        ack: PacketDyscomPowerModuleAck = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "DyscomStart")
        logger().info("Dyscom power module, module: %s, power: %s", ack.module.name, ack.power.name)
        return DyscomPowerModuleResult(ack.module, ack.power)


    async def sys(self, sys_type: DyscomSysType, filename: str = "") -> DyscomSysResult:
        """Sends dyscom sys and waits for response, returns type, state and filename"""
        p = PacketDyscomSys(sys_type, filename)
        ack: PacketDyscomSysAck = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "DyscomSys")
        if ack.state not in [DyscomSysState.SUCCESSFUL]:
            raise ProtocolError(f"Dyscom error sys {ack.state.name}")

        logger().info("Dyscom sys, type: %s, state: %s, filename: %s", ack.sys_type.name, ack.state.name, ack.filename)
        return DyscomSysResult(ack.sys_type, ack.state, ack.filename)


    def send_send_file_ack(self, block_number: int):
        """Sends dyscom send file ack and returns immediately without waiting for response"""
        logger().info("Dyscom send file ack, block_number: %d", block_number)
        p = PacketDyscomSendFileAck(block_number)
        self.send_packet(p)


    async def start(self):
        """Sends dyscom start and waits for response"""
        p = PacketDyscomStart()
        ack: PacketDyscomStartAck = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "DyscomStart")
        logger().info("Dyscom start")


    async def stop(self):
        """Sends dyscom stop and waits for response"""
        p = PacketDyscomStop()
        ack: PacketDyscomStopAck = await self.send_packet_and_wait(p)
        self._check_result_error(ack.result_error, "DyscomStop")
        logger().info("Dyscom stop")


    def send_start(self):
        """Sends dyscom start and returns immediately without waiting for response"""
        logger().info("Dyscom start")
        p = PacketDyscomStart()
        self.send_packet(p)


    def send_stop(self):
        """Sends dyscom stop and returns immediately without waiting for response"""
        logger().info("Dyscom stop")
        p = PacketDyscomStop()
        self.send_packet(p)


    async def get_file_content(self, filename: str) -> bytes:
        """Gets content of a file. Device must be in Idle operating mode"""
        om = await self.get_operation_mode()
        if om != DyscomGetOperationModeType.IDLE:
            raise ProtocolError(f"Error wrong operation mode {om.name}")

        # get meta information and sets device in mode DATATRANSFER_PRE
        # we need number of blocks to know how many SendFile commands we expect
        # and filesize to know exact filesize
        file_by_name = await self.get_file_by_name(filename)
        logger().info("Dyscom get file content, filesize: %d, number of blocks: %d",
                      file_by_name.filesize, file_by_name.number_of_blocks)

        # start measurement, so device send automatically SendFile packets
        await self.start()

        result = bytes()
        while True:
            # process all available packages
            ack = self.packet_buffer.get_packet_from_buffer()
            if ack:
                if ack.command == Commands.DL_SEND_FILE:
                    # process SendFile data
                    sf: PacketDyscomSendFile = ack
                    result += sf.data

                    # send acknowledge for this packet, so device can send
                    # next block automatically
                    self.send_send_file_ack(sf.block_number)

                    # check if we have all blocks
                    if sf.block_number >= file_by_name.number_of_blocks:
                        break
                else:
                    logger().warning("Unexpected command: %d", ack.command)

            await asyncio.sleep(0.01)

        # stop measurement, we have all blocks
        await self.stop()

        # trim to filesize (because SendFile sends always data with blocksize)
        result = result[0:file_by_name.filesize]
        return result


    async def get_meas_file_content(self, filename: str) -> tuple[DyscomFrequencyOut, dict[DyscomSignalType, list[float]]]:
        """Gets measurement data of a file. Device must be in Idle operating mode"""
        meas_data = await self.get_file_content(filename)

        result: dict[DyscomSignalType, list[float]] = {}
        # signal types differ from DyscomSignalType enum
        signal_type_map = {	1: 1, 2: 10, 3: 2, 4: 3, 5: 11, 6: 9, 7: 12}
        signal_types: list[DyscomSignalType] = []
        for x in range(meas_data[10]):
            signal_type = DyscomSignalType(signal_type_map[meas_data[11+x]])
            signal_types.append(signal_type)

            result[signal_type] = []

        # sample rate
        sample_rate = DyscomFrequencyOut(meas_data[3])

        # build string to unpack samples
        # each sample consist of a time difference and n time signal type values
        value_structure = "<I"
        for x in range(len(signal_types)):
            value_structure += "f"
        unpack_struct = struct.Struct(value_structure)

        # skip header
        pos = 512
        sample_size = unpack_struct.size
        while pos + sample_size < len(meas_data):
            r = unpack_struct.unpack(meas_data[pos:pos+sample_size])
            for index, value in enumerate(signal_types):
                result[value].append(r[1+index])

            # advance to next sample
            pos += sample_size

        return sample_rate, result
