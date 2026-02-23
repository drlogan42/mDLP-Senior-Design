'''
ButtonController - bridge model and view

Controller
- connect UI buttons to model method calls
-  connect model signals to ui updates
- purely a bridge, no logic, no io, no state management
'''

from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QObject
from pathlib import Path
import pyqtgraph as pg

class ButtonController(QObject):
    def __init__(self, main_window, state_manager, data_store, playback_manager, recording_manager):
        super().__init__()
        # Store references to View and Models
        self.main_window = main_window
        self.state_manager = state_manager
        self.data_store = data_store
        self.playback_manager = playback_manager
        self.recording_manager = recording_manager
        
        # Connect all signals
        self._connect_ui_signals()
        self._connect_model_signals()
        
        # Initialize UI state
        self._update_ui_from_state()
    
    # =-= UI Signal Connections =-=
    def _connect_ui_signals(self):
        # Control Panel buttons
        self.main_window.streaming_btn.clicked.connect(self.on_streaming_click)
        self.main_window.playback_btn.clicked.connect(self.on_playback_click)
        self.main_window.visible_btn.clicked.connect(self.on_visible_click)
        self.main_window.hidden_btn.clicked.connect(self.on_hidden_click)
        self.main_window.clear_btn.clicked.connect(self.on_clear_click)
        self.main_window.reset_btn.clicked.connect(self.on_reset_click)
        
        # Playback Panel buttons
        self.main_window.playback_browse_btn.clicked.connect(self.on_playback_browse_click)
        self.main_window.playback_play_btn.clicked.connect(self.on_playback_play_click)
        self.main_window.playback_stop_btn.clicked.connect(self.on_playback_stop_click)
        
        # Recording Panel buttons (for future recording_manager)
        self.main_window.recording_browse_btn.clicked.connect(self.on_recording_browse_click)
        self.main_window.recording_play_btn.clicked.connect(self.on_recording_play_click)
        self.main_window.recording_stop_btn.clicked.connect(self.on_recording_stop_click)

    # =-= Model Signal Connections =-=
    def _connect_model_signals(self):
        """Connect Model signals to UI update methods."""
        
        # Data Store signals
        self.data_store.data_added.connect(self.on_data_received)
        self.data_store.data_cleared.connect(self.on_data_cleared)
        
        # Playback Manager signals
        self.playback_manager.error_occurred.connect(self.on_playback_error)
        self.playback_manager.state_changed.connect(self.on_playback_state_changed)
        self.playback_manager.playback_finished.connect(self.on_playback_finished)
    
        # Recording Manager signals
        self.recording_manager.recording_started.connect(self.on_recording_started)
        self.recording_manager.recording_stopped.connect(self.on_recording_stopped)
        self.recording_manager.error_occurred.connect(self.on_recording_error)
        self.recording_manager.state_changed.connect(self.on_recording_state_changed)

    # =-= Control Panel Handlers =-=
    def on_streaming_click(self):
        self.state_manager.set_streaming_mode()  

        # Stop any active playback
        if self.playback_manager.is_playing():
            self.playback_manager.stop()

        # Update UI
        self._update_console("Switched to Streaming mode")
        self._update_status("Mode: Streaming")
        self._update_ui_from_state()

    def on_playback_click(self):
        """Handle Playback mode button click."""
        self.state_manager.set_playback_mode()
        
        # Update UI
        self._update_console("Switched to Playback mode")
        self._update_status("Mode: Playback")
        self._update_ui_from_state()
    
    
    def on_visible_click(self):
        self.state_manager.show_console()
        self.main_window.console_text.setVisible(True)
        self._update_console("Console shown")
    
    def on_hidden_click(self):
        self.state_manager.hide_console()
        self.main_window.console_text.setVisible(False)
    
    def on_clear_click(self):
        self.data_store.clear()
        self._update_console("Data cleared")
        self._update_stats()
    
    def on_reset_click(self):
        # Stop any active playback
        self.playback_manager.stop()
        
        # Clear data
        self.data_store.clear()
        
        # Reset state
        self.state_manager.reset_program()
        
        # Update UI
        self._update_console("Program reset")
        self._update_status("Status: Ready")
        self._update_ui_from_state()

    # =-= Playback Handlers =-=

    def on_playback_browse_click(self):
        file_path, _ = QFileDialog.getOpenFileName(self.main_window,"Select Playback File",str(Path.home()),"CSV Files (*.csv);;All Files (*)")
        
        if file_path:
            # Try to load the file
            success = self.playback_manager.load_file(file_path)
            
            if success:
                filename = Path(file_path).name
                self.main_window.playback_file_data.setText(filename)
                
                # Get file info and display
                info = self.playback_manager.get_file_info()
                self._update_console(f"Loaded: {filename} ({info['row_count']} rows)")
                
                # Update UI buttons
                self._update_ui_from_state()
            
            # Error handling is done via signal (on_playback_error)

    def on_playback_play_click(self):
        if not self.playback_manager.is_loaded():
            self._update_console("Error: No file loaded")
            return
        
        # Switch to playback mode if not already
        self.state_manager.set_playback_mode()
        
        # Start playback
        self.playback_manager.play()
        
        self._update_console("Playback started")
    
    def on_playback_stop_click(self):
        self.playback_manager.stop()
        self._update_console("Playback stopped")
    
    # =-= Recording Handlers =-=

    def on_recording_browse_click(self):
        from PyQt6.QtWidgets import QFileDialog
        
        folder = QFileDialog.getExistingDirectory(
            self.main_window,
            "Select Recording Folder",
            self.recording_manager.get_output_folder()
        )
        
        if folder:
            success = self.recording_manager.set_output_folder(folder)
            if success:
                folder_name = Path(folder).name
                self.main_window.data_folder_data.setText(folder_name)
                self._update_console(f"Recording folder set: {folder_name}")
    
    def on_recording_play_click(self):
        """Handle Start Recording button in Recording Panel."""
        if not self.recording_manager.is_recording():
            success = self.recording_manager.start_recording()
            if success:
                self.state_manager.is_recording = True
                self._update_console("Recording started")
                self._update_ui_from_state()
    
    def on_recording_stop_click(self):
        """Handle Stop Recording button in Recording Panel."""
        if self.recording_manager.is_recording():
            self.recording_manager.stop_recording()
            self.state_manager.is_recording = False
            self._update_console("Recording stopped")
            self._update_ui_from_state()
    
    def on_recording_started(self, filename: str):
        file_path = Path(filename)
        self._update_console(f"Recording started: {file_path.name}")
        self.main_window.file_name_data.setText(file_path.name)
    
    def on_recording_stopped(self, packet_count: int):
        self._update_console(f"Recording stopped: {packet_count} packets saved")
        self.main_window.file_name_data.setText("No file")
    
    def on_recording_error(self, error_message: str):
        self._update_console(f"Recording Error: {error_message}")
    
    def on_recording_state_changed(self, state: str):
        self._update_console(f"Recording: {state}")

    # =-= Model Signal Handlers =-=
    def on_data_received(self, row: dict):
        # Called evert time added row to data_store, whether from serial or playback
        self._update_plots(row)
        self._update_stats()
    
    def on_data_cleared(self):
        self._clear_plots()
        self._update_stats()
        self._update_console("Plots cleared")
    
    def on_playback_error(self, error_message: str):
        self._update_console(f"Playback Error: {error_message}")
        self._update_status(f"Error: {error_message}")
        # Make sure UI reflects stopped state
        self._update_ui_from_state()
    
    def on_playback_state_changed(self, state: str):
        self._update_console(f"Playback: {state}")
        self._update_ui_from_state()
    
    def on_playback_finished(self):
        self._update_console("Playback finished")
        self._update_status("Playback: Complete")
        self._update_ui_from_state()

    # =-= UI Helper Methods =-=
    def _update_console(self, message):
        """Update console for debugging messages only."""
        current_text = self.main_window.console_text.toPlainText()
        if current_text:
            new_text = f"{current_text}\n{message}"
        else:
            new_text = message
        self.main_window.console_text.setPlainText(new_text)
        
        # Auto-scroll to bottom
        cursor = self.main_window.console_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.main_window.console_text.setTextCursor(cursor)
    
    def _update_status(self, status_text):
        if "Mode:" in status_text:
            self.main_window.status1.setText(status_text)
        elif "Recording:" in status_text:
            self.main_window.status2.setText(status_text)
        else:
            self.main_window.status3.setText(status_text)
    
    def _update_ui_from_state(self):
        # Update mode status
        self.main_window.status1.setText(f"Mode: {self.state_manager.mode}")
        
        # Update recording status
        is_recording = self.recording_manager.is_recording()
        if is_recording:
            self.main_window.status2.setText("Recording: ON")
            self.main_window.recording_play_btn.setEnabled(False)
            self.main_window.recording_stop_btn.setEnabled(True)
        else:
            self.main_window.status2.setText("Recording: OFF")
            self.main_window.recording_play_btn.setEnabled(True)
            self.main_window.recording_stop_btn.setEnabled(False)
        
        # Update mode buttons
        if self.state_manager.mode == "Streaming":
            self.main_window.streaming_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
            self.main_window.playback_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        elif self.state_manager.mode == "Playback":
            self.main_window.streaming_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            self.main_window.playback_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        
        # Update playback button states
        if self.playback_manager.is_loaded():
            self.main_window.playback_play_btn.setEnabled(not self.playback_manager.is_playing())
            self.main_window.playback_stop_btn.setEnabled(self.playback_manager.is_playing())
        else:
            self.main_window.playback_play_btn.setEnabled(False)
            self.main_window.playback_stop_btn.setEnabled(False)
    

    
    def _update_plots(self, row: dict):
        """Update plots with new data from data_store."""
        # Map CSV data keys to plot channels based on hardware format
        channel_mapping = {
            'Channel 1': 'dac_counts',        # Plot 1 shows DAC values
            'Channel 2': 'integrator_adc',    # Plot 2 shows integrator ADC
            'Channel 3': 'ltc_adc_a',         # Plot 3 shows LTC ADC A
            'Channel 4': 'ltc_adc_b',         # Plot 4 shows LTC ADC B
            'Channel 5': 'frame_id',          # Plot 5 shows frame ID
            'Channel 6': 'packet_id'          # Plot 6 shows packet ID
        }
        
        # Use total received count as x-axis (time/sample number)
        x_value = self.data_store.total_received()
        
        # Update each plot with corresponding data
        for channel_name, data_key in channel_mapping.items():
            if data_key in row:
                y_value = row[data_key]
                self.main_window.update_plot(channel_name, x_value, y_value)
    
    def _clear_plots(self):
        self.main_window.clear_plots()
    
    def _update_stats(self):
        stats = self.data_store.get_stats()
        recording_info = self.recording_manager.get_info()
        
        if recording_info['is_recording']:
            status_text = f"Data: {stats['current_size']} | Recording: {recording_info['packet_count']}"
        else:
            status_text = f"Data Points: {stats['current_size']}"
        
        self.main_window.status3.setText(status_text)