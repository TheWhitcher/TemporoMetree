# Name:     uv_light_monitor.py
# By:       Christophe Landry & Zacharyah Whitcher
# Date:     2023-04-28
# Version:  1.0

# Imports
import RPi.GPIO as GPIO
import time

# UV Light
LED = 25

#PhotoResistor
ADC_CS = 21
ADC_CLK = 20
ADC_DIO = 16

# Setup the Components
def setup():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(ADC_CS, GPIO.OUT)
	GPIO.setup(ADC_CLK, GPIO.OUT)
	GPIO.setup(LED, GPIO.OUT)

# Clean up the GPIO
def destroy():
	GPIO.cleanup()

# Calculate the results from the Sensor
def getResult():
	GPIO.setup(ADC_DIO, GPIO.OUT)
	GPIO.output(ADC_CS, 0)
	
	GPIO.output(ADC_CLK, 0)
	GPIO.output(ADC_DIO, 1);  time.sleep(0.000002)
	GPIO.output(ADC_CLK, 1);  time.sleep(0.000002)
	GPIO.output(ADC_CLK, 0)

	GPIO.output(ADC_DIO, 1);  time.sleep(0.000002)
	GPIO.output(ADC_CLK, 1);  time.sleep(0.000002)
	GPIO.output(ADC_CLK, 0)

	GPIO.output(ADC_DIO, 0);  time.sleep(0.000002)

	GPIO.output(ADC_CLK, 1)
	GPIO.output(ADC_DIO, 1);  time.sleep(0.000002)
	GPIO.output(ADC_CLK, 0)
	GPIO.output(ADC_DIO, 1);  time.sleep(0.000002)
	
	dat1 = 0
	for i in range(0, 8):
		GPIO.output(ADC_CLK, 1);  time.sleep(0.000002)
		GPIO.output(ADC_CLK, 0);  time.sleep(0.000002)
		GPIO.setup(ADC_DIO, GPIO.IN)
		dat1 = dat1 << 1 | GPIO.input(ADC_DIO)  # or ?
	
	dat2 = 0
	for i in range(0, 8):
		dat2 = dat2 | GPIO.input(ADC_DIO) << i
		GPIO.output(ADC_CLK, 1);  time.sleep(0.000002)
		GPIO.output(ADC_CLK, 0);  time.sleep(0.000002)
	
	GPIO.output(ADC_CS, 1)
	GPIO.setup(ADC_DIO, GPIO.OUT)

	if dat1 == dat2:
		return dat1
	else:
		return 0

# Read the sensor and return the results
def readSensor(max_uv=100, min_uv=50):
	res = getResult() - 80
	if res < 0:
		res = 0
	if res > 100:
		res = 100
	#print ('res = %d' % res)

	if (res <= (max_uv + min_uv) / 2):
		GPIO.output(LED, GPIO.HIGH)
	elif (res > (max_uv + min_uv) / 2 ):
		GPIO.output(LED, GPIO.LOW)
	return res

# Main loop every 0.5 seconds
def loop():
	while True:
		readSensor(50)

# Main Program
if __name__ == '__main__':
	setup()
	try:
		loop()
	except KeyboardInterrupt: 
		destroy()
		print ('The end !')
	finally:
		destroy()
