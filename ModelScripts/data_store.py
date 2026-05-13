# data_store.py
# The main data buffer which stores incoming data rows. Thread safe and emits signals when data added or cleared. Used by SerialManager to feed data to the app and by PlaybackManager for playback.

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from collections import deque
from typing import Optional
import threading

class DataStore(QObject):
    data_added = pyqtSignal(dict)      
    data_batch_added = pyqtSignal(list)
    data_cleared = pyqtSignal()   
    _BATCH_INTERVAL_MS = 16  # 60 Hz batch emission

    def __init__(self, max_size: int = 10000):
        super().__init__()
        self._max_size = max_size
        self._buffer = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._total_received = 0

        # Pending rows waiting to be emitted as a batch
        self._pending_batch = []
        self._pending_lock = threading.Lock()

        # Timer to flush pending batch to signal consumers
        self._batch_timer = QTimer()
        self._batch_timer.setInterval(self._BATCH_INTERVAL_MS)
        self._batch_timer.timeout.connect(self._flush_batch)
        self._batch_timer.start()
    
    # =-= Add Data =-=
    def add(self, row: dict) -> None:
        with self._lock:
            self._buffer.append(row)
            self._total_received += 1
        with self._pending_lock:
            self._pending_batch.append(row)

    # Flush pending batch to emit signal, called by timer
    def _flush_batch(self):
        with self._pending_lock:
            if not self._pending_batch:
                return
            batch = self._pending_batch
            self._pending_batch = []
        self.data_batch_added.emit(batch)

    # Add multiple rows at once, used for file loading to bypass batch timer and emit all at once
    def add_silent(self, rows: list) -> None:
        if not rows:
            return
        with self._lock:
            for row in rows:
                self._buffer.append(row)
                self._total_received += 1
        self.data_batch_added.emit(rows)

    # 
    def add_bulk(self, rows: list, unlimited: bool = False) -> None:
        if not rows:
            return

        with self._lock:
            if unlimited and len(rows) > self._max_size:
                # Replace buffer with unlimited deque for bulk loading
                self._buffer = deque(rows)
                self._total_received += len(rows)
            else:
                # Normal behavior with size limit
                for row in rows:
                    self._buffer.append(row)
                    self._total_received += 1

        self.data_added.emit(rows[-1])
    
    # =-= Retrieve Data =-=
    # Get most recent n rows from buffer, n=1 default
    def get_latest(self, count: int = 1) -> list:
        with self._lock:
            if count >= len(self._buffer):
                return list(self._buffer)
            return list(self._buffer)[-count:]
    
    # Gets all rows in buffer, oldest first    
    def get_all(self) -> list:
        with self._lock:
            return list(self._buffer)
    
    # Gets single row by buffer index, 0 oldest, -1 newest
    def get_at(self, index: int) -> Optional[dict]:
        with self._lock:
            if 0 <= index < len(self._buffer):
                return self._buffer[index].copy()
            return None
        
    # Extract values for one channel across all rows, optionally limited to recent count
    def get_channel_data(self, channel_name: str, count: Optional[int] = None) -> list:
        with self._lock:
            if count is None:
                source = list(self._buffer)
            else:
                source = list(self._buffer)[-count:]

        return [row[channel_name] for row in source if channel_name in row]

    # Get column names from the most recent row.
    def get_channel_names(self) -> list:
        with self._lock:
            if not self._buffer:
                return []
            return list(self._buffer[-1].keys())

    # =-= Buffer Management =-=
    # Empty the buffer, used by reset and clear, emit signal to reset plots
    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()

        self.data_cleared.emit()

    # Current number of rows in the buffer
    def size(self) -> int:
        with self._lock:
            return len(self._buffer)
    
    # Check if buffer has no data
    def is_empty(self) -> bool:
        with self._lock:
            return len(self._buffer) == 0

    # Total rows ever added, including those dropped by max_size truncation.
    def total_received(self) -> int:
        with self._lock:
            return self._total_received

    @property
    # Maximum buffer capacity
    def max_size(self) -> int:
        return self._max_size
    # Get information about current buffer status for display in UI
    def get_stats(self) -> dict:
        with self._lock:
            current = len(self._buffer)
            return {
                'current_size': current,
                'max_size': self._max_size,
                'total_received': self._total_received,
                'percent_full': round((current / self._max_size) * 100, 1)
            }