from micropython import const
from machine import I2C
from time import sleep_ms, ticks_ms, ticks_diff


VEML7700_I2C_ADDRESS = const(0x10)

# Register addresses
VEML7700_ALS_CONFIG = const(0x00)
VEML7700_ALS_THREHOLD_HIGH = const(0x01)
VEML7700_ALS_THREHOLD_LOW = const(0x02)
VEML7700_ALS_POWER_SAVE = const(0x03)
VEML7700_ALS_DATA = const(0x04)
VEML7700_WHITE_DATA = const(0x05)
VEML7700_INTERRUPT_STATUS = const(0x06)

VEML7700_INTERRUPT_HIGH = const(0x4000)
VEML7700_INTERRUPT_LOW = const(0x8000)

# Gain constants
VEML7700_GAIN_1 = const(0x00)
VEML7700_GAIN_2 = const(0x01)
VEML7700_GAIN_1_8 = const(0x02)
VEML7700_GAIN_1_4 = const(0x03)

# Integration time constants
VEML7700_IT_100MS = const(0x00)
VEML7700_IT_200MS = const(0x01)
VEML7700_IT_400MS = const(0x02)
VEML7700_IT_800MS = const(0x03)
VEML7700_IT_50MS = const(0x08)
VEML7700_IT_25MS = const(0x0C)

# Persistence constants
VEML7700_PERS_1 = const(0x00)
VEML7700_PERS_2 = const(0x01)
VEML7700_PERS_4 = const(0x02)
VEML7700_PERS_8 = const(0x03)

# Power save mode constants
VEML7700_POWERSAVE_MODE1 = const(0x00)
VEML7700_POWERSAVE_MODE2 = const(0x01)
VEML7700_POWERSAVE_MODE3 = const(0x02)
VEML7700_POWERSAVE_MODE4 = const(0x03)

# Lux method constants
VEML_LUX_NORMAL = const(0)
VEML_LUX_CORRECTED = const(1)
VEML_LUX_AUTO = const(2)
VEML_LUX_NORMAL_NO_WAIT = const(3)
VEML_LUX_CORRECTED_NO_WAIT = const(4)


class VEML7700:
    def __init__(self, i2c):
        self.i2c = i2c
        self.last_read = ticks_ms()
        
        self.MAX_RES = 0.0036
        self.GAIN_MAX = 2
        self.IT_MAX = 800
        
        self._config = 0
        self._power_save = 0


    def init(self):
        try:
            self.read_register(VEML7700_ALS_CONFIG)
            self.enable(False)
            self.interrupt_enable(False)
            self.set_persistence(VEML7700_PERS_1)
            self.set_gain(VEML7700_GAIN_1_8)
            self.set_integration_time(VEML7700_IT_100MS)
            self.power_save_enable(False)
            self.enable(True)            
            self.last_read = ticks_ms()
            return True
        
        except:
            return False


    def read_register(self, reg):
        rcv_data = self.i2c.readfrom_mem(VEML7700_I2C_ADDRESS, reg, 2)
        return ((rcv_data[1] << 8) | rcv_data[0])


    def write_register(self, reg, value):
        send_value = bytearray(2)
        send_value[0] = (value & 0xFF)
        send_value[1] = ((value >> 8) & 0xFF)
        self.i2c.writeto_mem(VEML7700_I2C_ADDRESS, reg, send_value)


    def set_bit(self, reg, bit, value):
        current = self.read_register(reg)
        
        if(value):
            current |= (1 << bit)
        else:
            current &= ~(1 << bit)
        
        self.write_register(reg, current)


    def get_bit(self, reg, bit):
        current = self.read_register(reg)
        return (current >> bit) & 0x01


    def enable(self, enable):
        self.set_bit(VEML7700_ALS_CONFIG, 0, not enable)
        if(enable):
            sleep_ms(5)  


    def enabled(self):
        return not self.get_bit(VEML7700_ALS_CONFIG, 0)


    def interrupt_enable(self, enable):
        self.set_bit(VEML7700_ALS_CONFIG, 1, enable)


    def interrupt_enabled(self):
        return self.get_bit(VEML7700_ALS_CONFIG, 1)


    def set_persistence(self, pers):
        config = self.read_register(VEML7700_ALS_CONFIG)
        config = (config & ~(0x03 << 4)) | ((pers & 0x03) << 4)
        self.write_register(VEML7700_ALS_CONFIG, config)


    def get_persistence(self):
        config = self.read_register(VEML7700_ALS_CONFIG)
        return ((config >> 4) & 0x03)


    def set_integration_time(self, it, wait = True):
        if(wait):
            flush_delay = self.get_integration_time_value()
        else:
            flush_delay = 0
        
        config = self.read_register(VEML7700_ALS_CONFIG)
        config = (config & ~(0x0F << 6)) | ((it & 0x0F) << 6)
        self.write_register(VEML7700_ALS_CONFIG, config)
        
        if(flush_delay):
            sleep_ms(flush_delay)
        
        self.last_read = ticks_ms()
        

    def get_integration_time(self):
        config = self.read_register(VEML7700_ALS_CONFIG)
        return ((config >> 6) & 0x0F)


    def get_integration_time_value(self):
        it = self.get_integration_time()
        it_values = {
            VEML7700_IT_25MS: 25,
            VEML7700_IT_50MS: 50,
            VEML7700_IT_100MS: 100,
            VEML7700_IT_200MS: 200,
            VEML7700_IT_400MS: 400,
            VEML7700_IT_800MS: 800
        }
        
        return it_values.get(it, -1)


    def set_gain(self, gain):
        config = self.read_register(VEML7700_ALS_CONFIG)
        config = (config & ~(0x03 << 11)) | ((gain & 0x03) << 11)
        self.write_register(VEML7700_ALS_CONFIG, config)
        self.last_read = ticks_ms()


    def get_gain(self):
        config = self.read_register(VEML7700_ALS_CONFIG)
        return ((config >> 11) & 0x03)


    def get_gain_value(self):
        gain = self.get_gain()
        gain_values = {
            VEML7700_GAIN_1_8: 0.125,
            VEML7700_GAIN_1_4: 0.25,
            VEML7700_GAIN_1: 1.0,
            VEML7700_GAIN_2: 2.0
        }
        
        return gain_values.get(gain, -1)


    def power_save_enable(self, enable):
        self.set_bit(VEML7700_ALS_POWER_SAVE, 0, enable)


    def power_save_enabled(self):
        return self.get_bit(VEML7700_ALS_POWER_SAVE, 0)


    def set_power_save_mode(self, mode):
        power_save = self.read_register(VEML7700_ALS_POWER_SAVE)
        power_save = (power_save & ~(0x03 << 1)) | ((mode & 0x03) << 1)
        self.write_register(VEML7700_ALS_POWER_SAVE, power_save)


    def get_power_save_mode(self):
        power_save = self.read_register(VEML7700_ALS_POWER_SAVE)
        return ((power_save >> 1) & 0x03)
    

    def set_low_threshold(self, value):
        self.write_register(VEML7700_ALS_THREHOLD_LOW, value)


    def get_low_threshold(self):
        return self.read_register(VEML7700_ALS_THREHOLD_LOW)


    def set_high_threshold(self, value):
        self.write_register(VEML7700_ALS_THREHOLD_HIGH, value)


    def get_high_threshold(self):
        return self.read_register(VEML7700_ALS_THREHOLD_HIGH)


    def interrupt_status(self):
        return self.read_register(VEML7700_INTERRUPT_STATUS)


    def read_wait(self):
        time_to_wait = (2 * self.get_integration_time_value())
        time_waited = ticks_diff(ticks_ms(), self.last_read)
        
        if(time_waited < time_to_wait):
            sleep_ms(time_to_wait - time_waited)


    def read_als(self, wait = False):
        if(wait):
            self.read_wait()
        self.last_read = ticks_ms()
        
        return self.read_register(VEML7700_ALS_DATA)


    def read_white(self, wait = False):
        if(wait):
            self.read_wait()
        self.last_read = ticks_ms()
        
        return self.read_register(VEML7700_WHITE_DATA)


    def get_resolution(self):
        return (self.MAX_RES * 
                (self.IT_MAX / self.get_integration_time_value()) *
                (self.GAIN_MAX / self.get_gain_value()))


    def compute_lux(self, raw_als, corrected = False):
        lux = (self.get_resolution() * raw_als)
        if(corrected):
            lux = ((((6.0135e-13 * lux - 9.3924e-9) * lux + 8.1488e-5) * lux + 1.0023) * lux)
            
        return lux


    def read_lux(self, method = VEML_LUX_NORMAL):
        wait = True
        
        if(method == VEML_LUX_NORMAL_NO_WAIT):
            wait = False
            method = VEML_LUX_NORMAL
        elif(method == VEML_LUX_CORRECTED_NO_WAIT):
            wait = False
            method = VEML_LUX_CORRECTED
            
        if(method == VEML_LUX_NORMAL):
            return self.compute_lux(self.read_als(wait))
        elif(method == VEML_LUX_CORRECTED):
            return self.compute_lux(self.read_als(wait), True)
        elif(method == VEML_LUX_AUTO):
            return self.auto_lux()
        else:
            return -1


    def auto_lux(self):
        gains = [VEML7700_GAIN_1_8, VEML7700_GAIN_1_4, VEML7700_GAIN_1, VEML7700_GAIN_2]
        int_times = [VEML7700_IT_25MS, VEML7700_IT_50MS, VEML7700_IT_100MS, 
                    VEML7700_IT_200MS, VEML7700_IT_400MS, VEML7700_IT_800MS]

        it_index = 2
        gain_index = 0  
        use_correction = False

        self.set_gain(gains[gain_index])
        self.set_integration_time(int_times[it_index])

        als = self.read_als(True)

        if(als <= 100):
            while((als <= 100) and not ((gain_index == 3) and (it_index == 5))):
                if(gain_index < 3):
                    gain_index += 1
                    self.set_gain(gains[gain_index])
                elif(it_index < 5):
                    it_index += 1
                    self.set_integration_time(int_times[it_index])
                als = self.read_als(True)
        else:
            use_correction = True
            while((als > 10000) and (it_index > 0)):
                it_index -= 1
                self.set_integration_time(int_times[it_index])
                als = self.read_als(True)

        return self.compute_lux(als, use_correction)