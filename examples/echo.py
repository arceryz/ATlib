#!/bin/python
# SMS Echo server. Responds with same message.

from atlib import *

gsm = GSM_Device("/dev/serial0")
if gsm.get_sim_status() != Status.OK:
    pin = input("SIM Pin: ")
    gsm.unlock_sim(pin)
else:
    print("SIM already unlocked.")

print("Opening Server")
while True:
    recv = gsm.await_sms()
    if len(recv) > 0:
        for i in range(len(recv)):
            # Echo to each sender the same message.
            el = recv[i]
            nr = el[0]
            msg = el[3]
            newmsg = "ECHO: {:s}".format(msg)
            gsm.send_sms(nr, newmsg)
