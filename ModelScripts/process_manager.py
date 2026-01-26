# process_manager.py

import subprocess
import os
import signal
from ModelScripts.config import JULIA_BACKEND_PATH, JULIA_SIMULATOR_PATH

# Manages lifecycle of external Julia processes.
class ProcessManager:
    def __init__(self):
        self.backend_process = None
        self.simulator_process = None

    # Starts the Julia Backend Listener.
    def start_backend(self):
        if self._is_running(self.backend_process):
            raise ProcessLookupError("Backend is already running.")
        
        if not os.path.exists(JULIA_BACKEND_PATH):
            raise FileNotFoundError(f"Script not found: {JULIA_BACKEND_PATH}")

        self.backend_process = subprocess.Popen(['julia', JULIA_BACKEND_PATH])
        return True

    # Stops the Julia Backend Listener.
    def stop_backend(self):
        self._terminate_process(self.backend_process)
        self.backend_process = None

    #  Starts the Julia Instrument Simulator.
    def start_simulator(self):
        if self._is_running(self.simulator_process):
            raise ProcessLookupError("Simulator is already running.")
            
        if not os.path.exists(JULIA_SIMULATOR_PATH):
            raise FileNotFoundError(f"Script not found: {JULIA_SIMULATOR_PATH}")

        self.simulator_process = subprocess.Popen(['julia', JULIA_SIMULATOR_PATH])
        return True

    # Stops the Julia Instrument Simulator.
    def stop_simulator(self):
        self._terminate_process(self.simulator_process)
        self.simulator_process = None

    def _is_running(self, process):
        return process is not None and process.poll() is None

    def _terminate_process(self, process):
        if process:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()