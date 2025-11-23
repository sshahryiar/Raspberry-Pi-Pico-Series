from micropython import const
from machine import Pin, SPI
from utime import sleep_ms, sleep_us
import framebuf


DC_pin = const(8)
CS_pin = const(9)
SCK_pin = const(10)
MOSI_pin = const(11)
RST_pin = const(12)

SH1107_SET_LOWER_COLUMN_ADDRESS = const(0x00)
SH1107_SET_UPPER_COLUMN_ADDRESS = const(0x10)
SH1107_SET_PAGE_MEMORY_ADDRESSING_MODE = const(0x20)
SH1107_SET_VERTICAL_MEMORY_ADDRESSING_MODE = const(0x21)
SH1107_SET_CONSTRAST_CONTROL = const(0x81)
SH1107_SET_DC_DC_OFF_MODE = const(0x8A)
SH1107_SET_DC_DC_ON_MODE = const(0x8B)
SH1107_SET_SEGMENT_REMAP_NORMAL = const(0xA0)
SH1107_SET_SEGMENT_REMAP_REVERSE = const(0xA1)
SH1107_SET_ENTIRE_DISPLAY_OFF = const(0xA4)
SH1107_SET_ENTIRE_DISPLAY_ON = const(0xA5)
SH1107_SET_NORMAL_DISPLAY = const(0xA6)
SH1107_SET_REVERSE_DISPLAY = const(0xA7)
SH1107_SET_MULTIPLEX_RATIO = const(0xA8)
SH1107_SET_DC_DC_CONTROL_MODE = const(0xAD)
SH1107_DISPLAY_OFF = const(0xAE)
SH1107_DISPLAY_ON = const(0xAF)
SH1107_SET_PAGE_ADDRESS = const(0xB0)
SH1107_SET_COMMON_OUTPUT_SCAN_DIRECTION = const(0xC0)
SH1107_SET_DISPLAY_OFFSET = const(0xD3)
SH1107_SET_DISPLAY_CLOCK_FREQUENCY = const(0xD5)
SH1107_SET_PRECHARGE_DISCHARGE_PERIOD = const(0xD9)
SH1107_SET_VCOM_DESELECT_LEVEL = const(0xDB)
SH1107_SET_DISPLAY_START_LINE = const(0xDC)

CMD = False
DAT = True

LOW = False
HIGH = True


class OLED_13(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 128
        self.height = 64
        
        self.WHITE = 1
        self.BLACK = 0
        
        self.cs = Pin(CS_pin, Pin.OUT)
        self.rst = Pin(RST_pin, Pin.OUT)
        self.sck = Pin(SCK_pin, Pin.OUT)
        self.mosi = Pin(MOSI_pin, Pin.OUT)
        
        self.cs(HIGH)
        
        self.spi = SPI(1, 20000_000, polarity = 0, phase = 0,sck = self.sck, mosi = self.mosi,miso = None)
        
        self.dc = Pin(DC_pin, Pin.OUT)
        self.dc(HIGH)
        
        self.buffer = bytearray(self.height * (self.width // 8))
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_HMSB)
        self.init_display()
        
        
    def write(self, value, mode):
        self.dc(mode)
        self.cs(LOW)
        self.spi.write(bytearray([value]))
        self.cs(HIGH)


    def init_display(self):
        self.rst(HIGH)
        sleep_ms(1)
        self.rst(LOW)
        sleep_ms(10)
        self.rst(HIGH)
        
        self.write(SH1107_DISPLAY_OFF, CMD)

        self.write((SH1107_SET_LOWER_COLUMN_ADDRESS | 0x00), CMD)   
        self.write((SH1107_SET_UPPER_COLUMN_ADDRESS | 0x00), CMD)   

        self.write((SH1107_SET_PAGE_ADDRESS | 0x00), CMD)   
      
        self.write(SH1107_SET_DISPLAY_START_LINE, CMD)     
        self.write(0x00, CMD) 
        self.write(SH1107_SET_CONSTRAST_CONTROL, CMD)   
        self.write(0x6F, CMD)    
        self.write(SH1107_SET_VERTICAL_MEMORY_ADDRESSING_MODE, CMD) 
    
        self.write(SH1107_SET_SEGMENT_REMAP_NORMAL, CMD)   
        self.write((SH1107_SET_COMMON_OUTPUT_SCAN_DIRECTION | 0x00), CMD)    
        self.write(SH1107_SET_ENTIRE_DISPLAY_OFF, CMD)   

        self.write(SH1107_SET_NORMAL_DISPLAY, CMD)   
        self.write(SH1107_SET_MULTIPLEX_RATIO, CMD)   
        self.write(0x3F, CMD)   
  
        self.write(SH1107_SET_DISPLAY_OFFSET, CMD)    
        self.write(0x60, CMD)

        self.write(SH1107_SET_DISPLAY_CLOCK_FREQUENCY, CMD)    
        self.write(0x41, CMD)
    
        self.write(SH1107_SET_PRECHARGE_DISCHARGE_PERIOD, CMD)   
        self.write(0x22, CMD)   

        self.write(SH1107_SET_VCOM_DESELECT_LEVEL, CMD)   
        self.write(0x35, CMD)  
    
        self.write(SH1107_SET_DC_DC_CONTROL_MODE, CMD)    
        self.write(SH1107_SET_DC_DC_OFF_MODE, CMD)    
        self.write(SH1107_DISPLAY_ON, CMD)


    def show(self):
        self.write(SH1107_SET_PAGE_ADDRESS, CMD)
        for page in range(0, 64):
            self.column = (63 - page)
            
            self.write((SH1107_SET_LOWER_COLUMN_ADDRESS + (self.column & 0x0F)), CMD)
            self.write((SH1107_SET_UPPER_COLUMN_ADDRESS + (self.column >> 4)), CMD)
            
            for num in range(0, 16):
                self.write((self.buffer[(page * 16) + num]), DAT)

