from micropython import const
from machine import Pin, I2C


MCP23017_I2C_address = const(0x20)


class MCP23017:
    IODIRA = const(0x00)
    IODIRB = const(0x01)
    IPOLA = const(0x02)
    IPOLB = const(0x03)
    GPINTENA = const(0x04)
    GPINTENB = const(0x05)
    DEFVALA = const(0x06)
    DEFVALB = const(0x07)
    INTCONA = const(0x08)
    INTCONB = const(0x09)
    IOCON = const(0x0A)
    GPPUA = const(0x0C)
    GPPUB = const(0x0D)
    INTFA = const(0x0E)
    INTFB = const(0x0F)
    INTCAPA = const(0x10)
    INTCAPB = const(0x11)
    GPIOA = const(0x12)
    GPIOB = const(0x13)
    OLATA = const(0x14)
    OLATB = const(0x15)


    def __init__(self, i2c):
        self.i2c = i2c
        self.write(self.IOCON, 0x18);
        self.write(self.IODIRA, 0x00);
        self.write(self.IODIRB, 0x00);
        self.write(self.GPIOA, 0x00);
        self.write(self.GPIOB, 0x00);


    def write(self, reg, value):
        if not type(value) is bytearray:
            value = bytearray([value])
        
        self.i2c.writeto_mem(MCP23017_I2C_address, reg, value)
        
        
    def read(self, reg):
        retval = self.i2c.readfrom_mem(MCP23017_I2C_address, reg, 1)    
        return retval[0]
