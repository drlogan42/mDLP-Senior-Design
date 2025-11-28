# gui_window.py
# Defines the visual structure, layout, and styling (the View).

import sys
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout, QMessageBox)

# Scientific Plotting Library
try:
    import pyqtgraph as pg
except ImportError:
    # Fallback if not installed
    pg = None

class ScientificGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Async PyQt + ZMQ Controller")
        self.setGeometry(100, 100, 800, 600)
        
        # Data References and Timers
        self.data_reference = None 
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot_animation)
        
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- 1. Header Layout (Title Top-Left, Status Top-Right) ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 5) 

        # Title Label (Top Left)
        title_label = QLabel("Julia Backend / Python Frontend {Async Experiment Control}")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        header_layout.addWidget(title_label)

        header_layout.addStretch(1)

        # Status Labels Container (Right side, Vertical Stack)
        status_container = QVBoxLayout()
        status_container.setSpacing(2)

        # Status 1: Backend Listener Status
        self.backend_status_label = QLabel("Backend Status: Ready to start.")
        self.backend_status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.backend_status_label.setStyleSheet("font-style: italic; color: #444; font-size: 14px;")
        status_container.addWidget(self.backend_status_label)

        # Status 2: Simulator/Sender Status (New)
        self.simulator_status_label = QLabel("Simulator Status: Idle.")
        self.simulator_status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.simulator_status_label.setStyleSheet("font-style: italic; color: #444; font-size: 14px;")
        status_container.addWidget(self.simulator_status_label)

        header_layout.addLayout(status_container)
        
        main_layout.addLayout(header_layout)

        # --- 2. Real-Time Graphs (PyQtGraph, Light Mode) ---
        if pg:
            # Light Mode Settings
            pg.setConfigOption('background', 'w') 
            pg.setConfigOption('foreground', 'k') 
            
            self.graph_widget = pg.GraphicsLayoutWidget()
            
            # Plot 1: Voltage (Blue)
            self.plot_voltage = self.graph_widget.addPlot(title="Voltage Sensor")
            self.plot_voltage.setLabel('left', 'Voltage', units='V')
            self.plot_voltage.showGrid(x=True, y=True, alpha=0.6) 
            self.curve_voltage = self.plot_voltage.plot(pen=pg.mkPen('#0000FF', width=2)) 
            
            self.graph_widget.nextRow()
            
            # Plot 2: Current (Red)
            self.plot_current = self.graph_widget.addPlot(title="Current Sensor")
            self.plot_current.setLabel('left', 'Current', units='A')
            self.plot_current.setLabel('bottom', 'Time', units='s')
            self.plot_current.showGrid(x=True, y=True, alpha=0.6)
            self.plot_current.setXLink(self.plot_voltage)
            self.curve_current = self.plot_current.plot(pen=pg.mkPen('#FF0000', width=2))

            main_layout.addWidget(self.graph_widget, stretch=1)
        else:
            error_label = QLabel("Error: 'pyqtgraph' library not found.\nPlease install: pip install pyqtgraph")
            error_label.setStyleSheet("color: red; font-size: 16px; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(error_label)

        # --- 3. Control Panel (Button Columns) ---
        control_panel = QWidget()
        control_layout_outer = QHBoxLayout(control_panel)
        control_layout_outer.setContentsMargins(10, 10, 10, 10) 
        control_layout_outer.setSpacing(20) 
        
        button_width = 200 # Standard width for all buttons

        # Column 1: Backend Listener Control (Key change: use self.start_backend_button)
        buttons_layout_1 = QVBoxLayout()
        buttons_layout_1.setSpacing(10)

        self.start_backend_button = QPushButton("1. Start Backend Listener")
        self.start_backend_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_backend_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_backend_button.setFixedWidth(button_width) 
        buttons_layout_1.addWidget(self.start_backend_button)
        
        self.stop_backend_button = QPushButton("1. Stop Backend Listener")
        self.stop_backend_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        self.stop_backend_button.setEnabled(False)
        self.stop_backend_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_backend_button.setFixedWidth(button_width)
        buttons_layout_1.addWidget(self.stop_backend_button)

        control_layout_outer.addLayout(buttons_layout_1)
        
        # NOTE: Button connections are now handled in zmq_controller.py


        # Column 2: Simulator Control 
        buttons_layout_2 = QVBoxLayout()
        buttons_layout_2.setSpacing(10)

        self.start_simulator_button = QPushButton("2. Start Data Simulator")
        self.start_simulator_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_simulator_button.setFixedWidth(button_width) 
        self.start_simulator_button.setEnabled(False) 
        buttons_layout_2.addWidget(self.start_simulator_button)
        
        self.stop_simulator_button = QPushButton("2. Stop Data Simulator")
        self.stop_simulator_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        self.stop_simulator_button.setFixedWidth(button_width)
        self.stop_simulator_button.setEnabled(False) 
        buttons_layout_2.addWidget(self.stop_simulator_button)

        control_layout_outer.addLayout(buttons_layout_2)


        # Column 3: Placeholder Buttons
        buttons_layout_3 = QVBoxLayout()
        buttons_layout_3.setSpacing(10)

        self.button_3 = QPushButton("3. Button (Green)")
        self.button_3.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.button_3.setFixedWidth(button_width) 
        buttons_layout_3.addWidget(self.button_3)
        
        self.button_4 = QPushButton("3. Button (Red)")
        self.button_4.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        self.button_4.setFixedWidth(button_width)
        buttons_layout_3.addWidget(self.button_4)

        control_layout_outer.addLayout(buttons_layout_3)
        
        
        control_layout_outer.addStretch(1)

        main_layout.addWidget(control_panel)
        
        self.setStyleSheet("""
            QPushButton { padding: 12px 20px; border-radius: 6px; font-size: 14px; }
            QMainWindow { background-color: #f0f0f0; }
        """)

    # --- Plotting Logic ---
    
    def start_monitoring(self, data_storage_ref):
        self.data_reference = data_storage_ref
        if pg:
            self.curve_voltage.setData([], [])
            self.curve_current.setData([], [])
        self.timer.start(30)

    def stop_monitoring(self):
        self.timer.stop()

    def update_plot_animation(self):
        if not self.data_reference or not pg:
            return
        
        t = self.data_reference["timestamps"]
        v = self.data_reference["voltage"]
        c = self.data_reference["current"]
        
        if len(t) == 0:
            return

        limit = 1000
        t_data = t[-limit:]
        v_data = v[-limit:]
        c_data = c[-limit:]

        self.curve_voltage.setData(t_data, v_data)
        self.curve_current.setData(t_data, c_data)

    # --- Controller Interface Slots (Status and Control updates) ---
    
    def update_backend_status(self, message, color="#444", bold=False):
        style = f"font-size: 14px; color: {color};"
        if bold:
            style += " font-weight: bold;"
        self.backend_status_label.setText(f"Backend Status: {message}")
        self.backend_status_label.setStyleSheet(style)
        
    def update_simulator_status(self, message, color="#444", bold=False):
        style = f"font-size: 14px; color: {color};"
        if bold:
            style += " font-weight: bold;"
        self.simulator_status_label.setText(f"Simulator Status: {message}")
        self.simulator_status_label.setStyleSheet(style)
        
    def set_backend_controls_enabled(self, is_running):
        self.start_backend_button.setEnabled(not is_running)
        self.stop_backend_button.setEnabled(is_running)
        
    def set_simulator_controls_enabled(self, is_running):
        # Simulator controls are only enabled if the backend (Python ZMQ receiver) is running
        backend_running = self.stop_backend_button.isEnabled() 
        
        if backend_running:
            self.start_simulator_button.setEnabled(not is_running)
            self.stop_simulator_button.setEnabled(is_running)
        else:
            self.start_simulator_button.setEnabled(False)
            self.stop_simulator_button.setEnabled(False)
            
    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)