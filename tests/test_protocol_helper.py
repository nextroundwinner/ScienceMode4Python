"""Tests for ProtocolHelper.send_packet_and_wait"""
# pylint: disable=missing-function-docstring,protected-access
# test names are self-explanatory, docstrings would only restate them

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from science_mode_4.protocol.commands import Commands
from science_mode_4.protocol.exceptions import ProtocolError
from science_mode_4.protocol.protocol_helper import ProtocolHelper


def _fake_ack(command: int, number: int):
    return SimpleNamespace(command=command, number=number)


def _make_request_packet(command: int, number: int):
    return SimpleNamespace(command=command, number=number, get_data=lambda: b"")


def test_stale_acks_are_drained_without_sleeping_between_them():
    # regression test: the inner loop used to unconditionally "break" after
    # inspecting a single packet, even when it was discarded as stale/mismatched,
    # so each stale ack cost a full asyncio.sleep(0.01) cycle before the buffer was
    # checked again. Multiple queued stale acks should now be drained in one pass,
    # with no sleep needed as long as the matching ack is already available.
    request = _make_request_packet(command=10, number=3)
    matching_ack = _fake_ack(command=11, number=3)

    packet_buffer = MagicMock()
    packet_buffer.get_packet_from_buffer.side_effect = [
        _fake_ack(command=99, number=3),   # stale: wrong command
        _fake_ack(command=11, number=7),   # stale: wrong number
        matching_ack,
    ]

    with patch("science_mode_4.protocol.protocol_helper.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = asyncio.run(ProtocolHelper.send_packet_and_wait(request, request.number, packet_buffer))

    assert result is matching_ack
    assert packet_buffer.get_packet_from_buffer.call_count == 3
    mock_sleep.assert_not_called()


def test_general_error_ack_raises_immediately():
    request = _make_request_packet(command=10, number=1)
    error_ack = SimpleNamespace(command=Commands.GENERAL_ERROR, number=1,
                                 result_error=SimpleNamespace(name="PARAMETER_ERROR"))

    packet_buffer = MagicMock()
    packet_buffer.get_packet_from_buffer.side_effect = [error_ack]

    with patch("science_mode_4.protocol.protocol_helper.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ProtocolError):
            asyncio.run(ProtocolHelper.send_packet_and_wait(request, request.number, packet_buffer))


def test_no_ack_available_still_sleeps_and_eventually_times_out():
    request = _make_request_packet(command=10, number=1)

    packet_buffer = MagicMock()
    packet_buffer.get_packet_from_buffer.return_value = None

    with patch("science_mode_4.protocol.protocol_helper.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(ProtocolError):
            asyncio.run(ProtocolHelper.send_packet_and_wait(
                request, request.number, packet_buffer, timeout_in_seconds=0.03))

    assert mock_sleep.call_count > 0
    packet_buffer.remove_open_acknowledge.assert_called_once_with(request)
