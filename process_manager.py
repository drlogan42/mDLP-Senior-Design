# process_manager.py

import subprocess
import os
import signal
from config import JULIA_BACKEND_PATH, JULIA_SIMULATOR_PATH

class ProcessManager:
    """
    Manages the lifecycle of external Julia processes.
    """
    def __init__(self):
        self.backend_process = None
        self.simulator_process = None

    def start_backend(self):
        """Starts the Julia Backend Listener."""
        if self._is_running(self.backend_process):
            raise ProcessLookupError("Backend is already running.")
        
        if not os.path.exists(JULIA_BACKEND_PATH):
            raise FileNotFoundError(f"Script not found: {JULIA_BACKEND_PATH}")

        self.backend_process = subprocess.Popen(['julia', JULIA_BACKEND_PATH])
        return True

    def stop_backend(self):
        """Stops the Julia Backend."""
        self._terminate_process(self.backend_process)
        self.backend_process = None

    def start_simulator(self):
        """Starts the Julia Instrument Simulator."""
        if self._is_running(self.simulator_process):
            raise ProcessLookupError("Simulator is already running.")
            
        if not os.path.exists(JULIA_SIMULATOR_PATH):
            raise FileNotFoundError(f"Script not found: {JULIA_SIMULATOR_PATH}")

        self.simulator_process = subprocess.Popen(['julia', JULIA_SIMULATOR_PATH])
        return True

    def stop_simulator(self):
        """Stops the Simulator."""
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