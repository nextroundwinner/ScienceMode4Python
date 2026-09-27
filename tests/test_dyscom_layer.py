"""Tests for LayerDyscom"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

import asyncio
import datetime
import logging
import struct
from unittest.mock import AsyncMock, patch

from science_mode_4.device_i24 import DeviceI24
from science_mode_4.dyscom.dyscom_init import PacketDyscomInitAck
from science_mode_4.dyscom.dyscom_types import DyscomFilterType, DyscomFrequencyOut, DyscomInitFlag, DyscomInitParams,     DyscomSignalType
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


def test_init_warns_for_sd_storage_mode_with_duration_below_one_minute(caplog):
    # firmware stops a sd recording at the minute boundary of start time + duration, so
    # with the default duration of 0 a recording stops almost immediately (verified on a real I24)
    params = DyscomInitParams()
    params.flags = {DyscomInitFlag.ENABLE_SD_STORAGE_MODE}

    with caplog.at_level(logging.WARNING, logger="science_mode_4"):
        _run_init(params)

    assert any(r.levelno == logging.WARNING and "duration" in r.getMessage() for r in caplog.records)


def test_init_does_not_warn_for_sd_storage_mode_with_sufficient_duration(caplog):
    params = DyscomInitParams()
    params.flags = {DyscomInitFlag.ENABLE_SD_STORAGE_MODE}
    params.duration = datetime.timedelta(minutes=2)

    with caplog.at_level(logging.WARNING, logger="science_mode_4"):
        _run_init(params)

    assert not any(r.levelno == logging.WARNING for r in caplog.records)


def test_init_does_not_warn_for_live_data_mode(caplog):
    params = DyscomInitParams()
    params.flags = {DyscomInitFlag.ENABLE_LIVE_DATA_MODE}

    with caplog.at_level(logging.WARNING, logger="science_mode_4"):
        _run_init(params)

    assert not any(r.levelno == logging.WARNING for r in caplog.records)
