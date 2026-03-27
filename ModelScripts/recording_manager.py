'''
RecordingManager - Saves incoming data to CSV
'''

from PyQt6.QtCore import QObject, pyqtSignal
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional

class RecordingManager(QObject):

    recording_started = pyqtSignal(str)  # filename
    recording_stopped = pyqtSignal(int)  # packet count
    error_occurred = pyqtSignal(str)     # error message
    state_changed = pyqtSignal(str)      # state

    def __init__(self, data_store):
        super().__init__()
        self._data_store = data_store
        
        # Recording state
        self._is_recording = False
        self._output_folder = Path.home() / "Documents"  # Default folder
        self._current_file = None
        self._csv_writer = None
        self._file_handle = None
        self._packet_count = 0
        self._headers_written = False
        
        # Connect to data store
        self._data_store.data_added.connect(self._on_data_received)
        self._data_store.data_batch_added.connect(self._on_batch_received)
        
        self._set_state("idle")
    
    # =-= Recording Control =-=

    def set_output_folder(self, folder_path: str) -> bool:
        try:
            path = Path(folder_path)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            
            if not path.is_dir():
                self.error_occurred.emit(f"Not a directory: {folder_path}")
                return False
            
            self._output_folder = path
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Invalid folder: {str(e)}")
            return False
        
    def start_recording(self, filename: Optional[str] = None) -> bool:
        if self._is_recording:
            self.error_occurred.emit("Already recording")
            return False
        
        try:
            # Generate filename if not provided
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"recording_{timestamp}.csv"
            
            # Ensure .csv extension
            if not filename.endswith('.csv'):
                filename += '.csv'
            
            # Create full file path
            self._current_file = self._output_folder / filename
            
            # Open file for writing
            self._file_handle = open(self._current_file, 'w', newline='')
            self._csv_writer = csv.writer(self._file_handle)
            
            # Reset state
            self._packet_count = 0
            self._headers_written = False
            self._is_recording = True
            
            self._set_state("recording")
            self.recording_started.emit(str(self._current_file))
            
            return True
            
        except Exception as e:
            self._cleanup()
            self.error_occurred.emit(f"Failed to start recording: {str(e)}")
            return False

    def stop_recording(self) -> bool:
        if not self._is_recording:
            return True
        
        try:
            self._cleanup()
            self._set_state("idle")
            self.recording_stopped.emit(self._packet_count)
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Error stopping recording: {str(e)}")
            return False
        
    def _cleanup(self):
        self._is_recording = False
        
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None
        
        self._csv_writer = None
        self._current_file = None
        self._headers_written = False

    # Data Handling
    def _on_batch_received(self, rows: list):
        for row in rows:
            self._on_data_received(row)

    def _on_data_received(self, row: dict):
        if not self._is_recording or not self._csv_writer:
            return
        
        try:
            # Filter out metadata fields (starting with _)
            data_row = {k: v for k, v in row.items() if not k.startswith('_')}
            
            # Write headers on first row
            if not self._headers_written:
                headers = list(data_row.keys())
                self._csv_writer.writerow(headers)
                self._headers_written = True
            
            # Write data row
            values = list(data_row.values())
            self._csv_writer.writerow(values)
            
            # Flush to disk periodically
            self._packet_count += 1
            if self._packet_count % 10 == 0:
                self._file_handle.flush()
            
        except Exception as e:
            self.error_occurred.emit(f"Recording write error: {str(e)}")
            self.stop_recording()

    # State and Info
    def _set_state(self, new_state: str):
        self.state_changed.emit(new_state)
    
    def is_recording(self) -> bool:
        return self._is_recording
    
    def get_output_folder(self) -> str:
        return str(self._output_folder)
    
    def get_current_file(self) -> Optional[str]:
        if self._current_file:
            return str(self._current_file)
        return None
    
    def get_packet_count(self) -> int:
        return self._packet_count
    
    def get_info(self) -> dict:
        return {
            'is_recording': self._is_recording,
            'output_folder': str(self._output_folder),
            'current_file': str(self._current_file) if self._current_file else None,
            'packet_count': self._packet_count
        }

    