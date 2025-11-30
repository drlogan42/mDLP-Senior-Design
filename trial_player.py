# trial_player.py
# Contains the logic for reading a recorded CSV file and publishing it over ZMQ.

import zmq
import csv
import time
import json
import os
from PyQt6.QtCore import QObject, QThread, pyqtSignal

class TrialPlayerWorker(QObject):
    """
    Worker class to handle file reading and ZMQ publishing in a separate QThread.
    """
    finished = pyqtSignal()
    status_update = pyqtSignal(str, str, bool) # message, color, bold

    def __init__(self, file_path, address):
        super().__init__()
        self.file_path = file_path
        self.address = address
        self._running = True
        self.context = None
        self.socket = None
        self.data_rows = []
        self.data_loaded = False
        
    def _load_data(self):
        """Load data from CSV into memory."""
        self.data_rows = []
        try:
            with open(self.file_path, 'r', newline='') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                # Verify header columns
                expected_header = ["Elapsed_Time_s", "Recording_Time_s", "Voltage_V", "Current_A"]
                if header != expected_header:
                    raise ValueError(f"CSV header format is incorrect. Expected: {expected_header}, Found: {header}")
                    
                for row in reader:
                    self.data_rows.append({
                        "elapsed_time": float(row[0]),
                        "recording_time": float(row[1]),
                        "voltage": float(row[2]),
                        "current": float(row[3])
                    })
            self.data_loaded = True
            self.status_update.emit(f"File loaded: {len(self.data_rows)} samples.", "blue", True)
            
        except Exception as e:
            self.status_update.emit(f"Playback Error: Failed to load file. {e}", "red", True)
            self._running = False
            self.data_loaded = False

    def run(self):
        """Main loop for ZMQ Publisher thread."""
        self._load_data()
        
        if not self.data_loaded:
            self.finished.emit()
            return

        try:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.PUB)
            # LINGER 0 ensures the socket doesn't hang around after we close it
            self.socket.setsockopt(zmq.LINGER, 0)
            
            # --- ROBUST BINDING STRATEGY ---
            # Try to bind multiple times to handle OS holding the port (TIME_WAIT)
            bound = False
            for attempt in range(5):
                if not self._running: break
                try:
                    self.socket.bind(self.address)
                    bound = True
                    break
                except zmq.error.ZMQError:
                    self.status_update.emit(f"Port busy, retrying ({attempt+1}/5)...", "orange", False)
                    time.sleep(0.5)
            
            if not bound:
                raise zmq.error.ZMQError("Address already in use (Simulator failed to release port).")

            self.status_update.emit(f"Playback Started on {self.address}", "blue", True)
            
            # Allow time for subscribers to connect
            time.sleep(0.5) 
            
            t_start_playback = time.time()
            data_sent = 0

            # --- Playback Loop ---
            for i, row in enumerate(self.data_rows):
                if not self._running:
                    break
                    
                expected_time = row["recording_time"]
                current_time = time.time() - t_start_playback
                
                sleep_duration = expected_time - current_time
                if sleep_duration > 0:
                    time.sleep(sleep_duration)

                data_packet = {
                    "timestamp": row["elapsed_time"],
                    "voltage": row["voltage"],
                    "current": row["current"]
                }
                
                json_payload = json.dumps(data_packet)
                self.socket.send_string(json_payload)
                data_sent = i + 1
                
                if data_sent % 50 == 0:
                     self.status_update.emit(
                        f"Playing: {data_sent}/{len(self.data_rows)} | T: {current_time:.2f}s", 
                        "green", False
                    )

            if self._running:
                self.status_update.emit(f"Playback finished. Sent {data_sent} samples.", "blue", True)

        except zmq.error.ZMQError as e:
            self.status_update.emit(f"ZMQ Playback Error: {e}", "red", True)
        except Exception as e:
            self.status_update.emit(f"Fatal Playback Error: {e}", "red", True)
        finally:
            self.stop()
            self.finished.emit()

    def stop(self):
        """Gracefully stop the thread and close the ZMQ socket."""
        self._running = False
        if self.socket:
            try:
                self.socket.unbind(self.address)
            except zmq.error.ZMQError:
                pass
            self.socket.close()
            self.socket = None
        if self.context:
            self.context.term()
            self.context = None