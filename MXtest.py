"""
MPU9250 IMU Multiplexer Connection Test
Tests all channels to verify IMUs are connected and readable
"""

import time
from smbus2 import SMBus

class IMUTester:
    def __init__(self, bus_number=7, multiplexer_address=0x70):
        self.bus = SMBus(bus_number)
        self.multiplexer_addr = multiplexer_address
        self.bus_number = bus_number
        
    def _tca_select(self, channel):
        """Select active channel on TCA9548A multiplexer."""
        if channel < 0 or channel > 7:
            raise ValueError("Channel must be 0-7")
        self.bus.write_byte(self.multiplexer_addr, 1 << channel)
        time.sleep(0.05)  # Small delay for I2C bus to settle
    
    def detect_imu_on_channel(self, channel, address=0x69):
        """Detect if an IMU is present on a specific channel."""
        try:
            self._tca_select(channel)
            
            # Try to read WHO_AM_I register (0x75) - should return 0x71 for MPU9250
            who_am_i = self.bus.read_byte_data(address, 0x75)
            
            if who_am_i == 0x71:  # MPU9250 WHO_AM_I value
                return True, who_am_i
            else:
                return False, who_am_i
                
        except Exception as e:
            return False, f"Error: {e}"
    
    def test_imu_communication(self, channel, address=0x69):
        """Test basic communication with IMU on specific channel."""
        try:
            self._tca_select(channel)
            
            # Wake up the device
            self.bus.write_byte_data(address, 0x6B, 0x00)
            time.sleep(0.1)
            
            # Read WHO_AM_I
            who_am_i = self.bus.read_byte_data(address, 0x75)
            
            # Read some sample data
            data = self.bus.read_i2c_block_data(address, 0x3B, 6)  # Read accelerometer data
            
            return True, {
                'who_am_i': who_am_i,
                'raw_data': data[:6]  # First 6 bytes of accelerometer
            }
            
        except Exception as e:
            return False, f"Communication error: {e}"
    
    def scan_all_channels(self):
        """Scan all 8 channels for IMUs."""
        print("Scanning all multiplexer channels for IMUs...")
        print("=" * 60)
        
        results = {}
        for channel in range(8):
            detected, info = self.detect_imu_on_channel(channel)
            results[channel] = {
                'detected': detected,
                'info': info
            }
            
            status = "✓ DETECTED" if detected else "✗ NOT FOUND"
            print(f"Channel {channel}: {status}")
            
            if detected:
                print(f"         WHO_AM_I register: 0x{info:02x} (should be 0x71 for MPU9250)")
            else:
                if isinstance(info, str):
                    print(f"         {info}")
                else:
                    print(f"         WHO_AM_I returned: 0x{info:02x} (expected 0x71)")
            print()
        
        return results
    
    def test_specific_channels(self, channels_to_test):
        """Test specific channels with detailed communication tests."""
        print(f"Testing detailed communication on channels {channels_to_test}...")
        print("=" * 60)
        
        results = {}
        for channel in channels_to_test:
            print(f"Testing Channel {channel}:")
            
            # Test detection
            detected, detect_info = self.detect_imu_on_channel(channel)
            
            if detected:
                print("  ✓ IMU detected")
                print(f"  ✓ WHO_AM_I: 0x{detect_info:02x}")
                
                # Test communication
                comm_success, comm_info = self.test_imu_communication(channel)
                
                if comm_success:
                    print("  ✓ Communication test PASSED")
                    print(f"  ✓ Raw data sample: {comm_info['raw_data'][:3]}...")  # Show first 3 bytes
                    
                    # Read temperature as additional test
                    try:
                        self._tca_select(channel)
                        temp_raw = self.bus.read_i2c_block_data(0x69, 0x41, 2)  # Temperature registers
                        temp_value = self._convert_bytes_to_int(temp_raw[0], temp_raw[1])
                        print(f"  ✓ Temperature raw reading: {temp_value}")
                    except Exception as e:
                        print(f"  ⚠ Temperature read failed: {e}")
                        
                else:
                    print(f"  ✗ Communication test FAILED: {comm_info}")
                    
            else:
                print(f"  ✗ IMU not detected: {detect_info}")
            
            results[channel] = {
                'detected': detected,
                'communication_ok': comm_success if detected else False
            }
            print()
        
        return results
    
    def _convert_bytes_to_int(self, high, low):
        """Convert two bytes to signed 16-bit integer."""
        value = (high << 8) | low
        if value >= 32768:
            value -= 65536
        return value
    
    def close(self):
        """Close I2C bus."""
        self.bus.close()

def main():
    print("\n" + "=" * 70)
    print("MPU9250 IMU MULTIPLEXER CONNECTION TEST")
    print("=" * 70)
    print("Configuration:")
    print("  - I2C Bus: 7")
    print("  - Multiplexer Address: 0x70")
    print("  - IMU Address: 0x69")
    print("  - Expected Channels: 2, 3, 4")
    print("=" * 70)
    
    tester = None
    try:
        # Initialize tester
        tester = IMUTester(bus_number=7, multiplexer_address=0x70)
        
        # Step 1: Scan all channels
        print("\nSTEP 1: Scanning all multiplexer channels...")
        scan_results = tester.scan_all_channels()
        
        # Step 2: Detailed test of expected channels
        expected_channels = [2, 3, 4]
        print("\nSTEP 2: Detailed testing of expected channels...")
        detailed_results = tester.test_specific_channels(expected_channels)
        
        # Step 3: Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        working_imus = []
        problematic_imus = []
        
        for channel in expected_channels:
            if (channel in scan_results and scan_results[channel]['detected'] and
                channel in detailed_results and detailed_results[channel]['communication_ok']):
                working_imus.append(channel)
            else:
                problematic_imus.append(channel)
        
        print(f"Working IMUs: {working_imus}")
        print(f"Problematic IMUs: {problematic_imus}")
        
        if len(working_imus) == 3:
            print("\n🎉 SUCCESS: All 3 IMUs are working correctly!")
            print("You can now proceed with the main data collection script.")
        else:
            print(f"\n⚠ WARNING: Only {len(working_imus)} out of 3 IMUs are working.")
            if problematic_imus:
                print(f"Check channels: {problematic_imus}")
            
            print("\nTroubleshooting steps:")
            print("1. Verify I2C connections to multiplexer")
            print("2. Check IMU power (3.3V)")
            print("3. Verify IMU address jumpers (should be 0x69)")
            print("4. Check multiplexer channel connections")
            print("5. Run: sudo i2cdetect -y 7")
        
        # Step 4: Quick data read test
        if working_imus:
            print(f"\nSTEP 3: Quick data read test on working channels {working_imus}...")
            print("-" * 50)
            
            for channel in working_imus:
                print(f"\nChannel {channel} - Reading sensor data:")
                success, data = tester.test_imu_communication(channel)
                if success:
                    # Convert raw accelerometer data to meaningful values
                    raw_data = data['raw_data']
                    ax = tester._convert_bytes_to_int(raw_data[0], raw_data[1])
                    ay = tester._convert_bytes_to_int(raw_data[2], raw_data[3])
                    az = tester._convert_bytes_to_int(raw_data[4], raw_data[5])
                    
                    print(f"  Raw Accel - X: {ax:6d}, Y: {ay:6d}, Z: {az:6d}")
                    print(f"  Scaled Accel - X: {ax/4096.0:7.3f}g, Y: {ay/4096.0:7.3f}g, Z: {az/4096.0:7.3f}g")
                else:
                    print(f"  Failed to read data: {data}")
        
    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        print("\nCheck:")
        print("1. I2C bus number (try 1 instead of 7)")
        print("2. Multiplexer address (usually 0x70)")
        print("3. I2C permissions (try running with sudo)")
        print("4. Hardware connections")
    
    finally:
        if tester:
            tester.close()
        
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
