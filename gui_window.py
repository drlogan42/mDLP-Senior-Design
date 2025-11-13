# gui_window.py
# Defines the visual structure, layout, and styling (the View).

# Imports
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QPushButton, QLabel, QMessageBox
)


# MVPWindow creates the window, frame, title, and initializes all elements (static and interactive) 
class MVPWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Program Name
        self.setWindowTitle("MVP PyQt Modular - Julia Caller")  # Text
        self.setGeometry(100, 100, 600, 250)    # Position
        
        # Widgets initialization and Styling
        
        # Title text
        self.title_label = QLabel("Julia Backend / Python Frontend (Modular)")      # Text
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)     # Alignment
        self.title_label.setStyleSheet("font-size: 26px; font-weight: bold; margin-bottom: 15px; color: #333;")     # Style
        
        # Status
        self.status_label = QLabel(f"Initial Status: Ready. Press button to run Julia.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-style: italic; color: #444; font-size: 14px;")

        # Button 
        self.action_button = QPushButton("Run Julia 'Hello World'")
        self.action_button.setStyleSheet("padding: 12px 20px; background-color: #4A90E2; color: white; border-radius: 8px; font-size: 16px;")
        
        # Layout and Container Setup
        central_widget = QWidget()      # Main widget to act as a container
        main_layout = QVBoxLayout(central_widget)   # stack title, status, and button
        
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.status_label)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.action_button)
        button_layout.addStretch(1)
        
        main_layout.addLayout(button_layout)
        self.setCentralWidget(central_widget)

    # Status Update Method
    def update_status_text(self, message, style):
        self.status_label.setText(message)      # Change text of status
        self.status_label.setStyleSheet(style)  # Change color of status
    
    # Error Update Method
    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)      # Display pop-up error message

    # Enable Button Method
    def set_button_enabled(self, enabled, text):
        self.action_button.setEnabled(enabled)      # When pressed, enable
        self.action_button.setText(text)            # If process is busy set text