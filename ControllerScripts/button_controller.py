# 

class ButtonController:
    def __init__(self, main_window):
        self.main_window = main_window
        self.main_window.button.clicked.connect(self.on_button_click)
    
    def on_button_click(self):
        self.main_window.display_label.setText("Button Clicked!")