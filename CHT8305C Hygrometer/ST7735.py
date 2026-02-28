from micropython import const
from machine import Pin, SPI
from time import sleep_ms
import framebuf


ST7735_DC_pin = const(8)
ST7735_CS_pin = const(9)
ST7735_BL_pin = const(13)
ST7735_RST_pin = const(12)
ST7735_SCK_pin = const(10)
ST7735_MOSI_pin = const(11)

ST7735_NOP = const(0x00)
ST7735_SWRESET = const(0x01)
ST7735_RDDID = const(0x04)
ST7735_RDDST = const(0x09)
ST7735_RDDPM = const(0x0A)
ST7735_RDD_MADCTL = const(0x0B)
STT7735_RDD_COLMOD = const(0x0C)
ST7735_RDDIM = const(0x0D)
ST7735_RDDSM = const(0x0E)

ST7735_SLPIN = const(0x10)
ST7735_SLPOUT = const(0x11)
ST7735_PTLON = const(0x12)
ST7735_NORON = const(0x13)

ST7735_INVOFF = const(0x20)
ST7735_INVON = const(0x21)
ST7735_GAMSET = const(0x26)
ST7735_DISPOFF = const(0x28)
ST7735_DISPON = const(0x29)
ST7735_CASET = const(0x2A)
ST7735_RASET = const(0x2B)
ST7735_RAMWR = const(0x2C)
ST7735_RAMRD = const(0x2E)

ST7735_PTLAR = const(0x30)
ST7735_TEOFF = const(0x34)
ST7735_TEON = const(0x35)
ST7735_MADCTL = const(0x36)
ST7735_IDMOFF = const(0x38)
ST7735_IDMON = const(0x39)
ST7735_COLMOD = const(0x3A)

ST7735_RDID1 = const(0xDA)
ST7735_RDID2 = const(0xDB)
ST7735_RDID3 = const(0xDC)
ST7735_RDID4 = const(0xDD)

ST7735_FRMCTR1 = const(0xB1)
ST7735_FRMCTR2 = const(0xB2)
ST7735_FRMCTR3 = const(0xB3)
ST7735_INVCTR = const(0xB4)
ST7735_DISSET5 = const(0xB6)

ST7735_PWCTR1 = const(0xC0)
ST7735_PWCTR2 = const(0xC1)
ST7735_PWCTR3 = const(0xC2)
ST7735_PWCTR4 = const(0xC3)
ST7735_PWCTR5 = const(0xC4)
ST7735_VMCTR1 = const(0xC5)

ST7735_PWCTR6 = const(0xFC)

ST7735_GMCTRP1 = const(0xE0)
ST7735_GMCTRN1 = const(0xE1)

ST7735_MADCTL_MY = const(0x80)
ST7735_MADCTL_MX = const(0x40)
ST7735_MADCTL_MV = const(0x20)
ST7735_MADCTL_ML = const(0x10)
ST7735_MADCTL_RGB = const(0x08)
ST7735_MADCTL_MH = const(0x04)

ST7735_TFT_WIDTH = const(128)
ST7735_TFT_HEIGHT = const(160)

CMD = False
DAT = True

LOW = False
HIGH = True


class TFT18(framebuf.FrameBuffer):
    
    def __init__(self):
        self.width = ST7735_TFT_WIDTH
        self.height = ST7735_TFT_HEIGHT
        
        self.SQUARE = False
        self.ROUND = True

        self.NO = False
        self.YES = True
        
        self.BLACK = const(0x0000)
        self.BLUE = const(0x07E0)
        self.RED = const(0xF800)
        self.GREEN = const(0x001F)
        self.CYAN = const(0x01FE)
        self.MAGENTA = const(0xFFE0)
        self.YELLOW = const(0xF81F)
        self.WHITE = const(0xFFFF)        
        
        self.ST7735_CS = Pin(ST7735_CS_pin, Pin.OUT)
        self.ST7735_BL = Pin(ST7735_BL_pin, Pin.OUT)
        self.ST7735_RST = Pin(ST7735_RST_pin, Pin.OUT)
        self.ST7735_SCK = Pin(ST7735_SCK_pin, Pin.OUT)
        self.ST7735_MOSI = Pin(ST7735_MOSI_pin, Pin.OUT)

        self.ST7735_SPI = SPI(1, 10_000_000, polarity = False, phase = False, sck = self.ST7735_SCK, mosi = self.ST7735_MOSI, miso = None)
    
        self.ST7735_DC = Pin(ST7735_DC_pin, Pin.OUT)
        self.ST7735_DC.value(DAT)
        
        self.TFT_init()
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        
        self.ST7735_CS.value(LOW)
        self.set_RAM_address()
        self.ST7735_CS.value(HIGH)
        
        
    def disp_reset(self):
        self.ST7735_RST.value(HIGH)
        sleep_ms(20)
        self.ST7735_RST.value(LOW)
        sleep_ms(20)
        self.ST7735_RST.value(HIGH)
        sleep_ms(20)
        

    def send(self, value, mode):
        self.ST7735_DC.value(mode)
        self.ST7735_SPI.write(bytearray([value]))
        
        
    def TFT_init(self):
        self.disp_reset()
        self.ST7735_BL.value(HIGH)
        self.ST7735_CS.value(LOW)
        self.send(ST7735_SLPOUT, CMD)
        sleep_ms(120)

        self.send(ST7735_FRMCTR1, CMD)
        self.send(0x01, DAT)
        self.send(0x2C, DAT)
        self.send(0x2D, DAT)
        
        self.send(ST7735_FRMCTR2, CMD)
        self.send(0x01, DAT)
        self.send(0x2C, DAT)
        self.send(0x2D, DAT)
        
        self.send(ST7735_FRMCTR3, CMD)
        self.send(0x01, DAT)
        self.send(0x2C, DAT)
        self.send(0x2D, DAT)
        self.send(0x01, DAT)
        self.send(0x2C, DAT)
        self.send(0x2D, DAT)

        self.send(ST7735_INVCTR, CMD)
        self.send(0x07, DAT)

        self.send(ST7735_PWCTR1, CMD)
        self.send(0xA2, DAT) 
        self.send(0x02, DAT) 
        self.send(0x84, DAT)
        
        self.send(ST7735_PWCTR2, CMD)
        self.send(0xC5, DAT)

        self.send(ST7735_PWCTR3, CMD)
        self.send(0x0A, DAT)
        self.send(0x00, DAT)

        self.send(ST7735_PWCTR4, CMD)
        self.send(0x8A, DAT)
        self.send(0x2A, DAT)

        self.send(ST7735_PWCTR5, CMD)
        self.send(0x8A, DAT)
        self.send(0xEE, DAT)

        self.send(ST7735_VMCTR1, CMD)
        self.send(0x0E, DAT)
        
        self.send(ST7735_GMCTRP1, CMD)
        self.send(0x0F, DAT)
        self.send(0x1A, DAT)
        self.send(0x0F, DAT)
        self.send(0x18, DAT)
        self.send(0x2F, DAT)
        self.send(0x28, DAT)
        self.send(0x20, DAT)
        self.send(0x22, DAT)
        self.send(0x1F, DAT)
        self.send(0x1B, DAT)
        self.send(0x23, DAT)
        self.send(0x37, DAT)
        self.send(0x00, DAT)
        self.send(0x07, DAT)
        self.send(0x02, DAT)
        self.send(0x10, DAT)
        
        self.send(ST7735_GMCTRN1, CMD)
        self.send(0x0F, DAT)
        self.send(0x1B, DAT)
        self.send(0x0F, DAT)
        self.send(0x17, DAT)
        self.send(0x33, DAT)
        self.send(0x2C, DAT)
        self.send(0x29, DAT)
        self.send(0x2E, DAT)
        self.send(0x30, DAT)
        self.send(0x30, DAT)
        self.send(0x39, DAT)
        self.send(0x3F, DAT)
        self.send(0x00, DAT)
        self.send(0x07, DAT)
        self.send(0x03, DAT)
        self.send(0x10, DAT)
                 
        self.send(ST7735_COLMOD, CMD)
        self.send(0x05, DAT)
        
        self.set_rotation(3)
        self.invert_display(False)

        self.send(ST7735_DISPON, CMD)
        self.ST7735_CS.value(HIGH)
        sleep_ms(10)
        
        
    def invert_display(self, state):
        if(state == True):
            self.send(ST7735_INVON, CMD)
        else:
            self.send(ST7735_INVOFF, CMD)
        
        
    def set_rotation(self, rotation):
        self.send(ST7735_MADCTL, CMD)
        
        if(rotation == 0):
            self.send((ST7735_MADCTL_MX | ST7735_MADCTL_MY | ST7735_MADCTL_RGB), DAT)  
            self.width = ST7735_TFT_WIDTH
            self.height = ST7735_TFT_HEIGHT
        
        elif(rotation == 1):
            self.send((ST7735_MADCTL_MY | ST7735_MADCTL_MV | ST7735_MADCTL_RGB), DAT)  
            self.width = ST7735_TFT_HEIGHT
            self.height = ST7735_TFT_WIDTH
            
        elif(rotation == 2):
            self.send(ST7735_MADCTL_RGB, DAT)  
            self.width = ST7735_TFT_WIDTH
            self.height = ST7735_TFT_HEIGHT
        
        else:
            self.send((ST7735_MADCTL_MX | ST7735_MADCTL_MV | ST7735_MADCTL_RGB), DAT)  
            self.width = ST7735_TFT_HEIGHT
            self.height = ST7735_TFT_WIDTH       
        
        
    def set_windows(self, xs, ys, xe, ye):
        xs += 1
        xe += 1
        ys += 2
        ye += 2
    
        self.send(ST7735_CASET, CMD)
        self.send(0x00, DAT)
        self.send(xs, DAT)
        self.send(0x00, DAT)
        self.send(xe, DAT)

        self.send(ST7735_RASET, CMD)
        self.send(0x00, DAT)
        self.send(ys, DAT)
        self.send(0x00, DAT)
        self.send(ye, DAT)

        self.send(ST7735_RAMWR, CMD)


    def colour_generator(self, r, g, b):
        r = (r & 0xF8)
        g = ((g & 0xFC) >> 2)
        b = ((b & 0xF8) >> 3)
        
        colour = r
        colour |= (b << 8)
        colour |= ((g & 0x38) >> 3)
        colour |= ((g & 0x07) << 13)
    
        return colour
        

    def set_RAM_address(self):
        self.set_windows(0, 0, self.width - 1, self.height - 1) 
        
        
    def display(self):
        self.ST7735_CS.value(LOW)
        self.set_RAM_address()    
        self.ST7735_DC.value(DAT)
        self.ST7735_SPI.write(self.buffer)
        self.ST7735_CS.value(HIGH)
