from micropython import const
from machine import Pin, SPI
from utime import sleep_ms
import framebuf


ST7789_DC_pin = const(8)
ST7789_CS_pin = const(9)
ST7789_BL_pin = const(13)
ST7789_RST_pin = const(12)
ST7789_SCK_pin = const(10)
ST7789_MOSI_pin = const(11)


ST7789_NOP = const(0x00)
ST7789_SWRESET = const(0x01)
ST7789_RDDID = const(0x04)
ST7789_RDDST = const(0x09)
ST7789_RDDPM = const(0x0A)
ST7789_RDD_MADCTL = const(0x0B)
STT7789_RDD_COLMOD = const(0x0C)
ST7789_RDDIM = const(0x0D)
ST7789_RDDSM = const(0x0E)
ST7789_RDDSDR = const(0x0F)

ST7789_SLPIN = const(0x10)
ST7789_SLPOUT = const(0x11)
ST7789_PTLON = const(0x12)
ST7789_NORON = const(0x13)

ST7789_INVOFF = const(0x20)
ST7789_INVON = const(0x21)
ST7789_GAMSET = const(0x26)
ST7789_DISPOFF = const(0x28)
ST7789_DISPON = const(0x29)
ST7789_CASET = const(0x2A)
ST7789_RASET = const(0x2B)
ST7789_RAMWR = const(0x2C)
ST7789_RAMRD = const(0x2E)

ST7789_PTLAR = const(0x30)
ST7789_VSCRDEF = const(0x33)
ST7789_TEOFF = const(0x34)
ST7789_TEON = const(0x35)
ST7789_MADCTL = const(0x36)
ST7789_VSCRSADD = const(0x37)
ST7789_IDMOFF = const(0x38)
ST7789_IDMON = const(0x39)
ST7789_COLMOD = const(0x3A)
ST7789_RAMWRC = const(0x3C)
ST7789_RAMRDC = const(0x3E)

ST7789_TESCAN = const(0x44)
ST7789_RDTESCAN = const(0x45)

ST7789_WRDISBV = const(0x51)
ST7789_RDDISBV = const(0x52)
ST7789_WRCTRLD = const(0x53)
ST7789_RDCTRLD = const(0x54)
ST7789_WRCACE = const(0x55)
ST7789_RDCABC = const(0x56)
ST7789_WRCABCMB = const(0x5E)
ST7789_RDCABCMB = const(0x5F)

ST7789_RDABCSDR = const(0x68)

ST7789_RAMCTRL = const(0xB0)
ST7789_RGBCTRL = const(0xB1)
ST7789_PORCTRL = const(0xB2)
ST7789_FRCTRL1 = const(0xB3)
ST7789_PARCTRL = const(0xB5)
ST7789_GCTRL = const(0xB7)
ST7789_GTADJ = const(0xB8)
ST7789_DGMEN = const(0xBA)
ST7789_VCOMS = const(0xBB)
ST7789_POWSAVE = const(0xBC)
ST7789_DLPOFFSAVE = const(0xBD)

ST7789_LCMCTRL = const(0xC0)
ST7789_IDSET = const(0xC1)
ST7789_VDVVRHEN = const(0xC2)
ST7789_VRHS = const(0xC3)
ST7789_VDVSET = const(0xC4)
ST7789_VCMOFSET = const(0xC5)
ST7789_FRCTR2 = const(0xC6)
ST7789_CABCCTRL = const(0xC7)
ST7789_REGSEL1 = const(0xC8)
ST7789_REGSEL2 = const(0xCA)
ST7789_PWMFRSEL = const(0xCC)

ST7789_PWCTRL1 = const(0xD0)
ST7789_VAPVANEN = const(0xD2)
ST7789_RDID1 = const(0xDA)
ST7789_RDID2 = const(0xDB)
ST7789_RDID3 = const(0xDC)
ST7789_CMD2EN = const(0xDF)

ST7789_PVGAMCTRL = const(0xE0)
ST7789_NVGAMCTRL = const(0xE1)
ST7789_DGMLUTR = const(0xE2)
ST7789_DGMLUTB = const(0xE3)
ST7789_GATECTRL = const(0xE4)
ST7789_SPI2EN = const(0xE7)
ST7789_PWCTRL2 = const(0xE8)
ST7789_EQCTRL = const(0xE9)
ST7789_PROMCTRL = const(0xEC)

ST7789_PROMEN = const(0xFA)
ST7789_NVMSET = const(0xFC)
ST7789_PROMACT = const(0xFE)

ST7789_TFT_WIDTH = const(240)
ST7789_TFT_HEIGHT = const(135)

CMD = False
DAT = True

LOW = False
HIGH = True


class TFT114(framebuf.FrameBuffer):
    
    def __init__(self):
        self.width = ST7789_TFT_WIDTH
        self.height = ST7789_TFT_HEIGHT
        
        self.NO = False
        self.YES = True

        self.BLACK = const(0x0000)
        self.BLUE = const(0x1F00)
        self.RED = const(0x00F8)
        self.GREEN = const(0xE007)
        self.CYAN = const(0xF81F)
        self.MAGENTA = const(0x7FE0)
        self.YELLOW = const(0x07FF)
        self.WHITE = const(0xFFFF)   

        self.ST7789_CS = Pin(ST7789_CS_pin, Pin.OUT)
        self.ST7789_BL = Pin(ST7789_BL_pin, Pin.OUT)
        self.ST7789_RST = Pin(ST7789_RST_pin, Pin.OUT)
        self.ST7789_SCK = Pin(ST7789_SCK_pin, Pin.OUT)
        self.ST7789_MOSI = Pin(ST7789_MOSI_pin, Pin.OUT)

        self.ST7789_SPI = SPI(1, 10000_000, polarity = False, phase = False, sck = self.ST7789_SCK, mosi = self.ST7789_MOSI, miso = None)
        
        self.ST7789_DC = Pin(ST7789_DC_pin, Pin.OUT)

        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        
        self.TFT_init()
        
        
    def disp_reset(self):
        self.ST7789_RST.value(HIGH)
        self.ST7789_RST.value(LOW)
        self.ST7789_RST.value(HIGH)
        self.ST7789_BL.value(HIGH)


    def send(self, value, mode):
        self.ST7789_DC.value(mode)
        self.ST7789_CS.value(LOW)
        self.ST7789_SPI.write(bytearray([value]))
        self.ST7789_CS.value(HIGH)


    def TFT_init(self):
        self.disp_reset()

        self.send(ST7789_PORCTRL, CMD)
        self.send(0x0C, DAT)
        self.send(0x0C, DAT)
        self.send(0x00, DAT)
        self.send(0x33, DAT)
        self.send(0x33, DAT)

        self.send(ST7789_GCTRL, CMD)
        self.send(0x35, DAT)

        self.send(ST7789_VCOMS, CMD)
        self.send(0x19, DAT)

        self.send(ST7789_LCMCTRL, CMD)
        self.send(0x2C, DAT)

        self.send(ST7789_VDVVRHEN, CMD)
        self.send(0x01, DAT)

        self.send(ST7789_VRHS, CMD)
        self.send(0x12, DAT)

        self.send(ST7789_VDVSET, CMD)
        self.send(0x20, DAT)

        self.send(ST7789_FRCTR2, CMD)
        self.send(0x0F, DAT)

        self.send(ST7789_PWCTRL1, CMD)
        self.send(0xA4, DAT)
        self.send(0xA1, DAT)

        self.send(ST7789_PVGAMCTRL, CMD)
        self.send(0xD0, DAT)
        self.send(0x04, DAT)
        self.send(0x0D, DAT)
        self.send(0x11, DAT)
        self.send(0x13, DAT)
        self.send(0x2B, DAT)
        self.send(0x3F, DAT)
        self.send(0x54, DAT)
        self.send(0x4C, DAT)
        self.send(0x18, DAT)
        self.send(0x0D, DAT)
        self.send(0x0B, DAT)
        self.send(0x1F, DAT)
        self.send(0x23, DAT)

        self.send(ST7789_NVGAMCTRL, CMD)
        self.send(0xD0, DAT)
        self.send(0x04, DAT)
        self.send(0x0C, DAT)
        self.send(0x11, DAT)
        self.send(0x13, DAT)
        self.send(0x2C, DAT)
        self.send(0x3F, DAT)
        self.send(0x44, DAT)
        self.send(0x51, DAT)
        self.send(0x2F, DAT)
        self.send(0x1F, DAT)
        self.send(0x1F, DAT)
        self.send(0x20, DAT)
        self.send(0x23, DAT)

        self.send(ST7789_INVON, CMD)

        self.send(ST7789_MADCTL, CMD)
        self.send(0x70, DAT)

        self.send(ST7789_COLMOD, CMD)
        self.send(0x05, DAT)
        
        self.send(ST7789_SLPOUT, CMD)
        self.send(ST7789_DISPON, CMD)


    def colour_generator(self, r, g, b):
        r = (r & 0xF8)
        g = ((g & 0xFC) >> 2)
        b = ((b & 0xF8) >> 3)
        
        colour = r
        colour |= (b << 8)
        colour |= ((g & 0x38) >> 3)
        colour |= ((g & 0x07) << 13)
    
        return colour


    def show(self):
    	self.send(ST7789_CASET, CMD)
    	self.send(0x00, DAT)
        self.send(0x28, DAT)
        self.send(0x01, DAT)
        self.send(0x17, DAT)
        
        self.send(ST7789_RASET, CMD)
        self.send(0x00, DAT)
        self.send(0x35, DAT)
        self.send(0x00, DAT)
        self.send(0xBB, DAT)
        

        self.send(ST7789_RAMWR, CMD)

        self.ST7789_DC.value(DAT)
        self.ST7789_CS.value(LOW)
        self.ST7789_SPI.write(self.buffer)
        self.ST7789_CS.value(HIGH)
