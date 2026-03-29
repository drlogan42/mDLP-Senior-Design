'''
data_store.py is central data buffer for all incoming data

'''
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from collections import deque
from typing import Optional
import threading

class DataStore(QObject):
    # DataStore is thread-safe central data buffer

    data_added = pyqtSignal(dict)          # single row (legacy, used by bulk_load)
    data_batch_added = pyqtSignal(list)    # list of rows
    data_cleared = pyqtSignal()   

    # Batch emit interval — balances latency vs throughput
    _BATCH_INTERVAL_MS = 16  # 60 Hz batch emission for better responsiveness

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
        """Add single data row to buffer.
        
        Row is stored immediately but signal emission is batched
        via _flush_batch timer for performance at high data rates.
        """
        with self._lock:
            self._buffer.append(row)
            self._total_received += 1
        with self._pending_lock:
            self._pending_batch.append(row)

    def _flush_batch(self):
        """Emit accumulated rows as a single batch signal (called by timer)."""
        with self._pending_lock:
            if not self._pending_batch:
                return
            batch = self._pending_batch
            self._pending_batch = []
        self.data_batch_added.emit(batch)

    def add_silent(self, rows: list) -> None:
        """Add multiple rows in batch. Emits data_batch_added directly."""
        if not rows:
            return
        with self._lock:
            for row in rows:
                self._buffer.append(row)
                self._total_received += 1
        self.data_batch_added.emit(rows)

    # Dont know if i want to keep this if i want to read from a file as if serial
    def add_bulk(self, rows: list, unlimited: bool = False) -> None:

        # Add multiple rows at once without emitting per row for loading from file
        # emit single data_added with last row to trigger 
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

    def get_latest(self, count: int = 1) -> list:
        # Get most recent n rows from buffer, n=1 default
        with self._lock:
            if count >= len(self._buffer):
                return list(self._buffer)
            return list(self._buffer)[-count:]
        
    def get_all(self) -> list:
        # Gets all rows in buffer, oldest first
        with self._lock:
            return list(self._buffer)

    def get_at(self, index: int) -> Optional[dict]:
        # Gets single row by buffer index, 0 oldest, -1 newest
        with self._lock:
            if 0 <= index < len(self._buffer):
                return self._buffer[index].copy()
            return None
    
    def get_channel_data(self, channel_name: str, count: Optional[int] = None) -> list:
        # Extract values for one channel across all rows, optionally limited to recent count
        with self._lock:
            if count is None:
                source = list(self._buffer)
            else:
                source = list(self._buffer)[-count:]

        return [row[channel_name] for row in source if channel_name in row]

    def get_channel_names(self) -> list:
        # Get column names from the most recent row.
        with self._lock:
            if not self._buffer:
                return []
            return list(self._buffer[-1].keys())

    # =-= Buffer Management =-=
    def clear(self) -> None:
        # Empty the buffer, used by reset and clear, emit signal to reset plots
        with self._lock:
            self._buffer.clear()

        self.data_cleared.emit()

    def size(self) -> int:
        # Current number of rows in the buffer
        with self._lock:
            return len(self._buffer)

    def is_empty(self) -> bool:
        # Check if buffer has no data
        with self._lock:
            return len(self._buffer) == 0

    def total_received(self) -> int:
        # Total rows ever added, including those dropped by max_size truncation.
        # Useful for tracking data loss.
        with self._lock:
            return self._total_received

    @property
    def max_size(self) -> int:
        # Maximum buffer capacity
        return self._max_size
    def get_stats(self) -> dict:
        # Get information about current buffer status for display in UI
        with self._lock:
            current = len(self._buffer)
            return {
                'current_size': current,
                'max_size': self._max_size,
                'total_received': self._total_received,
                'percent_full': round((current / self._max_size) * 100, 1)
            }