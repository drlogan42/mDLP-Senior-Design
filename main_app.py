# main_app.py
# The application entry point.

# Basic imports
import sys
from PyQt6.QtWidgets import QApplication

# Import the modular components
from gui_window import ScientificGUI
from zmq_controller import ScientificController

# Main
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 1. Instantiate the components
    window = ScientificGUI() 
    controller = ScientificController(window) 
    # Note: All button connections are now handled inside the ScientificController's __init__ method.

    # 2. Execute
    window.show()   
    sys.exit(app.exec())