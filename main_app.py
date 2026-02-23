# main_app.py

# Import from Library
import sys      
from PyQt6.QtWidgets import QApplication

# Import from local files
from ViewScripts.main_window import MainWindow
from ModelScripts.state_manager import StateManager
from ModelScripts.data_store import DataStore
from ModelScripts.playback_manager import PlaybackManager
from ControllerScripts.button_controller import ButtonController
from ModelScripts.recording_manager import RecordingManager


if __name__ == "__main__":
    app = QApplication(sys.argv)    # Initialize Qt app anvironment
    
    # Create Model Layer
    state_manager = StateManager()
    data_store = DataStore(max_size=10000)
    playback_manager = PlaybackManager(data_store, playback_rate_ms=100)
    recording_manager = RecordingManager(data_store)

    # Create View Layer
    main_window = MainWindow()

    # Create Controller Layer
    controller = ButtonController(
        main_window=main_window,
        state_manager=state_manager,
        data_store=data_store,
        playback_manager=playback_manager,
        recording_manager=recording_manager
    )

    # Start App
    main_window.show() # Show the window
    sys.exit(app.exec())    # Execute the app event loop