# blocking_controller.py
# Houses logic of executing Julia script. Manages application state while external process runs

# Imports
import subprocess 
import os 
import sys

# Import constants
from config import JULIA_SCRIPT_PATH


#   Handles the execution of the external Julia script (the logic).
#   It requires a reference to the main window to update status.
    
class BlockingController:
    def __init__(self, window):     # Controller accepts MVPWindow as argument
        self.window = window    # Save a reference to this instance

    # Called when UI Button is clicked, runs subprocess and updates GUI via window reference
    def execute_julia(self):

        # Null reference check
        if not os.path.exists(JULIA_SCRIPT_PATH):   # If script doesnt match path throw err
            self.window.show_error("Error", f"Julia script not found: {JULIA_SCRIPT_PATH}")
            return
            
        # Pending status when loading
        self.window.update_status_text(
            "Status: Launching Julia...", 
            "font-style: italic; color: orange; font-size: 14px;"
        )
        self.window.set_button_enabled(False, "Running...")

        # Execute Julia with blocking
        try:
            result = subprocess.run(
                ['julia', JULIA_SCRIPT_PATH], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # SUCCESS
            output_text = result.stdout.strip()
            self.window.update_status_text(
                f"SUCCESS! Julia Output: {output_text}", 
                "font-style: italic; color: green; font-weight: bold; font-size: 14px;"
            )
            print(f"Julia Process finished. Output: {output_text}", file=sys.stderr)

        # Exceptions    
        except FileNotFoundError:
            # ERROR: Julia executable not found
            error_message = ("The 'julia' command could not be found. \n"
                             "Please ensure Julia is installed and added to your system's PATH.")
            self.window.update_status_text("ERROR: 'julia' executable not found.", "font-style: italic; color: red; font-weight: bold; font-size: 14px;")
            self.window.show_error("Error", error_message)
            
        except subprocess.CalledProcessError as e:
            # ERROR: Julia script failed at runtime
            error_output = e.stderr.strip() or "No detailed error provided."
            error_message = f"Julia script crashed. Stderr:\n{error_output}"
            self.window.update_status_text("ERROR: Julia script failed.", "font-style: italic; color: red; font-weight: bold; font-size: 14px;")
            self.window.show_error("Julia Runtime Error", error_message)
            
        except Exception as e:
            # UNKNOWN ERROR
            self.window.update_status_text(f"An unknown error occurred: {e}", "font-style: italic; color: red; font-weight: bold; font-size: 14px;")
            self.window.show_error("Unknown Error", str(e))
            
        finally:
            # CLEANUP
            self.window.set_button_enabled(True, "Run Julia 'Hello World'")