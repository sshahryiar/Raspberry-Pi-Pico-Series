from micropython import const
from time import sleep_ms


CHT8305C_I2C_ADDR = const(0x40)

# Register Addresses
CHT8305C_REG_TEMPERATURE = const(0x00)
CHT8305C_REG_HUMIDITY = const(0x01)
CHT8305C_REG_CONFIG = const(0x02)
CHT8305C_REG_ALERT = const(0x03)
CHT8305C_REG_MANUFACTURER_ID = const(0xFE)
CHT8305C_REG_VERSION_ID = const(0xFF)

# Configuration Register Bits
CHT8305C_CONFIG_SOFT_RESET = const(0x8000)
CHT8305C_CONFIG_CLOCK_STRETCH = const(0x4000)
CHT8305C_CONFIG_HEATER = const(0x2000)
CHT8305C_CONFIG_MODE = const(0x1000)
CHT8305C_CONFIG_VCCS = const(0x0800)
CHT8305C_CONFIG_TEMP_RES = const(0x0400)
CHT8305C_CONFIG_HUMI_RES = const(0x0300)
CHT8305C_CONFIG_ALERT_MODE = const(0x00C0)
CHT8305C_CONFIG_ALERT_PENDING = const(0x0020)
CHT8305C_CONFIG_ALERT_HUMI = const(0x0010)
CHT8305C_CONFIG_ALERT_TEMP = const(0x0008)

# Alert Register Bits
CHT8305C_ALERT_TEMP_HIGH = const(0xFF00)
CHT8305C_ALERT_TEMP_LOW = const(0x00FF)

# Constants
CHT8305C_VERSION_ID = const(0x8305)
CHT8305C_MANUFACTURER_ID = const(0x5959)


class CHT8305C:
    def __init__(self, i2c):
        self.i2c = i2c
        self.i2c_address = CHT8305C_I2C_ADDR

        if not self.check_sensor():
            raise RuntimeError("CHT8305C sensor not found at address 0x{:02X}".format(CHT8305C_I2C_ADDR))
        
        if not self.check_version():
            raise RuntimeError("CHT8305C sensor not found")
        
        self.soft_reset()
        self.set_heater(True)
        sleep_ms(1000)
        self.set_heater(False)
        sleep_ms(1000)
        self.clear_alerts()
        self.set_measurement_mode(False)
        self.set_alert_thresholds(None, None)
        self.set_temperature_resolution(True)
        self.set_humidity_resolution(2)
    

    def check_version(self):
        try:
            version_id = self.version_id
            return version_id == CHT8305C_VERSION_ID
        except:
            return False
        

    def check_sensor(self):
        try:
            mfg_id = self.manufacturer_id
            return mfg_id == CHT8305C_MANUFACTURER_ID
        except:
            return False
    

    def read_register(self, register):
        self.i2c.writeto(self.i2c_address, bytes([register]))
        sleep_ms(10)
        data = self.i2c.readfrom(self.i2c_address, 2)
        return ((data[0] << 8) | data[1])
    

    def write_register(self, register, value):
        data = bytes([register, (value >> 8) & 0xFF, value & 0xFF])
        self.i2c.writeto(self.i2c_address, data)
        sleep_ms(10)

    
    def read_measurement(self, register):
        return self.read_register(register)
    

    @property
    def temperature(self):
        raw = self.read_measurement(CHT8305C_REG_TEMPERATURE)
        temp = (((raw / 65536.0) * 165.0) - 40.0)
        return round(temp, 2)
    

    @property
    def humidity(self):
        raw = self.read_measurement(CHT8305C_REG_HUMIDITY)
        humidity = ((raw / 65536.0) * 100.0)
        return round(humidity, 2)
    

    @property
    def measurements(self):
        return (self.temperature, self.humidity)
    

    def soft_reset(self):
        config = self.read_register(CHT8305C_REG_CONFIG)
        config |= CHT8305C_CONFIG_SOFT_RESET
        self.write_register(CHT8305C_REG_CONFIG, config)
        sleep_ms(100)  # Wait for reset to complete
    

    def set_heater(self, enable):
        config = self.read_register(CHT8305C_REG_CONFIG)

        if enable:
            config |= CHT8305C_CONFIG_HEATER
        else:
            config &= ~CHT8305C_CONFIG_HEATER

        self.write_register(CHT8305C_REG_CONFIG, config)

    
    def set_measurement_mode(self, continuous = False):
        config = self.read_register(CHT8305C_REG_CONFIG)

        if continuous:
            config |= CHT8305C_CONFIG_MODE
        else:
            config &= ~CHT8305C_CONFIG_MODE

        self.write_register(CHT8305C_REG_CONFIG, config)
    

    def set_temperature_resolution(self, bits_14 = True):
        config = self.read_register(CHT8305C_REG_CONFIG)

        if bits_14:
            config |= CHT8305C_CONFIG_TEMP_RES
        else:
            config &= ~CHT8305C_CONFIG_TEMP_RES

        self.write_register(CHT8305C_REG_CONFIG, config)
    

    def set_humidity_resolution(self, resolution = 2):
        if resolution not in [0, 1, 2]:
            raise ValueError("Resolution must be 0 (8-bit), 1 (11-bit), or 2 (14-bit)")
        
        config = self.read_register(CHT8305C_REG_CONFIG)
        config &= ~CHT8305C_CONFIG_HUMI_RES
        config |= (resolution << 8)

        self.write_register(CHT8305C_REG_CONFIG, config)
    

    def set_alert_thresholds(self, temp_high = None, temp_low = None):
        alert = self.read_register(CHT8305C_REG_ALERT)
        
        if temp_high is not None:
            raw_high = (int((temp_high + 40) * 65536 / 165) >> 8)
            raw_high = max(0, min(255, raw_high))
            alert = ((alert & 0x00FF) | (raw_high << 8))
        
        if temp_low is not None:
            raw_low = (int((temp_low + 40) * 65536 / 165) >> 8)
            raw_low = max(0, min(255, raw_low))
            alert = ((alert & 0xFF00) | raw_low)
        
        self.write_register(CHT8305C_REG_ALERT, alert)
    

    def get_alert_status(self):
        config = self.read_register(CHT8305C_REG_CONFIG)
        return {
            'pending': bool(config & CHT8305C_CONFIG_ALERT_PENDING),
            'humidity': bool(config & CHT8305C_CONFIG_ALERT_HUMI),
            'temperature': bool(config & CHT8305C_CONFIG_ALERT_TEMP)
        }

    
    def clear_alerts(self):
        self.read_register(CHT8305C_REG_CONFIG)
    
    
    @property
    def manufacturer_id(self):
        return self.read_register(CHT8305C_REG_MANUFACTURER_ID)
    
    
    @property
    def version_id(self):
        return self.read_register(CHT8305C_REG_VERSION_ID)
    

    def get_config(self):
        return self.read_register(CHT8305C_REG_CONFIG)
    

    def set_config(self, config_value):
        self.write_register(CHT8305C_REG_CONFIG, config_value)
    
    
    @property
    def get_dew_point(self):
        temp = self.temperature
        humidity = self.humidity
        
        a = 17.27
        b = 237.7
        
        alpha = (((a * temp) / (b + temp)) + (humidity / 100.0))
        dew_point = ((b * alpha) / (a - alpha))
        
        return round(dew_point, 2)
    