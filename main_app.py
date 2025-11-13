# main_app.py
# The application entry point. Ensure separate pieces from UI, logic, and cofig occur properly without needing to know what each does

# Basic imports
import sys
from PyQt6.QtWidgets import QApplication

# Import the modular components
from gui_window import MVPWindow
from blocking_controller import BlockingController

# Main
if __name__ == "__main__":
    app = QApplication(sys.argv)     # Create QApplication object (engine to handle os integration, event loop, and PyQt environment)
    
    # Instanciate the components
    window = MVPWindow()     # Create the view (the UI window) as defined in gui_window.py

    controller = BlockingController(window)     # Create the Controller (the logic handler), referencing window

    # Connect Logic to UI
    window.action_button.clicked.connect(controller.execute_julia) # signal emitted by button click to run julia process.     # The UI doesn't know what's in the controller, only that it has a method to call.


    # Execute
    window.show()   # Show window 
    sys.exit(app.exec())    # Start event loop to listen for events