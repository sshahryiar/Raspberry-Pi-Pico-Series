from machine import Pin
from rp2 import PIO, StateMachine, asm_pio
from time import ticks_ms, sleep_ms


class HX711_PIO:
    @staticmethod
    def create_pio_program(pulses):
        
        @asm_pio(set_init = PIO.OUT_HIGH, in_shiftdir = PIO.SHIFT_LEFT, autopush = True, push_thresh = 24)
        def read_HX711():
            set(pins, 0) [1]
            wait(0, pin, 0)
            set(x, 23)
            label("24_bit_loop")
            set(pins, 1) [1]
            set(pins, 0) [1]
            in_(pins, 1)
            jmp(x_dec, "24_bit_loop")
            
            set(y, (pulses - 1))          
            label("extra_pulse_loop")
            set(pins, 1) [1]    
            set(pins, 0) [1]     
            jmp(y_dec, "extra_pulse_loop") 
         
        return read_HX711



    def __init__(self, dout_pin, sck_pin, sck_pulses = 25, _scale_factor = 1.757, _timeout = 1000, sm_id = 0, freq = 1000000):
        self.dout = Pin(dout_pin, Pin.IN, Pin.PULL_UP)
        self.sck = Pin(sck_pin, Pin.OUT)
        self.reset()
        self.scale_factor = _scale_factor
        self.timeout = _timeout
        self.offset = 0
        
        if(sck_pulses == 26):
            self.scale_factor = (self.scale_factor / 4)
        elif(sck_pulses == 27):
            self.scale_factor = (self.scale_factor / 2)
        
        pio_program = self.create_pio_program((sck_pulses - 24))
        
        self.sm = StateMachine(sm_id, pio_program,
                               freq = freq,
                               in_base = self.dout,
                               set_base = self.sck)
        
        self.sm.active(1)
        self.reset()
        self.noload_reading()


    def reset(self):
        self.power_down()
        self.power_up()
        sleep_ms(400)
    

    def power_down(self):
        self.sck.value(1)
        sleep_ms(1)  
    

    def power_up(self):
        self.sck.value(0)


    def get_raw(self):
        t0 = ticks_ms()
        while((self.sm.rx_fifo() > 0) and ((ticks_ms() - t0) > self.timeout)):
            self.sm.get()
        
        t0 = ticks_ms()
        while((self.sm.rx_fifo() == 0) and ((ticks_ms() - t0) > self.timeout)):
            pass
        
        raw = (self.sm.get() >> 8)

        if(raw & 0x800000):
            raw -= 0x1000000
            
        return raw
    

    def avg_reading(self, samples):
        i = samples
        value = 0
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
        value = (self.avg_reading(10) / self.scale_factor)
        
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