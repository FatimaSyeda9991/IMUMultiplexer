"""
MPU9250 IMU Sensor Test with I2C Multiplexer
Reads data from 3 MPU9250 sensors connected via TCA9548A multiplexer
Configuration:
- Bus: 7
- IMU Address: 0x69
- Multiplexer Channels: 2, 3, 4
"""

import time
import struct
from smbus2 import SMBus

class SimpleMPU9250:
    def __init__(self, bus_number=7, address=0x69):
        """Initialize MPU9250 sensor."""
        
        # Initialize I2C bus
        self.bus = SMBus(bus_number)
        self.addr = address
        
        # Wake up the device by writing 0 to PWR_MGMT_1 register (0x6B)
        self.bus.write_byte_data(self.addr, 0x6B, 0x00)
        time.sleep(0.1)  # Wait for sensor to stabilize
        
        print(f"✓ Simple MPU9250 initialized at address 0x{self.addr:02x}")
    
    def get_all_data(self):
        """
        Read all available sensor data from MPU9250
        Returns dictionary with sensor data.
        """
        # Read 14 bytes starting from ACCEL_XOUT_H register (0x3B)
        data = self.bus.read_i2c_block_data(self.addr, 0x3B, 14)
        
        # Convert raw bytes to acceleration values in m/s²
        ax = self._convert(data[0], data[1]) / 4096.0 * 9.80665
        ay = self._convert(data[2], data[3]) / 4096.0 * 9.80665  
        az = self._convert(data[4], data[5]) / 4096.0 * 9.80665
        accel_magnitude = (ax**2 + ay**2 + az**2)**0.5
        
        # Temperature conversion
        temp = self._convert(data[6], data[7]) / 333.87 + 21.0
        
        # Convert raw bytes to angular velocity in rad/s
        gx = self._convert(data[8], data[9]) / 32.8 * 0.0174533
        gy = self._convert(data[10], data[11]) / 32.8 * 0.0174533
        gz = self._convert(data[12], data[13]) / 32.8 * 0.0174533
        gyro_magnitude = (gx**2 + gy**2 + gz**2)**0.5
        
        return {
            'accel': (ax, ay, az),
            'accel_magnitude': accel_magnitude,
            'gyro': (gx, gy, gz),
            'gyro_magnitude': gyro_magnitude,
            'temp': temp
        }
    
    def _convert(self, high, low):
        """Convert two bytes to signed 16-bit integer."""
        value = (high << 8) | low
        if value >= 32768:
            value -= 65536
        return value
    
    def close(self):
        """Close I2C bus."""
        self.bus.close()

class IMUMultiplexer:
    def __init__(self, bus_number=7, multiplexer_address=0x70):
        """Initialize I2C multiplexer and IMUs."""
        
        # Initialize I2C bus
        self.bus = SMBus(bus_number)
        self.multiplexer_addr = multiplexer_address
        self.bus_number = bus_number
        
        # IMU configuration - channels 2, 3, 4 with address 0x69
        self.imu_channels = [2, 3, 4]
        self.imus = {}
        
        print("Initializing IMUs on multiplexer...")
        self._initialize_imus()
        
    def _tca_select(self, channel):
        """Select active channel on TCA9548A multiplexer."""
        if channel < 0 or channel > 7:
            raise ValueError("Channel must be 0-7")
        self.bus.write_byte(self.multiplexer_addr, 1 << channel)
        time.sleep(0.05)  # Small delay for I2C bus to settle
    
    def _initialize_imus(self):
        """Initialize all IMUs on their respective channels."""
        for channel in self.imu_channels:
            self._tca_select(channel)
            
            try:
                imu = SimpleMPU9250(self.bus_number, 0x69)  # Fixed address 0x69
                self.imus[channel] = imu
                print(f"✓ IMU initialized on channel {channel}, address 0x69")
            except Exception as e:
                print(f"✗ Failed to initialize IMU on channel {channel}: {e}")
    
    def read_all_imus(self):
        """Read data from all IMUs."""
        data = {}
        for channel, imu in self.imus.items():
            self._tca_select(channel)
            try:
                imu_data = imu.get_all_data()
                data[channel] = imu_data
            except Exception as e:
                print(f"Error reading IMU on channel {channel}: {e}")
                data[channel] = None
        return data
    
    def close(self):
        """Close all connections."""
        for imu in self.imus.values():
            imu.close()
        self.bus.close()

# ===========================================================================
# MAIN TEST PROGRAM
# ===========================================================================
print("\n" + "="*80)
print("MPU9250 IMU SENSOR TEST WITH I2C MULTIPLEXER")
print("="*80)
print("Configuration:")
print("  - I2C Bus: 7")
print("  - IMU Address: 0x69")
print("  - Multiplexer Channels: 2, 3, 4")
print("  - Sensors: 3x MPU9250 9-Axis IMU")
print("="*80)

try:
    # Initialize the multiplexer with IMUs
    print("\nInitializing multiplexer and IMUs...")
    imu_multiplexer = IMUMultiplexer(bus_number=7, multiplexer_address=0x70)
    
    if not imu_multiplexer.imus:
        print("No IMUs found! Check connections and try again.")
        exit()
    
    print(f"\n✓ Successfully initialized {len(imu_multiplexer.imus)} IMU(s)")
    for channel in imu_multiplexer.imus.keys():
        print(f"  - Channel {channel}: MPU9250 at 0x69")
    
    print("\n" + "="*80)
    print("STARTING CONTINUOUS SENSOR READINGS")
    print("="*80)
    print("Press Ctrl+C to stop reading")
    print("="*80)
    
    count = 0
    
    while True:
        # Read data from all IMUs
        imu_data = imu_multiplexer.read_all_imus()
        count += 1
        
        print(f"\n--- Reading {count} | Time: {time.strftime('%H:%M:%S')} ---")
        print("-" * 80)
        
        for channel, data in imu_data.items():
            if data is None:
                print(f"Channel {channel}: No data")
                continue
                
            print(f"CHANNEL {channel}:")
            print(f"  Temperature: {data['temp']:6.1f}°C")
            print(f"  Accelerometer: X={data['accel'][0]:7.3f}, Y={data['accel'][1]:7.3f}, Z={data['accel'][2]:7.3f} m/s²")
            print(f"  Accel Magnitude: {data['accel_magnitude']:7.3f} m/s²")
            print(f"  Gyroscope:     X={data['gyro'][0]:7.3f}, Y={data['gyro'][1]:7.3f}, Z={data['gyro'][2]:7.3f} rad/s")
            print(f"  Gyro Magnitude:  {data['gyro_magnitude']:7.3f} rad/s")
            print()
        
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\n" + "="*80)
    print("TEST STOPPED BY USER")
    print("="*80)
    print(f"Total readings: {count}")
    imu_multiplexer.close()
    
except Exception as e:
    print("\n" + "="*80)
    print("ERROR OCCURRED")
    print("="*80)
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {e}")
    print("\nTroubleshooting tips:")
    print("1. Check I2C wiring and connections")
    print("2. Verify all sensors are powered (3.3V)")
    print("3. Check multiplexer address (0x70)")
    print("4. Verify I2C bus 7 is available")
    print("5. Run: sudo i2cdetect -y 7 to detect devices")

# Final message
print("\n" + "="*80)
print("MPU9250 MULTIPLEXER TEST COMPLETE")
print("="*80)
