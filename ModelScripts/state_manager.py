class StateManager:
    def __init__(self):
        self.mode = "Streaming"  # Streaming or Recording
        self.is_recording = False
        self.console_visible = True
        self.playback_file = None
        self.recording_folder = None
        self.connection_status = "not connected"
        self.receiving = False
    
    # Streaming mode functions
    def set_streaming_mode(self):
        self.mode = "Streaming"
        return "Switched to Streaming mode"
    
    def set_playback_mode(self):
        self.mode = "Playback"
        return "Switched to Playback mode"
    
    # Console functions
    def show_console(self):
        self.console_visible = True
        return "Console visible"
    
    def hide_console(self):
        self.console_visible = False
        return "Console hidden"
    
    # Data functions
    def clear_data(self):
        self.playback_file = None
        self.recording_folder = None
        return "Data cleared"
    
    def reset_program(self):
        self.__init__()  # Reset to initial state
        return "Program reset"
    
    # Playback functions
    def set_playback_file(self, file_path):
        self.playback_file = file_path
        return f"Playback file set: {file_path}"
    
    def play_playback(self):
        if self.playback_file:
            return f"Playing: {self.playback_file}"
        return "No playback file selected"
    
    def stop_playback(self):
        return "Playback stopped"
    
    # Recording functions
    def set_recording_folder(self, folder_path):
        self.recording_folder = folder_path
        return f"Recording folder set: {folder_path}"
    
    def play_recording(self):
        if self.recording_folder:
            return f"Recording to: {self.recording_folder}"
        return "No recording folder selected"
    
    def stop_recording(self):
        return "Recording stopped"