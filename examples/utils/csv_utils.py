"""Provides a class to write values asynchronous to a .csv file"""


import csv
from queue import Empty, Full, Queue
import threading


class CsvHelper:
    """Class for holding values and write to .csv file"""


    def __init__(self, filename: str, header: list[str]):
        self._filename = filename
        self._header = header

        # this queue is used to synchronize data between background and main thread
        self._data_queue = Queue(maxsize=0)
        self._is_running = False


    def start(self):
        """Start background tread"""

        self._is_running = True

        # Create and start the data generator thread (aka background thread)
        data_thread = threading.Thread(target=self._background_task, daemon=True)
        data_thread.start()


    def stop(self):
        """Stop background thread"""
        self._is_running = False


    def append_values(self, package_nr: int, values: list[float], time_delta: int):
        """Appends values, runs in main thread context"""
        try:
            self._data_queue.put_nowait([package_nr] + values + [time_delta])
        except Full:
            # Queue is full, skip this update
            pass


    def _background_task(self):
        with open(self._filename, "w", encoding="utf-8", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(self._header)

            while self._is_running:
                try:
                    # blocking get with timeout: releases the GIL while waiting instead
                    # of busy-spinning, which was starving the main thread doing serial I/O
                    data = self._data_queue.get(timeout=0.1)
                    csv_writer.writerow(data)
                except Empty:
                    # No new data in the queue
                    pass
