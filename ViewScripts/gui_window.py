# gui_window.py
'''Display UI elements and capture user input'''

import sys
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout, QMessageBox, QFileDialog, QGridLayout)
import pyqtgraph as pg

# Main window class to build the UI and expose methods for controller to update display
class ScientificGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Window Title
        self.setWindowTitle("mDLP Python/Julia GUI")
        self.setGeometry(100, 100, 1050, 600)
        
        # Data References and Timers
        # data_reference holds a pointer to the Controller's plot_data buffer.
        self.data_reference = None 
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot_animation)
        
        self.init_ui()
    
    # Builds the UI structure
    # Sets up layouts, labels, buttons, and graphs
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # =-= Title and Status =-=
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 5) 

        # Title Label (Top Left)
        title_label = QLabel("mDLP Graphical User Interface")
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

        # Status 2: Simulator/Sender Status 
        self.simulator_status_label = QLabel("Simulator Status: Idle.")
        self.simulator_status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.simulator_status_label.setStyleSheet("font-style: italic; color: #444; font-size: 14px;")
        status_container.addWidget(self.simulator_status_label)
        
        # Status 3: Recording Status
        self.recording_status_label = QLabel("Recording Status: Idle.")
        self.recording_status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.recording_status_label.setStyleSheet("font-style: italic; color: #444; font-size: 14px;")
        status_container.addWidget(self.recording_status_label)

        # Status 4: Playback Status
        self.playback_status_label = QLabel("Playback Status: Idle.")
        self.playback_status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.playback_status_label.setStyleSheet("font-style: italic; color: #444; font-size: 14px;")
        status_container.addWidget(self.playback_status_label)

        # End Container
        header_layout.addLayout(status_container)
        main_layout.addLayout(header_layout)

        # =-= Create Graphs =-=
        # Light Mode 
        pg.setConfigOption('background', 'w') 
        pg.setConfigOption('foreground', 'k') 
        self.graph_widget = pg.GraphicsLayoutWidget()
        
        # =-= Preliminary Test Plots =-=
        
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

        # =-= Control Panel =-=
        control_panel = QWidget()
        control_layout_outer = QHBoxLayout(control_panel)
        control_layout_outer.setContentsMargins(10, 10, 10, 10) 
        control_layout_outer.setSpacing(20) 
        button_width = 200

        # Column 1: Backend Listener Control Buttons
        buttons_layout_1 = QVBoxLayout()
        buttons_layout_1.setSpacing(10)

        # Start Button
        self.start_backend_button = QPushButton("1. Start Backend Listener")
        self.start_backend_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_backend_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_backend_button.setFixedWidth(button_width) 
        buttons_layout_1.addWidget(self.start_backend_button)
        
        # Stop Button
        self.stop_backend_button = QPushButton("1. Stop Backend Listener")
        self.stop_backend_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        self.stop_backend_button.setEnabled(False)
        self.stop_backend_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_backend_button.setFixedWidth(button_width)
        buttons_layout_1.addWidget(self.stop_backend_button)

        # End Column 1
        control_layout_outer.addLayout(buttons_layout_1)
        

        # Column 2: Simulator Control Buttons
        buttons_layout_2 = QVBoxLayout()
        buttons_layout_2.setSpacing(10)

        # Start Button
        self.start_simulator_button = QPushButton("2. Start Data Simulator")
        self.start_simulator_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_simulator_button.setFixedWidth(button_width) 
        self.start_simulator_button.setEnabled(False) 
        buttons_layout_2.addWidget(self.start_simulator_button)
        
        # Stop Button
        self.stop_simulator_button = QPushButton("2. Stop Data Simulator")
        self.stop_simulator_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        self.stop_simulator_button.setFixedWidth(button_width)
        self.stop_simulator_button.setEnabled(False) 
        buttons_layout_2.addWidget(self.stop_simulator_button)

        # End Column 2
        control_layout_outer.addLayout(buttons_layout_2)


        # Column 3: Recording Control Buttons
        buttons_layout_3 = QVBoxLayout()
        buttons_layout_3.setSpacing(10)

        # Start Button
        self.start_recording_button = QPushButton("3. START Recording")
        self.start_recording_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_recording_button.setFixedWidth(button_width) 
        self.start_recording_button.setEnabled(False) 
        buttons_layout_3.addWidget(self.start_recording_button)
        
        # Stop Button
        self.stop_recording_button = QPushButton("3. STOP Recording (Save File)")
        self.stop_recording_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        self.stop_recording_button.setFixedWidth(button_width)
        self.stop_recording_button.setEnabled(False) 
        buttons_layout_3.addWidget(self.stop_recording_button)

        # End Column
        control_layout_outer.addLayout(buttons_layout_3)


        # Column 4: Playback Control Buttons
        buttons_layout_4 = QVBoxLayout()
        buttons_layout_4.setSpacing(10)

        # Select Recording Button
        self.select_file_button = QPushButton("4. Select Recording File")
        self.select_file_button.setStyleSheet("background-color: #007bff; color: white; font-weight: bold;")
        self.select_file_button.setFixedWidth(button_width) 
        self.select_file_button.setEnabled(False)
        buttons_layout_4.addWidget(self.select_file_button)
        
        # Start Button
        self.start_playback_button = QPushButton("4. START Playback")
        self.start_playback_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_playback_button.setFixedWidth(button_width) 
        self.start_playback_button.setEnabled(False)
        buttons_layout_4.addWidget(self.start_playback_button)
        
        # Stop Button
        self.stop_playback_button = QPushButton("4. STOP Playback")
        self.stop_playback_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        self.stop_playback_button.setFixedWidth(button_width)
        self.stop_playback_button.setEnabled(False)
        buttons_layout_4.addWidget(self.stop_playback_button)
        
        # End Column
        control_layout_outer.addLayout(buttons_layout_4)
        
        # Extra Stlyling
        control_layout_outer.addStretch(1)
        main_layout.addWidget(control_panel)
        self.setStyleSheet("""
            QPushButton { padding: 12px 20px; border-radius: 6px; font-size: 14px; }
            QMainWindow { background-color: #f0f0f0; }
        """)

    # =-= Real-Time Graphing Logic =-=

    # Start plot animation taking controller's data buffer ref
    def start_monitoring(self, data_storage_ref):
        self.data_reference = data_storage_ref
        # Clear initial data
        self.curve_voltage.setData([], [])
        self.curve_current.setData([], [])
        # Update interval set to 30ms (~33 FPS)
        self.timer.start(30)       # Avg CPU Load ~6% at 30

    # Stops plot update loop
    def stop_monitoring(self):
        self.timer.stop()

    # Reads live data buffer and updates plot curves (only last 1000 shown but all recorded if selected)
    def update_plot_animation(self):
        if not self.data_reference:
            return
        
        t = self.data_reference["timestamps"]
        v = self.data_reference["voltage"]
        c = self.data_reference["current"]
        
        if len(t) == 0:
            return

        # Optimization: Only show the last 'limit' samples to keep plot responsive
        limit = 1000
        t_data = t[-limit:]
        v_data = v[-limit:]
        c_data = c[-limit:]

        self.curve_voltage.setData(t_data, v_data)
        self.curve_current.setData(t_data, c_data)
        
        # Auto-range/auto-scroll 
        if len(t) > 1:
            self.plot_current.setXRange(t_data[0], t_data[-1], padding=0.02)
        else:
            # FIX: Removed the conflicting 'padding' argument from autoRange
            self.plot_current.autoRange('x')


    # =-= Controller Interface Splts  (Status and Control updates) =-=
    # These methods are called by the Controller to push state changes to the View.
    
    # Updates the status label for the Julia Backend
    def update_backend_status(self, message, color="#444", bold=False):
        style = f"font-size: 14px; color: {color};"
        if bold:
            style += " font-weight: bold;"
        self.backend_status_label.setText(f"Backend Status: {message}")
        self.backend_status_label.setStyleSheet(style)
    
    # Updates the status label for the Julia Simulator
    def update_simulator_status(self, message, color="#444", bold=False):
        style = f"font-size: 14px; color: {color};"
        if bold:
            style += " font-weight: bold;"
        self.simulator_status_label.setText(f"Simulator Status: {message}")
        self.simulator_status_label.setStyleSheet(style)

    # Updates the status label for the Data Recording
    def update_recording_status(self, message, color="#444", bold=False):
        style = f"font-size: 14px; color: {color};"
        if bold:
            style += " font-weight: bold;"
        self.recording_status_label.setText(f"Recording Status: {message}")
        self.recording_status_label.setStyleSheet(style)
    
    
    # Updates the status label for the Trial Playback
    def update_playback_status(self, message, color="#444", bold=False):
        style = f"font-size: 14px; color: {color};"
        if bold:
            style += " font-weight: bold;"
        self.playback_status_label.setText(f"Playback Status: {message}")
        self.playback_status_label.setStyleSheet(style)
    
    # Enables/disables Start/Stop Backend buttons based on running state 
    def set_backend_controls_enabled(self, is_running):
        self.start_backend_button.setEnabled(not is_running)
        self.stop_backend_button.setEnabled(is_running)

    # Enables/disables Start/Stop Simulator buttons, dependent on backend running
    def set_simulator_controls_enabled(self, is_running):
        backend_running = self.stop_backend_button.isEnabled() 
        
        if backend_running:
            self.start_simulator_button.setEnabled(not is_running)
            self.stop_simulator_button.setEnabled(is_running)
        else:
            self.start_simulator_button.setEnabled(False)
            self.stop_simulator_button.setEnabled(False)

    # Enables/disables Recording buttons. The Controller should only call this if both Backend AND Simulator are running.
    def set_recording_controls_enabled(self, is_running):
        backend_running = self.stop_backend_button.isEnabled() 
        
        if backend_running:
            self.start_recording_button.setEnabled(not is_running)
            self.stop_recording_button.setEnabled(is_running)
        else:
            self.start_recording_button.setEnabled(False)
            self.stop_recording_button.setEnabled(False)

    # Manages the state of the Playback controls based on system state.             
    def set_playback_controls_enabled(self, file_selected=False, is_playing=False, backend_running=False):
        if not backend_running:
            self.select_file_button.setEnabled(False)
            self.start_playback_button.setEnabled(False)
            self.stop_playback_button.setEnabled(False)
            self.update_playback_status("Backend needed for Playback.", "orange")
            return
            
        # If the backend is running, enable Select File
        self.select_file_button.setEnabled(not is_playing)
        
        # If a file is selected AND nothing else is running, allow starting playback
        can_start = file_selected and not is_playing
        self.start_playback_button.setEnabled(can_start)
        
        # Allow stopping if playback is active
        self.stop_playback_button.setEnabled(is_playing)
            
    # Displays a critical error message box
    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)