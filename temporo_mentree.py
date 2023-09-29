# Imports
import logging
import time
import math
import RPi.GPIO as GPIO
import ADC0832_1
import ADC0832_2
import threading
import smbus

GPIO.setmode(GPIO.BCM)

def delay(timer):
    time.sleep(timer/1000.0)

def delayMicroseconds(timer):
    time.sleep(timer/1000000.0)

class Screen():

    enable_mask = 1<<2
    rw_mask = 1<<1
    rs_mask = 1<<0
    backlight_mask = 1<<3

    data_mask = 0x00

    def __init__(self, cols = 16, rows = 2, addr=0x27, bus=1):
        self.cols = cols
        self.rows = rows        
        self.bus_num = bus
        self.bus = smbus.SMBus(self.bus_num)
        self.addr = addr
        self.display_init()

    def enable_backlight(self):
        self.data_mask = self.data_mask|self.backlight_mask

    def disable_backlight(self):
        self.data_mask = self.data_mask& ~self.backlight_mask

    def display_data(self, *args):
        self.clear()
        for line, arg in enumerate(args):
            self.cursorTo(line, 0)
            self.println(arg[:self.cols].ljust(self.cols))

    def cursorTo(self, row, col):
        offsets = [0x00, 0x40, 0x14, 0x54]
        self.command(0x80|(offsets[row]+col))

    def clear(self):
        self.command(0x10)

    def println(self, line):
        for char in line:
            self.print_char(char)     

    def print_char(self, char):
        char_code = ord(char)
        self.send(char_code, self.rs_mask)
    
    def display_init(self):
        delay(1.0)
        self.write4bits(0x30)
        delay(4.5)
        self.write4bits(0x30)
        delay(4.5)
        self.write4bits(0x30)
        delay(0.15)
        self.write4bits(0x20)
        self.command(0x20|0x08)
        self.command(0x04|0x08, delay=80.0)
        self.clear()
        self.command(0x04|0x02)
        delay(3)

    def command(self, value, delay = 50.0):
        self.send(value, 0)
        delayMicroseconds(delay)

    def send(self, data, mode):
        self.write4bits((data & 0xF0)|mode)
        self.write4bits((data << 4)|mode)

    def write4bits(self, value):
        value = value & ~self.enable_mask
        self.expanderWrite(value)
        self.expanderWrite(value | self.enable_mask)
        self.expanderWrite(value)        

    def expanderWrite(self, data):
        self.bus.write_byte_data(self.addr, 0, data|self.data_mask)

# Thermistat Components
BLUE_BUTTON = 16
RED_BUTTON = 26
BUZZER = 25

# Photoresistor Components
RGB_RED = 6
RGB_BLUE = 5
RGB_GREEN = 13

# Global Variables
is_alarm_active = False
is_activate = False
is_flashing = False
max_heat = 30
current_heat = 0
light_status = "Off"
stop_flag = False

def init():
    ADC0832_1.setup()
    ADC0832_2.setup()

    GPIO.setup(BLUE_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(RED_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUZZER, GPIO.OUT)
    GPIO.setup(RGB_RED, GPIO.OUT)
    GPIO.setup(RGB_BLUE, GPIO.OUT)
    GPIO.setup(RGB_GREEN, GPIO.OUT)

    GPIO.output(RGB_RED, GPIO.HIGH)
    GPIO.output(RGB_BLUE, GPIO.HIGH)
    GPIO.output(RGB_GREEN, GPIO.HIGH)
    GPIO.output(BUZZER, GPIO.LOW)

def thermistorLogic():
    global is_alarm_active
    global is_activate
    global max_heat
    global current_heat

    R25 = 10000
    T25 = 25 + 273.15
    B = 3455

    res = ADC0832_1.getADC(1)
    Vr = 3.3 * float(res) / 255

    if (Vr == 0):
        Vr = 0.1

    Rt = (3.3 * 10000) / Vr - 10000
    if (Rt > 0):
        ln = math.log(Rt/R25)
        Tk = 1 / ((ln / B) + (1/T25))
        Tc = Tk - 273.15 # Convert to Celcius
        current_heat = Tc    

    if(Tc >= max_heat and is_alarm_active):
        is_activate = True
    else:
        is_activate = False

def photoresistorLogic():
    global is_flashing

    res = ADC0832_2.getADC(1)
    vol = 3.3/255 * res
    if (vol <= (3.3/2)):
        is_flashing = True
    else:
        is_flashing = False

def alarm_status(channel):
    global is_alarm_active

    if (channel == RED_BUTTON):
        is_alarm_active = True

    if(channel == BLUE_BUTTON):
        is_alarm_active = False

def sound_the_alarm():
    global is_activate
    while not stop_flag:
        if is_activate:
            play_melody()
        else:
            GPIO.output(BUZZER, GPIO.LOW)
    
    GPIO.output(BUZZER, GPIO.LOW)

def play_melody():
    melody = [
        # First Verse
        (GPIO.HIGH, 0.2),  # C
        (GPIO.LOW, 0.2),
        #(GPIO.HIGH, 0.4),  # C
        #(GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # G
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # G
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # A
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # A
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # G
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.8),  # F
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.8),  # F
        # (GPIO.LOW, 0.2),

        # # Second Verse
        # (GPIO.HIGH, 0.4),  # E
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # E
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # D
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # D
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # C
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # C
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # E
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.8),  # D
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.8),  # D
        # (GPIO.LOW, 0.2),

        # # Third Verse
        # (GPIO.HIGH, 0.4),  # G
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # G
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # F
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # F
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # E
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # E
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # D
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.8),  # G
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.8),  # G
        # (GPIO.LOW, 0.2),

        # # Fourth Verse
        # (GPIO.HIGH, 0.4),  # F
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # F
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # E
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # E
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # D
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # D
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.4),  # C
        # (GPIO.LOW, 0.2),
        # (GPIO.HIGH, 0.8),  # G
    ]

    for state, duration in melody:
        GPIO.output(BUZZER, state)
        time.sleep(duration)

def light_the_light():
    global light_status
    while not stop_flag:
        if is_flashing:
            light_status = "On"
            # GPIO.HIGH means light is off and GPIO.LOW means light is on
            GPIO.output(RGB_RED, GPIO.LOW)
            GPIO.output(RGB_GREEN, GPIO.HIGH)
            GPIO.output(RGB_BLUE, GPIO.HIGH)
            time.sleep(0.1)

            GPIO.output(RGB_RED, GPIO.HIGH)
            GPIO.output(RGB_GREEN, GPIO.HIGH)
            GPIO.output(RGB_BLUE, GPIO.LOW)

            time.sleep(0.1)
        else:
            light_status = "Off"
            GPIO.output(RGB_RED, GPIO.HIGH)
            GPIO.output(RGB_GREEN, GPIO.HIGH)
            GPIO.output(RGB_BLUE, GPIO.HIGH)

def potentiometerLogic():
    global max_heat
    R25 = 10000
    T25 = 25 + 273.15
    B = 3455

    res = ADC0832_2.getADC(0)
    Vr = 3.3 * float(res) / 255

    if (Vr == 0):
        Vr = 0.1

    Rt = (3.3 * 10000) / Vr - 10000
    if (Rt > 0):
        ln = math.log(Rt/R25)
        Tk = 1 / ((ln / B) + (1/T25))
        Tc = Tk - 273.15 # Convert to Celcius
        max_heat = Tc    
    
def lcd_display():
    screen = Screen(bus=1, addr=0x27, cols=16, rows=2)
    screen.enable_backlight()

    while not stop_flag:
        temp_line = "Temp: {}/{}".format(round(current_heat,1), round(max_heat,1))
        light_line = "Light: {}".format(light_status)
        screen.display_data(temp_line, light_line)
        time.sleep(0.2)

    screen.display_data("","")
    screen.disable_backlight()

def loop():
    while True:
        thermistorLogic()
        photoresistorLogic()
        potentiometerLogic()
        time.sleep(0.2)

if __name__ == '__main__':
    init()

    GPIO.add_event_detect(RED_BUTTON, GPIO.FALLING, callback=alarm_status)
    GPIO.add_event_detect(BLUE_BUTTON, GPIO.FALLING, callback=alarm_status)

    alarm_thread = threading.Thread(target=sound_the_alarm)
    alarm_thread.start()

    led_thread = threading.Thread(target=light_the_light)
    led_thread.start()

    lcd_thread = threading.Thread(target=lcd_display)
    lcd_thread.start()
    try:
        loop()
    except KeyboardInterrupt:
        stop_flag = True 
        alarm_thread.join()
        led_thread.join()
        lcd_thread.join()
        GPIO.cleanup()
        #ADC0832_1.destroy()
        #ADC0832_2.destroy()
        logging.info("Stopping...")
        print ('\nThe end !')