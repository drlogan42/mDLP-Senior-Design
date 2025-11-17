# main_app.py
# The application entry point. Ensure separate pieces from UI, logic, and cofig occur properly without needing to know what each does

# Basic imports
import sys
from PyQt6.QtWidgets import QApplication

# Import the modular components
from gui_window import ScientificGUI
from zmq_controller import ScientificController

# Main
if __name__ == "__main__":
    app = QApplication(sys.argv)     # Create QApplication object (engine to handle os integration, event loop, and PyQt environment)
    
    # Instanciate the components
    window = ScientificGUI()     # Create the view (the UI window) as defined in gui_window.py

    controller = ScientificController(window)     # Create the Controller (the logic handler), referencing window

    # Connect Logic to UI
    window.start_button.clicked.connect(controller.start_experiment)
    window.stop_button.clicked.connect(controller.stop_experiment)

    # Execute
    window.show()   # Show window 
    sys.exit(app.exec())    # Start event loop to listen for events