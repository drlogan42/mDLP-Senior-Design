# main_app.py
'''Run program from here. Main entry point'''

# Import from Library
import sys
from PyQt6.QtWidgets import QApplication

# Import from Scripts
from gui_window import ScientificGUI
from zmq_controller import ScientificController

# Enter Main
if __name__ == "__main__":
    app = QApplication(sys.argv)    # Initialize Qt app anvironment
    
    # Instantiate components
    window = ScientificGUI()    # View: Create UI elements
    controller = ScientificController(window)   # Controller: Takes view instance, register clicks and status

    # Execute
    window.show()   
    sys.exit(app.exec())