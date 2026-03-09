class StateManager:
    """
    Tracks application-wide state: mode, console visibility, recording status.
    """
    VALID_MODES = ("Streaming", "Playback")

    def __init__(self):
        self.mode = "Streaming"  # Streaming or Playback
        self.is_recording = False
        self.console_visible = True
        self.playback_file = None
        self.recording_folder = None
        self.connection_status = "not connected"
        self.receiving = False
    
    # Mode Control
    def set_streaming_mode(self):
        self.mode = "Streaming"
    
    def set_playback_mode(self):
        self.mode = "Playback"
    
    # Console Control
    def show_console(self):
        self.console_visible = True
     
    def hide_console(self):
        self.console_visible = False

    # Reset
    def reset_program(self):
        """Reset all state to defaults."""
        self.mode = "Streaming"
        self.is_recording = False
        self.console_visible = True
        self.playback_file = None
        self.recording_folder = None
        self.connection_status = "not connected"
        self.receiving = False
