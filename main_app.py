# main_app.py
# The application entry point.

import sys
from PyQt6.QtWidgets import QApplication

from gui_window import ScientificGUI
from zmq_controller import ScientificController

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Instantiate the components
    window = ScientificGUI() 
    controller = ScientificController(window) 
    # NOTE: All button connections are now handled inside ScientificController.__init__

    # Execute
    window.show()   
    sys.exit(app.exec())