from machine import I2C, Pin
from time import sleep_ms
from TWI_LCD import TWI_LCD
from VEML7700 import VEML7700


LED = Pin(25, Pin.OUT)
i2c = I2C(0, scl = Pin(5), sda = Pin(4), freq = 100000)


lcd = TWI_LCD(i2c)
veml = VEML7700(i2c)


lcd.clear_home()
lcd.text(0, 0, "Total Lx:")
lcd.text(0, 1, "White Lx:")


if veml.init():
    print("VEML7700 initialized successfully")
else:
    print("Failed to initialize VEML7700")
    raise RuntimeError("Sensor not found")


while(True):
    LED.value(1)
    lux = veml.read_lux()
    white = veml.read_white()
    
    lcd.text(10, 0, str("%6d " %lux))
    lcd.text(10, 1, str("%6d " %white))

    print("Lux  : " + str("%6d " %veml.auto_lux()))
    print("Total: " + str("%6d " %lux))
    print("White: " + str("%6d " %white) + "\r\n")

    sleep_ms(500)
    LED.value(0)
    sleep_ms(500)