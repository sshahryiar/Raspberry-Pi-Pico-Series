from micropython import const
from time import sleep_ms


MCU90615_TX_FRAME_START = const(0xA5)
MCU90615_RX_FRAME_START = const(0x5A)
MCU90615_QUERY_MEASUREMENT_MODE = const(0x15)
MCU90615_CONTINUOUS_MEASUREMENT_MODE = const(0x45)
MCU90615_BAUDRATE_9600 = const(0xAE)
MCU90615_BAUDRATE_115200 = const(0xAF)
MCU90615_AUTO_DATA_OUT_ON_POWERUP = const(0x51)
MCU90615_NO_AUTO_DATA_OUT_ON_POWERUP = const(0x52)
MCU90615_TEMPERATURE_DATA_FRAME = const(0x45)

MCU90615_number_of_bytes_to_send = const(0x03)
MCU90615_number_of_bytes_to_read = const(0x09)


class MCU90615():
    def __init__(self, _uart):
        self.tx_data_frame = bytearray(MCU90615_number_of_bytes_to_send)
        self.rx_data_frame = bytearray(MCU90615_number_of_bytes_to_read)
        self.uart = _uart
        self.init()
        
        
    def init(self):
        self.set_baud(0)
        self.set_mode(0)
        self.set_auto_data_output(0)
    
    
    def generate_CRC(self, value, length):
        s = 0
        crc_value = 0
        
        for s in range (0, length):
            crc_value += value[s]
        
        return (crc_value & 0x00FF)       
    
    
    def set_baud(self, option):
        if(option):
            self.tx_data_frame[0] = MCU90615_TX_FRAME_START
            self.tx_data_frame[1] = MCU90615_BAUDRATE_9600
            self.tx_data_frame[2] = self.generate_CRC(tx_data_frame, 2)
        else:
            self.tx_data_frame[0] = MCU90615_TX_FRAME_START
            self.tx_data_frame[1] = MCU90615_BAUDRATE_115200
            self.tx_data_frame[2] = self.generate_CRC(self.tx_data_frame, 2)
            
        self.uart.write(self.tx_data_frame)
        
        
    def set_mode(self, option):
        if(option):
            self.tx_data_frame[0] = MCU90615_TX_FRAME_START
            self.tx_data_frame[1] = MCU90615_CONTINUOUS_MEASUREMENT_MODE
            self.tx_data_frame[2] = self.generate_CRC(tx_data_frame, 2)
        else:
            self.tx_data_frame[0] = MCU90615_TX_FRAME_START
            self.tx_data_frame[1] = MCU90615_QUERY_MEASUREMENT_MODE
            self.tx_data_frame[2] = self.generate_CRC(self.tx_data_frame, 2)

        self.uart.write(self.tx_data_frame)
        
        
    def set_auto_data_output(self, option):
        if(option):
            self.tx_data_frame[0] = MCU90615_TX_FRAME_START
            self.tx_data_frame[1] = MCU90615_AUTO_DATA_OUT_ON_POWERUP
            self.tx_data_frame[2] = self.generate_CRC(tx_data_frame, 2)
        else:
            self.tx_data_frame[0] = MCU90615_TX_FRAME_START
            self.tx_data_frame[1] = MCU90615_NO_AUTO_DATA_OUT_ON_POWERUP
            self.tx_data_frame[2] = self.generate_CRC(self.tx_data_frame, 2)
            
        self.uart.write(self.tx_data_frame)
        
        
    def read(self):
        Ta = 0
        To = 0
        self.set_mode(0)
        sleep_ms(100)
        
        if(self.uart.any() > 0):
            self.rx_data_frame = self.uart.read()
            
        if((self.rx_data_frame[0] == MCU90615_RX_FRAME_START) and (self.rx_data_frame[1] == MCU90615_RX_FRAME_START)):
            if((self.rx_data_frame[2] == MCU90615_TEMPERATURE_DATA_FRAME) and (self.rx_data_frame[3] == 0x04)):
                 if(self.rx_data_frame[8] == self.generate_CRC(self.rx_data_frame, 8)):
                     To = self.make_word(self.rx_data_frame[4], self.rx_data_frame[5])
                     To /= 100.0
                     Ta = self.make_word(self.rx_data_frame[6], self.rx_data_frame[7])
                     Ta /= 100.0
                    
                     return To, Ta
        
        else:
            return 0, 0
        
        
    @staticmethod
    def make_word(msb, lsb):
        return ((msb << 8) | lsb)
            