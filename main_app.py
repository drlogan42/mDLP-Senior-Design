# main_app.py
# Main app entry point for the GUI. It creates model, view, and controller instances and starts the Qt application loop.

# Imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PyQt6.QtWidgets import QApplication

# Import from local files
from ViewScripts.main_window import MainWindow
from ModelScripts.state_manager import StateManager
from ModelScripts.data_store import DataStore
from ModelScripts.playback_manager import PlaybackManager
from ModelScripts.serial_manager import SerialManager
from ControllerScripts.button_controller import ButtonController
from ModelScripts.recording_manager import RecordingManager


if __name__ == "__main__":
    app = QApplication(sys.argv)    # Initialize Qt app anvironment
    
    try:
        # Create Model Layer
        state_manager = StateManager()
        data_store = DataStore(max_size=25000)                                  # Change buffer size as needed here
        playback_manager = PlaybackManager(data_store, playback_rate_ms=100)
        serial_manager = SerialManager(data_store)
        recording_manager = RecordingManager(data_store)

        # Create View Layer
        main_window = MainWindow()

        # Create Controller Layer
        controller = ButtonController(
            main_window=main_window,
            state_manager=state_manager,
            data_store=data_store,
            playback_manager=playback_manager,
            serial_manager=serial_manager,
            recording_manager=recording_manager
        )

        # Start App
        main_window.show()
        sys.exit(app.exec())

    except Exception as e:
        print(f"Fatal error during startup: {e}")
        sys.exit(1)