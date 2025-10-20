import smbus2
import time
from mpu9250_jmdev.registers import *
from mpu9250_jmdev.mpu_9250 import MPU9250

# --- Constants ---
I2C_BUS = 1                 # I2C bus number
TCA9548A_ADDRESS = 0x70     # Multiplexer address
MPU_ADDRESS = 0x69          # Default MPU-9250 address

# Initialize I2C bus
bus = smbus2.SMBus(I2C_BUS)

# --- Function to select TCA9548A channel ---
def tca_select(channel):
    """Select active channel on TCA9548A multiplexer."""
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be 0-7")
    bus.write_byte(TCA9548A_ADDRESS, 1 << channel)
    print(f"Switched to TCA9548A channel {channel}")
    time.sleep(0.05)  # small delay for I2C bus to settle

# --- Initialize MPU-9250 on a given channel ---
def init_mpu(channel):
    tca_select(channel)
    imu = MPU9250(
        address_ak=MPU_ADDRESS,
        address_mpu_master=MPU_ADDRESS,
        bus=I2C_BUS,
        gfs=GFS_250,    # Gyro full scale ±250°/s
        afs=AFS_2G,     # Accel full scale ±2g
        mfs=AK8963_BIT_16,  # Magnetometer resolution
        mode=AK8963_MODE_C100HZ
    )
    imu.calibrate()     # Calibrate gyro and accel
    imu.configure()     # Apply settings
    print(f"Initialized MPU9250 on channel {channel}")
    return imu

# --- Initialize all 3 IMUs on channels 2, 3, 4 ---
channels = [2, 3, 4]
imus = {}
for ch in channels:
    imus[ch] = init_mpu(ch)

# --- Read data from each IMU ---
def read_imus():
    data = {}
    for ch, imu in imus.items():
        tca_select(ch)  # select channel before reading
        accel = imu.readAccelerometerMaster()
        gyro = imu.readGyroscopeMaster()
        mag = imu.readMagnetometerMaster()
        data[ch] = {
            "accel": accel,
            "gyro": gyro,
            "mag": mag
        }
    return data

# --- Example loop ---
try:
    while True:
        imu_data = read_imus()
        for ch, d in imu_data.items():
            print(f"Channel {ch} | Accel: {d['accel']} | Gyro: {d['gyro']} | Mag: {d['mag']}")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Stopping MPU reads.")
