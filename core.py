#!/usr/bin/env python
"""
Heart of the Bier-Automat. Will connect to the LegiLeser and decide if you get a beer.
is also responsible for starting all the (future) fancy stuff
"""

import MySQLdb as mdb
import ConfigParser
import datetime as dt
import legireader

def amivAuth(rfid):
    #Connect to amivid and get user object
    
    #Use login-name to check if he may get a beer (query amivid)
    
    #return result, first bool says if user was found, second if he may get a beer)
    
    return (True,True)
    
def visAuth(rfid):
    return (False,False)
    

def __getAuthorization(rfid):
    """Here later the real auth must be done, returning None, "AMIV", "VIS" or "MONEY" (or whatever)
    
    :param rfid: Integer holding the Legi-Card-Number
    :returns: Tuple of Username and auth. organization (can be 'noBeer') or 'notRegistered' if not registered
    """
    returnString = 'notRegistered'
    #Ask AMIV for auth
    if amivAuth(rfid)[0]:
        if amivAuth(rfid)[1]:
            return 'amiv'
        else:
            returnString = 'noBeer'
    #Ask VIS if not true from AMIV
    elif visAuth(rfid)[0]:
        if visAuth(rfid)[1]:
            return 'vis'
        else:
            returnString = 'noBeer'

    return returnString
    

def showCoreMessage(page, code=None, sponsor=None):
    """Displays a HTML-page on the Display in the core-part, showing the basic info if a legi was accepted"""
    if page == 'authorized':
        print "Authorized by %s, press the button!"%(sponsor)
        
    if page == 'notAuthorized':
        print "Not authorized, legi was: %s"%(code)
        
    if page == 'notRegistered':
        print "Not registered, legi was: %s"%(code)
        
    if page == 'freeBeer':
        print "You got your free beer, sponsored by %s"%(sponsor)

def startApp(appname):
    """Starts a custom app"""
    pass
        

if __name__ == "__main__":
    debug = True
    
    #Load Config Parameters
    config = ConfigParser.RawConfigParser()
    config.readfp(open('core.conf'))
    
    dbuser = config.get("mysql", "user")
    dbpass = config.get("mysql", "pass")
    dbdatabase = config.get("mysql", "db")
    dbhost = config.get("mysql", "host")
    
    print "ConfigFile core.conf read"

    #Connect to Log-DB
    conn = mdb.connect(dbhost,dbuser,dbpass,dbdatabase)
    cursor = conn.cursor()
    
    #Initialize connection to LegiLeser
    lr = legireader.LegiReader() #Also accepts device, baud and waittime parameters
    
    print "Connection to LegiReader established"
    
    authorize = None
    lastUser = 0
    lastUserTime = dt.datetime.min
    
    #Start endless-loop
    try:
        while 1:
            #Wait for new Legi or Button, read it
            print "Waiting for User Input (reading a Legi)"
            (legi,button) = lr.getLegiOrButton()
            
            print "Detected User Input - Legi=%s, Button=%s"%(legi,button)
            
            #check if legi may get a beer
            if legi:
                authorize = __getAuthorization(legi)
    
                if authorize == 'amiv' or authorize == 'vis':
                    showCoreMessage('authorized',sponsor=authorize)
                    lastUserTime = dt.datetime.now()
                    lastUser = legi
                elif authorize == 'noBeer':
                    showCoreMessage('notAuthorized',code=legi)
                elif authorize == 'notRegistered':
                    showCoreMessage('notRegistered',code=legi)
                else:
                    print >>sys.stderr, "Authorization failed"

            elif button and authorize:
                #A Button was pressed, check if a legi was read in the last two seconds
                if (dt.datetime.now()-lastUserTime < dt.timedelta(seconds=2)):
                    #Activate free beer
                    lr.setFreeBeer()
                    #Show that a free beer was server
                    showCoreMessage('freeBeer',sponsor=authorize)
                    #Log it
                    cursor.execute("INSERT INTO bierlog(username, org, time, slot) VALUES (%s,%s,NOW(),%s)",
                                   (lastUser,authorize, button))
                    #Un-Authorize user
                    authorize = None
                    
            else:
                #Something else happened, send it to the Debug-Output and continue
                if (debug): print "Did not detect anything useful while reading"
                continue
    finally:
        #Process crashed or it was terminated, close open connections
        if (debug): print "Program stopped, cleaning up..."
        cursor.close()
        conn.close()
