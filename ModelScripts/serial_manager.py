# Serial_Manager.py
# Manages serial port communication with mDLP by running background thread to read incoming bytes and feed them to parser
import serial
import serial.tools.list_ports
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from ModelScripts.mdlp_parser import MDLPParser
import time

class SerialReader(QObject):
    data_received = pyqtSignal(object, float)  # (bytes_chunk, timestamp)
    error_occurred = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._serial_port = None
        self._running = False
    
    def set_port(self, serial_port: serial.Serial):
        self._serial_port = serial_port

    # Background thread method to read from serial port
    def start_reading(self):
        self._running = True
        
        try:
            while self._running and self._serial_port and self._serial_port.is_open:
                # Check how many bytes are waiting
                waiting = self._serial_port.in_waiting

                if waiting > 0:
                    # Read all available bytes at once for efficiency
                    data = self._serial_port.read(waiting)
                    timestamp = time.time()

                    # Emit entire chunk at once
                    self.data_received.emit(bytes(data), timestamp)
                else:
                    # No data available, sleep briefly
                    # 1ms is fast enough for 115200 baud
                    QThread.msleep(1)

        except serial.SerialException as e:
            if self._running: 
                self.error_occurred.emit(f"Serial read error: {str(e)}")
                self.connection_lost.emit()
        except Exception as e:
            if self._running:
                self.error_occurred.emit(f"Unexpected error: {str(e)}")

    def stop_reading(self):
        self._running = False

# SerialManager class manages the serial connection and data flow
class SerialManager(QObject):
    connected = pyqtSignal(str)         
    disconnected = pyqtSignal()
    error_occurred = pyqtSignal(str)
    ports_updated = pyqtSignal(list)    

    # Default serial settings for mDLP
    DEFAULT_BAUD = 115200
    DEFAULT_TIMEOUT = 0.1   # Read timeout in seconds

    def __init__(self, data_store):
        super().__init__()
        self._data_store = data_store

        # Serial port
        self._serial_port = None
        self._port_name = None
        self._baud_rate = self.DEFAULT_BAUD

        # Background reader thread
        self._reader = None
        self._reader_thread = None

        # Parser, same class used by PlaybackManager
        self._parser = MDLPParser()
        self._parser.packet_ready.connect(self._on_packet_ready)
        self._parser.sweep_started.connect(self._on_sweep_started)
        self._parser.sweep_ended.connect(self._on_sweep_ended)

        # State
        self._is_connected = False
        
        # Timing: track connection start time for relative timestamps
        self._connection_start_time = None
        self._last_byte_time = 0.0  # Track last assigned timestamp for monotonicity
    
    # Port Discovery
    def scan_ports(self) -> list:
        ports = []
        for port_info in serial.tools.list_ports.comports():
            ports.append({
                'port': port_info.device,
                'description': port_info.description,
                'hwid': port_info.hwid,
            })

        # Sort by port name for consistent ordering
        ports.sort(key=lambda p: p['port'])
        self.ports_updated.emit(ports)
        return ports

    # Connection Control
    def connect(self, port_name: str, baud_rate: int = None) -> bool:
        if self._is_connected:
            self.disconnect()

        if baud_rate is None:
            baud_rate = self.DEFAULT_BAUD

        try:
            # Open serial port
            self._serial_port = serial.Serial(
                port=port_name,
                baudrate=baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.DEFAULT_TIMEOUT,
            )

            self._port_name = port_name
            self._baud_rate = baud_rate

            # Reset parser for fresh connection
            self._parser.reset()

            # Create background reader
            self._reader = SerialReader()
            self._reader.set_port(self._serial_port)
            self._reader.data_received.connect(self._on_data_received)
            self._reader.error_occurred.connect(self._on_reader_error)
            self._reader.connection_lost.connect(self._on_connection_lost)

            # Create and start thread
            self._reader_thread = QThread()
            self._reader.moveToThread(self._reader_thread)
            self._reader_thread.started.connect(self._reader.start_reading)
            self._reader_thread.start()

            self._is_connected = True
            self._connection_start_time = time.time()  # Record connection start for relative timestamps
            self.connected.emit(port_name)
            return True

        except serial.SerialException as e:
            self.error_occurred.emit(f"Failed to open {port_name}: {str(e)}")
            self._cleanup()
            return False
        except Exception as e:
            self.error_occurred.emit(f"Connection error: {str(e)}")
            self._cleanup()
            return False

    def disconnect(self) -> None:
        if not self._is_connected:
            return

        # Stop the reader first
        if self._reader:
            self._reader.stop_reading()

        # Stop the thread
        if self._reader_thread and self._reader_thread.isRunning():
            self._reader_thread.quit()
            self._reader_thread.wait(2000)  # Wait up to 2 seconds

        # Close the port
        if self._serial_port and self._serial_port.is_open:
            try:
                self._serial_port.close()
            except Exception:
                pass

        self._cleanup()
        self.disconnected.emit()

    def _cleanup(self):
        self._serial_port = None
        self._reader = None
        self._reader_thread = None
        self._is_connected = False
        self._connection_start_time = None
        self._last_byte_time = 0.0

    # =-= Data Flow =-=
    def _on_data_received(self, data: bytes, timestamp: float):
        if not self._connection_start_time:
            return
            
        # Calculate relative timestamp for parser
        relative_timestamp = timestamp - self._connection_start_time

        # Calculate inner byte interval based on baud rate (10 bits per byte)
        byte_interval = 10.0 / self._baud_rate  # seconds per byte
                
        # Monotonic ensured by starting from max of (relative_timestamp - chunk_duration) and (last_byte_time + byte_interval)
        n = len(data)
        chunk_duration = (n - 1) * byte_interval
        start_time = max(relative_timestamp - chunk_duration,
                         self._last_byte_time + byte_interval)
        
        feed = self._parser.feed_byte
        for i, byte_val in enumerate(data):
            synthetic_time = start_time + (i * byte_interval)
            feed(byte_val, synthetic_time)
        
        self._last_byte_time = start_time + chunk_duration

    def _on_packet_ready(self, row: dict):
        self._data_store.add(row)

    def _on_sweep_started(self, sweep_info: dict):
        # Future: could emit signal for UI to show sweep info
        pass

    def _on_sweep_ended(self, message: str):
        # Future: could emit signal for UI
        pass


    # =-= Error Handling =-=
    def _on_reader_error(self, error_message: str):
        self.error_occurred.emit(error_message)

    def _on_connection_lost(self):
        self._cleanup()
        self.disconnected.emit()
        self.error_occurred.emit("Serial connection lost")

    # =-= State Queries =-=
    def is_connected(self) -> bool:
        return self._is_connected

    def get_port_name(self) -> str:
        return self._port_name if self._port_name else "None"

    def get_baud_rate(self) -> int:
        return self._baud_rate

    def get_connection_info(self) -> dict:
        return {
            'connected': self._is_connected,
            'port': self._port_name or 'None',
            'baud_rate': self._baud_rate,
            'parser_stats': self._parser.get_diagnostics(),
        }