"""Provides packet classes for dyscom get with type file system status"""

from typing import NamedTuple

from science_mode_4.utils.byte_builder import ByteBuilder
from .dyscom_types import DyscomFileByNameMode, DyscomGetType
from .dyscom_helper import DyscomHelper
from .dyscom_get import PacketDyscomGet, PacketDyscomGetAck


class DyscomGetFileByNameResult(NamedTuple):
    """Helper class for dyscom get with type file by name"""
    filename: str
    block_offset: int
    filesize: int
    number_of_blocks: int
    mode: DyscomFileByNameMode


class PacketDyscomGetFileByName(PacketDyscomGet):
    """Packet for dyscom get with type file by name"""


    def __init__(self, filename: str = "", mode: DyscomFileByNameMode = DyscomFileByNameMode.MULTI_BLOCK):
        super().__init__()
        self._type = DyscomGetType.FILE_BY_NAME
        self._kind = int(self._type)
        self._filename = filename
        self._mode = mode


    @property
    def filename(self) -> str:
        """Getter for filename"""
        return self._filename


    @property
    def mode(self) -> DyscomFileByNameMode:
        """Getter for mode"""
        return self._mode


    def get_data(self) -> bytes:
        bb = ByteBuilder()
        bb.append_bytes(super().get_data())
        bb.append_bytes(DyscomHelper.str_to_bytes(self._filename, 128))
        # block offset
        bb.append_value(0, 4, True)
        # file size
        bb.append_value(0, 8, True)
        # number of blocks
        bb.append_value(0, 4, True)
        # mode
        bb.append_byte(self._mode)
        # maybe more parameters are necessary here
        # block_offset, file_size, n_blocks, mode
        return bb.get_bytes()


class PacketDyscomGetAckFileByName(PacketDyscomGetAck):
    """Packet for dyscom get for type file by name acknowledge"""


    def __init__(self, data: bytes):
        super().__init__(data)
        self._kind = int(DyscomGetType.FILE_BY_NAME)
        self._filename = ""
        self._block_offset = 0
        self._filesize = 0
        self._number_of_blocks = 0
        self._mode = DyscomFileByNameMode.UNDEFINED

        if not data is None:
            self._filename = DyscomHelper.bytes_to_str(data[2:130], 128)
            self._block_offset = int.from_bytes(data[130:134], "big")
            self._filesize = int.from_bytes(data[134:142], "big")
            self._number_of_blocks = int.from_bytes(data[142:146], "big")
            self._mode = DyscomFileByNameMode(data[146])



    @property
    def filename(self) -> str:
        """Getter for filename"""
        return self._filename


    @property
    def block_offset(self) -> int:
        """Getter for block offset"""
        return self._block_offset


    @property
    def filesize(self) -> int:
        """Getter for filesize"""
        return self._filesize


    @property
    def number_of_blocks(self) -> int:
        """Getter for number of blocks"""
        return self._number_of_blocks


    @property
    def mode(self) -> DyscomFileByNameMode:
        """Getter for mode"""
        return self._mode
