"""
COMPREHENSIVE I2C MULTIPLEXER DIAGNOSTIC
"""

from smbus2 import SMBus
import time
import sys

class MultiplexerDiagnostic:
    def __init__(self, bus_number=7, multiplexer_address=0x70):
        self.bus_number = bus_number
        self.multiplexer_addr = multiplexer_address
        self.bus = None
        
    def initialize_bus(self):
        """Initialize I2C bus with error handling."""
        try:
            self.bus = SMBus(self.bus_number)
            print(f"✓ I2C bus {self.bus_number} opened successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to open I2C bus {self.bus_number}: {e}")
            return False
    
    def test_multiplexer_presence(self):
        """Test if multiplexer is present and responsive."""
        try:
            # Try to read from multiplexer (it doesn't have readable registers, so we try to select channel 0)
            self.bus.write_byte(self.multiplexer_addr, 0x00)  # Select no channels
            print(f"✓ Multiplexer at 0x{self.multiplexer_addr:02x} is responsive")
            return True
        except Exception as e:
            print(f"✗ Multiplexer at 0x{self.multiplexer_addr:02x} not found: {e}")
            return False
    
    def scan_all_channels_detailed(self):
        """Scan all channels with detailed error reporting."""
        print("\n" + "="*60)
        print("DETAILED CHANNEL SCAN")
        print("="*60)
        
        for channel in range(8):
            print(f"\nChannel {channel}:")
            
            # Try to select the channel
            try:
                self.bus.write_byte(self.multiplexer_addr, 1 << channel)
                print(f"  ✓ Channel selection: OK")
                time.sleep(0.01)
            except Exception as e:
                print(f"  ✗ Channel selection failed: {e}")
                continue
            
            # Scan for devices on this channel
            devices_found = []
            for address in range(0x08, 0x78):  # Valid I2C addresses
                if address == self.multiplexer_addr:  # Skip multiplexer itself
                    continue
                    
                try:
                    self.bus.read_byte(address)
                    devices_found.append(address)
                except:
                    pass
            
            if devices_found:
                print(f"  ✓ Devices found: {[hex(addr) for addr in devices_found]}")
            else:
                print(f"  ✗ No devices found on this channel")
    
    def test_imu_detection(self, channels_to_test=[2, 3, 4], imu_address=0x69):
        """Test IMU detection on specific channels."""
        print("\n" + "="*60)
        print("IMU DETECTION TEST")
        print("="*60)
        
        for channel in channels_to_test:
            print(f"\nTesting Channel {channel} for IMU at 0x{imu_address:02x}:")
            
            # Select channel
            try:
                self.bus.write_byte(self.multiplexer_addr, 1 << channel)
                time.sleep(0.01)
                print(f"  ✓ Multiplexer channel selected")
            except Exception as e:
                print(f"  ✗ Channel selection failed: {e}")
                continue
            
            # Test IMU presence
            try:
                # Try to wake up IMU
                self.bus.write_byte_data(imu_address, 0x6B, 0x00)
                time.sleep(0.01)
                print(f"  ✓ IMU wake-up command sent")
            except Exception as e:
                print(f"  ✗ IMU wake-up failed: {e}")
                continue
            
            # Read WHO_AM_I register
            try:
                who_am_i = self.bus.read_byte_data(imu_address, 0x75)
                print(f"  ✓ WHO_AM_I register read: 0x{who_am_i:02x}")
                if who_am_i == 0x71:
                    print(f"  🎉 MPU9250 confirmed! (0x71 = MPU9250)")
                elif who_am_i == 0x73:
                    print(f"  ⚠ MPU9255 detected (0x73 = MPU9255)")
                else:
                    print(f"  ❓ Unexpected WHO_AM_I value: 0x{who_am_i:02x}")
            except Exception as e:
                print(f"  ✗ WHO_AM_I read failed: {e}")
    
    def test_alternative_addresses(self, channels_to_test=[2, 3, 4]):
        """Test both common MPU9250 addresses."""
        print("\n" + "="*60)
        print("ALTERNATIVE ADDRESS TEST")
        print("="*60)
        
        addresses_to_test = [0x68, 0x69]  # Common MPU9250 addresses
        
        for channel in channels_to_test:
            print(f"\nChannel {channel}:")
            
            for addr in addresses_to_test:
                try:
                    self.bus.write_byte(self.multiplexer_addr, 1 << channel)
                    time.sleep(0.01)
                    
                    # Try to read WHO_AM_I
                    who_am_i = self.bus.read_byte_data(addr, 0x75)
                    print(f"  ✓ Address 0x{addr:02x}: WHO_AM_I = 0x{who_am_i:02x}")
                    
                except Exception as e:
                    print(f"  ✗ Address 0x{addr:02x}: {e}")
    
    def test_multiplexer_channels(self):
        """Test if multiplexer channels are working by checking control register."""
        print("\n" + "="*60)
        print("MULTIPLEXER CHANNEL FUNCTIONALITY TEST")
        print("="*60)
        
        # Test each channel individually
        for channel in range(8):
            try:
                # Select only this channel
                self.bus.write_byte(self.multiplexer_addr, 1 << channel)
                time.sleep(0.01)
                
                # The multiplexer doesn't have a readable control register, 
                # but we can verify by trying to select and seeing if it accepts the command
                print(f"  ✓ Channel {channel}: Selection accepted")
                
            except Exception as e:
                print(f"  ✗ Channel {channel}: Selection failed - {e}")
    
    def close(self):
        """Close I2C bus."""
        if self.bus:
            self.bus.close()

def main():
    print("\n" + "="*70)
    print("COMPREHENSIVE I2C MULTIPLEXER DIAGNOSTIC")
    print("="*70)
    print("This will test:")
    print("1. I2C bus connectivity")
    print("2. Multiplexer presence")
    print("3. Individual channel functionality") 
    print("4. IMU detection on each channel")
    print("5. Alternative IMU addresses")
    print("="*70)
    
    diagnostic = MultiplexerDiagnostic(bus_number=7, multiplexer_address=0x70)
    
    try:
        # Step 1: Initialize bus
        if not diagnostic.initialize_bus():
            print("\n💡 TROUBLESHOOTING TIPS:")
            print("   - Try running with: sudo python3 script.py")
            print("   - Check if I2C is enabled: raspi-config → Interface Options → I2C")
            print("   - Try different bus number: 1 instead of 7")
            return
        
        # Step 2: Test multiplexer presence
        if not diagnostic.test_multiplexer_presence():
            print("\n💡 TROUBLESHOOTING TIPS:")
            print("   - Check multiplexer wiring (VCC, GND, SDA, SCL)")
            print("   - Verify multiplexer address (usually 0x70)")
            print("   - Check I2C pull-up resistors")
            return
        
        # Step 3: Test multiplexer channels
        diagnostic.test_multiplexer_channels()
        
        # Step 4: Scan all channels
        diagnostic.scan_all_channels_detailed()
        
        # Step 5: Test IMU detection
        diagnostic.test_imu_detection(channels_to_test=[2, 3, 4], imu_address=0x69)
        
        # Step 6: Test alternative addresses
        diagnostic.test_alternative_addresses(channels_to_test=[2, 3, 4])
        
        print("\n" + "="*70)
        print("DIAGNOSTIC COMPLETE")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
    
    finally:
        diagnostic.close()

if __name__ == "__main__":
    main()
