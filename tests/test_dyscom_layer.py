"""Tests for LayerDyscom"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

import asyncio
import datetime
import logging
import struct
from unittest.mock import AsyncMock, patch

import pytest
from science_mode_4.device_i24 import DeviceI24
from science_mode_4.dyscom.dyscom_get_file_by_name import DyscomGetFileByNameResult
from science_mode_4.dyscom.dyscom_init import PacketDyscomInitAck
from science_mode_4.dyscom.dyscom_send_file import PacketDyscomSendFile
from science_mode_4.dyscom.dyscom_types import DyscomFileByNameMode, DyscomFilterType, DyscomFrequencyOut, \
    DyscomGetOperationModeType, DyscomInitFlag, DyscomInitParams, DyscomSignalType
from science_mode_4.protocol.exceptions import ProtocolError
from science_mode_4.utils.null_connection import NullConnection


def _build_meas_file(samples: list[tuple[int, float, float]],
                     dsp_filter: DyscomFilterType = DyscomFilterType.PREDEFINED_FILTER_1) -> bytes:
    """Builds measurement file content with a 512 byte header and two signal types (BI, EMG_1)"""
    header = bytearray(512)
    # output frequency is written by firmware before filter is applied, so it may be stale
    # (observed on a real I24: 4K in header although filter 1 with 1K was used)
    header[3] = DyscomFrequencyOut.SAMPLES_PER_SECOND_4K
    header[4] = dsp_filter
    # number of signal types and their file specific ids (3 -> BI, 4 -> EMG_1)
    header[10] = 2
    header[11] = 3
    header[12] = 4
    body = b"".join(struct.pack("<Iff", *sample) for sample in samples)
    return bytes(header) + body


def test_get_meas_file_content_parses_last_sample_ending_at_file_end():
    # regression test: the loop condition used "<" instead of "<=", so the last
    # sample was dropped whenever the file ended exactly at a sample boundary
    samples = [(1, 1.0, 10.0), (2, 2.0, 20.0), (3, 3.0, 30.0)]
    dyscom = DeviceI24(NullConnection()).get_layer_dyscom()

    with patch.object(dyscom, "get_file_content", new_callable=AsyncMock, return_value=_build_meas_file(samples)):
        sample_rate, result = asyncio.run(dyscom.get_meas_file_content("test"))

    assert sample_rate == DyscomFrequencyOut.SAMPLES_PER_SECOND_1K
    assert result[DyscomSignalType.BI] == [1.0, 2.0, 3.0]
    assert result[DyscomSignalType.EMG_1] == [10.0, 20.0, 30.0]


def test_get_meas_file_content_ignores_incomplete_trailing_sample():
    samples = [(1, 1.0, 10.0), (2, 2.0, 20.0)]
    dyscom = DeviceI24(NullConnection()).get_layer_dyscom()
    # append a truncated sample, which must not be parsed
    content = _build_meas_file(samples) + b"\x00" * 5

    with patch.object(dyscom, "get_file_content", new_callable=AsyncMock, return_value=content):
        _, result = asyncio.run(dyscom.get_meas_file_content("test"))

    assert result[DyscomSignalType.BI] == [1.0, 2.0]
    assert result[DyscomSignalType.EMG_1] == [10.0, 20.0]


def test_get_meas_file_content_derives_sample_rate_from_filter_not_stale_header_frequency():
    dyscom = DeviceI24(NullConnection()).get_layer_dyscom()
    expected = {DyscomFilterType.FILTER_OFF: DyscomFrequencyOut.SAMPLES_PER_SECOND_4K,
                DyscomFilterType.PREDEFINED_FILTER_1: DyscomFrequencyOut.SAMPLES_PER_SECOND_1K,
                DyscomFilterType.PREDEFINED_FILTER_2: DyscomFrequencyOut.SAMPLES_PER_SECOND_4K,
                DyscomFilterType.PREDEFINED_FILTER_3: DyscomFrequencyOut.SAMPLES_PER_SECOND_1K}

    for dsp_filter, sample_rate in expected.items():
        content = _build_meas_file([(1, 1.0, 10.0)], dsp_filter)
        with patch.object(dyscom, "get_file_content", new_callable=AsyncMock, return_value=content):
            result_sample_rate, _ = asyncio.run(dyscom.get_meas_file_content("test"))
        assert result_sample_rate == sample_rate


def _run_init(params: DyscomInitParams):
    dyscom = DeviceI24(NullConnection()).get_layer_dyscom()
    ack = PacketDyscomInitAck(bytes(89))
    with patch.object(dyscom, "send_packet_and_wait", new_callable=AsyncMock, return_value=ack):
        asyncio.run(dyscom.init(params))


@pytest.mark.parametrize("duration", [datetime.timedelta(0), datetime.timedelta(seconds=59),
                                      datetime.timedelta(hours=24), datetime.timedelta(days=2)])
def test_init_warns_for_sd_storage_mode_with_duration_stopping_immediately(caplog, duration):
    # firmware stops a sd recording at the minute boundary of start time + duration, compared by
    # hour and minute only, so with a duration of 0 (default) or 24 hours a recording stops almost
    # immediately (both verified on a real I24)
    params = DyscomInitParams()
    params.flags = {DyscomInitFlag.ENABLE_SD_STORAGE_MODE}
    params.duration = duration

    with caplog.at_level(logging.WARNING, logger="science_mode_4"):
        _run_init(params)

    assert any(r.levelno == logging.WARNING and "duration" in r.getMessage() for r in caplog.records)


@pytest.mark.parametrize("duration", [datetime.timedelta(seconds=60), datetime.timedelta(minutes=2),
                                      datetime.timedelta(hours=23, minutes=59, seconds=59)])
def test_init_does_not_warn_for_sd_storage_mode_with_sufficient_duration(caplog, duration):
    params = DyscomInitParams()
    params.flags = {DyscomInitFlag.ENABLE_SD_STORAGE_MODE}
    params.duration = duration

    with caplog.at_level(logging.WARNING, logger="science_mode_4"):
        _run_init(params)

    assert not any(r.levelno == logging.WARNING for r in caplog.records)


def test_init_does_not_warn_for_live_data_mode(caplog):
    params = DyscomInitParams()
    params.flags = {DyscomInitFlag.ENABLE_LIVE_DATA_MODE}

    with caplog.at_level(logging.WARNING, logger="science_mode_4"):
        _run_init(params)

    assert not any(r.levelno == logging.WARNING for r in caplog.records)


def _send_file_packet(block_number: int, payload: bytes) -> PacketDyscomSendFile:
    return PacketDyscomSendFile(struct.pack(">IH", block_number, len(payload)) + payload)


def _run_get_file_content(packets: list, number_of_blocks: int, filesize: int, block_timeout_in_seconds: float = 5):
    """Runs get_file_content with a mocked device, packets are returned one by one by the packet buffer
    (None means no packet available), returns layer mock state and result or raised exception"""
    dyscom = DeviceI24(NullConnection()).get_layer_dyscom()
    file_by_name = DyscomGetFileByNameResult("test", 0, filesize, number_of_blocks, DyscomFileByNameMode.MULTI_BLOCK)
    remaining = list(packets)

    def get_packet_from_buffer(*_args):
        if remaining:
            item = remaining.pop(0)
            if isinstance(item, BaseException):
                raise item
            return item
        return None

    with patch.object(dyscom, "get_operation_mode", new_callable=AsyncMock, return_value=DyscomGetOperationModeType.IDLE), \
         patch.object(dyscom, "get_file_by_name", new_callable=AsyncMock, return_value=file_by_name), \
         patch.object(dyscom, "start", new_callable=AsyncMock), \
         patch.object(dyscom, "stop", new_callable=AsyncMock) as stop, \
         patch.object(dyscom, "send_send_file_ack") as send_ack, \
         patch.object(dyscom.packet_buffer, "get_packet_from_buffer", side_effect=get_packet_from_buffer):
        try:
            result = asyncio.run(dyscom.get_file_content("test", block_timeout_in_seconds))
        except Exception as e: # pylint:disable=broad-exception-caught
            result = e
    return result, stop, send_ack


def test_get_file_content_returns_blocks_trimmed_to_filesize():
    result, stop, send_ack = _run_get_file_content(
        [_send_file_packet(1, b"abcd"), None, _send_file_packet(2, b"efgh")], number_of_blocks=2, filesize=6)

    assert result == b"abcdef"
    assert [c.args[0] for c in send_ack.call_args_list] == [1, 2]
    stop.assert_awaited_once()


def test_get_file_content_ignores_duplicate_block():
    # regression test: every received block was appended, so a duplicate corrupted the content
    result, _, send_ack = _run_get_file_content(
        [_send_file_packet(1, b"abcd"), _send_file_packet(1, b"abcd"), _send_file_packet(2, b"efgh")],
        number_of_blocks=2, filesize=8)

    assert result == b"abcdefgh"
    assert [c.args[0] for c in send_ack.call_args_list] == [1, 2]


def test_get_file_content_raises_on_missing_block_and_stops_transfer():
    # regression test: the receive loop had no timeout, so a missing block (device never
    # resends one) made get_file_content hang forever and the device stayed in DATATRANSFER
    result, stop, _ = _run_get_file_content([_send_file_packet(1, b"abcd")], number_of_blocks=2, filesize=8,
                                            block_timeout_in_seconds=0.05)

    assert isinstance(result, ProtocolError)
    assert "block 2 of 2" in str(result)
    stop.assert_awaited_once()


def test_get_file_content_stops_transfer_and_keeps_original_error_if_stop_fails():
    dyscom_error = RuntimeError("connection lost")
    dyscom = DeviceI24(NullConnection()).get_layer_dyscom()
    file_by_name = DyscomGetFileByNameResult("test", 0, 4, 1, DyscomFileByNameMode.MULTI_BLOCK)

    with patch.object(dyscom, "get_operation_mode", new_callable=AsyncMock, return_value=DyscomGetOperationModeType.IDLE), \
         patch.object(dyscom, "get_file_by_name", new_callable=AsyncMock, return_value=file_by_name), \
         patch.object(dyscom, "start", new_callable=AsyncMock), \
         patch.object(dyscom, "stop", new_callable=AsyncMock, side_effect=ProtocolError("stop failed")) as stop, \
         patch.object(dyscom.packet_buffer, "get_packet_from_buffer", side_effect=dyscom_error):
        with pytest.raises(RuntimeError) as exc_info:
            asyncio.run(dyscom.get_file_content("test"))

    assert exc_info.value is dyscom_error
    stop.assert_awaited_once()


def test_get_file_content_with_zero_blocks_returns_empty_content():
    result, stop, send_ack = _run_get_file_content([], number_of_blocks=0, filesize=0)

    assert result == b""
    send_ack.assert_not_called()
    stop.assert_awaited_once()
