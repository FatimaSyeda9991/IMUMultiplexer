"""
SIMPLE TCA9548A DETECTION TEST
"""

import board
import adafruit_tca9548a

print("SIMPLE TCA9548A DETECTION TEST")
print("=" * 50)

try:
    # Initialize I2C
    i2c = board.I2C()
    print("✓ I2C initialized")
    
    # Initialize multiplexer
    tca = adafruit_tca9548a.TCA9548A(i2c)
    print("✓ TCA9548A multiplexer initialized")
    
    print("\nScanning all channels for I2C devices:")
    print("-" * 40)
    
    for channel in range(8):
        print(f"Channel {channel}: ", end="")
        
        if tca[channel].try_lock():
            try:
                # Scan for devices
                addresses = tca[channel].scan()
                # Remove multiplexer address (0x70)
                device_addresses = [hex(addr) for addr in addresses if addr != 0x70]
                
                if device_addresses:
                    print(device_addresses)
                else:
                    print("No devices")
                    
            except Exception as e:
                print(f"Error: {e}")
            finally:
                tca[channel].unlock()
        else:
            print("Failed to lock")
            
    print("\nScan complete!")

except Exception as e:
    print(f"❌ Failed: {e}")
    print("\nCheck:")
    print("1. I2C is enabled (raspi-config)")
    print("2. TCA9548A is properly wired")
    print("3. You're using the correct I2C bus")
