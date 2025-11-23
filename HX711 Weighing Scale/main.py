from machine import Pin
from SH1107 import OLED_13
from utime import sleep_ms
from HX711 import HX711
import math

LED = Pin(25, Pin.OUT)
scale = HX711(26, 27)
oled = OLED_13()


def map_value(value, x_min, x_max, y_min, y_max):
    return (y_min + (((y_max - y_min) / (x_max - x_min)) * (value - x_min)))


while(True):
    LED.value(0)
    oled.fill(oled.BLACK)
    oled.ellipse(33, 63, 25, 25, oled.WHITE)
    oled.hline(0, 10, 127, oled.WHITE)
    oled.text("0", 0, 56, oled.WHITE)
    oled.text("kG", 28, 25, oled.WHITE)
    oled.text("5", 60, 56, oled.WHITE)    
    oled.text("HX711 Scale", 20, 1, oled.WHITE)
    w = scale.get_mass()
    l = map_value(w, 0, 5000, -1.571, 1.571)
    oled.line(33, 63, (33 + int(20 * math.sin(l))), int(63 - (20 * math.cos(l))), oled.WHITE)
    oled.text(str("%4.1f g " % w), 64, 28, oled.WHITE)
    oled.show()
    sleep_ms(100)
    LED.value(1)
