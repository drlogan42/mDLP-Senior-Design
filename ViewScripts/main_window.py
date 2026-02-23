from PyQt6.QtWidgets import QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QGridLayout, QHBoxLayout, QTextEdit
from PyQt6.QtCore import Qt
import pyqtgraph as pg

'''
This Script houses the UI elements of the main window. Creates layouts, buttons, labels, and panels. Does not contain any logic for button clicks or data updates. Purely the view component of the MVC architecture.
'''

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
        control_panel.setFixedWidth(300)
        control_panel.setFixedHeight(175)

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
        self.console_text.setMaximumHeight(120)
        self.console_text.setReadOnly(True)  # Prevent user editing
        console_panel.setFixedWidth(300)
        console_panel.setFixedHeight(130)
        console_layout.addWidget(self.console_text)
        
            # Add to layout
        left_layout.addWidget(console_panel)




        # =-= Streaming Panel =-=-

            # Title
        streaming_title = QLabel("Streaming Panel")
        streaming_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        left_layout.addWidget(streaming_title)

            # Setup                
        streaming_panel = QWidget()
        streaming_panel_layout = QGridLayout(streaming_panel)
        streaming_panel.setStyleSheet("background-color: #e0e0e0;")
        streaming_panel_layout.setSpacing(10)
        streaming_panel_layout.setColumnStretch(0, 1)
        streaming_panel_layout.setColumnStretch(1, 0)
        streaming_panel.setFixedWidth(300)
        streaming_panel.setFixedHeight(130)

            # Port info
        streaming_panel_layout.addWidget(QLabel("Port:"), 0, 0)
        self.port_data = QLabel("00000")
        self.port_data.setStyleSheet("background-color: white; padding: 5px;")
        streaming_panel_layout.addWidget(self.port_data, 0, 1)

            # Baud Rate info
        streaming_panel_layout.addWidget(QLabel("BAUD Rate"), 1, 0)
        self.baud_data = QLabel("00000")
        self.baud_data.setStyleSheet("background-color: white; padding: 5px;")
        streaming_panel_layout.addWidget(self.baud_data, 1, 1)

            # Connection status
        streaming_panel_layout.addWidget(QLabel("Connection:"), 2, 0)
        self.connection_data = QLabel("not connected")
        self.connection_data.setStyleSheet("background-color: white; padding: 5px;")
        streaming_panel_layout.addWidget(self.connection_data, 2, 1)

            # Receiving status
        streaming_panel_layout.addWidget(QLabel("Receiving: "), 3, 0)
        self.receiving_data = QLabel("false")
        self.receiving_data.setStyleSheet("background-color: white; padding: 5px;")
        streaming_panel_layout.addWidget(self.receiving_data, 3, 1)

            # add to layout
        left_layout.addWidget(streaming_panel)




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
        playback_panel.setFixedWidth(300)
        playback_panel.setFixedHeight(100)

            # Playback text
        playback_panel_layout.addWidget(QLabel("Playback File:"), 0, 0)
        self.playback_file_data = QLabel("None")
        self.playback_file_data.setStyleSheet("background-color: white; padding: 5px;")
        playback_panel_layout.addWidget(self.playback_file_data, 0, 1)
        
            # Browse btn
        self.playback_browse_btn = QPushButton("Browse")
        self.playback_browse_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        playback_panel_layout.addWidget(self.playback_browse_btn, 0, 2)

            # Play & Stop
        self.playback_play_btn = QPushButton("Play")
        self.playback_play_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        playback_panel_layout.addWidget(self.playback_play_btn, 1, 1)
        self.playback_stop_btn = QPushButton("Stop")
        self.playback_stop_btn.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold;")
        playback_panel_layout.addWidget(self.playback_stop_btn, 1, 2)

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
        recording_panel.setFixedWidth(300)
        recording_panel.setFixedHeight(115)

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
        bottom_panel.setFixedWidth(300)
        bottom_panel.setFixedHeight(120)

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
        plot_panel.setFixedSize(1000, 1000)

        # Create 6 actual plot widgets for data channels
        self.plots = {}
        self.plot_data = {}
        channel_names = ['Channel 1', 'Channel 2', 'Channel 3', 'Channel 4', 'Channel 5', 'Channel 6']
        
        for i, channel in enumerate(channel_names):
            row = i // 2
            col = i % 2
            
            # Create plot widget with light mode styling
            plot_widget = pg.PlotWidget(title=channel)
            plot_widget.setBackground('white')  # Set background to white
            
            # Configure labels and grid
            plot_widget.setLabel('left', 'Value', color='black', size='10pt')
            plot_widget.setLabel('bottom', 'Time', color='black', size='10pt')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            
            # Style the axes
            ax = plot_widget.getAxis('left')
            ax.setPen(color='black', width=1)
            ax.setTextPen(color='black')
            
            ax = plot_widget.getAxis('bottom') 
            ax.setPen(color='black', width=1)
            ax.setTextPen(color='black')
            
            # Style the title
            plot_widget.plotItem.setTitle(channel, color='black', size='12pt')
            
            # Store reference and initialize data
            self.plots[channel] = plot_widget
            self.plot_data[channel] = {'x': [], 'y': []}
            
            plot_layout.addWidget(plot_widget, row, col)


        # add to container layout
        plot_container_layout.addWidget(plot_panel)
        main_layout.addWidget(plot_container)
        
        # =-= Add Main Layout to central widget =-=
        central_widget.setLayout(main_layout)
    
    def update_plot(self, channel_name, x_value, y_value):
        """Update a specific plot with new data point."""
        if channel_name in self.plots:
            self.plot_data[channel_name]['x'].append(x_value)
            self.plot_data[channel_name]['y'].append(y_value)
            
            # Keep only last 1000 points for performance
            if len(self.plot_data[channel_name]['x']) > 1000:
                self.plot_data[channel_name]['x'] = self.plot_data[channel_name]['x'][-1000:]
                self.plot_data[channel_name]['y'] = self.plot_data[channel_name]['y'][-1000:]
            
            # Update the plot
            self.plots[channel_name].plot(
                self.plot_data[channel_name]['x'], 
                self.plot_data[channel_name]['y'], 
                clear=True, 
                pen='blue'
            )
    
    def clear_plots(self):
        """Clear all plot data."""
        for channel in self.plots:
            self.plot_data[channel] = {'x': [], 'y': []}
            self.plots[channel].clear()




