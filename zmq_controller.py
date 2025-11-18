# zmq_controller.py
# Contains the ZMQ threading logic and the Julia process management (Controller and ZMQ Worker).

import sys
import os
import json
import time
import subprocess
import zmq

# PyQt6 components for multi-threading and signals
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer, Qt
from PyQt6.QtWidgets import QApplication

# --- Configuration (using common ZMQ port and script path) ---
# NOTE: Using the script path defined here for consistency with the rest of the file's logic.
from config import JULIA_SCRIPT_PATH, ZMQ_ADDRESS
# --- ZMQ Worker (Runs on a QThread) ---

class ZmqWorker(QObject):
    """
    Handles connection to the ZMQ stream in a non-blocking way.
    It runs in a separate QThread to prevent blocking the main GUI thread.
    Emits a signal whenever data is received from the Julia PUB socket.
    """
    # Signal emitted when a string message is received from ZMQ
    message_received = pyqtSignal(str) 
    
    def __init__(self, address):
        super().__init__()
        self.address = address
        self._running = True # Flag to control the infinite loop
        self.context = None  # ZMQ context object
        self.socket = None   # ZMQ socket object

    def run(self):
        """Main loop for the ZMQ subscriber thread (SLOT connected to QThread.started)."""
        try:
            self.context = zmq.Context()
            # ZMQ.SUB (Subscriber) socket is read-only and connects to the Julia PUB socket
            self.socket = self.context.socket(zmq.SUB)
            self.socket.connect(self.address)
            # Subscribe to all messages (empty filter/topic, b'' stands for all bytes)
            self.socket.setsockopt(zmq.SUBSCRIBE, b'')
            
            # Send initial connection status back to the main thread
            self.message_received.emit(f"ZMQ Worker connected to {self.address}",)
            
            while self._running:
                # Use poll() with a 100ms timeout to keep the loop responsive to stop signals
                if self.socket.poll(100, zmq.POLLIN):
                    # Data is ready to be received
                    message = self.socket.recv_string()
                    # Emit the data back to the GUI thread via the signal
                    self.message_received.emit(message) 
                
            print("ZMQ Worker loop terminated.")
            
        except zmq.error.ContextTerminated:
            # Expected exception during a clean shutdown when self.stop() is called
            pass
        except Exception as e:
            # Report critical errors back to the UI (main thread)
            self.message_received.emit(f"FATAL ZMQ ERROR: {e}")
        finally:
            # Clean up ZMQ resources
            if self.socket:
                self.socket.close()

    def stop(self):
        """Stops the infinite loop gracefully from the main thread (thread-safe termination)."""
        self._running = False
        # Terminating the context will interrupt the blocking socket.poll() or recv() call
        if self.context:
            self.context.term()
            
# --- Scientific Controller (Manages process lifecycle and data logic) ---

class ScientificController(QObject):
    """
    Manages the Julia process (subprocess.Popen) and the ZMQ worker thread (QThread).
    Acts as the Controller in the MVC pattern, handling user input and data flow.
    """
    def __init__(self, window):
        super().__init__()
        self.window = window # Reference to the GUI (View) for updating the UI
        self.julia_process = None
        self.zmq_thread = None
        self.zmq_worker = None
        
        # Hook into the main application close event to ensure Julia is terminated
        QApplication.instance().aboutToQuit.connect(self.stop_experiment)

    def start_experiment(self):
        """
        Launches the Julia backend process and starts the ZMQ worker thread.
        This is the SLOT connected to the Start button.
        """
        if self.julia_process is not None and self.julia_process.poll() is None:
            # Process is already running (poll() returns None if the process hasn't terminated)
            self.window.update_status("Experiment already running.", "#000", True)
            return

        # 1. Pre-checks and UI updates
        if not os.path.exists(JULIA_SCRIPT_PATH):
            self.window.show_error("Error", f"Julia script not found: {JULIA_SCRIPT_PATH}")
            return
        
        self.window.update_status("Launching Julia and ZMQ worker...", "orange", True)
        
        try:
            # 2. Launch Julia Process (Non-blocking: Popen)
            # Starts the Julia script as a separate OS process.
            # We use subprocess.DEVNULL for stdout/stderr to prevent Julia output from 
            # interfering with the main console or blocking the PyQt event loop.
            # self.julia_process = subprocess.Popen(
            #     ['julia', JULIA_SCRIPT_PATH],
            #     stdout=subprocess.DEVNULL, 
            #     stderr=subprocess.DEVNULL
            # )

            self.julia_process = subprocess.Popen(
                ['julia', JULIA_SCRIPT_PATH]
                # If you only want to see errors, you can keep stdout=subprocess.DEVNULL 
                # but removing both is safest for debugging
            )
            print(f"Julia Process started with PID: {self.julia_process.pid}")
            
            # 3. Setup and Start ZMQ Worker Thread
            self.zmq_thread = QThread()                 # Create the new thread
            self.zmq_worker = ZmqWorker(ZMQ_ADDRESS)    # Create the worker object
            self.zmq_worker.moveToThread(self.zmq_thread) # Move the worker to the new thread
            
            # Connect the thread's start signal to the worker's run method (SLOT)
            self.zmq_thread.started.connect(self.zmq_worker.run)
            
            # Connect the worker's signal (emitted from the worker thread) to the Controller's 
            # processing slot (runs on the main GUI thread)
            self.zmq_worker.message_received.connect(self._handle_zmq_message)

            self.zmq_thread.start() # Start the non-blocking thread
            
            # 4. Update UI to Running State
            self.window.set_controls_enabled(True)
            self.window.update_status("Experiment Running. Waiting for data...", "blue", True)
            
        except FileNotFoundError:
            self.window.show_error("Error", "Could not find 'julia' executable.")
            self.stop_experiment() # Clean up any started resources
        except Exception as e:
            self.window.show_error("Error", f"Failed to start process or ZMQ: {e}")
            self.stop_experiment() # Clean up any started resources

    def stop_experiment(self):
        """
        Terminates the ZMQ connection and the Julia subprocess.
        This is the SLOT connected to the Stop button and the app's quit event.
        """
        self.window.set_controls_enabled(False)
        self.window.update_status("Stopping experiment...", "gray", True)
        
        # 1. Stop ZMQ Worker Thread
        if self.zmq_worker:
            self.zmq_worker.stop() # Set the flag and terminate the context to stop the loop
        if self.zmq_thread:
            self.zmq_thread.quit()      # Stop the event loop in the thread
            self.zmq_thread.wait(1000)  # Wait up to 1 second for the thread to exit gracefully
            # Nullify references to allow garbage collection
            self.zmq_thread = None
            self.zmq_worker = None

        # 2. Terminate Julia Process
        if self.julia_process and self.julia_process.poll() is None:
            print(f"Terminating Julia process {self.julia_process.pid}...")
            # Send SIGTERM
            self.julia_process.terminate()
            try:
                # Give it a moment to shut down gracefully
                self.julia_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                 # Force kill if termination fails
                 self.julia_process.kill() 
            self.julia_process = None
            
        # 3. Final UI Update
        self.window.set_controls_enabled(False)
        self.window.update_status("Experiment STOPPED. System is idle.", "red", True)
        
    # --- Private Slot for Signal Handling ---

    def _handle_zmq_message(self, message):
        """
        Receives data from the ZmqWorker (runs on the GUI thread) and processes it.
        This is the main data processing logic in the Controller.
        """
        # Simple feedback loop for the MVP
        if "FATAL" in message:
            self.window.update_status(message, "red", True)
            self.stop_experiment() # Critical error, shut everything down
        elif "ZMQ Worker connected" in message:
            # Initial setup message confirming ZMQ is established
            self.window.update_status(message, "blue", True)
        else:
            # Assume this is the real-time data coming from Julia
            # In a real app, you would parse the JSON here and update a plot.
            # Example JSON parsing:
            # try:
            #     data = json.loads(message)
            #     self.window.update_plot(data)
            # except json.JSONDecodeError:
            #     print(f"Received non-JSON data: {message}")
            self.window.update_status(f"Data received: {message} (Real-Time)", "green")