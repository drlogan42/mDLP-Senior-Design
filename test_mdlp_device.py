# test_mdlp_device.py
import sys
import os
# Fix Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import serial
import struct
import time
import math
import random

class MDLPTestDevice:
    """Simulates mDLP device protocol - EXACT format for parser"""
    
    # Protocol constants (matching parser exactly)
    SYNC_HIGH = 0xDE    # 222 decimal
    SYNC_LOW = 0xAD     # 173 decimal
    TYPE_INIT = 2
    TYPE_PACKET = 3  
    TYPE_FOOT = 4
    
    def __init__(self, port_name: str, baud_rate: int = 115200):
        print(f"Connecting to {port_name} at {baud_rate} baud...")
        self.port = serial.Serial(port_name, baud_rate, timeout=1)
        self.frame_id = 1
        self.packet_id = 0
        self.sweep_count = 0
        print(f"Connected! Port: {self.port.name}")
        
    def send_packet(self, payload: bytes):
        """Send mDLP protocol packet with EXACT format parser expects"""
        # Protocol: SYNC_HIGH + SYNC_LOW + SIZE_LOW + SIZE_HIGH + CHECKSUM + PAYLOAD
        size = len(payload)
        
        # Simple checksum - sum of all payload bytes
        checksum = sum(payload) & 0xFF  
        
        # Build packet with correct byte order (BIG-ENDIAN size for parser)
        packet = bytes([
            self.SYNC_HIGH,     # 0xDE
            self.SYNC_LOW,      # 0xAD  
            (size >> 8) & 0xFF, # Size HIGH byte (MSB first!)
            size & 0xFF,        # Size LOW byte
            checksum            # Checksum
        ]) + payload
        
        self.port.write(packet)
        packet_type = payload[0] if payload else 0
        print(f"Sent TYPE_{packet_type} packet: {len(packet)} bytes total (payload: {size} bytes)")
        
    def send_init_packet(self, sample_count: int = 50):
        """Send INIT packet - EXACT format from parser comments"""
        self.sweep_count += 1
        self.packet_id = 0
        
        # Realistic values
        device_id = 0x1234
        version = 1
        sweep_step_time = 100  # 100 * 10µs = 1ms per step
        start_time = int(time.time())  # Unix timestamp
        
        # Build INIT payload exactly as parser expects:
        # [0] type, [1] version, [2-3] device_id (little-endian), 
        # [4] frame_id, [5-6] sample_count (little-endian),
        # [7-8] sweep_step_time (little-endian), [9-12] start_time (little-endian)
        
        payload = bytearray(13)  # Exactly 13 bytes
        
        payload[0] = self.TYPE_INIT                    # type (2)
        payload[1] = version                           # version
        payload[2] = device_id & 0xFF                  # device_id LOW
        payload[3] = (device_id >> 8) & 0xFF          # device_id HIGH  
        payload[4] = self.frame_id                     # frame_id
        payload[5] = sample_count & 0xFF               # sample_count LOW
        payload[6] = (sample_count >> 8) & 0xFF       # sample_count HIGH
        payload[7] = sweep_step_time & 0xFF            # sweep_step_time LOW
        payload[8] = (sweep_step_time >> 8) & 0xFF    # sweep_step_time HIGH
        payload[9] = start_time & 0xFF                 # start_time byte 0 (LSB)
        payload[10] = (start_time >> 8) & 0xFF        # start_time byte 1
        payload[11] = (start_time >> 16) & 0xFF       # start_time byte 2  
        payload[12] = (start_time >> 24) & 0xFF       # start_time byte 3 (MSB)
        
        self.send_packet(bytes(payload))
        
    def send_data_packet(self):
        """Send PACKET - EXACT format from parser comments"""
        self.packet_id += 1
        
        # Generate realistic measurement data
        # DAC: 16-bit unsigned (0-65535) - sine wave centered at mid-scale
        dac_raw = int(32768 + 16000 * math.sin(self.packet_id * 0.1))
        dac_raw = max(0, min(65535, dac_raw))  # Clamp to 16-bit range
        
        # Integrator: 16-bit signed (-32768 to 32767) - small random variation  
        integrator_raw = random.randint(-2000, 2000)
        
        # ADC values: 24-bit signed (-8388608 to 8388607) but realistic range
        # Simulate current measurements in reasonable range
        adc_a_raw = int(-214748 + 50000 * math.cos(self.packet_id * 0.05))  # Around ADC offset
        adc_b_raw = int(-214748 + 45000 * math.sin(self.packet_id * 0.03))  # Different phase
        
        # Build PACKET payload exactly as parser expects:
        # [0] type, [1] frame_id, [2] packet_id,
        # [3-4] DAC (little-endian uint16), [5-6] integrator (little-endian int16),
        # [7-9] ADC_A (big-endian 24-bit), [10-12] ADC_B (big-endian 24-bit)
        
        payload = bytearray(13)  # Exactly 13 bytes
        
        payload[0] = self.TYPE_PACKET              # type (3)
        payload[1] = self.frame_id                 # frame_id
        payload[2] = self.packet_id & 0xFF         # packet_id
        payload[3] = dac_raw & 0xFF                # DAC LOW
        payload[4] = (dac_raw >> 8) & 0xFF        # DAC HIGH
        
        # Integrator as signed 16-bit little-endian
        if integrator_raw < 0:
            integrator_raw = integrator_raw + 65536  # Convert to unsigned representation
        payload[5] = integrator_raw & 0xFF         # integrator LOW  
        payload[6] = (integrator_raw >> 8) & 0xFF  # integrator HIGH
        
        # ADC_A as 24-bit big-endian (MSB first)
        # Handle negative numbers in 24-bit two's complement
        if adc_a_raw < 0:
            adc_a_raw = adc_a_raw + 16777216  # Convert to unsigned 24-bit
        payload[7] = (adc_a_raw >> 16) & 0xFF      # ADC_A MSB
        payload[8] = (adc_a_raw >> 8) & 0xFF       # ADC_A middle
        payload[9] = adc_a_raw & 0xFF              # ADC_A LSB
        
        # ADC_B as 24-bit big-endian (MSB first)  
        if adc_b_raw < 0:
            adc_b_raw = adc_b_raw + 16777216  # Convert to unsigned 24-bit
        payload[10] = (adc_b_raw >> 16) & 0xFF     # ADC_B MSB
        payload[11] = (adc_b_raw >> 8) & 0xFF      # ADC_B middle
        payload[12] = adc_b_raw & 0xFF             # ADC_B LSB
        
        self.send_packet(bytes(payload))
        
    def send_foot_packet(self):
        """Send FOOT packet - end of sweep"""
        message = b"Sweep complete\x00\x00"  # Null-terminated string
        
        # Build FOOT payload: [0] type, [1] frame_id, [2...] message
        payload = bytearray()
        payload.append(self.TYPE_FOOT)     # type (4)
        payload.append(self.frame_id)      # frame_id
        payload.extend(message)            # message string
        
        self.send_packet(bytes(payload))
        
    def run_test_loop(self, sweeps: int = 999, samples_per_sweep: int = 100):
        """Run complete test sequence with proper timing (LONG RUNNING)"""
        print(f"\n=== Starting mDLP Test Sequence (LONG RUNNING) ===")
        print(f"Sweeps: {sweeps}, Samples per sweep: {samples_per_sweep}")
        print("Press Ctrl+C to stop...")
        
        try:
            for sweep in range(sweeps):
                print(f"\n--- Sweep {sweep + 1}/{sweeps} (Frame {self.frame_id}) ---")
                
                # Send INIT
                print("Sending INIT...")
                self.send_init_packet(samples_per_sweep)
                
                # Send data packets with consistent timing
                print(f"Sending {samples_per_sweep} data packets...")
                for sample in range(samples_per_sweep):
                    self.send_data_packet()
                    if sample % 20 == 0:  # Progress indicator  
                        print(f"  Sample {sample + 1}/{samples_per_sweep}")
                    time.sleep(0.005)  # 1ms between samples for smooth streaming
                    
                # Send FOOT
                print("Sending FOOT...")
                self.send_foot_packet()
                
                self.frame_id += 1
                
            print("\n=== Test Complete ===")
                
        except KeyboardInterrupt:
            print("\n!!! Test stopped by user (Ctrl+C) !!!")
        except Exception as e:
            print(f"\n!!! Error: {str(e)} !!!")
        finally:
            self.port.close()
            print("Port closed")

if __name__ == "__main__":
    # Use COM4 (virtual cable connects to COM5 for main app)
    test_device = MDLPTestDevice("COM4")  
    test_device.run_test_loop()