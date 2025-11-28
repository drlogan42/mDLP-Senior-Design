# zmq_controller.py
# Contains the ZMQ threading logic and the Julia process management (Controller and ZMQ Worker).

import sys
import os
import json
import zmq
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication

# Import config
from config import JULIA_BACKEND_PATH, JULIA_SIMULATOR_PATH, ZMQ_ADDRESS

# --- ZMQ Worker (Runs on a QThread) ---
class ZmqWorker(QObject):
    message_received = pyqtSignal(str) 
    # ... (ZmqWorker content remains unchanged) ...
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
        
        self.data_storage = {
            "timestamps": [],
            "voltage": [],
            "current": []
        }
        
        QApplication.instance().aboutToQuit.connect(self.stop_all)
        
        # --- NEW CONNECTION LOGIC ---
        # 1. Connect Backend Listener (Column 1)
        window.start_backend_button.clicked.connect(self.start_backend)
        window.stop_backend_button.clicked.connect(self.stop_backend)

        # 2. Connect Simulator Control (Column 2)
        window.start_simulator_button.clicked.connect(self.start_simulator)
        window.stop_simulator_button.clicked.connect(self.stop_simulator)
        # --- END NEW CONNECTION LOGIC ---


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
            # 1. Reset Data
            self.data_storage = {"timestamps": [], "voltage": [], "current": []}

            # 2. Launch Julia Backend (Listener)
            self.julia_backend_process = subprocess.Popen(['julia', JULIA_BACKEND_PATH])
            
            # 3. Start ZMQ Receiver Thread (Python side)
            self.zmq_thread = QThread()
            self.zmq_worker = ZmqWorker(ZMQ_ADDRESS)
            self.zmq_worker.moveToThread(self.zmq_thread)
            
            self.zmq_thread.started.connect(self.zmq_worker.run)
            self.zmq_worker.message_received.connect(self._handle_zmq_message)
            self.zmq_thread.start()
            
            # 4. Start GUI Plotting
            self.window.start_monitoring(self.data_storage)
            
            self.window.set_backend_controls_enabled(True)
            self.window.set_simulator_controls_enabled(False) # Disable simulator until ZMQ connects
            self.window.update_backend_status("Backend Listener running. Ready for Instrument Data...", "blue", True)
            
        except Exception as e:
            self.window.show_error("Error", f"Failed to start Backend: {e}")
            self.stop_all()

    def stop_backend(self):
        """Stops the main Julia Data Listener Backend and ZMQ receiver."""
        self.window.set_backend_controls_enabled(False)
        self.window.set_simulator_controls_enabled(False)
        
        self.stop_simulator() # Ensure simulator is off first
        
        # Stop ZMQ
        if self.zmq_worker:
            self.zmq_worker.stop()
        if self.zmq_thread:
            self.zmq_thread.quit()
            self.zmq_thread.wait(1000)
            self.zmq_thread = None
            self.zmq_worker = None

        # Stop Julia Backend
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
        
    # --- Simulator Control (Column 2) ---

    def start_simulator(self):
        """Starts the Julia Instrument Simulator (Data Sender)."""
        if self.julia_simulator_process is not None and self.julia_simulator_process.poll() is None:
            self.window.update_simulator_status("Simulator already running.", "gray", True)
            return
            
        if not os.path.exists(JULIA_SIMULATOR_PATH):
            self.window.show_error("Error", f"Simulator script not found: {JULIA_SIMULATOR_PATH}")
            return
            
        self.window.update_simulator_status("Launching Instrument Simulator (Data Sender)...", "orange", True)
        
        try:
            # Launch Julia Simulator
            self.julia_simulator_process = subprocess.Popen(['julia', JULIA_SIMULATOR_PATH])
            
            self.window.set_simulator_controls_enabled(True)
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
            
        self.window.set_simulator_controls_enabled(False)
        self.window.update_simulator_status("Simulator: STOPPED.", "red", True)

    # --- Data Processing Logic ---

    def _handle_zmq_message(self, message):
        """
        Parses JSON packets for Voltage/Current and stores them.
        """
        if "FATAL" in message:
            self.window.update_backend_status(message, "red", True)
            self.stop_all()
        elif "ZMQ Worker connected" in message:
            self.window.update_backend_status(message, "blue", True)
            # Enable simulator controls once ZMQ is ready to receive
            self.window.set_simulator_controls_enabled(False) 
            
        else:
            try:
                data_packet = json.loads(message)
                
                t = data_packet.get("timestamp")
                v = data_packet.get("voltage")
                c = data_packet.get("current")
                
                if t is not None:
                    self.data_storage["timestamps"].append(t)
                    self.data_storage["voltage"].append(v)
                    self.data_storage["current"].append(c)
                    
                    if len(self.data_storage["timestamps"]) % 10 == 0:
                         self.window.update_backend_status(f"Rx: V={v:.2f}V I={c:.4f}A", "green")
                    
            except json.JSONDecodeError:
                pass 
            except Exception as e:
                print(f"Data Processing Error: {e}")