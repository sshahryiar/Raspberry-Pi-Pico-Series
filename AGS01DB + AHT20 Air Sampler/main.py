from machine import Pin, I2C
from AHT20 import AHT20
from AGS01DB import AGS01DB
from SSD1306_I2C import OLED1306
from neopixel import NeoPixel
from time import sleep_ms


pin = Pin(16, Pin.OUT) 
np = NeoPixel(pin, 1)

i2c_fast = I2C(0, scl = Pin(5), sda = Pin(4), freq = 400000)
i2c_slow = I2C(1, scl = Pin(7), sda = Pin(6), freq = 100000)


display = OLED1306(i2c_fast)
rht = AHT20(i2c_slow)
voc = AGS01DB(i2c_slow)


def map_value(v, x_min, x_max, y_min, y_max):
    return int(y_min + (((y_max - y_min) / (x_max - x_min)) * (v - x_min)))


def constrain_value(v, max_v, min_v):
    if(v >= max_v):
        v = max_v
    
    if(v <= min_v):
        v = min_v
        
    return v


def draw_background():
    display.text("Air Sampler", 16, 1, display.WHITE)
    display.rect(0, 20, 60, 10, display.WHITE)
    display.rect(0, 35, 60, 10, display.WHITE)
    display.rect(0, 50, 60, 10, display.WHITE)
    
def draw_bar( position, value):
    v = map_value(value, 0, 100, 0,  60)
    v = constrain_value(v, 100, 0)
    display.fill_rect(0, (position + 2), v, 6, display.WHITE)
 
 
while(True):
   
    display.fill(display.BLACK)
    draw_background()
    
    rh, t, status, crc = rht.read_sensor()
    tvoc = voc.read_sensor()
    
    draw_bar(20, t)
    draw_bar(35, rh)
    draw_bar(50, tvoc)
    
    display.text(str("%3.1f'C " %t), 66, 20, display.WHITE)
    display.text(str("%3.1f" %rh) + "% ", 66, 35, display.WHITE)
    display.text(str("%3.1fppm " %tvoc), 66, 50, display.WHITE)
    
    display.show()
    np[0] = (int(t * 2.55), 0, 0)
    np.write()
    sleep_ms(300)
    np[0] = (0, int(rh * 2.55), 0)
    np.write()
    sleep_ms(300)
    np[0] = (0, 0, int(tvoc * 2.55))
    np.write()
    sleep_ms(300)
    