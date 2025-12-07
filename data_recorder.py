# data_recorder.py
# Buffers and saves the experimental data to a file

import csv
import time
import os

# Receives samples from zmq_controller and soters until stop is recieved.
class DataRecorder:
    def __init__(self):
        self.is_recording = False
        self.start_time = 0.0
        
        # List - based structure for fast appending data
        self.buffer = {
            "elapsed_time": [],
            "recording_time": [],
            "voltage": [],
            "current": []
        }

    # Initializes recorder state before a new trial begins
    def start(self):
        self.buffer = {"elapsed_time": [], "recording_time": [], "voltage": [], "current": []}
        self.start_time = time.time()
        self.is_recording = True

    # Appends new data sample, real-time insertion point
    def add_sample(self, timestamp, voltage, current):
        if not self.is_recording:
            # Drop data silently if recording is not active.
            return
        
        # Append data points to the respective lists.
        rec_time = time.time() - self.start_time
        self.buffer["elapsed_time"].append(timestamp)
        self.buffer["recording_time"].append(rec_time)
        self.buffer["voltage"].append(voltage)
        self.buffer["current"].append(current)

    def get_sample_count(self):
        return len(self.buffer["elapsed_time"])

    def get_current_duration(self):
        if self.is_recording:
            return time.time() - self.start_time
        return 0.0

    # Stop recording, commit buffered data to CSV file.
    def stop_and_save(self):
        self.is_recording = False
        num_samples = len(self.buffer["elapsed_time"])
        
        if num_samples == 0:
            return None

        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        filename = f"recorded_data_{timestamp_str}.csv"

        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Elapsed_Time_s", "Recording_Time_s", "Voltage_V", "Current_A"])
                
                for i in range(num_samples):
                    writer.writerow([
                        f"{self.buffer['elapsed_time'][i]:.4f}",
                        f"{self.buffer['recording_time'][i]:.4f}",
                        f"{self.buffer['voltage'][i]:.4f}",
                        f"{self.buffer['current'][i]:.6f}"
                    ])
            return filename
        except Exception as e:
            raise IOError(f"Failed to write to disk: {e}")