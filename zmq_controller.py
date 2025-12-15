# zmq_controller.py
# Mediator between GUI and all services (ProcessManager, DataRecorder, ZMQ Listener, Trial Player)

import json
import os
from PyQt6.QtCore import QThread, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication, QFileDialog

#  Import Dependancies
from process_manager import ProcessManager
from data_recorder import DataRecorder
from zmq_listener import ZmqListenerWorker
from trial_player import TrialPlayerWorker
from config import ZMQ_ADDRESS

# Init all components, connect UI signals to methods, and manage threading for async operations
class ScientificController(QObject):
    
    def __init__(self, window):
        super().__init__()
        # Controller requires view instance to manipulate it (Dipendency Injection Pattern).
        self.window = window
        
        # Controller directs all services
        self.process_manager = ProcessManager()
        self.recorder = DataRecorder()
        
        # Hold Qthread and Worker instances for ZMQ and Playback
        self.zmq_thread = None
        self.zmq_worker = None
        self.player_thread = None
        self.player_worker = None
        
        # State management
        self.selected_file_path = None
        self._playback_error_occurred = False
        
        # The Live Data Buffer
        self.plot_data = {"timestamps": [], "voltage": [], "current": []}
        
        # Ensure cleanup
        QApplication.instance().aboutToQuit.connect(self.stop_all)
        
        # Connect UI Signals
        self._connect_signals()

    # Connects every button in view to appropriate method within controller
    def _connect_signals(self):
        # Backend Control
        self.window.start_backend_button.clicked.connect(self.start_backend)
        self.window.stop_backend_button.clicked.connect(self.stop_backend)
        
        # Sim Contorl
        self.window.start_simulator_button.clicked.connect(self.start_simulator)
        self.window.stop_simulator_button.clicked.connect(self.stop_simulator)
        
        # Record Control
        self.window.start_recording_button.clicked.connect(self.start_recording)
        self.window.stop_recording_button.clicked.connect(self.stop_recording)
        
        # Playback Control
        self.window.select_file_button.clicked.connect(self.select_file)
        self.window.start_playback_button.clicked.connect(self.start_playback)
        self.window.stop_playback_button.clicked.connect(self.stop_playback)

    # =-= Process Management =-=

    # Starts Julia listener via ProcessManager. Init and start ZMNQ worker thread. Update GUI State
    def start_backend(self):
        try:
            self.process_manager.start_backend()
            self.window.update_backend_status("Launching Julia Backend...", "orange", True)
            
            # Reset Data
            self.plot_data = {"timestamps": [], "voltage": [], "current": []}
            
            # Start ZMQ Listener Thread
            self.zmq_thread = QThread()
            self.zmq_worker = ZmqListenerWorker(ZMQ_ADDRESS)
            self.zmq_worker.moveToThread(self.zmq_thread)
            self.zmq_thread.started.connect(self.zmq_worker.run)
            self.zmq_worker.message_received.connect(self._handle_zmq_message)
            self.zmq_thread.start()
            
            self.window.start_monitoring(self.plot_data)
            self._update_ui_state(backend_running=True)
            self.window.update_backend_status("Backend Listener Running.", "blue", True)
            
        except Exception as e:
            self.window.show_error("Backend Error", str(e))
            self.stop_all()

    def stop_backend(self):
        self.stop_simulator()
        self.stop_playback(restart_julia=False)
        
        # Stop ZMQ Thread
        if self.zmq_worker:
            self.zmq_worker.stop()
        if self.zmq_thread:
            self.zmq_thread.quit()
            self.zmq_thread.wait(1000)
            self.zmq_thread = None
            self.zmq_worker = None

        # Stop Process
        self.process_manager.stop_backend()
        
        self.window.stop_monitoring()
        self._update_ui_state(backend_running=False)
        self.window.update_backend_status("Backend STOPPED.", "red", True)

    def stop_all(self):
        self.stop_backend()

    # Starts Julia simulator process
    def start_simulator(self):
        self.stop_playback()
        try:
            self.process_manager.start_simulator()
            self.window.set_simulator_controls_enabled(True)
            self.window.set_recording_controls_enabled(False) # Don't record immediately
            self.window.set_playback_controls_enabled(False, False, True)
            self.window.update_simulator_status("Simulator: Sending Data", "green", True)
        except Exception as e:
            self.window.show_error("Simulator Error", str(e))

    # Stops Simulator
    def stop_simulator(self):
        self.process_manager.stop_simulator()
        self.recorder.stop_and_save() # Ensure recording stops if sim stops
        
        backend_running = self.window.stop_backend_button.isEnabled()
        self.window.set_simulator_controls_enabled(False)
        self.window.set_recording_controls_enabled(False)
        self.window.set_playback_controls_enabled(
            file_selected=(self.selected_file_path is not None),
            is_playing=False,
            backend_running=backend_running
        )
        self.window.update_simulator_status("Simulator: STOPPED.", "red", True)

    # =-= Recording Control =-=
    def start_recording(self):
        if not self.window.stop_backend_button.isEnabled():
            return
        
        self.recorder.start()
        self.window.set_recording_controls_enabled(True)
        self.window.update_recording_status("Recording data...", "green", True)

    def stop_recording(self):
        if not self.recorder.is_recording:
            return

        self.window.set_recording_controls_enabled(False)
        self.window.update_recording_status("Saving data...", "orange", True)
        
        try:
            filename = self.recorder.stop_and_save()
            if filename:
                self.selected_file_path = filename
                self.window.update_playback_status(f"File Selected: {filename}", "blue", True)
                self.window.update_recording_status(f"Saved to {filename}", "blue", True)
            else:
                self.window.update_recording_status("Stopped. No data recorded.", "red", True)
        except Exception as e:
             self.window.show_error("Save Error", str(e))

    # =-= Playback Control =-=
    def select_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self.window, "Select Data", "", "CSV Files (*.csv)")
        if filepath:
            self.selected_file_path = filepath
            self.window.update_playback_status(f"File: {os.path.basename(filepath)}", "blue", True)
            self._update_playback_ui(is_playing=False)

    def start_playback(self):
        if not self.selected_file_path: return

        # 1. Stop conflicts
        self.stop_simulator()
        self.stop_recording()
        
        # 2. Release Port (Stop Backend)
        self.window.update_backend_status("Pausing Backend for Playback...", "orange")
        self.process_manager.stop_backend()
        QThread.msleep(200) # Allow OS port release

        # 3. Start Player Thread
        self.player_thread = QThread()
        self.player_worker = TrialPlayerWorker(self.selected_file_path, ZMQ_ADDRESS)
        self.player_worker.moveToThread(self.player_thread)
        
        self._playback_error_occurred = False
        self.player_thread.started.connect(self.player_worker.run)
        self.player_worker.finished.connect(self.stop_playback)
        self.player_worker.status_update.connect(self._handle_playback_status)
        
        self.player_thread.start()
        self._update_playback_ui(is_playing=True)

    def stop_playback(self, restart_julia=True):
        if self.player_worker:
            self.player_worker.stop()
        if self.player_thread:
            self.player_thread.quit()
            self.player_thread.wait()
            self.player_thread = None
            self.player_worker = None

        if restart_julia:
            # -= Restart Backend if needed =-=
            try:
                self.process_manager.start_backend()
                self.window.update_backend_status("Backend Restored.", "blue", True)
            except: 
                pass # Already running or error

        self._update_playback_ui(is_playing=False)
        if not self._playback_error_occurred:
             self.window.update_playback_status("Playback STOPPED.", "red", True)

    # Helpers to update UI state based on backend/simulator/playback status
    def _update_ui_state(self, backend_running):
        self.window.set_backend_controls_enabled(backend_running)
        self.window.set_simulator_controls_enabled(False)
        self.window.set_recording_controls_enabled(False)
        self._update_playback_ui(is_playing=False)

    def _update_playback_ui(self, is_playing):
        backend_running = self.window.stop_backend_button.isEnabled() or (self.player_thread is not None)
        self.window.set_playback_controls_enabled(
            file_selected=(self.selected_file_path is not None),
            is_playing=is_playing,
            backend_running=backend_running
        )

    def _handle_playback_status(self, msg, color, bold):
        self.window.update_playback_status(msg, color, bold)
        if color == "red": self._playback_error_occurred = True

    #  ZMQ Message Handler to process incoming data
    def _handle_zmq_message(self, message):
        if "FATAL" in message:
            self.window.update_backend_status(message, "red", True)
            self.stop_all()
        elif "ZMQ Worker connected" in message:
            self.window.update_backend_status(message, "blue", True)
        else:
            try:
                data = json.loads(message)
                t, v, c = data.get("timestamp"), data.get("voltage"), data.get("current")
                
                if t is not None:
                    # 1. Update Plot Data
                    self.plot_data["timestamps"].append(t)
                    self.plot_data["voltage"].append(v)
                    self.plot_data["current"].append(c)
                    
                    # 2. Update Recorder
                    self.recorder.add_sample(t, v, c)

                    # 3. Update Status
                    if self.recorder.is_recording and self.recorder.get_sample_count() % 30 == 0:
                        self.window.update_recording_status(
                            f"Rec: {self.recorder.get_current_duration():.1f}s | {self.recorder.get_sample_count()} samples", "green"
                        )
                    elif len(self.plot_data["timestamps"]) % 10 == 0:
                        self.window.update_backend_status(f"Rx: V={v:.2f}V I={c:.4f}A", "green")
                        
            except json.JSONDecodeError:
                pass