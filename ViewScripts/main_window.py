from PyQt6.QtWidgets import QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QGridLayout, QHBoxLayout, QTextEdit, QComboBox, QSizePolicy
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg
import numpy as np

'''
This Script houses the UI elements of the main window. Creates layouts, buttons, labels, and panels. Does not contain any logic for button clicks or data updates. Purely the view component of the MVC architecture.
'''

class PlotRingBuffer:
    """Pre-allocated numpy ring buffer for efficient plot data storage.
    
    Avoids repeated memory allocation during high-rate data streaming.
    Overwrites oldest data when full (circular buffer behavior).
    """
    def __init__(self, max_size: int = 10000):  # Larger buffer for more data
        self.max_size = max_size
        self._x = np.zeros(max_size, dtype=np.float64)
        self._y = np.zeros(max_size, dtype=np.float64)
        self._head = 0      # Next write position
        self._count = 0     # Number of valid entries
        self.dirty = False   # True when new data added since last plot refresh

    def append(self, x: float, y: float):
        self._x[self._head] = x
        self._y[self._head] = y
        self._head = (self._head + 1) % self.max_size
        if self._count < self.max_size:
            self._count += 1
        self.dirty = True

    def append_bulk(self, x_arr, y_arr):
        """Append arrays of x/y values efficiently."""
        n = len(x_arr)
        if n == 0:
            return
        if n >= self.max_size:
            # More data than buffer can hold — keep last max_size points
            x_arr = x_arr[-self.max_size:]
            y_arr = y_arr[-self.max_size:]
            n = self.max_size
            self._x[:] = x_arr
            self._y[:] = y_arr
            self._head = 0
            self._count = self.max_size
        else:
            end = self._head + n
            if end <= self.max_size:
                self._x[self._head:end] = x_arr
                self._y[self._head:end] = y_arr
            else:
                first = self.max_size - self._head
                self._x[self._head:] = x_arr[:first]
                self._y[self._head:] = y_arr[:first]
                remainder = n - first
                self._x[:remainder] = x_arr[first:]
                self._y[:remainder] = y_arr[first:]
            self._head = (self._head + n) % self.max_size
            self._count = min(self._count + n, self.max_size)
        self.dirty = True

    def get_ordered(self):
        """Return (x_array, y_array) in chronological order as numpy views."""
        if self._count == 0:
            return np.empty(0), np.empty(0)
        if self._count < self.max_size:
            return self._x[:self._count], self._y[:self._count]
        # Buffer is full and wrapped — concatenate to get chronological order
        return (np.concatenate((self._x[self._head:], self._x[:self._head])),
                np.concatenate((self._y[self._head:], self._y[:self._head])))

    def resize(self, new_max_size: int):
        """Resize the buffer, preserving existing data up to new capacity."""
        if new_max_size == self.max_size:
            return
        x_old, y_old = self.get_ordered()
        keep = min(len(x_old), new_max_size)
        self.max_size = new_max_size
        self._x = np.zeros(new_max_size, dtype=np.float64)
        self._y = np.zeros(new_max_size, dtype=np.float64)
        if keep > 0:
            self._x[:keep] = x_old[-keep:]
            self._y[:keep] = y_old[-keep:]
        self._head = keep % new_max_size
        self._count = keep
        self.dirty = True

    def clear(self):
        self._head = 0
        self._count = 0
        self.dirty = True

    def __len__(self):
        return self._count

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # =-=-= Setup =-=-=
        self.setWindowTitle("Main Window")
        self.resize(1920, 1080)
        self.setMinimumSize(1280, 720)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("background-color: #f0f0f0")


        # =-= Main Layout =-=-
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)



        # =-= Left Panel  =-=-
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)  # Limit width but allow flexibility
        left_panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)




        # =-= Control Panel =-=-
            # Title
        control_title = QLabel("Control Panel")
        control_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        left_layout.addWidget(control_title)
        
            # Setup
        control_panel = QWidget()
        control_panel_layout = QGridLayout(control_panel)
        control_panel.setStyleSheet("background-color: #e0e0e0;")
        control_panel_layout.setSpacing(10)
        control_panel.setMinimumWidth(250)
        control_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

            # Streaming and Recording buttons
        control_panel_layout.addWidget(QLabel("Mode Select"), 0, 0)
        self.streaming_btn = QPushButton("Streaming")
        self.streaming_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        control_panel_layout.addWidget(self.streaming_btn, 0, 1)
        self.playback_btn = QPushButton("Playback")
        self.playback_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        control_panel_layout.addWidget(self.playback_btn, 0, 2)
        
            # Console Toggle
        control_panel_layout.addWidget(QLabel("Toggle Console"), 1, 0)
        self.visible_btn = QPushButton("Visible")
        self.visible_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        control_panel_layout.addWidget(self.visible_btn, 1, 1)
        self.hidden_btn = QPushButton("Hidden")
        self.hidden_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        control_panel_layout.addWidget(self.hidden_btn, 1, 2)
        
            # Clear Data
        control_panel_layout.addWidget(QLabel("Clear Data"), 2, 0)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        control_panel_layout.addWidget(self.clear_btn, 2, 1)
        
            # Reset Program
        control_panel_layout.addWidget(QLabel("Reset Program"), 3, 0)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        control_panel_layout.addWidget(self.reset_btn, 3, 1)

            # Add Control Panel to layout
        left_layout.addWidget(control_panel)




        # =-= Console Panel =-=-

            # Title
        console_title = QLabel("Console")
        console_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        left_layout.addWidget(console_title)

            # Setup
        console_panel = QWidget()
        console_layout = QVBoxLayout(console_panel)
        console_panel.setStyleSheet("background-color: #e0e0e0;")
        console_layout.setContentsMargins(5, 5, 5, 5)
        console_layout.setSpacing(5)
        
            # Text Area
        self.console_text = QTextEdit()
        self.console_text.setStyleSheet("background-color: white; padding: 5px;")
        self.console_text.setMinimumHeight(80)
        self.console_text.setMaximumHeight(150)
        self.console_text.setReadOnly(True)  # Prevent user editing
        console_panel.setMinimumWidth(250)
        console_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        console_layout.addWidget(self.console_text)
        
            # Add to layout
        left_layout.addWidget(console_panel)





        # =-= Serial Panel =-=-

            # Title
        serial_title = QLabel("Serial Connection")
        serial_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        left_layout.addWidget(serial_title)

            # Setup
        serial_panel = QWidget()
        serial_panel_layout = QGridLayout(serial_panel)
        serial_panel.setStyleSheet("background-color: #e0e0e0;")
        serial_panel_layout.setSpacing(10)
        serial_panel.setMinimumWidth(250)
        serial_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

            # Port selection
        serial_panel_layout.addWidget(QLabel("Port:"), 0, 0)
        self.serial_port_combo = QComboBox()
        self.serial_port_combo.setMinimumWidth(120)
        self.serial_port_combo.setStyleSheet("background-color: white; color: #333; padding: 2px;")
        serial_panel_layout.addWidget(self.serial_port_combo, 0, 1)
        self.serial_refresh_btn = QPushButton("Refresh")
        self.serial_refresh_btn.setStyleSheet("background-color: #607D8B; color: white; font-weight: bold;")
        serial_panel_layout.addWidget(self.serial_refresh_btn, 0, 2)

            # Baud rate
        serial_panel_layout.addWidget(QLabel("Baud:"), 1, 0)
        self.serial_baud_combo = QComboBox()
        self.serial_baud_combo.addItems(['921600', '460800', '230400', '115200', '57600', '38400', '19200', '9600'])
        self.serial_baud_combo.setCurrentText('921600')
        self.serial_baud_combo.setStyleSheet("background-color: white; color: #333; padding: 2px;")
        serial_panel_layout.addWidget(self.serial_baud_combo, 1, 1)

            # Connect & Disconnect
        self.serial_connect_btn = QPushButton("Connect")
        self.serial_connect_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        serial_panel_layout.addWidget(self.serial_connect_btn, 2, 1)
        self.serial_disconnect_btn = QPushButton("Disconnect")
        self.serial_disconnect_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.serial_disconnect_btn.setEnabled(False)
        serial_panel_layout.addWidget(self.serial_disconnect_btn, 2, 2)

            # Status
        self.serial_status_label = QLabel("Status: Disconnected")
        self.serial_status_label.setStyleSheet("color: #f44336; font-size: 11px;")
        self.serial_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        serial_panel_layout.addWidget(self.serial_status_label, 3, 0, 1, 3)

            # Add to layout
        left_layout.addWidget(serial_panel)
        









        # =-= Playback Panel =-=-

            #Title
        playback_title = QLabel("Playback Panel")
        playback_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        left_layout.addWidget(playback_title)

            # Setup             
        playback_panel = QWidget()
        playback_panel_layout = QGridLayout(playback_panel)
        playback_panel.setStyleSheet("background-color: #e0e0e0;")
        playback_panel_layout.setSpacing(10)
        playback_panel.setMinimumWidth(250)
        playback_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

            # Playback text
        playback_panel_layout.addWidget(QLabel("Playback File:"), 0, 0)
        self.playback_file_data = QLabel("None")
        self.playback_file_data.setStyleSheet("background-color: white; padding: 5px;")
        playback_panel_layout.addWidget(self.playback_file_data, 0, 1)
        
            # Browse btn
        self.playback_browse_btn = QPushButton("Browse")
        self.playback_browse_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        playback_panel_layout.addWidget(self.playback_browse_btn, 0, 2)

            # Speed selection
        playback_panel_layout.addWidget(QLabel("Speed:"), 1, 0)
        self.playback_speed_combo = QComboBox()
        self.playback_speed_combo.addItems(['0.1x', '0.25x', '0.5x', '1.0x', '2.0x', '5.0x', '10.0x'])
        self.playback_speed_combo.setCurrentText('1.0x')
        self.playback_speed_combo.setStyleSheet("background-color: white; color: #333; padding: 2px;")
        playback_panel_layout.addWidget(self.playback_speed_combo, 1, 1)

            # Play, Bulk Plot & Stop
        self.playback_play_btn = QPushButton("Play")
        self.playback_play_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        playback_panel_layout.addWidget(self.playback_play_btn, 2, 0)
        self.playback_bulk_btn = QPushButton("Bulk Plot")
        self.playback_bulk_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        playback_panel_layout.addWidget(self.playback_bulk_btn, 2, 1)
        self.playback_stop_btn = QPushButton("Stop")
        self.playback_stop_btn.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold;")
        playback_panel_layout.addWidget(self.playback_stop_btn, 2, 2)

            # add to layout
        left_layout.addWidget(playback_panel)




        # =-= Recording Panel  =-=-

            # Title
        recording_title = QLabel("Recording Panel")
        recording_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        left_layout.addWidget(recording_title)

            # Setup               
        recording_panel = QWidget()
        recording_panel_layout = QGridLayout(recording_panel)
        recording_panel.setStyleSheet("background-color: #e0e0e0;")
        recording_panel_layout.setSpacing(10)
        recording_panel.setMinimumWidth(250)
        recording_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

            # Data Folder info
        recording_panel_layout.addWidget(QLabel("Data Folder:"), 0, 0)
        self.data_folder_data = QLabel("None")
        self.data_folder_data.setStyleSheet("background-color: white; padding: 5px;")
        recording_panel_layout.addWidget(self.data_folder_data, 0, 1)
        
            # Browse btn
        self.recording_browse_btn = QPushButton("Browse")
        self.recording_browse_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        recording_panel_layout.addWidget(self.recording_browse_btn, 0, 2)

            # File Name info
        recording_panel_layout.addWidget(QLabel("File Name:"), 1, 0)
        self.file_name_data = QLabel("None")
        self.file_name_data.setStyleSheet("background-color: white; padding: 5px;")
        recording_panel_layout.addWidget(self.file_name_data, 1, 1)

            # Start & Stop buttons
        self.recording_play_btn = QPushButton("Start")
        self.recording_play_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        recording_panel_layout.addWidget(self.recording_play_btn, 2, 1)
        self.recording_stop_btn = QPushButton("Stop")
        self.recording_stop_btn.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold;")
        recording_panel_layout.addWidget(self.recording_stop_btn, 2, 2)

            # add to layout
        left_layout.addWidget(recording_panel)




        # =-= Status =-=-
            # Setup
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        bottom_panel.setMinimumWidth(250)
        bottom_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

            # Mode status
        self.status1 = QLabel("Mode : Streaming")
        self.status1.setStyleSheet("background-color: #FF6B6B; color: white; padding: 10px; font-weight: bold;")
        self.status1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.status1)

            # Recording status
        self.status2 = QLabel("Recording: False")
        self.status2.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        self.status2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.status2)

            # Error status
        self.status3 = QLabel("Status: OK")
        self.status3.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.status3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.status3)

            # Data stats (separate from status3 so error messages aren't overwritten)
        self.stats_label = QLabel("Data Points: 0")
        self.stats_label.setStyleSheet("background-color: #607D8B; color: white; padding: 5px; font-size: 11px;")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.stats_label)

            # add to layout
        left_layout.addWidget(bottom_panel)
        left_layout.addStretch()




        # =-= Add Left Panel to main layout =-=
        main_layout.addWidget(left_panel)



        # =-= Plot Panel Container =-=-
            # Setup
        plot_container = QWidget()
        plot_container_layout = QVBoxLayout(plot_container)
        plot_container_layout.setContentsMargins(0, 0, 0, 0)
        plot_container_layout.setSpacing(10)

            # Title
        plot_title = QLabel("Plot Panel")
        plot_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        plot_container_layout.addWidget(plot_title)

            # =- Plots -=
        plot_panel = QWidget()
        plot_panel.setStyleSheet("background-color: white;")
        plot_layout = QGridLayout(plot_panel)
        plot_layout.setSpacing(10)
        plot_panel.setMinimumSize(600, 400)
        plot_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Create 6 actual plot widgets for data channels
        self.plots = {}
        self.plot_data = {}      # channel -> PlotRingBuffer
        self.plot_colors = {}
        self.plot_curves = {}
        self.plot_x_combos = {}
        self.plot_y_combos = {}

        # Plot refresh rate limit (60 FPS for smooth rendering)
        self._plot_refresh_timer = QTimer()
        self._plot_refresh_timer.setInterval(16)  # 60 FPS
        self._plot_refresh_timer.timeout.connect(self._refresh_dirty_plots)
        self._plot_refresh_timer.start()

        # Track global min/max values for intelligent axis scaling
        self._axis_ranges = {}  # axis_key -> {'min': value, 'max': value}

        # Axis options available in dropdowns
        self.axis_options = [
            ('Time',           'time'),
            ('DAC Voltage',    'dac_v'),
            ('Integrator V',   'integrator_v'),
            ('ADC A Current',  'adc_a_current'),
            ('ADC B Current',  'adc_b_current'),
            ('Diff Voltage',   'diff_v'),
            ('Diff Current',   'diff_i'),
        ]
        self._axis_display_names = [name for name, _ in self.axis_options]
        self._axis_keys = [key for _, key in self.axis_options]
        
        # Channel config: (internal_name, display_title, default_y_index, pen_color)
        #   default_y_index refers to self.axis_options index
        channel_config = [
            ('Channel 1', 'DAC Voltage',         1, '#2196F3'),
            ('Channel 2', 'Integrator Voltage',   2, '#4CAF50'),
            ('Channel 3', 'ADC A Current',        3, '#FF9800'),
            ('Channel 4', 'ADC B Current',        4, '#F44336'),
            ('Channel 5', 'Differential Voltage', 5, '#9C27B0'),
            ('Channel 6', 'Differential Current', 6, '#00BCD4'),
        ]
        
        for i, (channel, title, default_y_idx, color) in enumerate(channel_config):
            grid_row = i // 2
            grid_col = i % 2

            # Container for dropdown row + plot
            cell_widget = QWidget()
            cell_layout = QVBoxLayout(cell_widget)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(2)

            # Axis selector row
            selector_row = QHBoxLayout()
            selector_row.setSpacing(4)

            x_label = QLabel("X:")
            x_label.setStyleSheet("font-size: 10px; color: #333;")
            x_combo = QComboBox()
            x_combo.addItems(self._axis_display_names)
            x_combo.setCurrentIndex(0)  # Default: Time
            x_combo.setStyleSheet("background-color: white; color: #333; padding: 1px; font-size: 10px;")
            x_combo.setFixedHeight(22)

            y_label = QLabel("Y:")
            y_label.setStyleSheet("font-size: 10px; color: #333;")
            y_combo = QComboBox()
            y_combo.addItems(self._axis_display_names)
            y_combo.setCurrentIndex(default_y_idx)
            y_combo.setStyleSheet("background-color: white; color: #333; padding: 1px; font-size: 10px;")
            y_combo.setFixedHeight(22)

            selector_row.addWidget(x_label)
            selector_row.addWidget(x_combo)
            selector_row.addWidget(y_label)
            selector_row.addWidget(y_combo)
            selector_row.addStretch()
            cell_layout.addLayout(selector_row)

            self.plot_x_combos[channel] = x_combo
            self.plot_y_combos[channel] = y_combo

            # Plot widget
            # Create initial title in "Y vs X" format
            initial_title = f"{self._axis_display_names[default_y_idx]} vs Time"
            plot_widget = pg.PlotWidget(title=initial_title)
            plot_widget.setBackground('white')
            
            plot_widget.setLabel('left', self._axis_display_names[default_y_idx], color='black', size='10pt')
            plot_widget.setLabel('bottom', 'Time', units='s', color='black', size='10pt')
            plot_widget.showGrid(x=True, y=True, alpha=0.5)
            
            ax = plot_widget.getAxis('left')
            ax.setPen(color='black', width=1)
            ax.setTextPen(color='black')
            
            ax = plot_widget.getAxis('bottom') 
            ax.setPen(color='black', width=1)
            ax.setTextPen(color='black')
            
            plot_widget.plotItem.setTitle(initial_title, color='black', size='12pt')

            # Performance: only render data within view range
            plot_widget.setClipToView(True)
            plot_widget.setDownsampling(mode='peak')
            
            # Disable auto-range so our intelligent scaling takes control
            plot_widget.enableAutoRange(enable=False)
            plot_widget.setAutoVisible(y=False)

            cell_layout.addWidget(plot_widget)
            
            self.plots[channel] = plot_widget
            self.plot_data[channel] = PlotRingBuffer(max_size=5000)
            self.plot_colors[channel] = color
            self.plot_curves[channel] = plot_widget.plot(pen=pg.mkPen(color, width=2))
            
            plot_layout.addWidget(cell_widget, grid_row, grid_col)


        # add to container layout
        plot_container_layout.addWidget(plot_panel)
        main_layout.addWidget(plot_container)
        
        # =-= Add Main Layout to central widget =-=
        central_widget.setLayout(main_layout)
    
    def update_plot(self, channel_name, x_value, y_value):
        """Buffer a new data point. Actual rendering happens on the refresh timer."""
        if channel_name not in self.plot_data:
            return
        self.plot_data[channel_name].append(x_value, y_value)

    def set_plot_data(self, channel_name, x_arr, y_arr):
        """Replace all data for a channel from pre-built arrays (bulk / axis change)."""
        if channel_name not in self.plot_data:
            return
        buf = self.plot_data[channel_name]
        n = len(x_arr)
        if n > buf.max_size:
            buf.resize(n)
        buf.clear()
        buf.append_bulk(np.asarray(x_arr, dtype=np.float64),
                        np.asarray(y_arr, dtype=np.float64))

    def flush_plots(self):
        """Force an immediate render of all dirty plots (call after bulk operations)."""
        self._refresh_dirty_plots()

    def _refresh_dirty_plots(self):
        """Redraw only plots whose data changed since last refresh."""
        for channel, buf in self.plot_data.items():
            if buf.dirty:
                x, y = buf.get_ordered()
                self.plot_curves[channel].setData(x, y)
                buf.dirty = False
                
                # Update axis ranges and apply intelligent scaling
                self._update_axis_ranges(channel, x, y)
                self._apply_intelligent_scaling(channel)

    def _update_axis_ranges(self, channel: str, x_data, y_data):
        """Update global min/max tracking for axis data."""
        if len(x_data) == 0:
            return
            
        x_key, y_key = self.get_axis_keys(channel)
        
        # Update X axis range (with special handling for time)
        if x_key != 'time':  # Non-time axes track global min/max
            if x_key not in self._axis_ranges:
                self._axis_ranges[x_key] = {'min': float('inf'), 'max': float('-inf')}
            self._axis_ranges[x_key]['min'] = min(self._axis_ranges[x_key]['min'], np.min(x_data))
            self._axis_ranges[x_key]['max'] = max(self._axis_ranges[x_key]['max'], np.max(x_data))
            
        # Update Y axis range  
        if y_key not in self._axis_ranges:
            self._axis_ranges[y_key] = {'min': float('inf'), 'max': float('-inf')}
        self._axis_ranges[y_key]['min'] = min(self._axis_ranges[y_key]['min'], np.min(y_data))
        self._axis_ranges[y_key]['max'] = max(self._axis_ranges[y_key]['max'], np.max(y_data))

    def _apply_intelligent_scaling(self, channel: str):
        """Apply intelligent axis scaling based on data ranges."""
        x_key, y_key = self.get_axis_keys(channel)
        plot = self.plots[channel]
        
        # Handle X axis
        if x_key == 'time':
            # Show a ~2s trailing window (matches live streaming scale)
            x_data, _ = self.plot_data[channel].get_ordered()
            if len(x_data) > 0:
                x_max = np.max(x_data)
                x_min_data = np.min(x_data)
                window = 2.0  # seconds visible at a time
                x_start = max(x_min_data, x_max - window)
                x_padding = window * 0.02
                plot.setXRange(x_start - x_padding, x_max + x_padding, padding=0)
        else:
            # For non-time axes, use global range with padding
            if x_key in self._axis_ranges:
                x_range = self._axis_ranges[x_key]
                x_span = x_range['max'] - x_range['min']
                x_padding = max(x_span * 0.05, abs(x_range['max']) * 0.01)  # 5% or 1% of max value
                plot.setXRange(x_range['min'] - x_padding, x_range['max'] + x_padding, padding=0)
        
        # Handle Y axis - always use global range with padding 
        if y_key in self._axis_ranges:
            y_range = self._axis_ranges[y_key] 
            y_span = y_range['max'] - y_range['min']
            y_padding = max(y_span * 0.05, abs(y_range['max']) * 0.01)  # 5% or 1% of max value
            plot.setYRange(y_range['min'] - y_padding, y_range['max'] + y_padding, padding=0)
    
    def get_axis_keys(self, channel_name):
        """Return (x_data_key, y_data_key) for the given channel based on dropdown selections."""
        x_idx = self.plot_x_combos[channel_name].currentIndex()
        y_idx = self.plot_y_combos[channel_name].currentIndex()
        return self._axis_keys[x_idx], self._axis_keys[y_idx]

    def update_plot_labels(self, channel_name):
        """Update axis labels and title to match current dropdown selections."""
        x_name = self.plot_x_combos[channel_name].currentText()
        y_name = self.plot_y_combos[channel_name].currentText()
        self.plots[channel_name].setLabel('bottom', x_name, color='black', size='10pt')
        self.plots[channel_name].setLabel('left', y_name, color='black', size='10pt')
        
        # Update plot title to show current axes
        title = f"{y_name} vs {x_name}"
        self.plots[channel_name].plotItem.setTitle(title, color='black', size='12pt')
        
        # Re-apply intelligent scaling for new axis selection
        if channel_name in self.plot_data and len(self.plot_data[channel_name]) > 0:
            x_data, y_data = self.plot_data[channel_name].get_ordered()
            self._update_axis_ranges(channel_name, x_data, y_data)
            self._apply_intelligent_scaling(channel_name)

    def clear_plots(self):
        """Clear all plot data and reset curves."""
        for channel in self.plots:
            self.plot_data[channel].clear()
            self.plot_curves[channel].setData([], [])
        # Reset axis ranges when plots are cleared
        self._axis_ranges.clear()

    def reset_axis_ranges(self):
        """Reset all tracked axis ranges (useful after loading new data).""" 
        self._axis_ranges.clear()
        # Trigger re-calculation of ranges for current data
        for channel, buf in self.plot_data.items():
            if len(buf) > 0:
                x_data, y_data = buf.get_ordered()
                self._update_axis_ranges(channel, x_data, y_data)
                self._apply_intelligent_scaling(channel)




