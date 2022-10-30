#!/bin/python
# Console SMS sender using ATlib.

from atlib import *

gsm = GSM_Device("/dev/serial0")
if gsm.is_sim_locked():
    pin = input("SIM Pin: ")
    gsm.unlock_sim(pin)
else:
    print("SIM already unlocked.")

while True:
    print("")
    nr = input("Phone number: ")
    msg = input("Message: ")

    if gsm.send_sms(nr, msg) != OK:
        print("Error sending message.")
