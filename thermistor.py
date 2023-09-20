#!/usr/bin/env python
import ADC0832
import time
import math

def init():
  ADC0832.setup()

def loop():
  while True:
    res = ADC0832.getADC(0)
    Vr = 3.3 * float(res) / 255
    Rt = 10000 * Vr / (3.3 - Vr)
    print ('Rt : %.2f' %Rt)
    time.sleep(0.2)
   
if __name__ == '__main__':
    init()
    try:
        loop()
    except KeyboardInterrupt: 
        ADC0832.destroy()
        print ('The end !')
