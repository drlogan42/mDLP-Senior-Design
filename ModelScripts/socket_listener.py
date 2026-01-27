# socket_listener.py
# This script defines a ZMQ listener worker that runs in its own thread
# to receive messages without blocking the main GUI thread.


# Import from Library and Local Scripts
import zmq
from PyQt6.QtCore import QObject, pyqtSignal

# Dedicated worker for subscribing to ZMQ topics.
# Class runs in its own thread to avoid blocking the main GUI thread.
class ZmqListenerWorker(QObject):
    message_received = pyqtSignal(str)
    
    # Initialize with ZMQ address to connect to.
    def __init__(self, address):
        super().__init__()
        self.address = address
        self._running = True
        self.context = None
        self.socket = None

    # Main loop to connect and listen for messages.
    def run(self):
        try:
            # Set up ZMQ context and subscriber socket.
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.SUB)
            self.socket.connect(self.address)
            self.socket.setsockopt(zmq.SUBSCRIBE, b'')
            
            self.message_received.emit(f"ZMQ Worker connected to {self.address}")
            
            # Listen for messages until stopped.
            while self._running:
                # Poll to allow for clean exit checks
                if self.socket.poll(100, zmq.POLLIN):
                    message = self.socket.recv_string()
                    self.message_received.emit(message)

        # Handle termination and other exceptions.    
        except zmq.error.ContextTerminated:
            pass
        except Exception as e:
            self.message_received.emit(f"FATAL ZMQ ERROR: {e}")
        finally:
            if self.socket:
                self.socket.close()

    # Stop the worker thread and clean up ZMQ context.
    def stop(self):
        self._running = False
        if self.context:
            self.context.term()