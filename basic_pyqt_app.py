# Preliminary GUI w/ Python Fontend and Julia Backend
# Logan Shaffer

# =-=-=-=-= Imports =-=-=-=-=
import sys        # Handles system tasks like exiting program
import subprocess # Allows Python to start Julia and other executables
import os         # Check if Julia exists before running
from PyQt6.QtCore import Qt # Alignment
from PyQt6.QtWidgets import ( # Only import necessary for readability and performance
    QApplication,  # Manages the event loop (update loop)
    QMainWindow,   # Main window to hold everything (the frame)
    QVBoxLayout,   # Vertical layout manager
    QHBoxLayout,   # Horizontal layout manager
    QWidget,       # Generic container widget
    QPushButton,   # Interactive component (the button)
    QLabel,        # Display component (the text)
    QMessageBox,   # For showing messages instead of print
)

# =-=-=-= Configuration =-=-=-=
JULIA_SCRIPT_PATH = "hello_julia.jl"    # Set the path of Julia

# =-=-= Main Window =-=-=
class MVPWindow(QMainWindow):
    """
    The main window class. Structure and behavior of the UI elements is here
    MVPWindow inherits from QMainWindow
    """
    # =-=-= Start =-=-=
    def __init__(self): #
        # Always call the parent constructor
        super().__init__()
        
        self.setWindowTitle("MVP PyQt Starter - Julia Caller")
        self.setGeometry(100, 100, 600, 250) # Increased size
        
        # --- 2. Widgets Initialization and Styling ---
        
        # Title Label (RE-INTEGRATED)
        self.title_label = QLabel("Julia Backend / Python Frontend")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 26px; font-weight: bold; margin-bottom: 15px; color: #333;")
        
        # Status Label (RE-INTEGRATED STYLE)
        self.status_label = QLabel(f"Initial Status: Ready. Press button to run Julia.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-style: italic; color: #444; font-size: 14px;")

        # Action Button (RE-INTEGRATED STYLE)
        self.action_button = QPushButton("Run Julia 'Hello World'")
        self.action_button.setStyleSheet(
            "padding: 12px 20px; "
            "background-color: #4A90E2; " # The characteristic blue color
            "color: white; "
            "border-radius: 8px; "
            "font-size: 16px;"
        )
        
        # --- 3. Layout and Container Setup ---
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Add the styled title label
        main_layout.addWidget(self.title_label)
        
        # Add the styled status label
        main_layout.addWidget(self.status_label)
        
        # NEW: Horizontal layout for centering the button
        button_layout = QHBoxLayout()
        button_layout.addStretch(1) # Pushes the button to the right
        button_layout.addWidget(self.action_button)
        button_layout.addStretch(1) # Pushes the button to the left (resulting in center)
        
        main_layout.addLayout(button_layout)
        
        # Set the container widget as the central element of the QMainWindow
        self.setCentralWidget(central_widget)
        
        # --- 4. Signals and Slots Connection ---
        self.action_button.clicked.connect(self.button_clicked)

    def button_clicked(self):
        """
        The slot that executes the external Julia script.
        (Logic remains unchanged, but styling updates are included inside the try block for success/error.)
        """
        # Ensure the Julia script file exists
        if not os.path.exists(JULIA_SCRIPT_PATH):
            QMessageBox.critical(self, "Error", f"Julia script not found: {JULIA_SCRIPT_PATH}")
            return
            
        self.status_label.setText("Status: Launching Julia...")
        self.status_label.setStyleSheet("font-style: italic; color: orange; font-size: 14px;") # Pending style
        self.action_button.setEnabled(False)

        try:
            result = subprocess.run(
                ['julia', JULIA_SCRIPT_PATH], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # If successful, update status with the output captured from Julia
            output_text = result.stdout.strip()
            self.status_label.setText(f"SUCCESS! Julia Output: {output_text}")
            self.status_label.setStyleSheet("font-style: italic; color: green; font-weight: bold; font-size: 14px;") # Success style
            print(f"Julia Process finished. Output: {output_text}")
            
        except FileNotFoundError:
            self.status_label.setText("ERROR: 'julia' executable not found.")
            self.status_label.setStyleSheet("font-style: italic; color: red; font-weight: bold; font-size: 14px;") # Error style
            QMessageBox.critical(self, "Error", 
                "The 'julia' command could not be found. \n"
                "Please ensure Julia is installed and added to your system's PATH environmental variable."
            )
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.strip() or "No detailed error provided."
            self.status_label.setText("ERROR: Julia script failed.")
            self.status_label.setStyleSheet("font-style: italic; color: red; font-weight: bold; font-size: 14px;") # Error style
            QMessageBox.critical(self, "Julia Runtime Error", 
                f"Julia script crashed. Stderr:\n{error_output}"
            )
        except Exception as e:
            self.status_label.setText(f"An unknown error occurred: {e}")
            self.status_label.setStyleSheet("font-style: italic; color: red; font-weight: bold; font-size: 14px;") # Error style
            QMessageBox.critical(self, "Unknown Error", str(e))
            
        finally:
            self.action_button.setEnabled(True)
            self.action_button.setText("Run Julia 'Hello World'")

        
# =- Awake -=
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MVPWindow()
    window.show()
    sys.exit(app.exec())