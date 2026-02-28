from machine import Pin, I2C
from ST7735 import TFT18
from CHT8305C import CHT8305C
from time import sleep_ms
from img import image_data, image_width, image_height
import math


LED = Pin(25, Pin.OUT)

i2c = I2C(id = 0, scl = Pin(5), sda = Pin(4), freq = 100000)
rht = CHT8305C(i2c)

tft = TFT18()
tft.fill(tft.BLACK)
tft.display()


def map_value(v, x_min, x_max, y_min, y_max):
    return (y_min + (((y_max - y_min)/(x_max - x_min)) * (v - x_min)))


def constrain(value, min_value, max_value):
    if(value > max_value):
        return max_value
    
    elif(value < min_value):
        return min_value
    
    else:
        return value
    
    
def draw_dial(x_pos, y_pos, value, value_min, value_max, dial_id, colour):
    if(dial_id == 1):
        a = -1.571
        b = 3.142
    else:
        a = -3.000
        b = 3.142
    
    circle(x_pos, y_pos, 3, colour)
    temp = constrain(value, value_min, value_max)
    line = map_value(temp, value_min, value_max, a, b)
    tft.line(x_pos, y_pos, (x_pos + int(20 * math.sin(line))), int(y_pos - (20 * math.cos(line))), colour)
    tft.text(str("%3.2f " %value), (x_pos - 18), (y_pos + 60), tft.WHITE)
    

def draw_dials():
    idx = 0
    for y in range(image_height):
        for x in range(image_width):
            high = image_data[idx]
            low = image_data[idx + 1]
            color = (low << 8) | high  # RGB565
            tft.pixel(x, (y + 20), color)
            idx += 2
    

def circle(xc, yc, r, c):
    tft.hline((xc - r), yc, (r * 2), c)
    for i in range(1, r):
        a = int(math.sqrt((r * r) - (i * i))) 
        tft.hline((xc - a), (yc + i), (a * 2), c) 
        tft.hline((xc - a), (yc - i), (a * 2), c)
    

while(True):
    tft.fill(tft.BLACK)
    tft.text("CHT8305C Hygrometer", 6, 6, tft.CYAN)
    draw_dials()
    
    tft.text("RH/%:", 20, 100, tft.YELLOW)
    tft.text("T/'C:", 100, 100, tft.YELLOW)
    
    draw_dial(39, 55, rht.humidity, 0, 100, 0, tft.BLUE)
    draw_dial(119, 55, rht.temperature, 0, 60, 1, tft.RED)
    
    print("T/'C: " + str(rht.temperature))
    print("RH/%: " + str(rht.humidity))
    
    LED.value(1)
    sleep_ms(500)
    LED.value(0)
    tft.display()    
    sleep_ms(500)
