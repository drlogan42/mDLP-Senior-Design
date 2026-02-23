'''
PlaybackManager loads CSV files and feeds rows to data_store on a timer to emulate serial data input for playback mode.

Model:
- Loads CSV file into memory once
- Uses QTimer to emit rows at controlled rate
Controller calls load_file(), play(), stop().
This calls data_store.add() on each timer tick.
'''

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
import csv
from pathlib import Path
from typing import Optional

class PlaybackManager(QObject):
    playback_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    state_changed = pyqtSignal(str)

    def __init__(self, data_store, playback_rate_ms: int = 100):
        super().__init__()
        self._data_store = data_store
        self._playback_rate_ms = playback_rate_ms

        # Playback state
        self._loaded_rows = []
        self._current_index = 0
        self._is_playing = False
        self._file_path = None

        # Timer for row-by-row emission
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer_tick)

        self._set_state("idle")
    
    # =-= File Loading =-=
    def load_file(self, file_path: str) -> bool:
        try:
            path = Path(file_path)
            if not path.exists():
                self.error_occurred.emit(f"File not found: {file_path}")
                return False
            
            if path.suffix.lower() != '.csv':
                self.error_occurred.emit(f"Not a CSV file: {path.suffix}")
                return False
            
            # Read CSV into list of dicts
            self._loaded_rows = []
            with open(path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    parsed_row = self._parse_row(row)
                    self._loaded_rows.append(parsed_row)
            
            if not self._loaded_rows:
                self.error_occurred.emit("CSV file is empty")
                return False
        
            # Reset playback state
            self._current_index = 0
            self._file_path = file_path
            self._set_state("loaded")
            
            return True
        
        except Exception as e:
            self.error_occurred.emit(f"Error loading file: {str(e)}")
            return False
    
    def _parse_row(self, row: dict) -> dict:
        parsed = {}
        for key, value in row.items():
            try:
                # Try int first (for frame_id, packet_id, adc counts)
                if '.' not in value:
                    parsed[key] = int(value)
                else:
                    parsed[key] = float(value)
            except (ValueError, TypeError):
                # Keep as string if conversion fails
                parsed[key] = value
        return parsed
    
    # =-= Playback Control =-=
    def play(self) -> None:
        if not self._loaded_rows:
            self.error_occurred.emit("No file loaded")
            return

        if self._is_playing:
            return  # Already playing
    
        # Wont want this in final product but testing with looping playback for now
        if self._current_index >= len(self._loaded_rows):
            # At end, restart from beginning
            self._current_index = 0

        self._is_playing = True
        self._timer.start(self._playback_rate_ms)
        self._set_state("playing")
    
    def stop(self) -> None:
        self._timer.stop()
        self._is_playing = False
        self._current_index = 0

        if self._loaded_rows:
            self._set_state("loaded")
        else:
            self._set_state("idle")

    def pause(self) -> None:
        if self._is_playing:
            self._timer.stop()
            self._is_playing = False
            self._set_state("paused")
    
    def _on_timer_tick(self) -> None:
        if self._current_index >= len(self._loaded_rows):
            # Reached end of file
            self.stop()
            self._set_state("finished")
            self.playback_finished.emit()
            return

        # Get current row and send to data_store
        current_row = self._loaded_rows[self._current_index]
        self._data_store.add(current_row)

        # Advance to next row
        self._current_index += 1

    # =-= State Management =-=

    def _set_state(self, new_state: str) -> None:
        self.state_changed.emit(new_state)

    def is_playing(self) -> bool:
        return self._is_playing

    def is_loaded(self) -> bool:
        return len(self._loaded_rows) > 0

    def get_progress(self) -> tuple:
        return (self._current_index, len(self._loaded_rows))

    def get_file_info(self) -> dict:
        if not self._loaded_rows:
            return {'loaded': False}

        return {
            'loaded': True,
            'filename': Path(self._file_path).name if self._file_path else "Unknown",
            'row_count': len(self._loaded_rows),
            'channels': list(self._loaded_rows[0].keys()) if self._loaded_rows else [],
            'current_row': self._current_index
        }

    def set_playback_rate(self, rate_ms: int) -> None:
        self._playback_rate_ms = max(10, rate_ms)  # Prevent too-fast rates
        if self._is_playing:
            self._timer.setInterval(self._playback_rate_ms)

    def get_playback_rate(self) -> int:
        """Get current playback rate in milliseconds."""
        return self._playback_rate_ms

