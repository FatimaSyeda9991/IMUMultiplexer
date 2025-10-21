"""
MPU9250 IMU TEST WITH TCA9548A MULTIPLEXER - CORRECTED
"""

import time
from smbus2 import SMBus

class IMUMultiplexer:
    def __init__(self, bus_number=1, multiplexer_address=0x70):
        """Initialize I2C multiplexer and IMUs."""
        print(f"Initializing TCA9548A multiplexer on bus {bus_number}...")
        
        try:
            # Initialize I2C bus
            self.bus = SMBus(bus_number)
            self.multiplexer_addr = multiplexer_address
            self.bus_number = bus_number
            
            # Test multiplexer presence
            self.bus.write_byte(self.multiplexer_addr, 0x00)  # Reset - select no channels
            print("✓ I2C Multiplexer switch reset")
            
            # IMU configuration
            self.imu_channels = [2, 3, 4]
            self.imus_initialized = False
            
            print("SCANNING ALL MULTIPLEXER CHANNELS:")
            self.scan_all_channels()
            
        except Exception as e:
            print(f"✗ ERROR: {e}")
            print("\nTry different bus numbers:")
            print("1. Change bus number in SMBus() to 1, 7, or 8")
            print("2. Run: sudo i2cdetect -l to list available buses")
            raise
    
    def _tca_select(self, channel):
        """Select active channel on TCA9548A multiplexer."""
        if channel < 0 or channel > 7:
            raise ValueError("Channel must be 0-7")
        self.bus.write_byte(self.multiplexer_addr, 1 << channel)
        time.sleep(0.01)  # Small delay for I2C bus to settle
    
    def scan_all_channels(self):
        """Scan all 8 channels for IMUs."""
        for channel in range(8):
            print(f"Channel {channel}: ", end="")
            try:
                self._tca_select(channel)
                
                # Test both common MPU9250 addresses
                devices_found = []
                for address in [0x68, 0x69]:
                    try:
                        # Try to wake up IMU
                        self.bus.write_byte_data(address, 0x6B, 0x00)
                        time.sleep(0.01)
                        
                        # Try to read WHO_AM_I register
                        who_am_i = self.bus.read_byte_data(address, 0x75)
                        if who_am_i in [0x71, 0x73]:  # MPU9250 or MPU9255
                            devices_found.append(f"0x{address:02x}(WHO_AM_I=0x{who_am_i:02x})")
                    except:
                        pass
                
                if devices_found:
                    print(f"✓ IMUs found: {devices_found}")
                else:
                    print("No IMUs found")
                    
            except Exception as e:
                print(f"Error: {e}")
    
    def initialize_imus(self):
        """Initialize all IMUs on their respective channels."""
        print("\nINITIALIZING IMUs ON SPECIFIED CHANNELS...")
        
        self.imus = {}
        for channel in self.imu_channels:
            print(f"Channel {channel}: ", end="")
            try:
                self._tca_select(channel)
                
                # Try both addresses
                imu_initialized = False
                for address in [0x68, 0x69]:
                    try:
                        # Wake up IMU
                        self.bus.write_byte_data(address, 0x6B, 0x00)
                        time.sleep(0.1)
                        
                        # Verify it's an MPU9250
                        who_am_i = self.bus.read_byte_data(address, 0x75)
                        if who_am_i in [0x71, 0x73]:
                            self.imus[channel] = {
                                'address': address,
                                'who_am_i': who_am_i
                            }
                            print(f"✓ MPU9250 at 0x{address:02x} (WHO_AM_I=0x{who_am_i:02x})")
                            imu_initialized = True
                            break
                    except:
                        continue
                
                if not imu_initialized:
                    print("✗ No IMU found")
                    
            except Exception as e:
                print(f"Error: {e}")
        
        self.imus_initialized = len(self.imus) > 0
        return self.imus_initialized
    
    def read_imu_data(self, channel):
        """Read sensor data from specific IMU channel."""
        if channel not in self.imus:
            return None
        
        try:
            self._tca_select(channel)
            address = self.imus[channel]['address']
            
            # Read 14 bytes starting from ACCEL_XOUT_H register (0x3B)
            data = self.bus.read_i2c_block_data(address, 0x3B, 14)
            
            # Convert acceleration (m/s²)
            ax = self._convert_bytes(data[0], data[1]) / 4096.0 * 9.80665
            ay = self._convert_bytes(data[2], data[3]) / 4096.0 * 9.80665  
            az = self._convert_bytes(data[4], data[5]) / 4096.0 * 9.80665
            
            # Temperature
            temp = self._convert_bytes(data[6], data[7]) / 333.87 + 21.0
            
            # Gyroscope (rad/s)
            gx = self._convert_bytes(data[8], data[9]) / 32.8 * 0.0174533
            gy = self._convert_bytes(data[10], data[11]) / 32.8 * 0.0174533
            gz = self._convert_bytes(data[12], data[13]) / 32.8 * 0.0174533
            
            return {
                'accel': (ax, ay, az),
                'gyro': (gx, gy, gz),
                'temp': temp
            }
            
        except Exception as e:
            print(f"Data reading failed on channel {channel}: {e}")
            return None
    
    def _convert_bytes(self, high, low):
        """Convert two bytes to signed 16-bit integer."""
        value = (high << 8) | low
        return value - 65536 if value >= 32768 else value
    
    def read_all_imus(self):
        """Read data from all initialized IMUs."""
        data = {}
        for channel in self.imus.keys():
            imu_data = self.read_imu_data(channel)
            if imu_data:
                data[channel] = imu_data
        return data
    
    def close(self):
        """Close I2C bus."""
        if hasattr(self, 'bus'):
            self.bus.close()

def main():
    print("\n" + "="*70)
    print("MPU9250 IMU TEST WITH TCA9548A MULTIPLEXER")
    print("="*70)
    
    # Try different bus numbers
    buses_to_try = [1, 7, 8]
    multiplexer = None
    
    for bus_num in buses_to_try:
        print(f"\nTrying bus {bus_num}...")
        try:
            multiplexer = IMUMultiplexer(bus_number=bus_num)
            print(f"✓ Successfully connected to multiplexer on bus {bus_num}")
            break
        except Exception as e:
            print(f"✗ Bus {bus_num} failed")
            continue
    
    if not multiplexer:
        print("\n❌ Could not connect to multiplexer on any bus!")
        return
    
    # Initialize IMUs
    if not multiplexer.initialize_imus():
        print("\n❌ No IMUs initialized! Check connections.")
        multiplexer.close()
        return
    
    print(f"\n✓ Successfully initialized {len(multiplexer.imus)} IMU(s)")
    
    # Continuous reading loop
    print("\n" + "="*70)
    print("STARTING CONTINUOUS READINGS")
    print("Press Ctrl+C to stop")
    print("="*70)
    
    try:
        count = 0
        while True:
            data = multiplexer.read_all_imus()
            count += 1
            
            print(f"\n--- Reading {count} ---")
            for channel, sensor_data in data.items():
                if sensor_data:
                    print(f"CH{channel}: Temp={sensor_data['temp']:.1f}°C, "
                          f"Accel=({sensor_data['accel'][0]:6.3f}, {sensor_data['accel'][1]:6.3f}, {sensor_data['accel'][2]:6.3f}) m/s², "
                          f"Gyro=({sensor_data['gyro'][0]:6.3f}, {sensor_data['gyro'][1]:6.3f}, {sensor_data['gyro'][2]:6.3f}) rad/s")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    
    finally:
        multiplexer.close()
        print("Test complete.")

if __name__ == "__main__":
    main()
