import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme

relay_1_pin = 26
relay_2_pin = 19
relay_3_pin = 13
relay_4_pin = 6

GPIO.setup(relay_1_pin, GPIO.OUT) #set Relay 1 output
GPIO.setup(relay_2_pin, GPIO.OUT) #set Relay 2 output

#Pi Zero users do not need to configure the pins for Relays 3 & 4, these are unused.
GPIO.setup(relay_3_pin, GPIO.OUT) #set Relay 3 output
GPIO.setup(relay_4_pin, GPIO.OUT) #set Relay 4 output

interval = 0.1 # How long we want to wait (seconds)
 
while True:
    GPIO.output(relay_1_pin, GPIO.HIGH) #turn relay 1 on
    time.sleep(interval)
    GPIO.output(relay_1_pin, GPIO.LOW) #turn relay 1 off
    time.sleep(interval)

    GPIO.output(relay_2_pin, GPIO.HIGH) #turn relay 1 on
    time.sleep(interval)
    GPIO.output(relay_2_pin, GPIO.LOW) #turn relay 1 off
    time.sleep(interval)

    #Not Used For Pi Zero
    GPIO.output(relay_3_pin, GPIO.HIGH) #turn relay 1 on
    time.sleep(interval)
    GPIO.output(relay_3_pin, GPIO.LOW) #turn relay 1 off
    time.sleep(interval)

    GPIO.output(relay_4_pin, GPIO.HIGH) #turn relay 1 on
    time.sleep(interval)
    GPIO.output(relay_4_pin, GPIO.LOW) #turn relay 1 off
    time.sleep(interval)
