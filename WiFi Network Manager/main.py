"""
WiFi Manager
Author: Shawon M. Shahryiar
Default SSID: MicroPython-AP Password: 12345678
"""


import WifiManager
from machine import Pin

LED = Pin("LED", Pin.OUT)


#WifiManager.reset()
# Call the manager
LED.on()
WifiManager.run()
LED.off

print("WiFi Ready!")

