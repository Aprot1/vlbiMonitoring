#!/usr/bin/env python3

import time
import sys
import serial

# ##############################################################################
# Adjustable vaiables

device='/dev/ttyS0'     # Serial port number
deactivate_alarm = 0    # for testing purposes. Deactivates radio when HIGH

# ##############################################################################
# Program code

# Function declarations ###################

def send_alarm():
    ser=serial.Serial(device)   # Open serial port
    # print("Sending Alarm")
    ser.setRTS(False)
    time.sleep(5)
    ser.setRTS(True)
    ser.setDTR(True)
    ser.close()

if __name__ == "__main__":
    send_alarm()
