#!/usr/bin/env python
"""
Connects to the AMIV REST Server
"""

import ConfigParser
import random
import hashlib, hmac
import datetime
import urllib
import simplejson
from operator import itemgetter
import sys

class AmivID:
    
    def __init__(self,apikey,secretkey,baseurl):
        """Prepares a connection to AmivID
        
        :param apikey: Shared Secret string
        :param baseurl: Optional, the URL of the REST service
        """
        self.baseurl = baseurl
        self.apikey = apikey
        self.secretkey = secretkey
        
    def __sign(self,item,request):
        """Computes the correct signature, sorting the request-array
        
        :param item: string which is searched for
        :param request: list of tuples (param, value)
        :returns: string which can be put in the GET-request
        """
        sortedRequest = sorted(request, key=itemgetter(0))
        encodeRequest = '%s?%s'%(item,urllib.urlencode(request))
        signature = hmac.new(self.secretkey,encodeRequest,hashlib.sha256).hexdigest()
        request.append(('signature', signature))
        finalRequest = '%s?%s'%(item,urllib.urlencode(request))
        return finalRequest
        
    def getUser(self,rfid):
        """Gets a User-Dict based on a rfid-code
        
        :param rfid: 6-Digit RFID number from Legi
        :returns: dict with user-infos
        """
        #Create request
        request = [('apikey', self.apikey),
                   ('token', int(datetime.datetime.now().strftime("%s"))),
                   ('type', 'rfid')]
        
        #Add query & signature
        finalRequest = self.__sign("%06d"%(rfid),request)
        
        try:
            userDict = simplejson.load(urllib.urlopen(self.baseurl+finalRequest))
        except ValueError as e:
            print "Error in amivID.getUser(), %s"%(e)
        return userDict
    
    def getBeer(self,username):
        """Gets the Infos if a user may get a beer (and how many)
        
        :param username: n.ethz or amiv.ethz.ch username
        :returns: True if he gets a beer, False otherwise
        """
        request = [('apikey', self.apikey),
                   ('token', int(datetime.datetime.now().strftime("%s")))]
        
        #Add query & signature
        finalRequest = self.__sign("%s/apps"%(username),request)
        
        try:
            beerDict = simplejson.load(urllib.urlopen(self.baseurl+finalRequest))
        except ValueError as e:
            print "Error in amivID.getBeer(), %s"%(e)
        return beerDict
