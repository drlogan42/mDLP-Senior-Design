# zmq_controller.py
# Contains the ZMQ threading logic and the Julia process management (Controller and ZMQ Worker).

import sys
import os
import json
import zmq
import subprocess
import time 
import csv  
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication, QFileDialog 

# Import the new modular component
from trial_player import TrialPlayerWorker 

# Import config
from config import JULIA_BACKEND_PATH, JULIA_SIMULATOR_PATH, ZMQ_ADDRESS

# --- ZMQ Worker (Runs on a QThread) ---
class ZmqWorker(QObject):
    message_received = pyqtSignal(str) 
    
    def __init__(self, address):
        super().__init__()
        self.address = address
        self._running = True
        self.context = None
        self.socket = None

    def run(self):
        try:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.SUB)
            self.socket.connect(self.address)
            self.socket.setsockopt(zmq.SUBSCRIBE, b'')
            
            self.message_received.emit(f"ZMQ Worker connected to {self.address}")
            
            while self._running:
                if self.socket.poll(100, zmq.POLLIN):
                    message = self.socket.recv_string()
                    self.message_received.emit(message) 
                
            print("ZMQ Worker loop terminated.")
            
        except zmq.error.ContextTerminated:
            pass
        except Exception as e:
            self.message_received.emit(f"FATAL ZMQ ERROR: {e}")
        finally:
            if self.socket:
                self.socket.close()

    def stop(self):
        self._running = False
        if self.context:
            self.context.term()
            
# --- Scientific Controller ---

class ScientificController(QObject):
    
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.julia_backend_process = None 
        self.julia_simulator_process = None
        
        self.zmq_thread = None
        self.zmq_worker = None
        
        self.selected_file_path = None
        self.player_thread = None
        self.player_worker = None
        
        # FIX 2: Attribute to track if the player thread finished due to an error
        self._playback_error_occurred = False
        
        self.data_storage = {
            "timestamps": [],
            "voltage": [],
            "current": []
        }
        
        self.is_recording = False
        self.recording_start_time = 0.0
        self.recording_data_store = {
            "elapsed_time": [],   
            "recording_time": [], 
            "voltage": [],
            "current": []
        }
        
        QApplication.instance().aboutToQuit.connect(self.stop_all)
        
        window.start_backend_button.clicked.connect(self.start_backend)
        window.stop_backend_button.clicked.connect(self.stop_backend)
        window.start_simulator_button.clicked.connect(self.start_simulator)
        window.stop_simulator_button.clicked.connect(self.stop_simulator)
        window.start_recording_button.clicked.connect(self.start_recording)
        window.stop_recording_button.clicked.connect(self.stop_recording)
        window.select_file_button.clicked.connect(self.select_file)
        window.start_playback_button.clicked.connect(self.start_playback)
        window.stop_playback_button.clicked.connect(self.stop_playback)
        
    # FIX 2: Helper to update status and track errors
    def _update_playback_status_and_track_error(self, message, color, bold=False):
        """Updates the status label and sets a flag if an error occurred."""
        self.window.update_playback_status(message, color, bold)
        if color == "red":
            self._playback_error_occurred = True

    # --- Master Control (Column 1: Backend Listener) ---
    def start_backend(self):
        """Starts the main Julia Data Listener Backend and the ZMQ receiver."""
        if self.julia_backend_process is not None and self.julia_backend_process.poll() is None:
            self.window.update_backend_status("Backend already running.", "#000", True)
            return

        if not os.path.exists(JULIA_BACKEND_PATH):
            self.window.show_error("Error", f"Backend script not found: {JULIA_BACKEND_PATH}")
            return
        
        self.window.update_backend_status("Launching Julia Data Listener Backend...", "orange", True)
        
        try:
            self.data_storage = {"timestamps": [], "voltage": [], "current": []}
            # The Julia Backend process acts as the default publisher/binder
            self.julia_backend_process = subprocess.Popen(['julia', JULIA_BACKEND_PATH])
            
            self.zmq_thread = QThread()
            self.zmq_worker = ZmqWorker(ZMQ_ADDRESS)
            self.zmq_worker.moveToThread(self.zmq_thread)
            
            self.zmq_thread.started.connect(self.zmq_worker.run)
            self.zmq_worker.message_received.connect(self._handle_zmq_message)
            self.zmq_thread.start()
            
            self.window.start_monitoring(self.data_storage)
            
            self.window.set_backend_controls_enabled(True)
            self.window.set_simulator_controls_enabled(False) 
            self.window.set_recording_controls_enabled(False)
            self.window.set_playback_controls_enabled(
                file_selected=(self.selected_file_path is not None),
                is_playing=False,
                backend_running=True
            )
            
            self.window.update_backend_status("Backend Listener running. Ready for Instrument Data...", "blue", True)
            
        except Exception as e:
            self.window.show_error("Error", f"Failed to start Backend: {e}")
            self.stop_all()

    def stop_backend(self):
        """Stops the main Julia Data Listener Backend and ZMQ receiver."""
        self.stop_simulator() 
        self.stop_playback(restart_julia=False) 
        
        self.window.set_backend_controls_enabled(False)
        self.window.set_simulator_controls_enabled(False)
        self.window.set_recording_controls_enabled(False)
        self.window.set_playback_controls_enabled(False, False, False)
        
        self.is_recording = False 
        self.window.update_recording_status("Idle.", "#444")
        self.window.update_playback_status("Idle.", "#444")
        
        if self.zmq_worker:
            self.zmq_worker.stop()
        if self.zmq_thread:
            self.zmq_thread.quit()
            self.zmq_thread.wait(1000)
            self.zmq_thread = None
            self.zmq_worker = None

        if self.julia_backend_process:
            self.julia_backend_process.terminate()
            try:
                self.julia_backend_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                 self.julia_backend_process.kill() 
            self.julia_backend_process = None
            
        self.window.stop_monitoring()
        self.window.update_backend_status("Backend Listener STOPPED.", "red", True)
        
    def stop_all(self):
        self.stop_backend()

    # --- Utility Method ---
    def _restart_julia_backend_process(self):
        """Restarts the Julia Backend process (the default data publisher) if the overall backend is running."""
        if self.julia_backend_process is None and self.window.stop_backend_button.isEnabled():
            self.window.update_backend_status("Restarting Julia Backend Data Source...", "orange")
            try:
                self.julia_backend_process = subprocess.Popen(['julia', JULIA_BACKEND_PATH])
                self.window.update_backend_status("Julia Backend Data Source Running.", "blue", True)
            except Exception as e:
                self.window.update_backend_status(f"Error restarting Julia: {e}", "red", True)
                self.stop_all()

    # --- Simulator Control (Column 2) ---

    def start_simulator(self):
        """Starts the Julia Instrument Simulator (Data Sender)."""
        if self.julia_simulator_process is not None and self.julia_simulator_process.poll() is None:
            self.window.update_simulator_status("Simulator already running.", "gray", True)
            return
            
        if not self.window.stop_backend_button.isEnabled():
            self.window.update_simulator_status("Start backend first.", "red")
            return

        self.stop_playback()
            
        if not os.path.exists(JULIA_SIMULATOR_PATH):
            self.window.show_error("Error", f"Simulator script not found: {JULIA_SIMULATOR_PATH}")
            return
            
        self.window.update_simulator_status("Launching Instrument Simulator (Data Sender)...", "orange", True)
        
        try:
            self.julia_simulator_process = subprocess.Popen(['julia', JULIA_SIMULATOR_PATH])
            
            self.window.set_simulator_controls_enabled(True)
            self.window.set_recording_controls_enabled(False)
            self.window.set_playback_controls_enabled(False, False, True)
            self.window.update_simulator_status("Simulator: Sending Data", "green", True)
        
        except Exception as e:
            self.window.show_error("Error", f"Failed to start Simulator: {e}")
            self.stop_simulator()

    def stop_simulator(self):
        """Stops the Julia Instrument Simulator (Data Sender)."""
        if self.julia_simulator_process:
            self.julia_simulator_process.terminate()
            try:
                self.julia_simulator_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                 self.julia_simulator_process.kill() 
            self.julia_simulator_process = None
            
        backend_running = self.window.stop_backend_button.isEnabled() 
        self.window.set_simulator_controls_enabled(False)
        self.window.set_recording_controls_enabled(False)
        self.window.set_playback_controls_enabled(
            file_selected=(self.selected_file_path is not None),
            is_playing=False,
            backend_running=backend_running
        )
        self.is_recording = False
        self.window.update_recording_status("Idle.", "#444")
        self.window.update_simulator_status("Simulator: STOPPED.", "red", True)

    # --- Recording Control (Column 3) ---

    def start_recording(self):
        """Initializes and starts the data recording process."""
        if not self.window.stop_backend_button.isEnabled():
            self.window.update_recording_status("Cannot record: Backend Listener is not running.", "red", True)
            return
        
        if not (self.window.stop_simulator_button.isEnabled() or self.player_thread or self.julia_backend_process):
            self.window.update_recording_status("Cannot record: Data source is not running.", "red", True)
            return

        self.recording_data_store = {
            "elapsed_time": [],
            "recording_time": [],
            "voltage": [],
            "current": []
        }
        
        self.is_recording = True
        self.recording_start_time = time.time()
        self.window.set_recording_controls_enabled(True)
        self.window.update_recording_status("Recording data...", "green", True)

    def stop_recording(self):
        """Stops the recording and saves the collected data to a file."""
        if not self.is_recording:
            return

        self.is_recording = False
        self.window.set_recording_controls_enabled(False)
        
        self.window.update_recording_status("Saving data...", "orange", True)

        try:
            data_to_save = self.recording_data_store
            num_samples = len(data_to_save["elapsed_time"])

            if num_samples == 0:
                 self.window.update_recording_status("Recording STOPPED. No data recorded.", "red", True)
                 return
            
            timestamp_str = time.strftime("%Y%m%d_%H%M%S")
            filename = f"recorded_data_{timestamp_str}.csv"
            
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                
                writer.writerow(["Elapsed_Time_s", "Recording_Time_s", "Voltage_V", "Current_A"])
                
                for i in range(num_samples):
                    writer.writerow([
                        f"{data_to_save['elapsed_time'][i]:.4f}",
                        f"{data_to_save['recording_time'][i]:.4f}",
                        f"{data_to_save['voltage'][i]:.4f}",
                        f"{data_to_save['current'][i]:.6f}"
                    ])

            self.selected_file_path = filename # Auto-select the recorded file
            self.window.update_playback_status(
                f"File Selected: {os.path.basename(filename)}", 
                "blue", 
                True
            )

            self.window.update_recording_status(
                f"Recording STOPPED. Saved {num_samples} points to {filename}", 
                "blue", 
                True
            )

        except Exception as e:
            self.window.show_error("File Save Error", f"Failed to save data: {e}")
            self.window.update_recording_status("Recording STOPPED. Save FAILED.", "red", True)


    # --- NEW PLAYBACK CONTROL (Column 4) ---

    def select_file(self):
        """Opens a file dialog for selecting the recorded data file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self.window, 
            "Select Recorded Data File", 
            "", 
            "CSV Files (*.csv)"
        )

        backend_running = self.window.stop_backend_button.isEnabled()
        
        if filepath:
            self.selected_file_path = filepath
            self.window.update_playback_status(
                f"File Selected: {os.path.basename(filepath)}", 
                "blue", 
                True
            )
            self.window.set_playback_controls_enabled(
                file_selected=True, 
                is_playing=False, 
                backend_running=backend_running
            )
        else:
            self.selected_file_path = None
            self.window.update_playback_status("No file selected.", "orange")
            self.window.set_playback_controls_enabled(
                file_selected=False, 
                is_playing=False, 
                backend_running=backend_running
            )

    def start_playback(self):
        """Starts the playback worker thread, resolving ZMQ binding conflict."""
        if not self.selected_file_path:
            self.window.update_playback_status("Error: No file selected.", "red", True)
            return
            
        if not self.window.stop_backend_button.isEnabled():
            self.window.update_playback_status("Error: Start backend first.", "red", True)
            return

        # 1. Ensure all other publisher/recorder modes are off
        self.stop_simulator() 
        self.stop_recording() 
        
        # 2. Terminate the JULIA BACKEND process to free the ZMQ BIND port
        if self.julia_backend_process:
            self.window.update_backend_status("Stopping Julia Backend (data source) to enable Playback.", "orange")
            self.julia_backend_process.terminate()
            try:
                self.julia_backend_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                 self.julia_backend_process.kill() 
            self.julia_backend_process = None
            
        # FIX 1: Add delay to allow OS to release the port (TIME_WAIT state)
        QThread.msleep(200)

        # 3. Setup worker and thread (now binding is safe)
        self.player_thread = QThread()
        self.player_worker = TrialPlayerWorker(self.selected_file_path, ZMQ_ADDRESS)
        self.player_worker.moveToThread(self.player_thread)
        
        # FIX 2: Reset error flag
        self._playback_error_occurred = False 
        
        # 4. Connect signals (Use the new tracking method)
        self.player_thread.started.connect(self.player_worker.run)
        self.player_worker.finished.connect(self.stop_playback)
        self.player_worker.status_update.connect(self._update_playback_status_and_track_error)

        # 5. Start
        self.player_thread.start()
        
        self.window.set_playback_controls_enabled(
            file_selected=True, 
            is_playing=True, 
            backend_running=True
        )
        self.window.update_playback_status("Playback started...", "green", True)

    def stop_playback(self, restart_julia=True):
        """Stops the playback worker thread and restarts the Julia backend process."""
        if self.player_worker:
            self.player_worker.stop()
        if self.player_thread:
            self.player_thread.quit()
            self.player_thread.wait(1000)
            self.player_thread = None
            self.player_worker = None
            
        # 1. Restart the Julia Backend process to restore the original data source
        if restart_julia:
            self._restart_julia_backend_process() 
            
        # 2. Update controls
        backend_running = self.window.stop_backend_button.isEnabled()
        self.window.set_playback_controls_enabled(
            file_selected=(self.selected_file_path is not None), 
            is_playing=False, 
            backend_running=backend_running
        )
        
        # FIX 2: Only overwrite status if no error was reported by the thread
        if not self._playback_error_occurred:
             self.window.update_playback_status("Playback STOPPED.", "red", True)


    # --- Data Processing Logic ---

    def _handle_zmq_message(self, message):
        """
        Parses JSON packets for Voltage/Current, stores them, and handles recording.
        """
        if "FATAL" in message:
            self.window.update_backend_status(message, "red", True)
            self.stop_all()
        elif "ZMQ Worker connected" in message:
            self.window.update_backend_status(message, "blue", True)
            
            backend_running = self.window.stop_backend_button.isEnabled()
            self.window.set_simulator_controls_enabled(False) 
            self.window.set_recording_controls_enabled(False)
            self.window.set_playback_controls_enabled(
                file_selected=(self.selected_file_path is not None),
                is_playing=False,
                backend_running=backend_running
            )
            
        else:
            try:
                data_packet = json.loads(message)
                
                t = data_packet.get("timestamp") 
                v = data_packet.get("voltage")
                c = data_packet.get("current")
                
                if t is not None:
                    # 1. Update live plotting data store
                    self.data_storage["timestamps"].append(t)
                    self.data_storage["voltage"].append(v)
                    self.data_storage["current"].append(c)
                    
                    # 2. Handle Recording
                    if self.is_recording:
                        current_rec_time = time.time() - self.recording_start_time
                        
                        self.recording_data_store["elapsed_time"].append(t)
                        self.recording_data_store["recording_time"].append(current_rec_time)
                        self.recording_data_store["voltage"].append(v)
                        self.recording_data_store["current"].append(c)

                        if len(self.recording_data_store["elapsed_time"]) % 30 == 0:
                            self.window.update_recording_status(
                                f"Recording: {current_rec_time:.1f} s | Samples: {len(self.recording_data_store['elapsed_time'])}", 
                                "green"
                            )
                    
                    # 3. Update backend status (for plot continuity)
                    if not self.is_recording and len(self.data_storage["timestamps"]) % 10 == 0:
                         self.window.update_backend_status(f"Rx: V={v:.2f}V I={c:.4f}A", "green")
                    
            except json.JSONDecodeError:
                pass 
            except Exception as e:
                print(f"Data Processing Error: {e}")