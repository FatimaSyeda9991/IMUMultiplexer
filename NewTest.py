#!/usr/bin/python3
"""
MPU9250 IMU TEST WITH TCA9548A MULTIPLEXER
Using the simple I2C switch class
"""

import time
import smbus
from smbus2 import SMBus

# Your TCA9548A I2C multiplexer class
class I2C_SW(object):
    def __init__(self, name, address, bus_nr):
        self.name = name
        self.address = address
        self.bus_nr = bus_nr
        self.bus = smbus.SMBus(bus_nr)

    def chn(self, channel):
        """Change to i2c channel 0..7"""
        self.bus.write_byte(self.address, 2**channel)
        time.sleep(0.01)  # Added small delay

    def _rst(self):
        """Block all channels"""
        self.bus.write_byte(self.address, 0)
        print(self.name, ' ', 'Switch reset')

    def _all(self):
        """Read all 8 channels"""
        self.bus.write_byte(self.address, 0xff)
        print(self.name, ' ', 'Switch read all lines')

# Simple MPU9250 class
class MPU9250_Simple:
    def __init__(self, bus, address=0x69):
        self.bus = bus
        self.addr = address
        
        # Wake up the device
        self.bus.write_byte_data(self.addr, 0x6B, 0x00)
        time.sleep(0.1)
    
    def detect(self):
        """Check if MPU9250 is present"""
        try:
            who_am_i = self.bus.read_byte_data(self.addr, 0x75)
            return who_am_i
        except:
            return None
    
    def read_data(self):
        """Read accelerometer and gyroscope data"""
        try:
            # Read 14 bytes starting from ACCEL_XOUT_H (0x3B)
            data = self.bus.read_i2c_block_data(self.addr, 0x3B, 14)
            
            # Convert to acceleration (m/s²)
            ax = self._convert(data[0], data[1]) / 4096.0 * 9.80665
            ay = self._convert(data[2], data[3]) / 4096.0 * 9.80665  
            az = self._convert(data[4], data[5]) / 4096.0 * 9.80665
            
            # Temperature
            temp = self._convert(data[6], data[7]) / 333.87 + 21.0
            
            # Convert to gyroscope (rad/s)
            gx = self._convert(data[8], data[9]) / 32.8 * 0.0174533
            gy = self._convert(data[10], data[11]) / 32.8 * 0.0174533
            gz = self._convert(data[12], data[13]) / 32.8 * 0.0174533
            
            return {
                'accel': (ax, ay, az),
                'gyro': (gx, gy, gz),
                'temp': temp,
                'success': True
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _convert(self, high, low):
        """Convert two bytes to signed 16-bit integer"""
        value = (high << 8) | low
        return value - 65536 if value >= 32768 else value

def scan_all_channels(switch):
    """Scan all channels for I2C devices"""
    print("SCANNING ALL MULTIPLEXER CHANNELS:")
    print("=" * 50)
    
    for channel in range(8):
        switch.chn(channel)
        print(f"Channel {channel}: ", end="")
        
        devices = []
        for addr in [0x68, 0x69]:  # Common IMU addresses
            try:
                # Try to read WHO_AM_I register
                who_am_i = switch.bus.read_byte_data(addr, 0x75)
                devices.append(f"0x{addr:02x}(0x{who_am_i:02x})")
            except:
                pass
        
        if devices:
            print(devices)
        else:
            print("No IMUs found")

def test_imus(switch, channels_to_test):
    """Test IMUs on specific channels"""
    print(f"\nTESTING IMUs ON CHANNELS {channels_to_test}:")
    print("=" * 50)
    
    imus = {}
    
    for channel in channels_to_test:
        print(f"\nChannel {channel}:")
        switch.chn(channel)
        
        # Try both addresses
        for imu_addr in [0x68, 0x69]:
            try:
                imu = MPU9250_Simple(switch.bus, imu_addr)
                who_am_i = imu.detect()
                
                if who_am_i == 0x71:  # MPU9250
                    print(f"  ✓ MPU9250 found at 0x{imu_addr:02x}")
                    
                    # Test reading data
                    data = imu.read_data()
                    if data['success']:
                        print(f"  ✓ Data reading successful")
                        print(f"    Temp: {data['temp']:.1f}°C")
                        imus[channel] = imu
                    else:
                        print(f"  ✗ Data reading failed: {data['error']")
                        
                    break  # Found IMU, no need to check other address
                    
            except Exception as e:
                continue  # Try next address
        
        if channel not in imus:
            print("  ✗ No IMU found")
    
    return imus

def continuous_read(switch, imus, read_interval=1.0):
    """Continuous reading from all detected IMUs"""
    print(f"\nSTARTING CONTINUOUS READINGS:")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        count = 0
        while True:
            count += 1
            print(f"\n--- Reading {count} ---")
            
            for channel, imu in imus.items():
                switch.chn(channel)
                data = imu.read_data()
                
                if data['success']:
                    print(f"CH{channel}: Temp:{data['temp']:5.1f}°C | "
                          f"Accel:({data['accel'][0]:6.3f},{data['accel'][1]:6.3f},{data['accel'][2]:6.3f}) | "
                          f"Gyro:({data['gyro'][0]:6.3f},{data['gyro'][1]:6.3f},{data['gyro'][2]:6.3f})")
                else:
                    print(f"CH{channel}: READ ERROR")
            
            time.sleep(read_interval)
            
    except KeyboardInterrupt:
        print("\nStopped by user")

def main():
    print("MPU9250 IMU TEST WITH TCA9548A MULTIPLEXER")
    print("=" * 60)
    
    try:
        # Initialize the multiplexer - CHANGE BUS NUMBER IF NEEDED!
        print("Initializing TCA9548A multiplexer...")
        SW = I2C_SW('I2C_Multiplexer', 0x70, 7)  # Try bus 1, 7, or 8
        
        # Test multiplexer
        SW._rst()
        
        # Scan all channels
        scan_all_channels(SW)
        
        # Test IMUs on expected channels
        expected_channels = [2, 3, 4]
        imus = test_imus(SW, expected_channels)
        
        # Summary
        print(f"\nSUMMARY: Found {len(imus)}/{len(expected_channels)} IMUs")
        if imus:
            print(f"Working channels: {list(imus.keys())}")
            
            # Start continuous reading
            if input("\nStart continuous readings? (y/n): ").lower().startswith('y'):
                continuous_read(SW, imus)
        else:
            print("\nNo IMUs found. Check:")
            print("1. Bus number (try 1, 7, or 8)")
            print("2. IMU power (3.3V)")
            print("3. I2C connections")
            print("4. Run: sudo i2cdetect -y [bus_number]")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\nTry different bus numbers:")
        print("1. Change bus_nr in I2C_SW() to 1, 7, or 8")
        print("2. Run: sudo i2cdetect -l  to list available buses")

if __name__ == "__main__":
    main()
