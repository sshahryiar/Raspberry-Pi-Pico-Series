from micropython import const
from time import sleep_ms


# Default I2C Address
DPS310_I2C_ADDRESS = const(0x77)

# Register Definitions
DPS310_REG_PSR_B2 = const(0x00)
DPS310_REG_PSR_B1 = const(0x01)
DPS310_REG_PSR_B0 = const(0x02)
DPS310_REG_TMP_B2 = const(0x03)
DPS310_REG_TMP_B1 = const(0x04)
DPS310_REG_TMP_B0 = const(0x05)
DPS310_REG_PRS_CFG = const(0x06)
DPS310_REG_TMP_CFG = const(0x07)
DPS310_REG_MEAS_CFG = const(0x08)
DPS310_REG_CFG = const(0x09)
DPS310_REG_RESET = const(0x0C)
DPS310_REG_ID = const(0x0D)
DPS310_REG_COEF = const(0x10)         # Coefficient register start
DPS310_REG_COEF_SRC = const(0x28)

# Measurement Configuration (MEAS_CFG) bit masks
DPS310_MEAS_CTRL = const(0x07)        # Measurement control bits
DPS310_SENSOR_RDY = const(0x40)       # Sensor initialization complete
DPS310_COEF_RDY = const(0x80)         # Coefficients ready
DPS310_PRS_RDY = const(0x10)          # Pressure data ready
DPS310_TMP_RDY = const(0x20)          # Temperature data ready

# Temperature Configuration (TMP_CFG) bit masks
DPS310_TMP_EXT = const(0x80)           # Use external temperature sensor
DPS310_TMP_RATE = const(0x70)          # Temperature measurement rate
DPS310_TMP_PRC = const(0x07)           # Temperature oversampling rate

# Pressure Configuration (PRS_CFG) bit masks
DPS310_PRS_RATE = const(0x70)          # Pressure measurement rate
DPS310_PRS_PRC = const(0x07)           # Pressure oversampling rate

# Configuration Register (CFG) bit masks
DPS310_FIFO_EN = const(0x02)           # FIFO enable
DPS310_SPI_MODE = const(0x01)          # SPI mode
DPS310_FIFO_EMPTY = const(0x04)        # FIFO empty
DPS310_FIFO_FULL = const(0x08)         # FIFO full

# Reset command
DPS310_RESET_CMD = const(0x89)

# Valid configuration values
DPS310_VALID_OSR = [1, 2, 4, 8, 16, 32, 64, 128]
DPS310_VALID_RATES = [1, 2, 4, 8, 16, 32, 64, 128]

# Mapping dictionaries
DPS310_VALUE_TO_INDEX = {1: 0, 2: 1, 4: 2, 8: 3, 16: 4, 32: 5, 64: 6, 128: 7}


class DPS310:
    """Driver for the DPS310 pressure and temperature sensor"""
    
    def __init__(self, i2c, address: int = DPS310_I2C_ADDRESS, 
                 temp_osr: int = 64, press_osr: int = 64,
                 temp_rate: int = 64, press_rate: int = 64):
        
        self.i2c = i2c
        self.addr = address

        # Validate and store configuration
        self.temp_osr = self.validate_OSR(temp_osr)
        self.press_osr = self.validate_OSR(press_osr)
        self.temp_rate = self.validate_rate(temp_rate)
        self.press_rate = self.validate_rate(press_rate)

        # Scaling factors for raw values (indexed by OSR)
        self.scaling_factor = [
            524288,   # 2^19 (OSR=1)
            1572864,  # 2^20 + 2^19 (OSR=2)
            3670016,  # 2^21 + 2^20 + 2^19 (OSR=4)
            7864320,  # 2^22 + 2^21 + 2^20 + 2^19 (OSR=8)
            253952,   # OSR=16
            516096,   # OSR=32
            1040384,  # OSR=64
            2088960   # OSR=128
        ]
        
        # Scale indices for current configuration
        self.temp_scale = DPS310_VALUE_TO_INDEX[self.temp_osr]
        self.press_scale = DPS310_VALUE_TO_INDEX[self.press_osr]
        
        # Calibration coefficients
        self.C0 = self.C1 = 0
        self.C00 = self.C10 = 0
        self.C01 = self.C11 = 0
        self.C20 = self.C21 = 0
        self.C30 = 0
        
        # Initialize sensor
        self.init()
        
    
    def validate_OSR(self, osr: int) -> int:
        if osr not in DPS310_VALID_OSR:
            raise ValueError(f"Invalid OSR: {osr}. Must be one of {DPS310_VALID_OSR}")
        return osr


    def validate_rate(self, rate: int) -> int:
        if rate not in DPS310_VALID_RATES:
            raise ValueError(f"Invalid rate: {rate}. Must be one of {DPS310_VALID_RATES}")
        return rate
    
    
    def write(self, reg: int, value: int) -> None:
        try:
            self.i2c.writeto_mem(self.addr, reg, bytes([value]))
        except OSError as e:
            raise OSError(f"DPS310 write failed at 0x{reg:02X}: {e}") from e


    def read_bytes(self, reg: int, length: int) -> bytes:
        try:
            return self.i2c.readfrom_mem(self.addr, reg, length)
        except OSError as e:
            raise OSError(f"DPS310 read failed at 0x{reg:02X}: {e}") from e
    

    def read_uint(self, reg: int, length: int) -> int:
        data = self.read_bytes(reg, length)
        value = 0
        for b in data:
            value = (value << 8) | b
        return value
    

    def wait_for_bit(self, reg: int, mask: int, expected_value: int, 
                     timeout_ms: int = 1000, poll_ms: int = 10) -> bool:
        steps = (timeout_ms // poll_ms)
        for _ in range(steps):
            try:
                value = self.read_uint(reg, 1)
                if (value & mask) == expected_value:
                    return True
            except DPS310Error:
                pass
            sleep_ms(poll_ms)
        return False
    
    
    def init(self):
        cfg_reg = 0x00

        sensor_id = self.read_uint(DPS310_REG_ID, 1)
        
        if(sensor_id != 0x10):
            raise OSError(f"DPS310 not found! ID=0x{sensor_id:02X}")

        self.write(DPS310_REG_RESET, DPS310_RESET_CMD)
        sleep_ms(100)
        
        if not self.wait_for_bit(DPS310_REG_MEAS_CFG, DPS310_SENSOR_RDY, DPS310_SENSOR_RDY):
            raise RuntimeError("Timeout waiting for sensor initialization") 
        
        coef_src = self.read_uint(DPS310_REG_COEF_SRC, 1)
        
        if(coef_src & 0x80):
            use_external_temp = DPS310_TMP_EXT
        else:
            use_external_temp = 0

        # Build configuration values
        press_cfg = (DPS310_VALUE_TO_INDEX[self.press_rate] << 4) | DPS310_VALUE_TO_INDEX[self.press_osr]
        temp_cfg = (use_external_temp | 
                   (DPS310_VALUE_TO_INDEX[self.temp_rate] << 4) | 
                   DPS310_VALUE_TO_INDEX[self.temp_osr])

        # Apply configuration
        self.write(DPS310_REG_PRS_CFG, press_cfg)
        self.write(DPS310_REG_TMP_CFG, temp_cfg)
        self.write(DPS310_REG_MEAS_CFG, 0x00)  # Stop measurements

        if(self.press_osr > 8):
            cfg_reg |= 0x04  # P_SHIFT bit

        if(self.temp_osr > 8):
            cfg_reg |= 0x08  # T_SHIFT bit   

        self.write(DPS310_REG_CFG, cfg_reg)  

        # Wait for coefficients to be ready
        if not self.wait_for_bit(DPS310_REG_MEAS_CFG, DPS310_COEF_RDY, DPS310_COEF_RDY):
            raise RuntimeError("Timeout waiting for coefficients") 
        
        self.read_coefficients()


    def deinit(self):
        self.stop_continuous()
        self.i2c.deinit() 
        

    def read_coefficients(self) -> None:
        data = self.read_bytes(DPS310_REG_COEF, 18)
        
        if(len(data) != 18):
            raise OSError("Failed to read coefficients: unexpected data length") 
        
        # Extract and store coefficients
        self.C0 = self.twos_complement(((self.make_word(data, 0, 2) & 0xFFF0) >> 4), 12)
        self.C1 = self.twos_complement((self.make_word(data, 1, 2) & 0x0FFF), 12)
        self.C00 = self.twos_complement(((self.make_word(data, 3, 3) & 0xFFFFF0) >> 4), 20)
        self.C10 = self.twos_complement((self.make_word(data, 5, 3) & 0x0FFFFF), 20)
        self.C01 = self.twos_complement(self.make_word(data, 8, 2), 16)
        self.C11 = self.twos_complement(self.make_word(data, 10, 2), 16)
        self.C20 = self.twos_complement(self.make_word(data, 12, 2), 16)
        self.C21 = self.twos_complement(self.make_word(data, 14, 2), 16)
        self.C30 = self.twos_complement(self.make_word(data, 16, 2), 16)

    
    def read_raw_from_buffer(self, data):
        P = self.make_word(data, 0, 3)
        P = self.twos_complement(P & 0x00FFFFFF, 24)

        T = self.make_word(data, 3, 3)
        T = self.twos_complement(T & 0x00FFFFFF, 24)

        return T, P
    

    def read_raw(self):
        self.write(DPS310_REG_MEAS_CFG, 0x07)

        if not self.wait_for_bit(DPS310_REG_MEAS_CFG, 
                                  DPS310_PRS_RDY | DPS310_TMP_RDY,
                                  DPS310_PRS_RDY | DPS310_TMP_RDY):
            raise RuntimeError("Timeout waiting for measurement completion")
        
        # Stop measurement
        self.write(DPS310_REG_MEAS_CFG, 0x00)
        
        # Read both pressure and temperature in one transaction
        data = self.read_bytes(DPS310_REG_PSR_B2, 6)
        
        if(len(data) != 6):
            raise OSError("Failed to read pressure and temperature data: unexpected length")
        
        return self.read_raw_from_buffer(data)
        

    def process_raw(self, T_raw, P_raw):
        # Scale
        T_scaled = T_raw / self.scaling_factor[self.temp_scale]
        P_scaled = P_raw / self.scaling_factor[self.press_scale]

        # Temperature
        temperature = (self.C0 * 0.5) + (self.C1 * T_scaled)

        # Pressure
        temp_comp = (T_scaled * self.C01) + (
            T_scaled * P_scaled * (self.C11 + (self.C21 * P_scaled))
        )

        pressure = (
            self.C00
            + P_scaled * (self.C10 + P_scaled * (self.C20 + (self.C30 * P_scaled)))
        )

        pressure += temp_comp
        pressure /= 100.0

        return temperature, pressure

    
    def read_compensated(self):
        T_raw, P_raw = self.read_raw()
        return self.process_raw(T_raw, P_raw)
    
    
    def read_sensor(self):
        try:
            return self.read_compensated()
        except (OSError, ValueError, RuntimeError) as e:
            return None, None
        
        
    def start_continuous(self):
        self.write(DPS310_REG_MEAS_CFG, 0x07)  # Continuous both


    def stop_continuous(self):
        self.write(DPS310_REG_MEAS_CFG, 0x00)


    def read_continuous(self):
        if not self.wait_for_bit(DPS310_REG_MEAS_CFG, 
                                DPS310_PRS_RDY | DPS310_TMP_RDY,
                                DPS310_PRS_RDY | DPS310_TMP_RDY):
            raise RuntimeError("Timeout waiting for data ready")
        
        data = self.read_bytes(DPS310_REG_PSR_B2, 6)
        
        if(len(data) != 6):
            raise OSError("Failed to read pressure and temperature data: unexpected length")

        T, P = self.read_raw_from_buffer(data)
        
        return self.process_raw(T, P)
    

    def read_fifo(self, count):
        results = []
        for _ in range(count):
            if self.wait_for_bit(...):  # Check FIFO not empty
                results.append(self.read_continuous())
        return results
    
    
    def read_altitude(self, sea_level_pressure = 1013.25):
        try:
            _, pressure = self.read_compensated()
            return self.calculate_altitude(pressure, sea_level_pressure)
        except (OSError, ValueError, RuntimeError):
            return None
    

    def calculate_altitude(self, pressure, sea_level_pressure = 1013.25):
        return 44330.0 * (1.0 - (pressure / sea_level_pressure) ** 0.1903)
    
    
    @staticmethod
    def make_word(data: bytes, offset: int, length: int) -> int:
        val = 0
        for i in range(length):
            val = (val << 8) | data[offset + i]
        return val
    
    
    @staticmethod
    def twos_complement(value: int, bits: int) -> int:
        if value & (1 << (bits - 1)):
            value -= (1 << bits)
        return value
