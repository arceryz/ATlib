# ATlib
Python library for sending and receiving SMS texts using AT commands. Higher and lower level features supported. Tested with SIM800L.

The API is relatively straightforward. The API is not asynchronous meaning all methods return the result directly.
Take a look at [atlib.py](/atlib.py) for the full library.

# API

The API features two classes for interfacing with the GSM modem. 

The low level is the AT_Device class.
This class exposes only a synchronous API for sending AT commands and reading responses. It abstracts
the painful process of AT commands not directly responding due to latency. Responses are detected by a 
terminated OK or ERROR string. The `read()` commands returns a tokenized list of the reply for easy parsing.
- Opening serial connection.
- Synchronizing baudrate (by sending "AT" and awaiting response).
- Sending AT commands.
- Reading AT commands reliably.
- Detecting errors.

The high level is the GSM_Device class. This class inherits from AT_Device. 
This class provides higher level features such as 
- Unlocking the device sim using pin.
- Sending text messages.
- Reading text messages (by category unread, all, read, etc).
This is still a w.i.p class for my personal use cases. Might be extended with call support later on.

# Contributing

If you have problems with your modem, you can open issues here. I have tested all commands with 
a properly hooked up SIM800L on a Raspberry Pi Bullseye. Know that not all devices support
all AT commands, and therefore may fail when using this library. However most devices should support
the basics.

# Examples

A minimal example can be found in [/examples](/examples) directory. Refer to the library
itself to see many AT commands in action already (e.g sending commands, checking responses).
See below for a minimal texting application:

```python
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
```
