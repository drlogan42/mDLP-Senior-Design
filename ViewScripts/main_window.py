from PyQt6.QtWidgets import QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QGridLayout, QHBoxLayout
from PyQt6.QtCore import Qt

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
        streaming_btn = QPushButton("Streaming")
        streaming_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        control_panel_layout.addWidget(streaming_btn, 0, 1)
        recording_btn = QPushButton("Recording")
        recording_btn.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold;")
        control_panel_layout.addWidget(recording_btn, 0, 2)
        
            # Console Toggle
        control_panel_layout.addWidget(QLabel("Toggle Console"), 1, 0)
        visible_btn = QPushButton("Visible")
        visible_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        control_panel_layout.addWidget(visible_btn, 1, 1)
        hidden_btn = QPushButton("Hidden")
        hidden_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        control_panel_layout.addWidget(hidden_btn, 1, 2)
        
            # Clear Data
        control_panel_layout.addWidget(QLabel("Clear Data"), 2, 0)
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        control_panel_layout.addWidget(clear_btn, 2, 1)
        
            # Reset Program
        control_panel_layout.addWidget(QLabel("Reset Program"), 3, 0)
        reset_btn = QPushButton("Reset")
        reset_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        control_panel_layout.addWidget(reset_btn, 3, 1)

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
        console_text = QLabel("")
        console_text.setStyleSheet("background-color: white; padding: 5px;")
        console_text.setMaximumHeight(120)
        console_panel.setFixedWidth(300)
        console_panel.setFixedHeight(130)
        console_layout.addWidget(console_text)
        
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
        port_data = QLabel("00000")
        port_data.setStyleSheet("background-color: white; padding: 5px;")
        streaming_panel_layout.addWidget(port_data, 0, 1)

            # Baud Rate info
        streaming_panel_layout.addWidget(QLabel("BAUD Rate"), 1, 0)
        baud_data = QLabel("00000")
        baud_data.setStyleSheet("background-color: white; padding: 5px;")
        streaming_panel_layout.addWidget(baud_data, 1, 1)

            # Connection status
        streaming_panel_layout.addWidget(QLabel("Connection:"), 2, 0)
        connection_data = QLabel("not connected")
        connection_data.setStyleSheet("background-color: white; padding: 5px;")
        streaming_panel_layout.addWidget(connection_data, 2, 1)

            # Receiving status
        streaming_panel_layout.addWidget(QLabel("Receiving: "), 3, 0)
        receiving_data = QLabel("false")
        receiving_data.setStyleSheet("background-color: white; padding: 5px;")
        streaming_panel_layout.addWidget(receiving_data, 3, 1)

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
        playback_file_data = QLabel("None")
        playback_file_data.setStyleSheet("background-color: white; padding: 5px;")
        playback_panel_layout.addWidget(playback_file_data, 0, 1)
        
            # Browse btn
        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        playback_panel_layout.addWidget(browse_btn, 0, 2)

            # Play & Stop
        play_btn = QPushButton("Play")
        play_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        playback_panel_layout.addWidget(play_btn, 1, 1)
        stop_btn = QPushButton("Stop")
        stop_btn.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold;")
        playback_panel_layout.addWidget(stop_btn, 1, 2)

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
        data_folder_data = QLabel("None")
        data_folder_data.setStyleSheet("background-color: white; padding: 5px;")
        recording_panel_layout.addWidget(data_folder_data, 0, 1)
        
            # Browse btn
        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        recording_panel_layout.addWidget(browse_btn, 0, 2)

            # File Name info
        recording_panel_layout.addWidget(QLabel("File Name:"), 1, 0)
        file_name_data = QLabel("None")
        file_name_data.setStyleSheet("background-color: white; padding: 5px;")
        recording_panel_layout.addWidget(file_name_data, 1, 1)

            # Play & Stop buttons
        play_btn = QPushButton("Play")
        play_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        recording_panel_layout.addWidget(play_btn, 2, 1)
        stop_btn = QPushButton("Stop")
        stop_btn.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold;")
        recording_panel_layout.addWidget(stop_btn, 2, 2)

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
        status1 = QLabel("Mode : Streaming")
        status1.setStyleSheet("background-color: #FF6B6B; color: white; padding: 10px; font-weight: bold;")
        status1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(status1)

            # Recording status
        status2 = QLabel("Recording: False")
        status2.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        status2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(status2)

            # Error status
        status3 = QLabel("Status: OK")
        status3.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        status3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(status3)

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
        plot_panel.setStyleSheet("background-color: #e0e0e0;")
        plot_layout = QGridLayout(plot_panel)
        plot_layout.setSpacing(10)
        plot_panel.setFixedSize(1000, 1000)

            # 6 plots in 3x2 grid
        for row in range(3):
            for col in range(2):
                plot_widget = QLabel(f"Plot {row * 2 + col + 1}")
                plot_widget.setStyleSheet("background-color: white; border: 1px solid #999;")
                plot_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                plot_layout.addWidget(plot_widget, row, col)

        # add to container layout
        plot_container_layout.addWidget(plot_panel)
        main_layout.addWidget(plot_container)




        # =-= Add Main Layout to central widget =-=
        central_widget.setLayout(main_layout)
