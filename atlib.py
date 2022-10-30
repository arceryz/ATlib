#--- Python ATlib. ---#
# Allows reading and writing to an AT interface style port.
# Writing is performed with no checks. Reading is performed with header
# analysis based on replies and returns an array.
# 
# Supports the basic AT commands and even prompts from AT+CMGS.
# Implement the error handling logic in your applications.
# Most methods return a boolean that is true if there is an error.
#
# Written by swordstrike1.

from serial import *
from time import *

ERROR = 1
OK = 0


class AT_Device:
    """ Base class for all device with AT commands. 
    For higher level GSM features, use GSM_Device."""


    def __init__(self, path):
        """ Open AT device. Nothing else."""
        self.serial = Serial(path, timeout=0.5)
        print("AT serial device opened at {:s}".format(path))

    
    def __del__(self):
        """ Close AT device. """
        self.serial.close()
       

    def write(self, cmd):
        """ Write a single line to the serial port. """
        encoded = (cmd + "\r\n").encode()
        self.serial.write(encoded)
        return OK


    def write_ctrlz(self):
        """ Write the terminating CTRL-Z to end a prompt. """
        self.serial.write(bytes([26]))
        return OK


    def read(self, timeout=20, end="9999999"):
        """ Read a single whole response from an AT command.
        Returns a list of tokens for parsing. """
        resp = ""
        wait = 0
        delay = 0.01
        while True:
            # Query available bytes in a semi-busy loop.
            avail = self.serial.in_waiting

            if(avail > 0):
                # Parse new incoming bytes in chunks until a header is read.
                raw = self.serial.read(avail)
                resp += raw.decode("utf-8")
                if resp.endswith("\r\nOK\r\n") or \
                        resp.endswith("\r\nERROR\r\n") or \
                        resp.endswith("> ") or \
                        end in resp:

                    # Split the response by line and clean entries.
                    table = resp.split("\r\n")
                    for i in range(len(table) - 1, -1, -1):
                        cur = table[i]
                        new = cur.replace("\r", "") 
                        table[i] = new
                        if new == "":
                            table.pop(i)
                    return table

            # Keep waiting for bytes until timeout has passed.
            sleep(delay)
            wait += delay
            if wait > timeout:
                return [ resp, "TIMEOUT" ]


    def read_err(self, msg=""):
        """ Reads output and returns ERROR on error. """
        resp = self.read()[-1]
        err = (resp == "ERROR" or resp == "TIMEOUT")
        if err:
            print("Error: {:s}.".format(msg))
        return err


    def sync_baudrate(self):
        """ Synchronize the device baudrate to the port. 
        You should always call this first. Returns status."""

        print("Performing baudrate synchronization")
        # Write AT and test whether received OK response.
        # A broken serial port will not reply.
        self.write("AT")
        resp = self.read(5)
        status = resp[-1]
        if status == "OK":
            print("Successful")
            return OK
        else:
            print("Error")
            print(resp)
            return ERROR


class GSM_Device(AT_Device):
    """ A class that provides higher level GSM features such
    as sending/receiving SMS and unlocking sim pin."""


    def __init__(self, path):
        """ Open GSM Device. Device sim still needs to be unlocked. """
        print("Opening GSM device.")
        super().__init__(path)
        self.sync_baudrate()


    def reboot(self):
        """ Reboot the GSM device. Returns status. """

        print("Rebooting device.")
        self.write("AT+CFUN=1,1")
        if self.read_err("Rebooting"):
            return ERROR
        return OK


    def is_sim_locked(self):
        """ Returns status of sim lock. True of locked. """
        self.write("AT+CPIN?")
        resp = self.read()
        if "READY" in resp[1]:
            return False
        if "SIM PUK" in resp[1]:
            # This is a special case.
            print("Max tries reached. PUK code is required.")
            return True
        else:
            return True


    def unlock_sim(self, pin):
        """ Unlocks the sim card using pin. Can block for a long time.
        Returns status."""

        # Test whether sim is already unlocked.
        if not self.is_sim_locked(): return OK

        # Unlock sim.
        print("Unlocking SIM card using pin {:s}.".format(pin))
        self.write("AT+CPIN={:s}".format(pin))
        if self.read_err():
            print("Error setting pin.")
            return ERROR

        # Wait until unlocked.
        print("Awaiting ready status.")
        resp = self.read(end="SMS Ready")
        print("Sim unlocked.")
        return OK


    def send_sms(self, nr, msg):
        """ Sends a text message to specified number. 
        Returns status."""

        # Set text mode.
        print("Sending \"{:s}\" to {:s}.".format(msg, nr))
        self.write("AT+CMGF=1")
        if self.read_err("Text mode"): return ERROR
       
        # Write message.
        self.write("AT+CMGS=\"{:s}\"".format(nr))
        if self.read_err("Set number"): return ERROR
        self.write(msg)
        self.read()
        self.write_ctrlz()
        if self.read_err("Sending message"): return ERROR

        print("Message sent.")
        return OK


    def receive_sms(self, category="REC UNREAD"):
        """ Receive text messages. The category can be one of several AT modes: REC UNREAD (default), REC READ, STO UNSENT, STO SENT, ALL.
        Not all modes may work for a given device.
        """
        # Read unread. After reading they will not show up here anymore!
        print("Scanning {:s} messages...".format(category))
        self.write("AT+CMGF=1")
        if self.read_err("Text mode"): return ERROR
        self.write("AT+CMGL=\"{:s}\"".format(category))
        resp = self.read()

        if resp[-1] != "OK": return ERROR

        # TotalElements = 2 + 2 * TotalMessages.
        # First and last elements are echo/result.
        table = []
        for i in range(1, len(resp) - 1, 2):
            header = resp[i].split(",")
            message = resp[i + 1]
          
            # Extract elements and strip garbage.
            sender = header[2].replace("\"", "")
            date = header[4].replace("\"", "")
            time = header[5].split("+")[0]
            el = [sender, date, time, message]
            table.append(el)

        print("Received {:d} messages.".format(len(table)))
        return table


    def await_sms(self, timeout=100):
        """ Block until SMS is received. Returns list of messages if any."""
        sec = 0
        while True:
            table = self.receive_sms()
            if len(table) > 0:
                return table
            sleep(1)
            sec += 1
            if sec >= timeout:
                return []
