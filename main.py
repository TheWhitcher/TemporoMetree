# Imports
import logging
import time
import math
import RPi.GPIO as GPIO
import ADC0832
import threading

GPIO.setmode(GPIO.BCM)

BLUE_BUTTON = 16
RED_BUTTON = 26
BUZZER = 25

is_alarm_active = False
is_activate = False

#LCD
# SCL = 
# # SDA =

def init():
    ADC0832.setup()
    GPIO.setup(BLUE_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(RED_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUZZER, GPIO.OUT)

    # GPIO.input(BLUE_BUTTON, GPIO.LOW)
    # GPIO.input(RED_BUTTON, GPIO.LOW)
    GPIO.output(BUZZER, GPIO.LOW)

def thermistorLogic(): # TODO
    global is_alarm_active
    global is_activate

    R25 = 10000
    T25 = 25 + 273.15
    B = 3455

    res = ADC0832.getADC(1)
    Vr = 3.3 * float(res) / 255

    Rt = (3.3 * 10000) / Vr - 10000
    if (Rt > 0):
        ln = math.log(Rt/R25)
        Tk = 1 / ((ln / B) + (1/T25))
        Tc = Tk - 273.15 # Convert to Celcius
        print('Tc : %.2f' %Tc)
    
    if(Tc >= 30 and is_alarm_active): #TODO 30 is replaced by potentiometer value
        is_activate = True
    else:
        is_activate = False
    
    time.sleep(0.2)

def alarm_status(channel):
    global is_alarm_active

    if (channel == RED_BUTTON):
        is_alarm_active = True

    if(channel == BLUE_BUTTON):
        is_alarm_active = False

def sound_the_alarm():
    global is_activate
    
    print(is_activate)
    if is_activate:
        GPIO.output(BUZZER, GPIO.HIGH)
        time.sleep(0.2)

        GPIO.output(BUZZER, GPIO.LOW)
        time.sleep(0.2)
    else:
        GPIO.output(BUZZER, GPIO.LOW)

def loop():
    GPIO.add_event_detect(RED_BUTTON, GPIO.FALLING, callback=alarm_status)
    GPIO.add_event_detect(BLUE_BUTTON, GPIO.FALLING, callback=alarm_status)

    alarm_thread = threading.Thread(target=sound_the_alarm)
    alarm_thread.start()

    while True:
        thermistorLogic()

if __name__ == '__main__':
    init()
    try:
        loop()
    except KeyboardInterrupt: 
        GPIO.cleanup()
        ADC0832.destroy()
        logging.info("Stopping...")
        print ('The end !')


# SETUP
#     GPIO.setup(RGB_RED, GPIO.OUT)
#     GPIO.output(RGB_RED, GPIO.HIGH)
    
#     GPIO.setup(RGB_BLUE, GPIO.OUT)
#     GPIO.output(RGB_BLUE, GPIO.HIGH)

#     GPIO.setup(RGB_GREEN, GPIO.OUT)
#     GPIO.output(RGB_GREEN, GPIO.HIGH)

# def new function
        # if isFlashing:
        #     # GPIO.HIGH means light is off
        #     # GPIO.LOW means light is on
        #     GPIO.output(RGB_RED, GPIO.LOW)
        #     GPIO.output(RGB_GREEN, GPIO.HIGH)
        #     GPIO.output(RGB_BLUE, GPIO.HIGH)
        #     time.sleep(0.2)

        #     GPIO.output(RGB_RED, GPIO.HIGH)
        #     GPIO.output(RGB_GREEN, GPIO.HIGH)
        #     GPIO.output(RGB_BLUE, GPIO.LOW)

        #     time.sleep(0.2)
        # else:
        #     GPIO.output(RGB_RED, GPIO.HIGH)
        #     GPIO.output(RGB_GREEN, GPIO.HIGH)
        #     GPIO.output(RGB_BLUE, GPIO.HIGH)