from micropython import const
from utime import sleep_ms
import framebuf  


disp_width                                   = const(128)
disp_height                                  = const(64)
disp_pages                                   = const((disp_height >> 3))

# Constants
SSD1306_I2C_address                          = const(0x3C)

SSD1306_SET_CONTRAST                         = const(0x81)
SSD1306_DISPLAY_ALL_ON_RESUME                = const(0xA4)
SSD1306_DISPLAY_ALL_ON                       = const(0xA5)
SSD1306_NORMAL_DISPLAY                       = const(0xA6)
SSD1306_INVERT_DISPLAY                       = const(0xA7)
SSD1306_DISPLAY_OFF                          = const(0xAE)
SSD1306_DISPLAY_ON                           = const(0xAF)
SSD1306_SET_DISPLAY_OFFSET                   = const(0xD3)
SSD1306_SET_COM_PINS                         = const(0xDA)
SSD1306_SET_VCOM_DETECT                      = const(0xDB)
SSD1306_SET_DISPLAY_CLOCK_DIV                = const(0xD5)
SSD1306_SET_PRECHARGE                        = const(0xD9)
SSD1306_SET_MULTIPLEX                        = const(0xA8)
SSD1306_SET_LOW_COLUMN                       = const(0x00)
SSD1306_SET_HIGH_COLUMN                      = const(0x10)
SSD1306_SET_START_LINE                       = const(0x40)
SSD1306_MEMORY_MODE                          = const(0x20)
SSD1306_COLUMN_ADDR                          = const(0x21)
SSD1306_PAGE_ADDR                            = const(0x22)
SSD1306_COM_SCAN_INC                         = const(0xC0)
SSD1306_COM_SCAN_DEC                         = const(0xC8)
SSD1306_SEG_REMAP                            = const(0xA0)
SSD1306_CHARGE_PUMP                          = const(0x8D)
SSD1306_EXTERNAL_VCC                         = const(0x01)
SSD1306_SWITCH_CAP_VCC                       = const(0x02)

# Scrolling constants
SSD1306_ACTIVATE_SCROLL                      = const(0x2F)
SSD1306_DEACTIVATE_SCROLL                    = const(0x2E)
SSD1306_SET_VERTICAL_SCROLL_AREA             = const(0xA3)
SSD1306_RIGHT_HORIZONTAL_SCROLL              = const(0x26)
SSD1306_LEFT_HORIZONTAL_SCROLL               = const(0x27)
SSD1306_VERTICAL_AND_RIGHT_HORIZONTAL_SCROLL = const(0x29)
SSD1306_VERTICAL_AND_LEFT_HORIZONTAL_SCROLL  = const(0x2A)


class OLED1306(framebuf.FrameBuffer):

    def __init__(self, _i2c, _i2c_addr = SSD1306_I2C_address):
        self.width = disp_width
        self.height = disp_height
        self._pages = disp_pages
        
        self.WHITE = 1
        self.BLACK = 0
        
        self.i2c = _i2c
        self.i2c_addr = _i2c_addr

        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]   
        
        self.buffer = bytearray(self._pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()
        sleep_ms(100)


    def write_command(self, cmd):
        self.temp[0] = 0x80  
        self.temp[1] = cmd
        self.i2c.writeto(self.i2c_addr, self.temp)

    
    def write_data(self, value):
        self.write_list[1] = value
        self.i2c.writevto(self.i2c_addr, self.write_list)


    def init_display(self):
        self.write_command(SSD1306_DISPLAY_OFF)
        self.write_command(SSD1306_SET_DISPLAY_CLOCK_DIV)
        self.write_command(0x80)

        self.write_command(SSD1306_SET_MULTIPLEX)
        self.write_command((self.height - 1))

        self.write_command(SSD1306_SET_DISPLAY_OFFSET)
        self.write_command(0x00)

        self.write_command((SSD1306_SET_START_LINE | 0x00))
   
        self.write_command(SSD1306_CHARGE_PUMP)
        self.write_command(0x14)  # 0x10  # 0x14

        self.write_command(SSD1306_MEMORY_MODE)
        self.write_command(0x00)

        self.write_command((SSD1306_SEG_REMAP | 0x01))
        self.write_command(SSD1306_COM_SCAN_DEC)
        self.write_command(SSD1306_SET_COM_PINS)
        self.write_command(0x12)

        self.write_command(SSD1306_SET_CONTRAST)
        self.write_command(0xCF) # 0x9F # 0xCF

        self.write_command(SSD1306_SET_PRECHARGE)
        self.write_command(0xF1) # 0x22 # 0xF1

        self.write_command(SSD1306_SET_VCOM_DETECT)
        self.write_command(0x40)

        self.write_command(SSD1306_DISPLAY_ALL_ON_RESUME)
        self.write_command(SSD1306_NORMAL_DISPLAY)
        self.write_command(SSD1306_DISPLAY_ON)


    def show(self):
        x0 = 0
        x1 = (self.width - 1)
        if (self.width == 64):
            # displays with width of 64 pixels are shifted by 32
            x0 += 32
            x1 += 32
            
        self.write_command(SSD1306_COLUMN_ADDR)
        self.write_command(x0)
        self.write_command(x1)
        self.write_command(SSD1306_PAGE_ADDR)
        self.write_command(0x00)
        self.write_command((self._pages - 1))
        self.write_data(self.buffer)
