#!/usr/bin/env python
"""
Heart of the Bier-Automat. Will connect to the LegiLeser and decide if you get a beer.
is also responsible for starting all the (future) fancy stuff
"""

import MySQLdb as mdb
import ConfigParser
import datetime as dt
import legireader
import amivid
import visid
import os.path

def amivAuth(rfid):
    """Checks if the user may get a beer sponsored by AMIV
    :param rfid: Legi-Code of user
    :returns: tuple (user,bool) where the first value says returns the user-login (or None) and the second if he may get a beer
    """
    #Connect to amivid and get user object
    aid = amivid.AmivID(apikey=config.get("amivid", "apikey"),secretkey=config.get("amivid", "secretkey"),baseurl=config.get("amivid", "baseurl"))
    user = aid.getUser(rfid)
    if not user:
        return(None,False)
    login = user['nethz']
    
    #Use login-name to check if he may get a beer 
    #Old: API-Query beer = aid.getBeer(login)
    #New: Take it from the user object
    beer = user['apps']
    
    #return result, first bool says if user was found, second if he may get a beer)
    return (login,int(beer['beer']) > 0)
    
def visAuth(rfid):
    """Checks if the user may get a beer sponsored by AMIV
    :param rfid: Legi-Code of user
    :returns: tuple (user,bool) where the first value says returns the user-login (or None) and the second if he may get a beer
    """
    #Get secret key
    #config = ConfigParser.RawConfigParser()
    #config.readfp(open('core.conf'))
    
    #Connect to visid and get user object
    vid = visid.VisID(baseurl=config.get("visid", "baseurl"))
    user = vid.getUser(rfid)
    if not user:
        return(None,False)
    login = user['nethz']
    
    #Use login-name to check if he may get a beer 
    beer = vid.getBeer(login)
    
    #return result, first bool says if user was found, second if he may get a beer)
    return (login,int(beer['beer']) > 0)
    

def __getAuthorization(rfid):
    """Here later the real auth must be done, returning None, "AMIV", "VIS" or "MONEY" (or whatever)
    
    :param rfid: Integer holding the Legi-Card-Number
    :returns: Tuple of Username and auth. organization (can be 'noBeer') or (None,'notRegistered') if not registered
    """
    returnString = 'notRegistered'
    returnUser = None
    #Ask AMIV for auth
    aA = amivAuth(rfid)
    if aA[0]:
        if aA[1]:
            return (aA[0],'amiv')
        else:
            returnUser = aA[0]
            returnString = 'noBeer'
    #Ask VIS if not true from AMIV
    vA = visAuth(rfid)
    if vA[0]:
        if vA[1]:
            return (vA[0],'vis')
        else:
            returnUser = vA[0]
            returnString = 'noBeer'

    return (returnUser,returnString)
    

def showCoreMessage(page, code=None, sponsor=None, user=None):
    """Displays a HTML-page on the Display in the core-part, showing the basic info if a legi was accepted"""
    if page == 'authorized':
        
        print "%s authorized by %s, press the button!"%(user,sponsor)
        
    if page == 'notAuthorized':
        print "Not authorized, user was: %s"%(user)
        
    if page == 'notRegistered':
        print "Not registered, legi was: %s"%(code)
        
    if page == 'freeBeer':
        print "%s got a free beer, sponsored by %s"%(user,sponsor)

def startApp(appname):
    """Starts a custom app"""
    pass
        

if __name__ == "__main__":
    debug = False
    
    #Load Config Parameters
    config = ConfigParser.RawConfigParser()
    config.readfp(open(os.path.dirname(__file__) + '/core.conf')) #changed this as well because not right directory otherwise (Fadri)
    
    dbuser = config.get("mysql", "user")
    dbpass = config.get("mysql", "pass")
    dbdatabase = config.get("mysql", "db")
    dbtable = config.get("mysql", "table")
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
            #print "Waiting for User Input (reading a Legi)"
            (legi,button) = lr.getLegiOrButton()
            
            #print "Detected User Input - Legi=%s, Button=%s"%(legi,button)
            
            #check if legi may get a beer
            if legi:
                #For debug: Time the auth-query
                #starttime = dt.datetime.now()
                authorize = __getAuthorization(legi)
                #print "Auth-Time: %s"%(dt.datetime.now()-starttime)
    
                if authorize[1] == 'amiv' or authorize[1] == 'vis':
                    showCoreMessage('authorized',sponsor=authorize[1],user=authorize[0])
                    lastUserTime = dt.datetime.now()
                    lastUser = authorize[0]
                    #Activate free beer
                    lr.setFreeBeer()
                elif authorize[1] == 'noBeer':
                    showCoreMessage('notAuthorized',user=authorize[0])
                elif authorize[1] == 'notRegistered':
                    showCoreMessage('notRegistered',code=legi)
                else:
                    print >>sys.stderr, "Authorization failed"

            elif button and authorize:
                #A Button was pressed, check if a legi was read in the last two seconds
                if (dt.datetime.now()-lastUserTime < dt.timedelta(seconds=5)):
                    #Show that a free beer was server
                    showCoreMessage('freeBeer',sponsor=authorize[1],user=authorize[0])
                    #Log it
                    queryString = "INSERT INTO %s(username, org, time, slot) VALUES (%%s,%%s,NOW(),%%s)"%(dbtable)
                    cursor.execute(queryString,
                                   (lastUser,authorize[1], button))
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
