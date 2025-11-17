# gui_window.py
# Defines the visual structure, layout, and styling (the View).

# Imports
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout, QMessageBox)


# ScientificGUI creates the window, frame, title, and initializes all elements (static and interactive) 
class ScientificGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Program Name
        self.setWindowTitle("Async PyQt + ZMQ Controller")  # Text
        self.setGeometry(100, 100, 700, 300)    # Position
        self.init_ui()
    
    def init_ui(self):
        # Initializes the main GUI layout and components
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Title text
        title_label = QLabel("Julia Backend / Python Frontend {Async Experiment Control (ZMQ)}")      # Text
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px; color: #333;")
        main_layout.addWidget(title_label)


        # Status
        self.status_label = QLabel("Status: Ready to start.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-style: italic; color: #444; font-size: 16px;")
        main_layout.addWidget(self.status_label)

        # Control Panel 
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 15, 0, 15)
        control_layout.addStretch(1)

        self.start_button = QPushButton("1. Start Experiment (Launch Julia)")
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white;") # Green
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("2. Stop Experiment (Terminate Julia)")
        self.stop_button.setStyleSheet("background-color: #F44336; color: white;") # Red
        self.stop_button.setEnabled(False) # Start disabled
        control_layout.addWidget(self.stop_button)

        control_layout.addStretch(1)
        main_layout.addWidget(control_panel)
        
        self.setStyleSheet("""
            QPushButton { padding: 12px 20px; border-radius: 8px; font-size: 14px; }
            QMainWindow { background-color: #fafafa; }
        """)

    # --- Controller/Model Interface Slots (Methods the Controller calls) ---
    def update_status(self, message, color="#444", bold=False):
        """Updates the status label with a custom message and color."""
        style = f"font-size: 16px; color: {color};"
        if bold:
            style += " font-weight: bold;"
        self.status_label.setText(message)
        self.status_label.setStyleSheet(style)
        
    def set_controls_enabled(self, is_running):
        """Enables/disables buttons based on the current state."""
        self.start_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)
            
    def show_error(self, title, message):
        """Displays a critical error message."""
        QMessageBox.critical(self, title, message)