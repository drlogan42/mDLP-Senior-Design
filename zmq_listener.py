# zmq_listener.py
import zmq
from PyQt6.QtCore import QObject, pyqtSignal

class ZmqListenerWorker(QObject):
    """
    Dedicated worker for subscribing to ZMQ topics.
    """
    message_received = pyqtSignal(str)
    
    def __init__(self, address):
        super().__init__()
        self.address = address
        self._running = True
        self.context = None
        self.socket = None

    def run(self):
        try:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.SUB)
            self.socket.connect(self.address)
            self.socket.setsockopt(zmq.SUBSCRIBE, b'')
            
            self.message_received.emit(f"ZMQ Worker connected to {self.address}")
            
            while self._running:
                # Poll to allow for clean exit checks
                if self.socket.poll(100, zmq.POLLIN):
                    message = self.socket.recv_string()
                    self.message_received.emit(message)
            
        except zmq.error.ContextTerminated:
            pass
        except Exception as e:
            self.message_received.emit(f"FATAL ZMQ ERROR: {e}")
        finally:
            if self.socket:
                self.socket.close()

    def stop(self):
        self._running = False
        if self.context:
            self.context.term()