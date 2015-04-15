#!/usr/bin/env python
#Written by Jason Hardies while working with the Stork project at the U of Arizona - FA05
#pseprlib2.py - second attempt at psepr lib.

import socket
import os
import sys
import urllib
import string
import time
import re
import random
import inspect
import types
import threading
import stat

import pseprmessages as messages #the basic xml messages clients send put here to avoid mess in this module

DEFAULT_LEASE_DURATION = 1800

# smbaker: wrapper for storklog in case it is not available
def log_nest(module, function, tag, subtag, info):
   try:
      import storklog
      storklog.log_nest(module, function, tar, subtag, info)
   except:
      pass

class InvalidInstanceException(Exception):
    """The exception raised by test_instance_type when a given instance does not match a given class"""
    def __init__(self,value):self.value=value
    def __str__(self):return repr(self.value)

def test_instance_type(inst,tclass,errorprefix=''):
    """Raises the exception InvalidInstanceException when inst is not an instance of
    class tclass.  It will prepend the exception message with the string errorprefix
    in the case of an exception."""
    if not type(inst) == types.InstanceType:
        raise InvalidInstanceException(errorprefix+str(inst) +" is not an instance (and not of type "+tclass.__name__+")!")
    if not tclass in inspect.getmro(inst.__class__):
        raise InvalidInstanceException(errorprefix+str(inst) +" is not an instance of class (or a class derived from) "+tclass.__name__+"!")

class PsEPRServerManager:
    """A class used to load in a list of servers from a file of a format matching that
    of the Java PsEPR library server settings file.  The class is used to return a server
    address from the loaded file.
    """

    # JRP 12/8/06 NOTE: We do not want to initialize this Dict object to just one value
    # instead, we want to make sure we are always forced to load the server list
    # from the online xml file...
    # we were having problems with rutgers.edu (it was denying our connections)
    # and we were causing a DOS attack
    #
    # Now, we are making sure we are using the server list, picking random servers
    # and waiting 1 seconds after a failed connection attempt before moving
    # onto the next server to try

    #__servers={"jabber.services.planet-lab.org":5222} #this server is no longer on the main list
    #__servers={"planetlab1.rutgers.edu":23345} #not all servers work...
    #__servers={"planetlab2.cs.virginia.edu":23345}

    __serverrecompiled=re.compile(r"<(\w+)>\W*<server>([a-z0-9.-]+)<\/server>\W*<port>([0-9]+)<\/port>\W*<\/\1>")

    def __init__(self,serverfile=None,serverurl=None):
        """Constructor.
        If serverfile is not None, then the class will attempt to load in data from
        the given file, otherwise, if serverurl is not None, it will attempt to load
        server data from the serverurl URL.
        """
        if not serverfile is None:
            self.load_server_list(serverfile) #load in the list of servers/ports
        elif not serverurl is None:
            self.load_server_list_from_url(serverurl)

    def __load_server_list(self,lstring):
        rd=lstring
        matches=self.__serverrecompiled.findall(rd)
        if matches is None or len(matches)==0:
            return
        self.__servers={}
        for i in matches:
            self.__servers[i[1]]=int(i[2])

    def load_server_list(self,filename):
        """Loads in server data from the file filename, replacing the existing serverdata.
        """
        if not os.path.isfile(filename):
            return #ignore this error for now
        fo=open(filename,"r")
        rd=fo.read()
        fo.close()
        self.__load_server_list(rd)

        #Stork Logging
        log_nest('pseprlib2', 'load_server_list', 'loadserver', 'file', str(self.__servers))

    def load_server_list_from_url(self, url="http://www.dsmt.org/PsEPRServer/jClient.xml"):
        """Loads in server data from the URL url.  The default address of the url is
        that of the file used by the java client library.
        """
        # try to load a cached copy first, so that we avoid loading the psepr
        # web server.
        if self.load_server_list_cache(url):
            return
        try:
            uo=urllib.urlopen(url)
            rd=uo.read()
            uo.close()
            self.__load_server_list(rd)
            self.save_server_list_cache(url, rd)
        except:
            pass

        #Stork Logging
        log_nest('pseprlib2', 'load_server_list_from_url', 'loadserver', 'url', str(self.__servers))

    def load_server_list_cache(self, url):
        """ returns True if a cached copy was found and loaded """ 
        fn = os.path.join("/tmp", url.replace("/", "_"))
        if os.path.exists(fn):
            mtime = os.stat(fn)[stat.ST_MTIME]
            elapsed = abs(int(mtime - time.time()))
            # if the cached copy is less than 60 minutes old, then use it
            if elapsed < 3600:
               # print "using cached copy of " + url + " (" +str(elapsed)+ " seconds old)"
               self.load_server_list(fn)
               return True
        return False

    def save_server_list_cache(self, url, data):
        fn = os.path.join("/tmp", url.replace("/", "_"))
        try:
            file = open(fn, "w")
            file.write(data)
            file.close()
        except OSError:
            pass
        except IOError:
            pass

    def get_server(self,index=-1):
        """Will return a random server address pair (hostname,port) if no index is
        specified, otherwise, will return the server of the given index.
        """
        #returns a random server
        keys=self.__servers.keys()
        if index<0 or index>len(keys):
           key=random.choice(keys)
        else:
           key=keys[index]
        return (key,self.__servers[key])
        
    def force_selection(self,server):
        """Forces get_server to return a given address by replacing the server dictionary
        with a given server entry.
        
        server must be a dictionary of one entry eg: {'jabber.services.planet-lab.org':5222}"""
        if type(server) != types.DictType and len(server.keys())!=1:
            return False
        self.__servers=server
        return True
        

class SocketListener(threading.Thread):
    """
        Written to simplify a threaded socket listener (as compared to asyncore.dispatcher)
        and to use noticeably less cpu (compared to asyncore.dispatcher -- max of 2% vs. 50% on a 2.6ghz wintel box).
    """
    def __init__(self,host,port,handler_func=None,error_handler=None):
        """Constructor.
        host=hostname of server
        port=port of server
        handler_func = function to call when receiving data (which will be passed as a single string)
        """
        threading.Thread.__init__(self)
        self.host=host
        self.port=port
        self.socket=None
        self.listening=False
        self.handler=handler_func
        if self.handler is None:self.handler=self.default_handler
        self.errorhandler=error_handler
        if self.errorhandler is None:self.errorhandler=self.default_error_handler
        self.buffer=""
    def connect(self):
        """Tries connecting to the server.  May raise exceptions of server name invalid.
        Returns true if able to connect, false if socket looks to be already in use.
        """
        self.connecting=True
        if not self.socket is None:
            return False #still connected?
        try:
            self.socket=socket.socket()
            # JRP 12/8/06
            # commented out the setblocking call
            # and added the settimeout call
            self.socket.setblocking(1)
            self.socket.settimeout(30)
            self.socket.connect((self.host,self.port))

            # SMB: set timeout to 30 seconds. This is used in do_iteration
            # so that it is pseudo-nonblocking, and can return, allowing the
            # resubscribe timer to resubscribe.
            self.socket.settimeout(30)
        except socket.error,e:
            # JRP 12/8/06
            # if we are denied access, sleep here for 1 second
            # to prevent the possibility of hammering the psepr
            # routers
            if self.debug:
                print "sleeping for 1 seconds after failed connection"
            time.sleep(1)

            self.errorhandler(self,str(e))
            self.close()
            return False
        self.listening=True
        self.start()
        return True
    def accept(self,sockaddr):
        self.socket=sockaddr[0]
        if self.socket is None:
            return
        self.socket.setblocking(0)
        self.listening=True
        self.start()
    def close(self):
        """Closes the connection, stops the thread, and resets the socket.
        Will return false if socket is reset.
        """
        self.listening=False
        if self.socket is None:
            return False #no connection
        self.socket.close()
        self.socket=None
        return True
    def default_error_handler(self,obj,msg):
        """An example error handler"""
        #was probably disconnected
        self.close()
        #print "ERROR",obj,msg
    def default_handler(self,data):
        """An example default handler that puts all incoming data in self.buffer.
        """
        if data=="":self.close()#connection has closed?
        self.buffer+=data #the handler must be able to buffer the data since the
        #                   connection can't tell when it receives the end of one
        #                   message or the beginning of another.
    def send(self,data):
        """
            for sending strings directly through the socket
            data should be of type string or a type that can be acceptably made into a string via str()
        """
        data=str(data)

	#Stork Logging
	log_nest('pseprlib2', 'send', 'pseprmessage', 'sent', data)

        while len(data)>0:
            sent=0
            try:sent=self.socket.send(data)
            except Exception,e:
                self.errorhandler(self,str(e))
                break
            data=data[sent:]
            
    def run(self):
        """Runs when the thread starts.  Handles listening.
        """
        while self.do_iteration():
            time.sleep(0.5) #to prevent the loop from eating up cpu

    def do_iteration(self):
        if self.listening:
            if self.socket is None:
                self.close()
                return False #best after the timer in case it was killed in its sleep
            try:
                data = self.socket.recv(8192)#if no data, will raise exception
                if data=="":
                    self.close()#was disconnected
                self.handler(data)
            except socket.timeout:
                # SMB:
                # socket.settimeout() was used and the socket has timed out
                # return True to the caller since this was not an error
                return True
            except:
                pass
            return True
        return False

class PsEPRListener(SocketListener):
    """A subclass of SocketListener that handles sending and receiving PsEPRMessages.
    Note: authentificated will be true if the PsEPRListener was able to authentificate itself
    and lease a channel.
    """
    messagerecompiled=re.compile("<message .*>.*<channel>(.*)<\/channel>.*<from>.*<service>(.*)<\/service>.*<instance>(.*)<\/instance>.*<payload.*<field>(.*)<\/field>.*<value>(.*)<\/value>",re.DOTALL)#.*</message> # removed because the messages will get split on </message>
    #re.DOTALL so .* will match \n as well...
    def __fixchannelname(self,channel):
        if channel is None or len(channel)==0:channel="/"
        elif len(channel)==1 and channel[0]!='/':channel="/%s/" %(channel)
        else:
            if channel[0]!='/':channel='/'+channel
            if channel[-1]!='/':channel=channel+'/'
        return channel
    def __init__(self,username,password,channel,message_handler,manager=None,leaseduration=DEFAULT_LEASE_DURATION,autoconnect=True,debug=False):
        """Constructor.
        username=psepr username
        password=psepr password
        channel=psepr channel
        message_handler= method to be called with psepr message data
        manager=the PsEPRManager object to get a server from (if None, will create an empty manager object.
        leaseduration=the duration (in seconds) to pass to psepr when leasing a channel
        autoconnect= if true, the constructor will call the connect method
        debug=if true, will print out various information while running
        """
        test_instance_type(manager,PsEPRServerManager,"PsEPRListener:")
        self.serverman=manager
        self.debug=debug
        if self.serverman is None:self.serverman=PsEPRServerManager()
        self.server=self.serverman.get_server()
        if self.debug:
            print "PsEPRListener:selected server " + str(self.server)
            print "PsEPRListener:doing socketlistener init."
        SocketListener.__init__(self,self.server[0],self.server[1],self.default_handler)

        self.username=username
        self.password=password
        self.channel=self.__fixchannelname(channel)
        self.message_handler=message_handler
        self.leaseduration=leaseduration
        #self.leasetimer=None
        self.leasetime=-1

        self.authentificated=False        
        if self.debug:
            print "PsEPRListener:<",self.username,self.password,self.channel,self.server,self.leaseduration,">"

        self.auth=0 #where it's at in the authorization process
        if autoconnect:self.connect()
    def connect(self):
        """Connects to the server and starts the authentification process.
        """
        #override so it will start authorization process.
        if self.debug:print "PsEPRListener:doing connection."
        self.authentificated=False
        if not SocketListener.connect(self):
            if self.debug:print "No connection!"
            return False
        if self.debug:print "PsEPRListener:Connected..."

        # JRP 12/8/06
        # these last four lines look like it tries to
        # coummunicate with the router after a connection
        # they were commented out, but I uncommented them
        # 
        # this seemed to have the problem I was running
        # into where it was stuck in a loop printing
        # out "waiting for authentification <x> seconds
        # and it would wait until 60 then bomb out
        # and try another server 
        self.send(messages.connect1 %(self.server[0]))
        if self.debug:
            msg=messages.connect1 %(self.server[0])
            print "sent:",[msg]
        self.auth=1
        return True
    def close(self):
        """Closes the connection, stops all lease timers.
        """
        self.authentificated=False
        if self.debug:print "PsEPRListener:Closing..."
        #if not self.leasetimer is None:
        #    self.leasetimer.stop()
        self.leasetime=-1
        return SocketListener.close(self)
    def send_message(self,channel,toservice,toinstance,field,value,expiration=90):
        """sends a message via psepr (not recommended if authentificated is false)
        channel=psepr channel to send on
        toservice=string value for the Service field to send To
        toinstance=value to insert in the Instance field in the To tag
        field=string to insert as the value of the Payload/Field tag
        value=string to insert as the value of the Payload/Value tag
        expiration=integer value to pass as the expiration value of the payload.
        
            Note: toservice and toinstance can individually be None, however if toservice is None,
            the value of toinstance will not be used.  The two values are used mainly to restrict the number of
            listeners on a channel who can receive a certain message.
        """
        channel=self.__fixchannelname(channel)
        if toservice is None:
            self.send(messages.message1 %("id_"+str(random.randint(1,10000)),self.channel,self.username,socket.gethostname(),field,value,expiration))
            if self.debug:
                msg=messages.message1 %("id_"+str(random.randint(1,10000)),self.channel,self.username,socket.gethostname(),field,value,expiration)
                print "sending message:",[msg]
        elif toinstance is None:
            self.send(messages.message2 %("id_"+str(random.randint(1,10000)),self.channel,toservice,self.username,socket.gethostname(),field,value,expiration))
            if self.debug:
                msg=messages.message2 %("id_"+str(random.randint(1,10000)),self.channel,toservice,self.username,socket.gethostname(),field,value,expiration)
                print "sending message:",[msg]
        else:
            self.send(messages.message3 %("id_"+str(random.randint(1,10000)),self.channel,toservice,toinstance,self.username,socket.gethostname(),field,value,expiration))
            if self.debug:
                msg=messages.message3 %("id_"+str(random.randint(1,10000)),self.channel,toservice,toinstance,self.username,socket.gethostname(),field,value,expiration)
                print "sending message:",[msg]
    def send_messages(self,channel,toservice,toinstance,fvdict,expiration=90):
        """
            same as send_message, but multiple field/value pairs can be sent with a single command by placing
            the field/value pairs into the dictionary fvdict.
        """
        for i in fvdict.keys():
            self.send_message(channel,toservice,toinstance,i,fvdict[i],expiration)
    def resubscribe(self):
        """A method called to subscribe/resubscribe to a channel.

        This method should never be called by a user, it is instead to be used internally
        and by PsEPRReLeaseTimer objects.
        """
        msg=messages.subscribe1%("subscribe_"+str(random.randint(1,10000)),self.channel,self.username,socket.gethostname(),self.leaseduration,self.username+"-"+str(random.randint(0,10000)))
        if self.debug:
            print "PsEPRListener:sending subscribe message"
        self.send(msg)
        if self.debug:
            print "PsEPRListener:sent subscribe message:",[msg]
        #self.leasetimer=PsEPRReLeaseTimer(self,self.leaseduration)
        self.leasetime=time.time()
    def default_handler(self,data):
        """parses incoming psepr data and passes along full messages to the handler
        specified in the constructor.  Data passed to the handler is of the following
        tuple format(as defined by the messagerecompiled regular expression):
        (channelname,fromservice,frominstance,fieldname,fieldvalue)
        """

        #Stork Logging
        log_nest('pseprlib2', 'default_handler', 'pseprmessage', 'received', data)

        if data=='':#may indicate the connection was closed...
            if self.debug:print "PsEPRListener:ERROR?",[data],"Connection closed?"
            self.close()
            return
        if data=="</stream:stream>":#error? problem?
            if self.debug:print "PsEPRListener:ERROR?",[data]
            self.close()
            return
        #if self.debug and self.auth<5:print "received:",[data]
        if self.debug:print "PsEPRListener:received:",self.auth,[data]
        #must also handle the other error - the full-xml error message, but need a sample to work with
        if self.auth==1:
            self.send(messages.logon1%("logon_1",self.username))
            if self.debug:
                msg=messages.logon1%("logon_1",self.username)
                if self.debug:print "PsEPRListener:sending logon sequence msg:",[msg]
        elif self.auth==2:
            self.send(messages.logon2%("logon_2",self.username,self.password))
            if self.debug:
                msg=messages.logon2%("logon_2",self.username,self.password)
                if self.debug:print "PsEPRListener:sending logon sequence msg2:",[msg]
        elif self.auth==3:
            self.resubscribe()
        elif self.auth>=4:# parse the subscribe response as well, since many of them may be seen
            #add to buffer
            self.buffer+=data
            #split the messages by '</message>' -- set the buffer to the last item
            msgs=self.buffer.split('</message>')
            self.buffer=msgs[-1]
            msgs=msgs[:-1]
            if self.debug:
                print "PsEPRListener:msgcount(includes subscription messages):",len(msgs)
            for i in msgs:
                m=self.messagerecompiled.search(i)
                if not m is None:# a match!
                    self.message_handler(m.groups())
        if self.auth<5:
            self.auth+=1
            if self.auth>4:self.authentificated=True

    def run(self):
        #override the run method to send be able to handle resubscribe timer in-class
        while SocketListener.do_iteration(self):
            if not self.authentificated and self.auth==0:
                if self.debug:
                    print "PsEPRListener:sending first message"
                self.send(messages.connect1 %(self.server[0]))
                if self.debug:
                    msg=messages.connect1 %(self.server[0])
                    print "PsEPRListener:sent:",[msg]
                self.auth=1
                if self.debug:
                    print "PsEPRListener:first message sent."
                continue
            if self.authentificated and self.leasetime==-1:
                self.resubscribe()
            elif self.authentificated and time.time()>=self.leasetime+(self.leaseduration*0.9):
                self.resubscribe()
            time.sleep(0.5)
        if self.debug:
            print "PsEPRListener:do_iteration false -- left while loop."
        #ensure disconnected...
        self.close()

def GetPsEPRListener(username,password,msghandler,channel="/edu/arizona/stork2/psepr/",leaseduration=DEFAULT_LEASE_DURATION,timeout=60,servermanager=None,debug=False):
    """Attempts to find and return a valid PsEPRListener object and will keep attempting until it does.
    username=username for psepr
    password=password for psepr
    msghandler=message handler function to pass to the pseprlistener constructor
    channel=channel name to use - default is /edu/arizona/stork2/psepr/
    leaseduration=leaseduration to use - default is DEFAULT_LEASE_DURATION
    timeout=number of seconds to wait for an authentificated connection. - default is 60
    """
    if debug:print "GetPsEPRListener:Getting pseprlistener."
    if not servermanager:
        mgr=PsEPRServerManager()
        mgr.load_server_list_from_url()
    else:
        test_instance_type(servermanager,PsEPRServerManager,"GetPsEPRListener:")
        mgr=servermanager
    auth=False
    lst=None
    while not auth:
        if debug:print "GetPsEPRListener:starting pseprlistener sequence."
        otime=time.time()
        try:
            lst=PsEPRListener(username,password,channel,msghandler,mgr,leaseduration,True,debug)
            while not lst.authentificated and lst.listening:
                if debug:print "GetPsEPRListener:waiting for authentification:",time.time()-otime,"seconds waiting."
                time.sleep(1.0)
                if time.time()-otime>=timeout:break
            if lst.authentificated:auth=True
            else:
                if debug:print "GetPsEPRListener:closing listener - timeout?"
                lst.close()
        except:auth=False
    if debug:print "GetPsEPRListener:Found listener:",lst
    return lst

def __empty_msg_handler(data):pass

def SendPsEPRMessage(username,password,fieldname,data,channel="/edu/arizona/stork2/psepr/",toservice=None,toinstance=None,timeout=60,debug=False):
    """Creates a simple message handler and sends a single message with it.
    username=psepr username
    password=psepr password
    fieldname=Payload/Field tag value
    data = Payload/Value tag value
    channel=channel to send on - default = /edu/arizona/stork2/psepr/
    toservice= service to specify to send to - default is None
    toinstance= instance to specify to send to - default is None
    timeout=timeout to pass to GetPsEPRListener - default is 60
    """
    lst=GetPsEPRListener(username,password,__empty_msg_handler,channel,60,timeout,None,debug)
    lst.send_message(channel,toservice,toinstance,fieldname,data)
    lst.close()

def __test_msg_handler(data):print "handled:",data

def __test(username,password,seconds=60,leasetimer=180,messagespacing=5):
    """A simple testing function
    username= username
    password=password
    seconds = general number of seconds to wait before ending the test.
    leasetimer= number of seconds for the lease timer
    messagespacing= number of seconds between test messages
    """
    print "Testing the pseprlib..."
    mgr=PsEPRServerManager()#("jClient.xml")
    mgr.load_server_list_from_url()
    print "Testing Server Manager:",mgr.get_server()
    print "Starting the listener..."
    #lst=PsEPRListener(username,password,"/org/dsmt/ns/org.dsmt.container-mgr/",__test_msg_handler,mgr,DEFAULT_LEASE_DURATION,True,True)
    #lst=PsEPRListener(username,password,"/edu/arizona/stork2/psepr/test",__test_msg_handler,mgr,DEFAULT_LEASE_DURATION,True,True)
    lst=GetPsEPRListener(username,password,__test_msg_handler,"/edu/arizona/stork2/psepr/test",leasetimer,60,mgr,True)
    counter=0
    txt=""
    if os.path.isfile("/etc/resolv.conf"):
        fo=open("/etc/resolv.conf","r")
        txt=fo.read()
        fo.close()
    else:
        txt="""Simple Example Message:
    Test Test Test Test!"""
    print "Starting test..."
    for i in range(seconds):
        time.sleep(1)
        counter+=1
        if counter>=3:
            print i,"Seconds(appr.)."
            if lst.authentificated:
                lst.send_message("/edu/arizona/stork2/psepr/test/","arizona5",None,"resolv.conf",txt)
            else:print "Still waiting for authentification..."
            counter=0
    print "Ending test..."
    lst.close()
