from machine import Pin
from time import ticks_ms, sleep_ms


class HX711:
    
    def __init__(self, _dout_pin, _sck_pin, _sck_pulses = 25, _scale_factor = 449.0, _timeout = 1000):
        self.dout = Pin(_dout_pin, Pin.IN, Pin.PULL_UP)
        self.sck = Pin(_sck_pin, Pin.OUT)
        self.scale_factor = _scale_factor
        self.sck_pulses = _sck_pulses
        
        if(self.sck_pulses == 26):
            self.scale_factor = (self.scale_factor / 4)
        elif(self.sck_pulses == 27):
            self.scale_factor = (self.scale_factor / 2)
        
        self.timeout = _timeout
        self.offset = 0
        self.reset()
        self.noload_reading()
    
    
    def get_raw(self):
        i = 24
        value = 0
        
        t0 = ticks_ms()
        self.sck.value(0)
        while(self.dout.value() and ((ticks_ms() - t0) < self.timeout)):
            pass
        
        while(i > 0):
            self.sck.value(1)
            value <<= 1
            self.sck.value(0)
            
            if(self.dout.value()):
                value += 1
                
            i -= 1
        
        extra_pulses = (self.sck_pulses - 24)
        
        for i in range(0, extra_pulses):
            self.sck.value(1)
            self.sck.value(0)
        
        if(value & 0x800000):
            value -= 0x1000000
        
        return value
    
    
    def avg_reading(self, samples):
        i = samples
        value = 0;
        self.power_up()
        
        while(i > 0):
            value += self.get_raw()
            i -= 1
        
        value /= samples
        value -= self.offset
        
        self.power_down()
        
        return abs(value)
    
    
    def noload_reading(self):
        self.offset = self.avg_reading(25) 
        
    
    def get_mass(self):
        value = self.avg_reading(10) / self.scale_factor
        
        if((value <= 0) or (value > 5000)):
            value = 0
        
        return value
    
    
    def reset(self):
        self.power_down()
        self.power_up()
        sleep_ms(400)
    

    def power_down(self):
        self.sck.value(1)
        sleep_ms(1)  # Minimum 60μs required
    

    def power_up(self):
        self.sck.value(0)