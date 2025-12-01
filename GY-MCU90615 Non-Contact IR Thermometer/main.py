from machine import UART, I2C, Pin
from MCU90615 import MCU90615
from TWI_LCD import TWI_LCD
from utime import sleep_ms


LED = Pin(25, Pin.OUT)
i2c = I2C(0, scl = Pin(5), sda = Pin(4), freq = 400000)
uart = UART(1, baudrate = 115200, bits = 8, parity = None, stop = 1, tx = Pin(8), rx = Pin(9))


lcd = TWI_LCD(i2c)
temp = MCU90615(uart)


lcd.clear_home()
lcd.load_custom_symbol()

lcd.text(0, 0, "T.obj/ C:")
lcd.print_custom_symbol(6, 0, 0)
lcd.text(0, 1, "T.amb/ C:")
lcd.print_custom_symbol(6, 1, 0)


while(True):
    LED.value(1)
    To, Ta = temp.read()
    lcd.text(11, 0, str("%3.2f " %To))
    lcd.text(11, 1, str("%3.2f " %Ta))
    print("T.obj/'C: " + str("%3.2f " %To))
    print("T.amb/'C: " + str("%3.2f " %Ta) + "\r\n")
    sleep_ms(500)
    LED.value(0)
    sleep_ms(500)