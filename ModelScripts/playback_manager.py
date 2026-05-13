# playback_manager.py
# Manages playback of recorded CSV files. Loads files, parses them, and emits data to DataStore at scheduled intervals to simulate real-time streaming.
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QElapsedTimer
import csv
from pathlib import Path
from ModelScripts.mdlp_parser import MDLPParser, is_raw_mdlp_format

class PlaybackManager(QObject):
    playback_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    state_changed = pyqtSignal(str)
    tick_updated = pyqtSignal() 

    # Timer for controlled playback ticks
    _TICK_INTERVAL_MS = 16  # ~60 fps

    def __init__(self, data_store, playback_rate_ms: int = 100):
        super().__init__()
        self._data_store = data_store
        self._playback_rate_ms = playback_rate_ms

        # Playback state
        self._loaded_rows = []
        self._current_index = 0
        self._is_playing = False
        self._file_path = None
        self._is_raw_format = False

        # Speed multiplier
        self._speed_multiplier = 1.0

        # Timing for playback scheduling
        self._elapsed = QElapsedTimer()
        self._playback_time_offset = 0.0  # data-time at which playback started
        self._wall_start_ms = 0  # elapsed ms when playback started/resumed

        # Timer for tick driven emission
        self._timer = QTimer()
        self._timer.setInterval(self._TICK_INTERVAL_MS)
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
            
            # Detect format and load accordingly
            self._is_raw_format = is_raw_mdlp_format(file_path)
            
            if self._is_raw_format:
                self._loaded_rows = self._load_raw_mdlp(file_path)
            else:
                self._loaded_rows = self._load_parsed_csv(file_path)
            
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
    
    # Internal loading methods
    def _load_raw_mdlp(self, file_path: str) -> list:
        file_parser = MDLPParser()
        parsed_rows = []
        
        # Connect to local list collector
        file_parser.packet_ready.connect(lambda row: parsed_rows.append(row))
        
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                # Extract timestamp
                time_val = None
                for time_col in ['Time [s]', 'Time_s_', 'time', 'Time']:
                    if time_col in row and row[time_col].strip():
                        time_val = float(row[time_col])
                        break
                
                # Extract byte value
                byte_val = None
                for val_col in ['Value', 'value', 'Data', 'data']:
                    if val_col in row and row[val_col].strip():
                        byte_val = int(float(row[val_col]))
                        break
                
                if time_val is not None and byte_val is not None:
                    file_parser.feed_byte(byte_val, time_val)
        
        return parsed_rows
    
    # For parsed CSV, just load all into memory 
    def _load_parsed_csv(self, file_path: str) -> list:
        rows = []
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                parsed_row = self._parse_row(row)
                rows.append(parsed_row)
        return rows

    # Convert values to appropriate types
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
    def bulk_load(self) -> bool:
        if not self._loaded_rows:
            self.error_occurred.emit("No file loaded")
            return False

        if self._is_playing:
            self.stop()

        self._data_store.add_bulk(self._loaded_rows, unlimited=True)
        self._current_index = len(self._loaded_rows)
        self._set_state("bulk_loaded")
        return True

    def play(self) -> None:
        if not self._loaded_rows:
            self.error_occurred.emit("No file loaded")
            return

        if self._is_playing:
            return  # Already playing
    
        if self._current_index >= len(self._loaded_rows):
            self._current_index = 0

        # Record the data-time origin for this playback session
        self._playback_time_offset = self._get_row_time(self._current_index)
        self._elapsed.start()
        self._wall_start_ms = 0

        self._is_playing = True
        self._timer.start(self._TICK_INTERVAL_MS)
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
    
    # Resume from paused state
    def _get_row_time(self, index: int) -> float:
        row = self._loaded_rows[index]
        return row.get('timestamp', row.get('sample_time', row.get('Elapsed_Time_s', index * 0.001)))

    def _on_timer_tick(self) -> None:
        if self._current_index >= len(self._loaded_rows):
            self._timer.stop()
            self._is_playing = False
            self._current_index = 0
            self._set_state("finished")
            self.playback_finished.emit()
            return

        # Calc time elapsed in wall-clock since playback started/resumed
        wall_elapsed_s = self._elapsed.elapsed() / 1000.0
        data_elapsed = wall_elapsed_s * self._speed_multiplier
        target_time = self._playback_time_offset + data_elapsed

        # Collect all rows whose timestamp <= target_time
        batch = []
        while self._current_index < len(self._loaded_rows):
            row_time = self._get_row_time(self._current_index)
            if row_time > target_time:
                break
            batch.append(self._loaded_rows[self._current_index])
            self._current_index += 1
            if len(batch) >= 500:
                break

        if batch:
            self._data_store.add_silent(batch)
            self.tick_updated.emit()

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
            'current_row': self._current_index,
            'format': 'raw_mdlp' if self._is_raw_format else 'parsed_csv'
        }

    # =-= Playback Speed Control =-=
    def set_speed(self, multiplier: float) -> None:
        if multiplier <= 0:
            return
        # If playing, adjust the time origin so the switch is seamless
        if self._is_playing and self._current_index < len(self._loaded_rows):
            current_data_time = self._get_row_time(self._current_index)
            self._playback_time_offset = current_data_time
            self._elapsed.restart()
        self._speed_multiplier = multiplier

    def get_speed(self) -> float:
        return self._speed_multiplier

    def set_playback_rate(self, rate_ms: int) -> None:
        self._playback_rate_ms = max(10, rate_ms)
        if self._is_playing:
            self._timer.setInterval(self._playback_rate_ms)

    def get_playback_rate(self) -> int:
        return self._playback_rate_ms