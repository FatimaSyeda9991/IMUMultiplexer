"""
Quick I2C Bus Scan
"""

from smbus2 import SMBus
import sys

def scan_i2c_bus(bus_number=7):
    print(f"Scanning I2C bus {bus_number}...")
    print("Address: 0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F")
    print("        " + "-" * 48)
    
    try:
        bus = SMBus(bus_number)
        
        for base in range(0, 128, 16):
            line = f"0x{base:02x}: "
            for offset in range(16):
                address = base + offset
                if address < 0x03 or address > 0x77:
                    line += "   "
                    continue
                    
                try:
                    bus.read_byte(address)
                    line += f"{address:02x} "
                except:
                    line += "-- "
            
            print(line)
            
        bus.close()
        print("\n✓ Scan completed successfully")
        
    except Exception as e:
        print(f"✗ Failed to scan bus {bus_number}: {e}")
        print("Try running with 'sudo' or check bus number")

if __name__ == "__main__":
    bus_num = 7
    if len(sys.argv) > 1:
        bus_num = int(sys.argv[1])
    
    scan_i2c_bus(bus_num)
