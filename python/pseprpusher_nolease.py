#!/usr/bin/python


import sys
import os
import time
import urllib
import re
import random

from socket import *
#import socket as socket
#import storkerror
import arizonareport
import arizonaxml as xmllib
import pseprmessages as messages
import arizonacrypt as cryptlib

    #__servers={"jabber.services.planet-lab.org":5222} #this server is no longer on the main list
global __servers;

__servers={"planetlab1.rutgers.edu":23345} #not all servers work...

    #__servers={"planetlab2.cs.virginia.edu":23345}
__serverrecompiled=re.compile(r"<(\w+)>\W*<server>([a-z0-9.-]+)<\/server>\W*<port>([0-9]+)<\/port>\W*<\/\1>")

########################### MAIN ###############################
def main():
   
   if len(sys.argv)!=4:
      print """Usage:  pseprpusher.py FILENAME NEWFILENAME PRIVATEKEY
      Where FILENAME is the file you wish to push out via PsEPR,
      NEWFILENAME is the filename/path to send via psepr,
      and PRIVATEKEY is the full file path of the private key to use"""
      sys.exit()

   fname=sys.argv[1]

   if not os.path.isfile(fname):
      print fname,"is not a valid file."
      sys.exit(1)

   #copy the file
   fo=open(fname,"r")
   rd=fo.read()
   fo.close()
   tfname="/tmp/"+os.path.split(fname)[1]
   if tfname=="/tmp/":
      print "ERROR: unable to extract filename from path:",fname
      sys.exit(1)
   tfname+=str(time.time())#in case multiple updates are attempted simultaneously
   fo=open(tfname,"w")
   fo.write(rd)
   fo.close()

   #sign it
   try:
      cryptlib.XML_sign_file_using_privatekey_fn(tfname,sys.argv[3])
   except:
      print "ERROR: unable to sign message."
      if tfname and os.path.isfile(tfname):os.unlink(tfname)
      sys.exit(1)

   #read and delete
   fo=open(tfname,"r")
   fdata=fo.read()
   fo.close()

   os.unlink(tfname)

   #ensure that it's xml safe
   fdata=xmllib.escape(fdata)
   
   serverHost = 'planetlab2.cs.ubc.ca'
   #server     = get_server()
   #serverHost = server[0]
   #serverPort = server[1]
   serverPort  = 23343
   channel = "/edu/arizona/stork2/test/"
   service = "arizona_stork2"
   passw    = "etlk3vXZ23d"




   #send it
   #pseprlib.SendPsEPRMessage("arizona_stork2","etlk3vXZ23d",sys.argv[2],fdata)
   
   print 'connecting to: '+serverHost+':'+str(serverPort)
   try:
       sockobj = socket(AF_INET, SOCK_STREAM)
       sockobj.connect((serverHost, serverPort))
       #except:
       #    print "failed to connect to "+serverHost+":"+str(serverPort)
       #    print e
       #    sys.exit(1)

       #xmlmsg = xmlmsg.replace('\n','').replace('\t','')

       #sockobj.send("hello")
       #sockobj.send( str(messages.message4 %(service,passw,channel,service,service,"jplichta.ipupdater.com",sys.argv[2],fdata) ) )
       fdata = "hello"
       sockobj.send( str(messages.message4 %(service,passw,channel,service,service,gethostname(),sys.argv[2],fdata) ) )
       #data = sockobj.recv(1024)
       #print 'client recieved:', `data`
       sockobj.close()
       
       #print str(messages.message4 %(service,passw,channel,service,service,"jplichta.ipupdater.com",sys.argv[2],fdata) )
       
       print "message sent ok\n"
   except Exception, e:
       print "failed to connect to "+str(serverHost)
       print e
       sys.exit(1)




def __load_server_list(lstring):
        global __servers;
        #print "in __load_server_list: "+str(lstring)
        rd=lstring
        matches=__serverrecompiled.findall(rd)
        if matches is None or len(matches)==0:
            return
        __servers={}
        for i in matches:
            #print i
            __servers[i[1]]=int(i[2])
            
def load_server_list(filename):
        """Loads in server data from the file filename, replacing the existing serverdata.
        """
        if not os.path.isfile(filename):
            return #ignore this error for now
        fo=open(filename,"r")
        rd=fo.read()
        fo.close()
        __load_server_list(rd)
        
def load_server_list_from_url(url="http://www.dsmt.org/PsEPRServer/jClient.xml"):
        """Loads in server data from the URL url.  The default address of the url is
        that of the file used by the java client library.
        """
        try:
            uo=urllib.urlopen(url)
            rd=uo.read()
            uo.close()
            __load_server_list(rd)
           
        except:pass
        
def get_server(index=-1):
        """Will return a random server address pair (hostname,port) if no index is
        specified, otherwise, will return the server of the given index.
        """
        #returns a random server
        keys=__servers.keys()
        if index<0 or index>len(keys):key=random.choice(keys)
        else:key=keys[index]
        return (key,__servers[key])


# Start main
if __name__ == "__main__":
   try:
      #storkerror.init_error_reporting("pseprpusher.py")
      load_server_list_from_url()
      main()
   except KeyboardInterrupt:
      arizonareport.send_out(0, "Exiting via keyboard interrupt...")
      sys.exit(0)
