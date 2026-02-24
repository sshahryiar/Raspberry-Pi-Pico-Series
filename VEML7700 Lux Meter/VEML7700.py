from micropython import const
from time import sleep_ms, ticks_ms, ticks_diff


VEML7700_I2C_ADDRESS = const(0x10)

# ---------------------------------------------------------------------------
# Register addresses
# ---------------------------------------------------------------------------
VEML7700_ALS_CONFIG = const(0x00)
VEML7700_ALS_THRESHOLD_HIGH = const(0x01)
VEML7700_ALS_THRESHOLD_LOW = const(0x02)
VEML7700_ALS_POWER_SAVE = const(0x03)
VEML7700_ALS_DATA = const(0x04)
VEML7700_WHITE_DATA = const(0x05)
VEML7700_INTERRUPT_STATUS = const(0x06)

# ---------------------------------------------------------------------------
# Interrupt flags (read from register 0x06)
# ---------------------------------------------------------------------------
VEML7700_INTERRUPT_HIGH = const(0x4000)
VEML7700_INTERRUPT_LOW = const(0x8000)

# ---------------------------------------------------------------------------
# Gain constants  (ALS_GAIN bits [12:11] of ALS_CONFIG)
# Datasheet: 00=x1, 01=x2, 10=x1/8, 11=x1/4
# ---------------------------------------------------------------------------
VEML7700_GAIN_1 = const(0x00)   # x1
VEML7700_GAIN_2 = const(0x01)   # x2
VEML7700_GAIN_1_8 = const(0x02)   # x1/8  (lowest gain, widest range)
VEML7700_GAIN_1_4 = const(0x03)   # x1/4

# ---------------------------------------------------------------------------
# Integration time constants  (ALS_IT bits [9:6] of ALS_CONFIG)
# ---------------------------------------------------------------------------
VEML7700_IT_100MS = const(0x00)
VEML7700_IT_200MS = const(0x01)
VEML7700_IT_400MS = const(0x02)
VEML7700_IT_800MS = const(0x03)
VEML7700_IT_50MS = const(0x08)
VEML7700_IT_25MS = const(0x0C)

# ---------------------------------------------------------------------------
# Persistence protect number constants
# ---------------------------------------------------------------------------
VEML7700_PERS_1 = const(0x00)
VEML7700_PERS_2 = const(0x01)
VEML7700_PERS_4 = const(0x02)
VEML7700_PERS_8 = const(0x03)

# ---------------------------------------------------------------------------
# Power-save mode constants
# ---------------------------------------------------------------------------
VEML7700_POWERSAVE_MODE1 = const(0x00)
VEML7700_POWERSAVE_MODE2 = const(0x01)
VEML7700_POWERSAVE_MODE3 = const(0x02)
VEML7700_POWERSAVE_MODE4 = const(0x03)

# ---------------------------------------------------------------------------
# read_lux() method selectors
# ---------------------------------------------------------------------------
VEML_LUX_NORMAL = const(0)   # raw lux, waits for fresh sample
VEML_LUX_CORRECTED = const(1)   # polynomial-corrected, waits
VEML_LUX_AUTO = const(2)   # auto gain/IT selection
VEML_LUX_NORMAL_NO_WAIT = const(3)   # raw lux, no wait
VEML_LUX_CORRECTED_NO_WAIT = const(4) # corrected, no wait

VEML7700_AUTO_DARK_THRESHOLD = const(100)
VEML7700_AUTO_BRIGHT_THRESHOLD = const(60000)


class VEML7700:
    _IT_MAX = 800
    _MAX_RES = 0.0036
    _GAIN_MAX = 1

    def __init__(self, i2c):
        self.i2c = i2c
        self.last_read = ticks_ms()
        self._config = 0
        self.init()


    def init(self):
        try:
            if(VEML7700_I2C_ADDRESS not in self.i2c.scan()):
                print("VEML7700: device not found on I2C bus")
                return False

            self.interrupt_enable(False)
            self.set_persistence(VEML7700_PERS_1)
            self.set_gain(VEML7700_GAIN_1_8)
            self.set_integration_time(VEML7700_IT_100MS, wait=False)
            self.power_save_enable(False)

            self.enable(True)
            sleep_ms(self.get_integration_time_value() * 2)

            self.last_read = ticks_ms()
            return True

        except Exception as e:
            print("VEML7700 init error:", e)
            return False


    def read_register(self, reg):
        try:
            data = self.i2c.readfrom_mem(VEML7700_I2C_ADDRESS, reg, 2)
            return ((data[1] << 8) | data[0])
        except Exception as e:
            print(f"VEML7700 read error reg 0x{reg:02X}:", e)
            return None


    def write_register(self, reg, value):
        try:
            buf = bytearray(2)
            buf[0] =  (value & 0xFF)
            buf[1] = ((value >> 8) & 0xFF)
            
            self.i2c.writeto_mem(VEML7700_I2C_ADDRESS, reg, buf)

            if reg == VEML7700_ALS_CONFIG:
                self._config = value

        except Exception as e:
            print(f"VEML7700 write error reg 0x{reg:02X}:", e)


    def set_bit(self, reg, bit, value):
        current = self.read_register(reg)

        if(current is None):
            return None
        
        if(value):
            current |=  (1 << bit)
        else:
            current &= ~(1 << bit)

        self.write_register(reg, current)


    def get_bit(self, reg, bit):
        current = self.read_register(reg)

        if(current is None):
            return None
        
        return ((current >> bit) & 0x01)

   
    def enable(self, enable):
        self.set_bit(VEML7700_ALS_CONFIG, 0, not enable)
        if(enable):
            sleep_ms(5)  

    def enabled(self):
        val = self.get_bit(VEML7700_ALS_CONFIG, 0)
        return False if val is None else not val


    def interrupt_enable(self, enable):
        self.set_bit(VEML7700_ALS_CONFIG, 1, enable)


    def interrupt_enabled(self):
        return self.get_bit(VEML7700_ALS_CONFIG, 1)


    def interrupt_status(self):
        return self.read_register(VEML7700_INTERRUPT_STATUS)


    def set_persistence(self, pers):
        config = self.read_register(VEML7700_ALS_CONFIG)

        if(config is None):
            return None
        
        config = (config & ~(0x03 << 4)) | ((pers & 0x03) << 4)
        self.write_register(VEML7700_ALS_CONFIG, config)


    def get_persistence(self):
        config = self.read_register(VEML7700_ALS_CONFIG)

        if(config is None):
            return None
        
        return ((config >> 4) & 0x03)


    def set_integration_time(self, it, wait=True):
        old_it_ms = self.get_integration_time_value() if wait else 0

        config = self.read_register(VEML7700_ALS_CONFIG)
        
        if(config is None):
            return None
        
        config = (config & ~(0x0F << 6)) | ((it & 0x0F) << 6)
        self.write_register(VEML7700_ALS_CONFIG, config)

        if(wait):
            new_it_ms = self.get_integration_time_value()
            sleep_ms(old_it_ms + new_it_ms)

        self.last_read = ticks_ms()


    def get_integration_time(self):
        config = self.read_register(VEML7700_ALS_CONFIG)
        if(config is None):
            return None
        return ((config >> 6) & 0x0F)


    def get_integration_time_value(self):
        it = self.get_integration_time()

        it_map = {
            VEML7700_IT_25MS:  25,
            VEML7700_IT_50MS:  50,
            VEML7700_IT_100MS: 100,
            VEML7700_IT_200MS: 200,
            VEML7700_IT_400MS: 400,
            VEML7700_IT_800MS: 800,
        }

        if(it not in it_map):
            print(f"VEML7700: unknown IT bits 0x{it:02X}, defaulting to 100ms")
            return 100
        
        return it_map[it]


    def set_gain(self, gain):
        config = self.read_register(VEML7700_ALS_CONFIG)
        if(config is None):
            return None
        config = (config & ~(0x03 << 11)) | ((gain & 0x03) << 11)
        self.write_register(VEML7700_ALS_CONFIG, config)
        self.last_read = ticks_ms()


    def get_gain(self):
        config = self.read_register(VEML7700_ALS_CONFIG)
        if(config is None):
            return None
        return ((config >> 11) & 0x03)


    def get_gain_value(self):
        gain = self.get_gain()
        gain_map = {
            VEML7700_GAIN_1_8: 0.125,
            VEML7700_GAIN_1_4: 0.25,
            VEML7700_GAIN_1: 1.0,
            VEML7700_GAIN_2: 2.0,
        }
        if(gain not in gain_map):
            return None
        return gain_map[gain]


    def power_save_enable(self, enable):
        self.set_bit(VEML7700_ALS_POWER_SAVE, 0, enable)


    def power_save_enabled(self):
        return self.get_bit(VEML7700_ALS_POWER_SAVE, 0)


    def set_power_save_mode(self, mode):
        ps = self.read_register(VEML7700_ALS_POWER_SAVE)

        if(ps is None):
            return None
        
        ps = (ps & ~(0x03 << 1)) | ((mode & 0x03) << 1)
        self.write_register(VEML7700_ALS_POWER_SAVE, ps)


    def get_power_save_mode(self):
        ps = self.read_register(VEML7700_ALS_POWER_SAVE)
        if(ps is None):
            return None
        return ((ps >> 1) & 0x03)


    def set_low_threshold(self, value):
        self.write_register(VEML7700_ALS_THRESHOLD_LOW, value)


    def get_low_threshold(self):
        return self.read_register(VEML7700_ALS_THRESHOLD_LOW)


    def set_high_threshold(self, value):
        self.write_register(VEML7700_ALS_THRESHOLD_HIGH, value)


    def get_high_threshold(self):
        return self.read_register(VEML7700_ALS_THRESHOLD_HIGH)


    def read_wait(self):
        time_to_wait = (2 * self.get_integration_time_value())
        time_elapsed = ticks_diff(ticks_ms(), self.last_read)
        remaining = (time_to_wait - time_elapsed)
        if(remaining > 0):
            sleep_ms(remaining)


    def read_als(self, wait=False):
        if(wait):
            self.read_wait()
        raw = self.read_register(VEML7700_ALS_DATA)
        
        if(raw is not None):
            self.last_read = ticks_ms()
        
        return raw


    def read_white(self, wait=False):
        if(wait):
            self.read_wait()
        
        raw = self.read_register(VEML7700_WHITE_DATA)
        
        if(raw is not None):
            self.last_read = ticks_ms()

        return raw


    def get_resolution(self):
        gain_val = self.get_gain_value()
        it_ms = self.get_integration_time_value()

        if(gain_val is None or it_ms is None):
            return None

        return (self._MAX_RES
                * (self._IT_MAX / it_ms)
                * (self._GAIN_MAX / gain_val))


    def _apply_correction(self, lux):
        return (((6.0135e-13 * lux - 9.3924e-9) * lux
                 + 8.1488e-5) * lux + 1.0023) * lux


    def _needs_correction(self, lux):
        return (lux is not None
                and lux > 1000
                and self.get_gain() == VEML7700_GAIN_1_8
                and self.get_integration_time() == VEML7700_IT_25MS)


    def compute_lux(self, raw_als, corrected = False):
        if(raw_als is None):
            return None
        res = self.get_resolution()

        if(res is None):
            return None
        
        lux = res * raw_als
            
        if(corrected):
            lux = self._apply_correction(lux)
        
        return lux


    def read_lux(self, method=VEML_LUX_NORMAL):
        wait = True

        if(method == VEML_LUX_NORMAL_NO_WAIT):
            wait   = False
            method = VEML_LUX_NORMAL
        elif(method == VEML_LUX_CORRECTED_NO_WAIT):
            wait   = False
            method = VEML_LUX_CORRECTED

        if(method == VEML_LUX_NORMAL):
            return self.compute_lux(self.read_als(wait))
        elif(method == VEML_LUX_CORRECTED):
            return self.compute_lux(self.read_als(wait), corrected=True)
        elif(method == VEML_LUX_AUTO):
            return self.auto_lux()
        else:
            return -1


    def auto_lux(self):
        gains     = [VEML7700_GAIN_1_8, VEML7700_GAIN_1_4,
                     VEML7700_GAIN_1,   VEML7700_GAIN_2]
        int_times = [VEML7700_IT_25MS,  VEML7700_IT_50MS,
                     VEML7700_IT_100MS, VEML7700_IT_200MS,
                     VEML7700_IT_400MS, VEML7700_IT_800MS]

        it_index = 2   
        gain_index = 0   

        self.set_gain(gains[gain_index])
        self.set_integration_time(int_times[it_index], wait=True)

        als = self.read_als(wait=False)
        
        if(als is None):
            return None

        if(als > VEML7700_AUTO_BRIGHT_THRESHOLD):
            while(als > VEML7700_AUTO_BRIGHT_THRESHOLD):
                if(it_index == 0):
                    print("VEML7700 auto_lux: unrecoverable saturation")
                    return None
                
                it_index -= 1
                self.set_integration_time(int_times[it_index], wait=True)
                als = self.read_als(wait=False)
                
                if(als is None):
                    return None

        elif(als <= VEML7700_AUTO_DARK_THRESHOLD):
            while(als <= VEML7700_AUTO_DARK_THRESHOLD):
                if(gain_index < len(gains) - 1):
                    gain_index += 1
                    self.set_gain(gains[gain_index])
                    als = self.read_als(wait=True)   

                elif(it_index < len(int_times) - 1):
                    it_index += 1
                    self.set_integration_time(int_times[it_index], wait=True)
                    als = self.read_als(wait=False)  

                else:
                    break

                if(als is None):  
                    return None

        lux = self.compute_lux(als)
        return self._apply_correction(lux) if self._needs_correction(lux) else lux
    