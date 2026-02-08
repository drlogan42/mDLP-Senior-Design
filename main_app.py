# main_app.py

# Import from Library
import sys      
from PyQt6.QtWidgets import QApplication

# new
from ViewScripts.main_window import MainWindow
#from ControllerScripts.button_controller import ButtonController

# Old
#from ViewScripts.gui_window import ScientificGUI
#from ControllerScripts.socket_controller import ScientificController


if __name__ == "__main__":
    app = QApplication(sys.argv)    # Initialize Qt app anvironment
    
    # new
    main_window = MainWindow() # Create instance of the main window
    #controller = ButtonController(main_window) # Create instance of the controller
    main_window.show() # Show the window
    sys.exit(app.exec())    # Execute the app event loop


    # =-=-=- old
    # Instantiate components
    #window = ScientificGUI()    # View: Create UI elements
    #controller = ScientificController(window)   # Controller: Takes view instance, register clicks and status

    # Execute
    #window.show()   # Show the GUI window on screen
    #sys.exit(app.exec())    # 