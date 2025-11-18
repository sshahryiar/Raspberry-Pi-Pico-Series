from machine import I2C
from micropython import const
import time

# Device I2C address
AGS01DB_I2C_ADDR = const(0x11)


class AGS01DB:
    def __init__(self, _i2c):
        self.i2c = _i2c
        self.addr = AGS01DB_I2C_ADDR

        if(self.addr not in self.i2c.scan()):
            raise OSError("AGS01DB not found!")


    def _crc8(self, data):
        i = 8
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for i in range(8):
                if(crc & 0x80):
                    crc = ((crc << 1) ^ 0x31)
                else:
                    crc = (crc << 1)
        return (crc & 0xFF)


    def read_sensor(self):
        voc_ppm = 0
        cmd = bytes([0x00, 0x02])
        try:
            self.i2c.writeto(self.addr, cmd)
            time.sleep_ms(400)  
        
            data = self.i2c.readfrom(self.addr, 4)
            raw = data[0:2]
            crc = data[2]

            if self._crc8(raw) != crc:
                raise ValueError("CRC mismatch – bad data received!")

            voc_raw = (raw[0] << 8) | raw[1]
            voc_ppm = voc_raw / 10.0
        except:
            pass
        return voc_ppm


    def get_serial_id(self):
        cmd = bytes([0x0A, 0x01])
        self.i2c.writeto(self.addr, cmd)
        time.sleep_ms(10)
        data = self.i2c.readfrom(self.addr, 3)
        raw = data[0:2]
        crc = data[2]

        if(self._crc8(raw) != crc):
            raise ValueError("CRC mismatch – failed to read serial ID!")

        return (raw[0] << 8) | raw[1]
