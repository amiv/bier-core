#!/usr/bin/env python
"""
Heart of the Bier-Automat. Will connect to the LegiLeser and decide if you get a beer.
is also responsible for starting all the (future) fancy stuff
"""

import MySQLdb as mdb
import ConfigParser
import datetime as dt

def __getAuthorization(legi):
    """Here later the real auth must be done, returning None, "AMIV", "VIS" or "MONEY" (or whatever)
    
    :param legi: Integer holding the Legi-Card-Number
    :returns: String saying who authorized the beer
    """
    return 'DummyTrue'

def showPage(page, code=None, sponsor=None):
    """Displays a HTML-page on the Display, for now just some debug output"""
    if page == 'authorized':
        print "Authorized, press the button!"
        
    if page == 'notAuthorized':
        print "Not authorized, legi was: %s"%(code)
        
    if page == 'freeBeer':
        print "You got your free beer, sponsored by %s"%(sponsor)
        

if __name__ == "__main__":
    debug = True
    
    #Load Config Parameters
    config = ConfigParser.RawConfigParser(allow_no_value=True)
    config.readfp(open('core.conf'))
    
    dbuser = config.get("mysql", "user")
    dbpass = config.get("mysql", "pass")
    dbdatabase = config.get("mysql", "db")
    dbhost = config.get("mysql", "host")

    #Connect to Log-DB
    conn = mdb.connect(dbhost,dbuser,dbpass,dbdatabase)
    cursor = conn.cursor()
    
    #Initialize connection to LegiLeser
    import legireader
    lr = legireader.LegiReader() #Also accepts device, baud and waittime parameters
    
    authorize = None
    lastLegi = 0
    lastLegiTime = dt.datetime.min
    
    #Start endless-loop
    try:
        while 1:
            #Wait for new Legi or Button, read it
            (legi,button) = lr.getLegiOrButton
            
            #check if legi may get a beer
            if legi:
                authorize = __getAuthorization(legi)
    
                if authorize:
                    showPage('authorized')
                    lastLegiTime = dt.datetime.now()
                    lastLegi = legi
                else:
                    showPage('notAuthorized',code=legi)
                    
                
            elif button and authorize:
                #A Button was pressed, check if a legi was read in the last two seconds
                if (dt.datetime.now()-lastLegiTime < dt.timedelta(seconds=2)):
                    #Activate free beer
                    lr.setFreeBeer()
                    #Show that a free beer was server
                    showPage('freeBeer',sponsor=authorize)
                    #Log it
                    cursor.execute("INSERT INTO beerBeer(cardNo, drinkType, authority) VALUES (%s,%s,%s)",
                                   (lastLegi,button,authorize))
                    
            else:
                #Something else happened, send it to the Debug-Output and continue
                if (debug): print "Did not detect anything useful while reading"
                continue
    finally:
        #Process crashed or it was terminated, close open connections
        if (debug): print "Program stopped, cleaning up..."
        cursor.close()
        conn.close()
        
        
    #Cl