from micropython import const
from time import sleep_ms


# SHT4x Default I2C Address
SHT4X_I2C_ADDRESS   = const(0x44)

# Measurement commands
SHT4X_MEAS_HIGH_REP  = const(0xFD)   # High repeatability (slow, ~10 ms)
SHT4X_MEAS_MED_REP   = const(0xF6)   # Medium repeatability (~5 ms)
SHT4X_MEAS_LOW_REP   = const(0xE0)   # Low repeatability (fast, ~2 ms)

# Heater + measurement commands
SHT4X_HEAT_200MW_1S  = const(0x39)   # 200 mW, 1 s pulse
SHT4X_HEAT_200MW_01S = const(0x32)   # 200 mW, 0.1 s pulse
SHT4X_HEAT_110MW_1S  = const(0x2F)   # 110 mW, 1 s pulse
SHT4X_HEAT_110MW_01S = const(0x24)   # 110 mW, 0.1 s pulse
SHT4X_HEAT_20MW_1S   = const(0x1E)   # 20 mW,  1 s pulse
SHT4X_HEAT_20MW_01S  = const(0x15)   # 20 mW,  0.1 s pulse

# Other commands
SHT4X_SOFT_RESET     = const(0x94)
SHT4X_GET_SERIAL     = const(0x89)

# Measurement delays (ms) — from datasheet table 5, with small margin
_DELAY_MS = {
    SHT4X_MEAS_HIGH_REP:  10,
    SHT4X_MEAS_MED_REP:    6,
    SHT4X_MEAS_LOW_REP:    3,
    SHT4X_HEAT_200MW_1S: 1100,
    SHT4X_HEAT_110MW_1S: 1100,
    SHT4X_HEAT_20MW_1S:  1100,
    SHT4X_HEAT_200MW_01S: 110,
    SHT4X_HEAT_110MW_01S: 110,
    SHT4X_HEAT_20MW_01S:  110,
}

# CRC polynomial: x^8 + x^5 + x^4 + 1
SHT4X_CRC_POLY = const(0x31)


class SHT4x:
    def __init__(self, i2c, address = SHT4X_I2C_ADDRESS):
        self._i2c = i2c
        self.addr = address
        self._raw_temp = 0
        self._raw_hum  = 0
        self._HUM_SCALE = (125.0 / 65535.0)
        self._TEMP_SCALE = (175.0 / 65535.0)
        self._buf = bytearray(6)
        
        self.init()


    def init(self):
        if not self.is_connected():
            raise OSError(f"SHT4x not found at 0x{self.addr:02X}")

        if not self.reset():
            raise OSError("SHT4x reset failed")

        serial = self.serial_number()
        if serial is None:
            raise OSError("Failed to read serial number")

        print(f"SHT4x: serial 0x{serial:08X}")
        return True

    
    def is_connected(self):
        try:
            self._i2c.writeto(self.addr, b'')
            return True
        except OSError:
            return False


    def reset(self):
        try:
            if not self.write(SHT4X_SOFT_RESET):
                return False
            sleep_ms(2)
            return True
        except OSError as e:
            print(f"SHT4x: reset error: {e}")
            return False
        
    
    def write(self, cmd):
        for _ in range(3):
            try:
                self._i2c.writeto(self.addr, bytes([cmd]))
                return True
            except OSError:
                sleep_ms(2)
        else:
            print("SHT4x: write failed")
            return False


    def read(self, cmd = SHT4X_MEAS_HIGH_REP):       
        if not self.write(cmd):
            return False

        sleep_ms(_DELAY_MS.get(cmd, 10))

        for _ in range(3):
            try:
                self._i2c.readfrom_into(self.addr, self._buf)
                break
            except OSError:
                sleep_ms(2)
        else:
            print("SHT4x: read failed after retries")
            return False

        if(self._buf[2] != self.compute_crc8(self._buf[0:2])):
            print("SHT4x: temperature CRC error")
            return False
        
        if(self._buf[5] != self.compute_crc8(self._buf[3:5])):
            print("SHT4x: humidity CRC error")
            return False

        self._raw_temp = ((self._buf[0] << 8) | self._buf[1])
        self._raw_hum  = ((self._buf[3] << 8) | self._buf[4])

        return True


    def serial_number(self):
        try:
            if not self.write(SHT4X_GET_SERIAL):
                return None
            sleep_ms(5)
            self._i2c.readfrom_into(self.addr, self._buf)
        except OSError as e:
            print(f"SHT4x: serial read error: {e}")
            return None

        if((self._buf[2] != self.compute_crc8(self._buf[0:2])) or (self._buf[5] != self.compute_crc8(self._buf[3:5]))):
            print("SHT4x: serial number CRC error")
            return None

        return ((self._buf[0] << 24) | (self._buf[1] << 16) | (self._buf[3] << 8) | self._buf[4])


    def temperature(self):
        return ((self._raw_temp * self._TEMP_SCALE) - 45.0)


    def humidity(self):
        hum = ((self._raw_hum * self._HUM_SCALE) - 6.0)
        return max(0.0, min(100.0, hum))
    
    
    def read_sensor(self, cmd=SHT4X_MEAS_HIGH_REP):
        if not self.read(cmd):
            return None, None
        return self.temperature(), self.humidity()


    def compute_crc8(self, data):
        crc = 0xFF

        for byte in data:
            crc ^= byte
            
            for _ in range(8):
                if(crc & 0x80):
                    crc = ((crc << 1) ^ SHT4X_CRC_POLY)
                else:
                    crc = (crc << 1)
                crc &= 0xFF

        return crc
