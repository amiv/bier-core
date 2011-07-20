#!/usr/bin/env python
"""Class which can connect to the Legi Reader
- Read Legi
- Read pressed Button
- Enables Free Beer
"""
import serial
import time

class LegiReader:
    """Constructor, establishes a connection with the given parameters
    
    :param device: Port where the Legi Reader is connected to
    :param baud: Baudrate, default: 9600
    :param waittime: Timeout for Connection (float, in seconds). Default: 0.1
    """
    def __init__(self,device='/dev/ttyS0',baud=9600,waittime=0.1):
        self.ser = serial.Serial(device, baud, timeout=waittime)
        
    """Close the serial connection when the object is terminated"""
    def __del__(self):
        self.ser.close()
        
    """Returns a tuple holding a legi-id (or False if Button pressed) and the Button which was pressed (or False if Legi read)

    :returns: (legi,button)
    (c) by Stephan Mueller"""
    def getLegiOrButton(self):
        try:
            while 1:
                b = ''
                # wait for start byte
                while b == '' or b != '@':
                    b = self.ser.read(1)
     
                #First Byte says if it is a legi (l) or a button (c) which was pressed 
                b = self.ser.read(1)
                
                if b == 'l':
                    b = self.ser.read(6)
                    return (int(b),False)
                elif b == 'c':
                    b = self.ser.read(1)
                    return (False,int(b))

        except ValueError as e:
            print "Not a Legi or Button which was pressed. This was read: %s"%(b)
            raise e
        
        
    legiNow = True
    """Demo-Funktion, will simulate a 'random' legi every 5 seconds, and a button 1 second later
    Returns a tuple holding a legi-id (or False if Button pressed) and the Button which was pressed (or False if Legi read)

    :returns: (legi,button)"""
    def getLegiOrButtonFake(self):
        if (self.legiNow):
            print "Fake LegiReader: waiting 5 seconds until Legi 013579 will be read"
            self.legiNow = False
            time.sleep(5)
            return (int('013579'),False)
        else:
            print "Fake LegiReader: waiting 1 second until button 1 is pressed"
            self.legiNow = True
            time.sleep(1)
            return (False,int('1'))
        
    def setFreeBeer(self,slots=(True,True,False,False)):
        """Sets the Jumper so that a free beer can be released
        Because of a bug slot 1+2 will always be active at the same time
        
        :param slots: Sets which slots will give a free beer/drink
        """
        #Convert slots to jumper
        # Jumper 1 = Fach 3
        # Jumper 2 = Fach 4
        # Jumper 3+4 = Fach 1+2 (somehow combined)
        jumper = [0,0,0,0]
        if slots[0]:
            jumper[2] += 2
            jumper[3] += 2
        elif slots[1]:
            jumper[2] += 2
            jumper[3] += 2
        if slots[2]:
            jumper[0] += 2
        if slots[3]:
            jumper[1] += 2
        
        #Activate LEDs, send Jumpers to Automat
        led = 'FFFF'
        out = '@s'+str(jumper[0])+str(jumper[1])+str(jumper[2])+str(jumper[3])+led+str(0)
        self.ser.write( out+'\r' )
        
        print "Activated FreeBeers, now the button must be pressed in 5 seconds"