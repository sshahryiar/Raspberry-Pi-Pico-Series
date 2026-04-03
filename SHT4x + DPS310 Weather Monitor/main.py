from machine import I2C, Pin
from SHT4x import SHT4x, SHT4X_MEAS_MED_REP
from DPS310 import DPS310
from ST7789 import TFT114
from img import image_data, image_width, image_height
from time import sleep_ms
import math


LED = Pin(25, Pin.OUT)
display = TFT114()
i2c = I2C(1, scl = Pin(3), sda = Pin(2), freq = 100000)


hygrometer = SHT4x(i2c)
barometer = DPS310(i2c)


def map_value(v, x_min, x_max, y_min, y_max):
    return (y_min + (((y_max - y_min)/(x_max - x_min)) * (v - x_min)))


def constrain(value, min_value, max_value):
    if(value > max_value):
        return max_value
    
    elif(value < min_value):
        return min_value
    
    else:
        return value
    
    
def circle(xc, yc, r, c):
    display.hline((xc - r), yc, (r * 2), c)
    for i in range(1, r):
        a = int(math.sqrt((r * r) - (i * i))) 
        display.hline((xc - a), (yc + i), (a * 2), c) 
        display.hline((xc - a), (yc - i), (a * 2), c)
    
    
def draw_dials(x_offset, y_offset):
    idx = 0
    for y in range(image_height):
        for x in range(image_width):
            high = image_data[idx]
            low = image_data[idx + 1]
            color = (low << 8) | high  # RGB565
            display.pixel((x + x_offset), (y + y_offset), color)
            idx += 2


def draw_dial(x_pos, y_pos, value, value_min, value_max, colour):    
    y_pos = (y_pos + 15)
    circle(x_pos, y_pos, 5, colour)
    temp = constrain(value, value_min, value_max)
    line = map_value(temp, value_min, value_max, -1.35, -0.15)
    display.line(x_pos, y_pos, (x_pos + int(53 * math.sin(line))), int(y_pos - (53 * math.cos(line))), colour)
    display.text(str("%4.2f " %value), (x_pos - 52), (y_pos + 40), colour)


while(True):
    tb, p = barometer.read_sensor()
    th, rh = hygrometer.read_sensor()
    
    if((tb != None) and (th != None) and (p != None) and (rh != None)):
        LED.on()
        tc = ((tb + th) / 2.0)
        
        print("Temp. Baro/'C: " + str("%2.2f" %tb))
        print("Temp. Hygr/'C: " + str("%2.2f" %th))
        print("Temp. Avg./'C: " + str("%2.2f" %tc))
        print("R. Humidity/%: " + str("%2.2f" %rh))
        print("Pressure/mBar: " + str("%4.2f" %p))
        
        display.fill(display.BLACK)
        display.text("SHT40 & DPS310 Weather Monitor", 0, 2, display.WHITE)
        draw_dials(0, 15)
        draw_dials(81, 15)
        draw_dials(162, 15)
        
        display.text("T.Avg./'C", 0, 106, display.RED)
        display.text("R. Hum./%", 80, 106, display.BLUE)
        display.text("Prs./mBar", 168, 106, display.MAGENTA)
        
        draw_dial(67, 67, tc, 0, 100, display.RED)
        draw_dial(148, 67, rh, 0, 100, display.BLUE)
        draw_dial(228, 67, p, 750, 1500, display.MAGENTA)
        display.show()

    else:
        print("Read failed")
        
    sleep_ms(400)
    LED.off()
    sleep_ms(600)
    