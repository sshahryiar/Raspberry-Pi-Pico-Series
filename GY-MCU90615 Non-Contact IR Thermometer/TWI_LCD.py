from micropython import const
from MCP23017 import MCP23017
from time import sleep_ms


"""

Pin out of MCP23017 to LCD

DIYMORE MCP23017 1602/2004/12864 I2C LCD Driver Module Pin Mapping
------------------------------------------------------------------

GPIOA
    A7   A6   A5   A4   A3   A2   A1   A0
    RS   RW   EN   X    X    X    GND  X

GPIOB
    B7   B6   B5   B4   B3   B2   B1   B0
    D7   D6   D5   D4   D3   D2   D1   D0


ROBOTDYN MCP23017 1602/2004/12864 I2C LCD Driver Module Pin Mapping
-------------------------------------------------------------------

GPIOA
    A7   A6   A5   A4   A3   A2   A1   A0
    EN   RW   RS   X    L-   L+   X    X

GPIOB
    B7   B6   B5   B4   B3   B2   B1   B0
    D7   D6   D5   D4   D3   D2   D1   D0

"""


LCD_clear_display = const(0x01)
LCD_goto_home = const(0x02)

LCD_cursor_direction_inc = const(0x06)
LCD_cursor_direction_dec = const(0x04)
LCD_display_shift = const(0x05)
LCD_display_no_shift = const(0x04)

LCD_display_on = const(0x0C)
LCD_display_off = const(0x0A)
LCD_cursor_on = const(0x0A)
LCD_cursor_off = const(0x08)
LCD_blink_on = const(0x09)
LCD_blink_off = const(0x08)

LCD_8_pin_interface = const(0x30)
LCD_4_pin_interface = const(0x20)
LCD_2_row_display = const(0x28)
LCD_1_row_display = const(0x20)
LCD_5x10_dots = const(0x60)
LCD_5x7_dots = const(0x20)

LCD_line_1_y_pos = const(0x00)
LCD_line_2_y_pos = const(0x40)
LCD_line_3_y_pos = const(0x14)
LCD_line_4_y_pos = const(0x54)

LCD_DAT = const(1)
LCD_CMD = const(0)


class TWI_LCD:
    DIYMORE = const(0)
    ROBOTDYN = const(1)

    LCD_8_bit_mode = const(0)
    LCD_4_bit_mode = const(1)

    def __init__(self, i2c, model = DIYMORE, mode = LCD_8_bit_mode):
        self.lcd_ctrl = 0x00
        self.mode = mode
        self.model = model
        self.io = MCP23017(i2c)

        self.init()


    def init(self):
        if(self.mode == self.LCD_8_bit_mode):
            self.send((LCD_8_pin_interface | LCD_2_row_display | LCD_5x7_dots), LCD_CMD)
            sleep_ms(10)
            self.send((LCD_8_pin_interface | LCD_2_row_display | LCD_5x7_dots), LCD_CMD)
            sleep_ms(10)
            self.send((LCD_8_pin_interface | LCD_2_row_display | LCD_5x7_dots), LCD_CMD)
        else:
            self.send((LCD_4_pin_interface | LCD_2_row_display | LCD_5x7_dots), LCD_CMD)
            sleep_ms(10)
            self.send((LCD_4_pin_interface | LCD_2_row_display | LCD_5x7_dots), LCD_CMD)
            sleep_ms(10)
            self.send((LCD_4_pin_interface | LCD_2_row_display | LCD_5x7_dots), LCD_CMD)

        self.send((LCD_display_on | LCD_cursor_off | LCD_blink_off), LCD_CMD)
        self.send((LCD_clear_display), LCD_CMD)
        self.send((LCD_cursor_direction_inc | LCD_display_no_shift), LCD_CMD)


    def send(self, value, type):
        if(type == LCD_CMD):
            if(self.model == self.DIYMORE):
                self.lcd_ctrl &= 0x7F
            else:
                self.lcd_ctrl &= 0xDF
        else:
            if(self.model == self.DIYMORE):     
                self.lcd_ctrl |= 0x82
            else:
                self.lcd_ctrl |= 0x20

        self.io.write(self.io.GPIOA, self.lcd_ctrl)
        self.write(value)
        sleep_ms(1)


    def clear_home(self):
        self.send(LCD_clear_display, LCD_CMD)
        self.send(LCD_goto_home, LCD_CMD)


    def gotoxy(self, x_pos, y_pos):
        if(y_pos == 1):
            self.send((0x80 | (LCD_line_2_y_pos + x_pos)), LCD_CMD)
        elif(y_pos == 2):
            self.send((0x80 | (LCD_line_3_y_pos + x_pos)), LCD_CMD)
        elif(y_pos == 3):
            self.send((0x80 | (LCD_line_4_y_pos + x_pos)), LCD_CMD)
        else:
            self.send((0x80 | (LCD_line_1_y_pos + x_pos)), LCD_CMD)


    def toggle_EN(self):
        if(self.model == self.DIYMORE):
            self.lcd_ctrl |= 0x22
        else:
            self.lcd_ctrl |= 0x80

        self.io.write(self.io.GPIOA, self.lcd_ctrl)
        sleep_ms(1)

        if(self.model == self.DIYMORE):
            self.lcd_ctrl &= 0xDF
        else:
            self.lcd_ctrl &= 0x7F

        self.io.write(self.io.GPIOA, self.lcd_ctrl)
        sleep_ms(1)


    def write(self, value):
        if(self.mode == self.LCD_8_bit_mode):
            self.io.write(self.io.GPIOB, value)
            self.toggle_EN()
        else:
            self.io.write(self.io.GPIOB, (value & 0xF0))
            self.toggle_EN()
            self.io.write(self.io.GPIOB, ((value & 0x0F) << 0x04))
            self.toggle_EN()		


    def put_chr(self, x_pos, y_pos, ch):
        self.gotoxy(x_pos, y_pos)
        self.send(ord(ch), LCD_DAT)
            

    def text(self, x_pos, y_pos, ch_string):        
        for chr in ch_string:
            self.put_chr(x_pos, y_pos, chr)
            x_pos += 1


    def load_custom_symbol(self):
    	i = 0
    	custom_symbol = [
    					 0x00, 0x06, 0x09, 0x09, 0x06, 0x00, 0x00, 0x00
    					]
    	self.send(0x40, LCD_CMD)

    	for i in range(len(custom_symbol)):
    		self.send(custom_symbol[i], LCD_DAT)

    	self.send(0x80, LCD_CMD)


    def print_custom_symbol(self, x_pos, y_pos, index):
    	self.gotoxy(x_pos, y_pos)
    	self.send(index, LCD_DAT)
