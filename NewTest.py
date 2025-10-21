"""
TCA9548A IMU TEST USING ADAPTER LIBRARY
Tests 3 MPU9250 sensors on channels 2, 3, 4
"""

import time
import board
import adafruit_tca9548a
from smbus2 import SMBus

class MPU9250_Simple:
    """Simple MPU9250 driver compatible with the multiplexer"""
    
    def __init__(self, i2c, address=0x69):
        self.i2c = i2c
        self.addr = address
        
        # Wake up the device
        self._write_byte(0x6B, 0x00)
        time.sleep(0.1)
    
    def _write_byte(self, register, value):
        """Write a byte to the specified register"""
        self.i2c.writeto(self.addr, bytes([register, value]))
    
    def _read_bytes(self, register, length):
        """Read bytes from the specified register"""
        result = bytearray(length)
        self.i2c.writeto_then_readfrom(self.addr, bytes([register]), result)
        return result
    
    def detect(self):
        """Check if MPU9250 is present and identify it"""
        try:
            who_am_i = self._read_bytes(0x75, 1)[0]
            return who_am_i
        except:
            return None
    
    def read_accel_gyro(self):
        """Read accelerometer and gyroscope data"""
        try:
            # Read 14 bytes starting from ACCEL_XOUT_H (0x3B)
            data = self._read_bytes(0x3B, 14)
            
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

def scan_all_channels(tca):
    """Scan all channels for I2C devices"""
    print("SCANNING ALL CHANNELS FOR I2C DEVICES:")
    print("=" * 50)
    
    devices_found = {}
    
    for channel in range(8):
        print(f"Channel {channel}: ", end="")
        
        if tca[channel].try_lock():
            try:
                # Scan for devices on this channel
                addresses = tca[channel].scan()
                # Filter out the multiplexer itself (0x70)
                filtered_addresses = [addr for addr in addresses if addr != 0x70]
                
                if filtered_addresses:
                    print([hex(addr) for addr in filtered_addresses])
                    devices_found[channel] = filtered_addresses
                else:
                    print("No devices found")
                    
            except Exception as e:
                print(f"Scan error: {e}")
            finally:
                tca[channel].unlock()
        else:
            print("Failed to lock channel")
    
    return devices_found

def test_imu_on_channels(tca, channels_to_test, imu_address=0x69):
    """Test IMU detection and functionality on specific channels"""
    print(f"\nTESTING IMUs ON CHANNELS {channels_to_test} AT ADDRESS 0x{imu_address:02x}:")
    print("=" * 60)
    
    imus = {}
    
    for channel in channels_to_test:
        print(f"\nChannel {channel}:")
        
        if tca[channel].try_lock():
            try:
                # Try to initialize IMU
                imu = MPU9250_Simple(tca[channel], imu_address)
                
                # Test detection
                who_am_i = imu.detect()
                
                if who_am_i is not None:
                    print(f"  ✓ IMU detected - WHO_AM_I: 0x{who_am_i:02x}")
                    
                    if who_am_i == 0x71:
                        print("  ✓ Confirmed: MPU9250")
                    elif who_am_i == 0x73:
                        print("  ⚠ Detected: MPU9255")
                    else:
                        print(f"  ❓ Unknown device: 0x{who_am_i:02x}")
                    
                    # Test data reading
                    data = imu.read_accel_gyro()
                    if data['success']:
                        print("  ✓ Data reading: SUCCESS")
                        print(f"    Temp: {data['temp']:.1f}°C")
                        print(f"    Accel: ({data['accel'][0]:6.3f}, {data['accel'][1]:6.3f}, {data['accel'][2]:6.3f}) m/s²")
                        print(f"    Gyro:  ({data['gyro'][0]:6.3f}, {data['gyro'][1]:6.3f}, {data['gyro'][2]:6.3f}) rad/s")
                        
                        imus[channel] = imu
                    else:
                        print(f"  ✗ Data reading failed: {data['error']}")
                else:
                    print("  ✗ No IMU detected")
                    
            except Exception as e:
                print(f"  ✗ IMU test failed: {e}")
            finally:
                tca[channel].unlock()
        else:
            print("  ✗ Failed to lock channel")
    
    return imus

def continuous_read(tca, imus, read_interval=1.0):
    """Continuous reading from all detected IMUs"""
    print(f"\nSTARTING CONTINUOUS READINGS (every {read_interval}s):")
    print("=" * 70)
    print("Press Ctrl+C to stop")
    print("=" * 70)
    
    try:
        count = 0
        while True:
            count += 1
            print(f"\n--- Reading {count} | {time.strftime('%H:%M:%S')} ---")
            
            for channel, imu in imus.items():
                if tca[channel].try_lock():
                    try:
                        data = imu.read_accel_gyro()
                        if data['success']:
                            print(f"CH{channel}: Temp:{data['temp']:5.1f}°C | "
                                  f"Accel:({data['accel'][0]:6.3f},{data['accel'][1]:6.3f},{data['accel'][2]:6.3f}) | "
                                  f"Gyro:({data['gyro'][0]:6.3f},{data['gyro'][1]:6.3f},{data['gyro'][2]:6.3f})")
                        else:
                            print(f"CH{channel}: READ ERROR - {data['error']}")
                    except Exception as e:
                        print(f"CH{channel}: EXCEPTION - {e}")
                    finally:
                        tca[channel].unlock()
                else:
                    print(f"CH{channel}: Failed to lock channel")
            
            time.sleep(read_interval)
            
    except KeyboardInterrupt:
        print("\nStopped by user")

def main():
    print("\n" + "="*70)
    print("TCA9548A IMU TEST USING ADAPTER LIBRARY")
    print("="*70)
    print("Configuration:")
    print("  - IMU Address: 0x69")
    print("  - Expected channels: 2, 3, 4")
    print("="*70)
    
    try:
        # Initialize I2C and multiplexer
        print("Initializing I2C and TCA9548A...")
        i2c = board.I2C()  # Uses board.SCL and board.SDA
        tca = adafruit_tca9548a.TCA9548A(i2c)
        print("✓ TCA9548A initialized successfully")
        
        # Step 1: Scan all channels
        devices_found = scan_all_channels(tca)
        
        # Step 2: Test IMUs on expected channels
        expected_channels = [2, 3, 4]
        imus = test_imu_on_channels(tca, expected_channels, imu_address=0x69)
        
        # Step 3: Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Channels scanned: 0-7")
        print(f"IMUs found: {len(imus)}/{len(expected_channels)}")
        
        if imus:
            print(f"Working channels: {list(imus.keys())}")
            
            # Step 4: Continuous reading if IMUs found
            if input("\nStart continuous readings? (y/n): ").lower().startswith('y'):
                continuous_read(tca, imus)
        else:
            print("\nNo IMUs found. Check:")
            print("1. IMU power (3.3V)")
            print("2. I2C connections")
            print("3. IMU address (AD0 pin should be high for 0x69)")
            print("4. Multiplexer channel connections")
            
    except Exception as e:
        print(f"\n❌ INITIALIZATION FAILED: {e}")
        print("\nTroubleshooting:")
        print("1. Check I2C is enabled: raspi-config → Interface Options → I2C")
        print("2. Verify wiring: SDA, SCL, power, ground")
        print("3. Try running with: sudo python3 script.py")

if __name__ == "__main__":
    main()
