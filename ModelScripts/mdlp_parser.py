'''
MDLP Parser streams parsed binary protocol for data stream 

Processes raw bytes one at a time using state machine
'''


from PyQt6.QtCore import QObject, pyqtSignal
import struct

class MDLPParser(QObject):
    # Signal emitted when complete data packet is parsed
    
    # Dict contains timestamp, frame_id, packet_id, dac_v, integrator_v, adc_a_current, adc_b_current, etc.
    packet_ready = pyqtSignal(dict)

    #Singal for sweep start (INIT)
    sweep_started = pyqtSignal(dict)

    #Signal for sweep end (FOOT)
    sweep_ended = pyqtSignal(str)

    #  Protocol Constants
    SYNC_HIGH = 0xDE    # 222 decimal
    SYNC_LOW = 0xAD     # 173 decimal

    TYPE_INIT = 2
    TYPE_PACKET = 3
    TYPE_FOOT = 4

    # Hardware Calibration Constants

    DAC_RES = 2 ** 16       # 65536 - DAC resolution (16-bit)
    DAC_FS = 5.077          # DAC full-scale voltage
    DAC_ZS = -0.077         # DAC zero-scale voltage

    # ADC: 20 bit over ±5V, 590kΩ gain resistor
    ADC_COUNT_TO_CURR = 10.0 / (2 ** 20 * 590000)

    #ADC offset = 2.048V * (2^20 / 10V) = 214748.3648
    ADC_OFF = 214748

    # End of Matlab start of state machine
    # these have _ in front to show they are internal state variables, not constants
    _STATE_WAIT_SYNC1 = 0   # Waiting for 0xDE
    _STATE_WAIT_SYNC2 = 1   # Got 0xDE, waiting for 0xAD
    _STATE_SIZE_HI = 2      # Waiting for payload size high byte
    _STATE_SIZE_LO = 3      # Waiting for payload size low byte
    _STATE_CHECKSUM = 4     # Waiting for checksum byte
    _STATE_PAYLOAD = 5      # Collecting payload bytes

    #start python stuff

    def __init__(self):
        super().__init__()

        #state machine 
        self._state = self._STATE_WAIT_SYNC1
        self._payload_size = 0
        self._payload_buffer = []
        self._payload_bytes_remaining = 0

        # Current sweep context (set by INIT, used by PACKET)
        self._current_sweep = None
        self._sweep_count = 0
        self._packet_index = 0 #sample counter withtin current sweep

        #Timestamp tracking
        self._current_timestamp = 0.0
        self._sync_timestamp = 0.0 # timestamp of the SYNC that started this packet

    def reset(self):
        '''Reset parser to initial state. call when starting a new file or reconnecting serial'''
        self._state = self._STATE_WAIT_SYNC1
        self._payload_size = 0
        self._payload_buffer = []
        self._payload_bytes_remaining = 0
        self._current_sweep = None
        self._sweep_count = 0
        self._packet_index = 0
        self._current_timestamp = 0.0
        self._sync_timestamp = 0.0
    
    def feed_byte(self, byte_value: int, timestamp: float = 0.0) -> None:
        ''' 
        Feed a single byte into parser state machine

        Args:
            byte_value : Int 0-255, one byte from serial or CSV
            timestamp: Time in sec

        Call for every byte received. When complete packet is assembled, signals emitted auto
        '''

        self._current_timestamp = timestamp
        
        if self._state == self._STATE_WAIT_SYNC1:
            # Looking for first sync byte (0xDE = 222)
            if byte_value == self.SYNC_HIGH:
                self._sync_timestamp = timestamp
                self._state = self._STATE_WAIT_SYNC2
            
        elif self._state == self._STATE_WAIT_SYNC2:
            # Got 0xDE, expecting 0xAD
            if byte_value == self.SYNC_LOW:
                # Valid SYNC found
                self._state = self._STATE_SIZE_HI
            elif byte_value == self.SYNC_HIGH:
                # Got another 0xDE — maybe the real start, stay in SYNC2
                self._sync_timestamp = timestamp
            else:
                # Not a valid SYNC, go back to waiting
                self._state = self._STATE_WAIT_SYNC1
                
        elif self._state == self._STATE_SIZE_HI:
            # Payload size high byte
            self._payload_size = byte_value << 8
            self._state = self._STATE_SIZE_LO
            
        elif self._state == self._STATE_SIZE_LO:
            # Payload size low byte
            self._payload_size |= byte_value
            
            # payload shouldn't be huge
            if self._payload_size > 1024:
                # Bad packet, reset
                self._state = self._STATE_WAIT_SYNC1
            else:
                self._state = self._STATE_CHECKSUM
                
        elif self._state == self._STATE_CHECKSUM:
            # Checksum byte ignored for now but stored
            self._payload_buffer = []
            self._payload_bytes_remaining = self._payload_size
            
            if self._payload_size > 0:
                self._state = self._STATE_PAYLOAD
            else:
                # Empty payload case
                self._state = self._STATE_WAIT_SYNC1
                
        elif self._state == self._STATE_PAYLOAD:
            # Collecting payload bytes
            self._payload_buffer.append(byte_value)
            self._payload_bytes_remaining -= 1
            
            if self._payload_bytes_remaining == 0:
                # Complete packet received — process it
                self._process_complete_packet()
                self._state = self._STATE_WAIT_SYNC1
    
    def _process_complete_packet(self) -> None:
        '''Route complete payload to approp handler'''
        if not self._payload_buffer:
            return
        
        packet_type = self._payload_buffer[0]

        if packet_type == self.TYPE_INIT:
            self._handle_init()
        elif packet_type == self.TYPE_PACKET:
            self._handle_data_packet()
        elif packet_type == self.TYPE_FOOT:
            self._handle_foot()
        
    def _handle_init(self) -> None:
        """
        Process INIT packet — sweep configuration.
        
        PAYLOAD layout (0-indexed in Python):
        [0]  type (2)
        [1]  version
        [2]  device_id LOW       ← Little-endian
        [3]  device_id HIGH
        [4]  frame_id
        [5]  sample_count LOW
        [6]  sample_count HIGH
        [7]  sweep_step_time LOW
        [8]  sweep_step_time HIGH
        [9]  start_time byte 0 (LSB)
        [10] start_time byte 1
        [11] start_time byte 2
        [12] start_time byte 3 (MSB)
        """
        p = self._payload_buffer
        
        if len(p) < 13:
            return #incomplete INIT
        
        self._sweep_count +=1
        self._packet_index = 0

        sample_count = p[5] + (p[6] << 8)
        sweep_step_time = p[7] + (p[8] << 8)

        # Calc sweep freq {freq = 1 / (step_time * 10µs * sample_count)}
        if sample_count > 0 and sweep_step_time > 0:
            sweep_freq = 1.0 / (sweep_step_time * 10e-6 * sample_count)
        else:
            sweep_freq = 0.0

        self._current_sweep = {
            'sweep_id': self._sweep_count,
            'version': p[1],
            'device_id': p[2] + (p[3] << 8),
            'frame_id': p[4],
            'sample_count': sample_count,
            'sweep_step_time_count': sweep_step_time,
            'sweep_freq': sweep_freq,
            'start_time_internal': (p[9] + (p[10] << 8) + (p[11] << 16) + (p[12] << 24)),
            'start_time': self._sync_timestamp,
        }

        self.sweep_started.emit(self._current_sweep.copy())

    def _handle_data_packet(self) -> None:
        """
        Process PACKET — one data sample.
        
        PAYLOAD layout (0-indexed):
        [0]    type (3)
        [1]    frame_id
        [2]    packet_id
        [3]    DAC LOW            ← Little-endian uint16
        [4]    DAC HIGH
        [5]    integrator LOW     ← Little-endian int16 (SIGNED)
        [6]    integrator HIGH
        [7]    ADC_A MSB          ← Big-endian 3 bytes, 24-bit signed, /16
        [8]    ADC_A middle
        [9]    ADC_A LSB
        [10]   ADC_B MSB
        [11]   ADC_B middle
        [12]   ADC_B LSB
        """
        p = self._payload_buffer
        
        if len(p) < 13 or self._current_sweep is None:
            return
        
        self._packet_index += 1

        # Extract RAW Values

        frame_id = p[1]
        packet_id = p[2]

        # DAC : 2 bytes, little endian unsigned
        dac_raw = p[3] + (p[4] <<8)

        # Integrator : 2 bytes, little endian signed in16
        integrator_raw = struct.unpack('<h', bytes([p[5], p[6]]))[0]

        # ADC A: 3 bytes at 7,8,9 big endian order in protocol
        adc_a_raw = self._convert_adc_24bit(p[7], p[8], p[9])

        # ADC B: 3 bytes at [10,11,12], same format
        adc_b_raw = self._convert_adc_24bit(p[10], p[11], p[12])

        #Convert to physical units

        # DAC voltage
        dac_v = (4.22 / 2.0) * ((((self.DAC_FS - self.DAC_ZS) * dac_raw) / self.DAC_RES) + self.DAC_ZS)

        # Integrator voltage
        integrator_v = -(10.0 * (2.5 / 4096.0) * integrator_raw)

        # ADC currents
        adc_a_current = self.ADC_COUNT_TO_CURR * (adc_a_raw + self.ADC_OFF)
        adc_b_current = self.ADC_COUNT_TO_CURR * (adc_b_raw - self.ADC_OFF)

        # Derived values (from MATLAB plotting code)
        bias_a = -dac_v + integrator_v
        bias_b = dac_v + integrator_v
        diff_v = 2.0 * dac_v
        diff_i = adc_a_current - adc_b_current

        # Calculate sample time within sweep
        sweep = self._current_sweep
        if sweep['sweep_freq'] > 0 and sweep['sample_count'] > 0:
            sample_time = (sweep['start_time'] + 
                          (self._packet_index / sweep['sample_count']) / sweep['sweep_freq'])
        else:
            sample_time = self._sync_timestamp

        # Build output dict — these keys are what data_store and plots will use
        result = {
            'timestamp': self._sync_timestamp,
            'sample_time': sample_time,
            'sweep_id': sweep['sweep_id'],
            'frame_id': frame_id,
            'packet_id': packet_id,
            'dac_raw': dac_raw,
            'dac_v': dac_v,
            'integrator_raw': integrator_raw,
            'integrator_v': integrator_v,
            'adc_a_raw': adc_a_raw,
            'adc_b_raw': adc_b_raw,
            'adc_a_current': adc_a_current,
            'adc_b_current': adc_b_current,
            'bias_a': bias_a,
            'bias_b': bias_b,
            'diff_v': diff_v,
            'diff_i': diff_i,
            'sweep_freq': sweep['sweep_freq'],
            'sample_count': sweep['sample_count'],
        }
        
        self.packet_ready.emit(result)

    def _handle_foot(self) -> None:
        """Process FOOT packet — end-of-sweep message."""
        p = self._payload_buffer
        
        if len(p) < 3:
            return
        
        try:
            message = bytes(p[2:]).decode('ascii', errors='ignore').strip('\x00')
        except Exception:
            message = ""
        
        self.sweep_ended.emit(message)

    def _convert_adc_24bit(self, msb: int, mid: int, lsb: int) -> float:
        '''
        Convert 3-byte ADC value to signed float, matching MATLAB exactly.
        Step by step:
        1. Bytes come in as [MSB, MID, LSB] (big-endian from device)
        2. MATLAB reverses to [LSB, MID, MSB] for little-endian typecast
        3. Sign-extends MSB bit 7 to a 4th byte (0x00 or 0xFF)
        4. Typecasts 4 bytes to int32
        5. Divides by 16 (2^4)
        
        Args:
            msb: Most significant byte (contains sign bit)
            mid: Middle byte
            lsb: Least significant byte
            
        Returns:
            Signed float value after /16 scaling
        '''
        # Sign extension: if bit 7 of MSB is set, extend with 0xFF, else 0x00
        sign_byte = 0xFF if (msb & 0x80) else 0x00
        
        # Pack as little-endian int32: [LSB, MID, MSB, SIGN]
        packed = struct.pack('BBBB', lsb, mid, msb, sign_byte)
        value = struct.unpack('<i', packed)[0]  # '<i' = little-endian signed int32
        
        # Divide by 16 (the ADC value is left-shifted by 4 bits)
        return value / 16.0
    
    # Utils

    def get_sweep_count(self) -> int:
        """Number of sweeps seen so far."""
        return self._sweep_count
    
    def get_current_sweep(self) -> dict:
        """Get current sweep info, or empty dict if none."""
        return self._current_sweep.copy() if self._current_sweep else {}
    
def is_raw_mdlp_format(file_path: str) -> bool:
    """
    Quick check: does this CSV look like raw mDLP byte data?
    
    Checks for:
    - Has 'Time [s]' or 'Time_s_' column
    - Has 'Value' column  
    - First few values are in 0-255 range (byte values)
    """
    import csv
    
    try:
        with open(file_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            
            has_time = any(h in headers for h in ['Time [s]', 'Time_s_', 'time', 'Time'])
            has_value = any(h in headers for h in ['Value', 'value', 'Data', 'data'])
            
            if not (has_time and has_value):
                return False
            
            # Check first 10 values are byte-range
            for i, row in enumerate(reader):
                if i >= 10:
                    break
                for col in ['Value', 'value', 'Data', 'data']:
                    if col in row and row[col].strip():
                        val = int(row[col])
                        if val < 0 or val > 255:
                            return False
                        break
            
            return True
    except Exception:
        return False


