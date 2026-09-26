"""Tests for LayerDyscom"""
# pylint: disable=missing-function-docstring
# test names are self-explanatory, docstrings would only restate them

import asyncio
import struct
from unittest.mock import AsyncMock, patch

from science_mode_4.device_i24 import DeviceI24
from science_mode_4.dyscom.dyscom_types import DyscomFrequencyOut, DyscomSignalType
from science_mode_4.utils.null_connection import NullConnection


def _build_meas_file(samples: list[tuple[int, float, float]]) -> bytes:
    """Builds measurement file content with a 512 byte header and two signal types (BI, EMG_1)"""
    header = bytearray(512)
    header[3] = DyscomFrequencyOut.SAMPLES_PER_SECOND_1K
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
