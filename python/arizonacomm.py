#! /usr/bin/env python

"""
<Program Name>
   arizonacomm.py

<Started>   
   November 7, 2005

<Author>
   Jeffry Johnston

<Purpose>
   Client-server communications.
"""

import socket
import sys
import time
import types
import arizonageneral
import arizonareport
import traceback
from threading import Thread
import storklog


# How much to read at one time
BLOCK_SIZE = 1024

# End of command sequence
EOL = "\r\n"

# Default command start character
COMMAND_START = "$"

# Default pulse character (completely ignored in input)
PULSE = "#"

# Default escape character
ESCAPE = "\\"

# Replacement escape character for the lost PULSE character
# Will be ESCAPE + PULSE_REPLACE
PULSE_REPLACE = "p" # \p

glo_comm = None
glo_data = ""
glo_stop = False





def connect(host, port):
   """ 
   <Purpose>
      Connects to a listening server on the given host and port.

   <Arguments>
      host:
	      Hostname or IP address of the machine to connect to.
      port:
	      Port to connect on.

   <Exceptions>
      TypeError if a bad parameter is detected.
      IOError if socket communications fails.
   
   <Side Effects>
      Sets glo_comm and glo_data.

   <Returns>
      None.
   """
   global glo_comm

   # check params
   arizonageneral.check_type_simple(host, "host", str, "arizonacomm.connect")
   arizonageneral.check_type_simple(port, "port", int, "arizonacomm.connect")

   __init_session()

   __check_connection()
   if glo_comm == None:
      try:
	 glo_comm = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	 glo_comm.connect((host, port))
      except socket.error, e:
	 raise IOError, e   





def listen(host, port, handler, max_pending=5):
   """ 
   <Purpose>
      Listens for client connections on the given local host and port.  
      When a connection is established, forks off a child process for the 
      connection and passes control to the specified handler function, 
      while the parent continues to listen for additional connections.

      The handler will be passed two arguments, a str and an int: the 
      connected ip address and port.  The handler return value will be 
      ignored.

   <Arguments>
      port:
	      Port to listen for connections on.
      handler:	 
	      Function that handles the connection.  Should return as soon
	      as possible so that future connections may be handled 
	      promptly.  Will be passed two arguments (str and int): the 
	      connected ip address and port.  Any handler return value 
	      will be ignored.
      max_pending:
	      Maximum allowable number of pending connections.

   <Exceptions>
      TypeError if a bad parameter is detected.
      IOError if socket communications fails.
   
   <Side Effects>
      Sets glo_comm and glo_data.

   <Returns>
      None.
   """
   global glo_comm

   # check params
   arizonageneral.check_type_simple(host, "host", str, "arizonacomm.listen")
   arizonageneral.check_type_simple(port, "port", int, "arizonacomm.listen")
   arizonageneral.check_type(handler, "handler", [types.FunctionType, types.MethodType], "arizonacomm.listen")
   arizonageneral.check_type_simple(max_pending, "max_pending", int, "arizonacomm.listen")
   
   # Close the connection if one is currently open
   __check_connection()
   if glo_comm:
      glo_comm.close()

   # Flush any previous communication data
   __init_session()

   # Get ready to accept connections...
   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   s.bind((host, port))
   s.listen(max_pending)

   while True:
      try:
	 comm, addr = s.accept()
      except socket.error, e:
	 # to handle signal interrupt exceptions
	 if str(e)[:3] == "(4,":
	    continue 
	 else:
	    raise IOError, e

      # Set up the new session
      glo_comm = comm
      __init_session()

      # Call the user provided function
      handler(addr[0], addr[1])

      # Close the connection if they forgot...
      __check_connection()
      if glo_comm:
	 glo_comm.close()
      




def handle_session(commands, command_start=COMMAND_START):
   """ 
   <Purpose>
      Monitors the current connection, awaiting data and commands.
      Once a command has been detected, the data is dispatched to 
      the function associated with the received command.  
      
      Compatible functions take a single string as input.  Any
      return value is ignored.  
      
      Note: now turns off blocking on the socket to better catch
      disconnections.
   <Arguments>
      commands:
	      Dictionary of command -> function associations, where 
	      command is the input to look for, and function is a pointer 
	      to the function to call to process the received command 
	      data.  Commands should not start with the command_start
	      character (it is added automatically).
      command_start:
	      Command start character.  If encountered in the input, it 
              will trigger a command, unless it is repeated, in which case
	      the command_start character is treated as input.  For 
              example, if the command_start character is `$', then `$cmd'
              is a command, but `$$' is treated as a regular input 
              character `$'.	 

   <Exceptions>
      TypeError if a bad parameter is detected.
      IOError if socket communications fails.
   
   <Side Effects>
      Modifies glo_data.

   <Returns>
      Returns a list of the unique items in the original list.
   """
   global glo_data
   global glo_stop
   
   # check params
   arizonageneral.check_type(commands, "commands", [[dict, str]], "arizonacomm.handle_session")
   arizonageneral.check_type_simple(command_start, "command_start", str, "arizonacomm.handle_session")
   if len(command_start) != 1:
      raise TypeError("arizonacomm.handle_connection: command_start string must be exactly 1 character in length.")
   for command in commands:
      arizonageneral.check_type(commands[command], "command " + command + " in commands", [types.FunctionType, types.MethodType], "arizonacomm.handle_connection")

   arizonareport.send_out(4, "[" + arizonageneral.getusername() + "] Escape character: `" + command_start + "'")
   arizonareport.send_out(4, "[" + arizonageneral.getusername() + "] Handling commands: " + ", ".join(commands))

   glo_stop = False
   while not glo_stop:      
      # find a command
      i_start = 0
      while i_start >= 0:
         i_start = glo_data.find(command_start, i_start)
         
         # Found a command_start character, but is it doubled?  If it is, 
         # then this is just data, and not the start of a command.
         if i_start > 0 and glo_data[i_start + 1: ] == command_start:
            # skip past the doubled command_start 
            i_start += 2
         else:
            break

      # was a command found? (i.e. was there an command_start character?)
      if i_start >= 0:
         i_end = -1
         while i_end < 0:
            # read command until the EOL character
            i_end = glo_data.find(EOL, i_start + 1)
            if i_end < 0:
               # no command end, read another block from the connection
               glo_data += __read().replace(PULSE, "")
               
         # separate command from data      
         # original block: data, command_start, command
         command = __unescape(glo_data[i_start + 1: i_end]) # strip off command_start
         data = glo_data[: i_start] 

         # replace doubled command_start's in data with single characters
         data = __unescape(data.replace(command_start + command_start, command_start))
         
         # remove used data from global buffer (it has been processed)
         glo_data = glo_data[i_end + len(EOL): ]
         if commands.has_key(command):
            arizonareport.send_out(4, "[" + arizonageneral.getusername() + "] Received command: `" + str(command) + "', with data `" + str(data) + "'.")
            storklog.log_nest("arizonacomm", "handle_session", "command", command, data)
            commands[command](data)
         else:
            # bad command sent: disconnect 
            print "[" + arizonageneral.getusername() + "] Bad command: `" + str(command) + "', data `" + str(data) + "'.  Disconnecting."
            storklog.log_nest("arizonacomm", "handle_session", "bad", command, data)
            disconnect()
            break
      else:
         # no command, read another block of data from the connection
         glo_data += __read().replace(PULSE, "")

   arizonareport.send_out(4, "[" + arizonageneral.getusername() + "] Session ended")





def send(command, data, command_start=COMMAND_START):
   """ 
   <Purpose>
      Send a change mode command to the remote connection.

   <Arguments>
      command:
	      Command string (the new mode).  
      data:
	      Data for the command.
      command_start:
              Character sent to indicate the start of a command.	      

   <Exceptions>
      TypeError if a bad parameter is detected.
      IOError if socket communications fails.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   # check params
   arizonageneral.check_type_simple(command, "command", str, "arizonacomm.send")
   arizonageneral.check_type_simple(data, "data", str, "arizonacomm.send")
   arizonageneral.check_type_simple(command_start, "command_start", str, "arizonacomm.send")
   if len(command_start) != 1:
      raise TypeError("arizonacomm.send: command_start string must be exactly 1 character in length.")
   if len(command) < 1:
      raise TypeError("arizonacomm.send: command must be at least 1 character in length.")
   
   # send command
   #arizonareport.send_out(4, "[DEBUG] Sending command: `" + command + "', with data: `" + data + "'.")
   storklog.log_nest("arizonacomm", "send", "", command, data)
      
   data = data.replace(command_start, command_start + command_start)
   buf = data + command_start + command + EOL
   while len(buf) > 0:
      try:
         #arizonareport.send_out(4, "[DEBUG] Send: " + str(traceback.format_stack()))
	 sent = glo_comm.send(buf)
      except socket.error, e:
	 raise IOError, e   
      buf = buf[sent:]





def sendraw(data):
   """ 
   <Purpose>
      Send raw data to the remote connection.

   <Arguments>
      data:
	      Data to be sent.

   <Exceptions>
      TypeError if a bad parameter is detected.
      IOError if socket communications fails.
   
   <Side Effects>
      None.

   <Returns>
      None
   """
   # check params
   arizonageneral.check_type_simple(data, "data", str, "arizonacomm.send")

   storklog.log_nest("arizonacomm", "sendraw", "", "", data)
   
   # send data
   while len(data) > 0:
      try:
	 sent = glo_comm.send(data)
      except socket.error, e:
	 raise IOError, e   
      data = data[sent:]




def __unescape(s):
   escape = False
   r = ""
   for c in s:
      if escape:
         escape = False
         if c == ESCAPE:
            # example: \\ -> \ (doubled escape)
            r += ESCAPE
         elif c == PULSE_REPLACE:
            # example: \p -> # (replace with lost PULSE)
            r += PULSE
         else:
            # bad escape sequence
            raise ValueError, "Invalid escape sequence: " + str(ESCAPE) + str(c) + ", glo_data=`" + str(glo_data) + "'"
      elif c == ESCAPE:
        # character is the escape character, don't do anything yet
        escape = True
      else:
         # example ab -> b (last char wasn't an escape char, so print this one)
         r += c
       
   # Duy Nguyen - Workaround: Problem in executing storknestrpm 
   #if escape:
      # if string ended with an escape character
      #raise ValueError, "Unterminated escape sequence, glo_data=`" + str(glo_data) + "'"
      
   return r





def __init_session():
   """ 
   <Purpose>
      Initializes a new command session.  

   <Arguments>
      None

   <Exceptions>
      None.
   
   <Side Effects>
      Sets glo_stop = False, glo_data = ""

   <Returns>
      None.
   """
   global glo_stop
   global glo_data
   glo_stop = False
   glo_data = ""





def end_session():
   """ 
   <Purpose>
      End the current command session.  Note: to disconnect, use the 
      disconnect function.

   <Arguments>
      None

   <Exceptions>
      None.
   
   <Side Effects>
      Sets glo_stop = True

   <Returns>
      None.
   """
   global glo_stop
   glo_stop = True





def disconnect(reason=""):
   """ 
   <Purpose>
      Disconnect the current connection.  Note: to end the current session
      without disconnecting, use end_session function.

   <Arguments>
      None

   <Exceptions>
      None.
   
   <Side Effects>
      Sets glo_stop = True

   <Returns>
      None.
   """
   global glo_comm
   end_session()
   
   try:
      glo_comm.close()
   except socket.error, e:
      raise IOError, e   
   glo_comm = None   
   arizonareport.send_out(4, "[" + arizonageneral.getusername() + "] Disconnecting (" + str(reason) + ")")





def __check_connection():
   """ 
   <Purpose>
      Checks to see if the current connection has been broken.

   <Arguments>
      None

   <Exceptions>
      None.
   
   <Side Effects>
      Sets glo_comm = None if not connected.

   <Returns>
      None.
   """
   global glo_comm,EOL
   if glo_comm != None:
      try:
	 # check if we're truely alive with a blocking socket... 
	 glo_comm.sendall(PULSE)
      except socket.error:
	 glo_comm = None
	 arizonareport.send_out(4, "[" + arizonageneral.getusername() + "] Socket error (connection closed)")





def __read():
   """ 
   <Purpose>
      Reads a block of data from the current connection.

   <Arguments>
      None

   <Exceptions>
      IOError if socket communications fails.
   
   <Side Effects>
      None.

   <Returns>
      Data read from the connection.
   """
   try:
      data = glo_comm.recv(BLOCK_SIZE)
      if len(data) == 0:
	 # if nothing was received then the connection has been lost
	 arizonareport.send_out(4, "[" + arizonageneral.getusername() + "] Nothing received, disconnecting")
	 disconnect()
   except socket.error, e:
      raise IOError, e

   return data




#just a wrapper
def check_types(list,function,modulename=None):arizonageneral.check_types(list,function,modulename)

class single_conn(Thread):
   """
   <Purpose>
      Wraps up the client side of arizonacomm into a single class.
   <Author>
      Jason Hardies
   <Side Effects>
      Defaults to running itself in a thread.
   """
   EOL='\r\n'
   ESCAPE = "$"
   def __init__(self,host,port,commands,handler=None,escape=ESCAPE,autostart=True,nonblocking=False):
      """
      <Purpose>
	 Initializes the class.
	 (see handle_session above for more details)
      <Arguments>
	 host,port = host,port to connect to
	 commands = commands (as in the handle_session function above)
	 escape = escape character
	 autostart = whether to automatically start the thread (default: true)
	 nonblocking = whether to use nonblocking sockets or not (default: false)
      <Exceptions>
	 TypeError if a bad parameter is detected.
      <Side Effects>
	 if autostart is true, will start itself in a thread.
      """
      Thread.__init__(self)
      self.host=host
      self.port=port
      self.commands=commands
      self.escape=escape
      self.handler=handler
      self.connected=False
      self.nonblocking=nonblocking
      self.done=False
      self.sock=None
      self.readsleep=0.2 # see the comment in read()
      self.retrysleep=600 # how long to sleep before attempting to reconnect
      if handler is None:self.handler=handler=self.default_handler
      tlist=[[host,str],[port,int],[commands,[[dict,str]]],[handler,[types.FunctionType,types.MethodType]],[escape,str],[autostart,bool],[nonblocking,bool]]
      check_types(tlist,single_conn.__init__)
      #DEBUG:print "single_conn:init:autostarting"
      if autostart:self.start()
   def stop(self):
      """
      <Purpose>
	 Should stop the thread.  If nonblocking is set to false, it may remain waiting for the next read.
      """
      #DEBUG:print "single_conn:stop:stopping"
      self.done=True
      self.disconnect()
   def disconnect(self):
      """
      <Purpose>
	 Attempts to disconnect and reset the socket variable.
      """
      #DEBUG:print "single_conn:disconnect:attempting disconnect"
      if not self.sock is None:
	 #DEBUG:print "single_conn:disconnect:attempting to close socket"
	 try:self.sock.close()
	 except:pass
	 self.sock=None
      self.connected=False
   def connect(self,host=None,port=None):
      """
      <Purpose>
	 Connects to the specified host/port.  This will be done automatically if start() or run() are called.
      <Arguments>
	 host,port = host,port to connect to
      <Exceptions>
	 TypeError if a bad parameter is detected.
      <Returns>
	 A bool indicating the success of the connection.
      """
      #DEBUG:print "single_conn:connect:starting connect sequence",self.connected
      if self.connected and not self.sock is None:return True
      if not host is None:self.host=host
      if not port is None:self.port=port
      check_types([[host,[types.NoneType,str]],[port,[types.NoneType,int]]],single_conn.connect)
      try:
	 self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	 self.sock.connect((self.host, self.port))
	 #DEBUG:print "single_conn:connect:connected"
	 if self.nonblocking:self.sock.setblocking(0)
      except socket.error, e:
	 #DEBUG:print "single_conn:connect:error:",str(e)
	 try:self.sock.close()
	 except:pass
	 self.sock=None
	 return False
      self.connected=True
      return True
   def send(self,command,data,escape=ESCAPE):
      """
      <Purpose>
	 Sends a mesage to the host. Modeled after the send function above.
      <Arguments>
	 command = command string (does not require a starting escape)
	 data = data string
	 escape = escape character
      <Exceptions>
	 TypeError if a bad parameter is detected.
      """
      #DEBUG:print "single_conn:send:starting send"
      # check params
      tlist=[[command,str],[data,str],[escape,str]]
      check_types(tlist, single_conn.send)
      if len(escape) != 1:
	 #DEBUG:print "single_conn:send:bad escape char:",[escape]
	 raise TypeError("arizonacomm.single_conn.send: escape string must be exactly 1 character in length.")
   
      # send command
      #print "[DEBUG] Sending command: `" + command + "', with data: `" + data + "'."   
      data = data.replace(escape, escape*2)
      if command[0]==escape:command=command[1:]
      command=command.replace(escape,escape*2)
      buf = data + escape + command + EOL
      while len(buf) > 0:
	 try:
	    sent = self.sock.send(buf)
	 except socket.error, e:
	    #DEBUG:print "single_conn:send:send error",str(e)
	    raise IOError, e   
	 buf = buf[sent:]
      #DEBUG:print "single_conn:send:message sent"
   def recv(self,length=1024,loop=True):
      """
      <Purpose>
	 Receives data based on the type of connection.
      <Arguments>
	 length = how many bytes to specify to recv.
	 loop   = whether to loop until data is received
      <Exceptions>
	 TypeError if a bad parameter is detected.
      <Returns>
	 None if no data (or a blocking socket received an empty string), otherwise the data.
      """
      #paramcheck
      #DEBUG:print "single_conn:recv:starting recv"
      check_types([[length,int],[loop,bool]],single_conn.recv)
      done=False
      data=''
      while not done:
	 if not loop:done=True
	 if self.nonblocking:
	    try:
	       data=self.sock.recv(length)
	       if len(data) ==0:#lost connection
		  self.disconnect()
		  return None
	       else:return data
	    except socket.error:pass
	 else:
	    try:
	       data=self.sock.recv(length)
	       if len(data)>0:return data
	    except socket.error,e:
	       #DEBUG:print "single_conn:recv:socket error:",str(e)
	       #connection issue - disconnect!
	       self.disconnect()
	       return None
	 time.sleep(self.readsleep) #doesn't matter how small this value is, as long as it sleeps a little, that will prevent it from eating up cpu
      return None
   def default_handler(self,commands,recvmethod=None,escape=ESCAPE):
      """
      <Purpose>
	 The default handler for incoming data.
	 (see handle_session above for more details)
      <Arguments>
	 commands = commands (as in the handle_session function above)
	 recvmethod = the method to use to receive the data (defaults to self.recv)
	 escape = escape character
      <Exceptions>
	 TypeError if a bad parameter is detected.
      <Side Effects>
	 Calls the methods associated with commands received.
      """
      global glo_restr
      #DEBUG:print "single_conn:default_handler:starting"
      if recvmethod is None:recvmethod=self.recv
      # check params - note that recvmethod could be either a function or method type
      check_types([[commands,[[dict,str]]],[recvmethod,[types.MethodType,types.FunctionType]],[escape,str]],single_conn.default_handler)
      if len(escape) != 1:
	 raise TypeError("arizonacomm.single_conn.default_handler: escape string must be exactly 1 character in length.")
      for command in commands:
	 arizonageneral.check_type(commands[command], "command " + command + " in commands", [types.FunctionType,types.MethodType], "arizonacomm.single_conn.default_handler")
      
      if not hasattr(self,'buffer'):self.buffer=''
      connected=True #an assumption that may be changed with the first call of the recv method
      
      #esc=escape
      #if escape in ".$^+*?(){}()\\[]|":esc="\\"+escape
      #cescape=re.compile(glo_restr.replace('%s',esc),re.S)
      
      while connected:
	 #DEBUG:print "single_conn:default_handler:starting loop iteration"
	 data=None
	 try:data=recvmethod()
	 except:data=None
	 if data is None:
	    connected=False
	    break
	 self.buffer+=data
	 while self.EOL in self.buffer:
	    #DEBUG:print "single_conn:default_handler:starting EOL iteration"
	    cmdstr,self.buffer=self.buffer.split(self.EOL,1)
	    if not escape in cmdstr:
	       # bad command sent: disconnect
	       print "Invalid command string: `" + cmdstr + "'.  Disconnecting."   
	       connected=False
	       disconnect()
	       break
	    #find the command break
	    cmdb=len(cmdstr)
	    while cmdb!=-1:
	       cmdb=cmdstr.rfind(escape,0,cmdb-1)
	       if not cmdstr[cmdb-1]==escape:
	          break
	    cmdstr=[cmdstr[:cmdb].replace(escape*2,escape),cmdstr[cmdb+1:].replace(escape*2,escape)]
	    #try:cmdstr=cescape.match(cmdstr).groups()
	    #except AttributeError,e:
	    #   print "Invalid command string: `" + cmdstr + "'.  Disconnecting."   
	    #   connected=False
	    #   disconnect()
	    #   break
	    #cmdstr=[cmdstr[0].replace(escape*2,escape),cmdstr[-1].replace(escape*2,escape)]
	    if not (commands.has_key(cmdstr[1]) or commands.has_key(escape+cmdstr[1])): #order is data,command -- this should also weed out the case where all the escapes are escaped (ie. no single escapes to point out the command)
	       # bad command sent: disconnect
	       print "Bad command in: `" + str(cmdstr) + "'.  Disconnecting."   
	       connected=False
	       disconnect()
	       break
	    if commands.has_key(cmdstr[1]):commands[cmdstr[1]](cmdstr[0])
	    else:commands[escape+cmdstr[1]](cmdstr[0])

   def run(self):
      """
      <Purpose>
	 The main loop of the class.  Handles connecting, reconnecting, and calling the handler.
      """
      #DEBUG:print "single_conn:run:starting"
      while not self.done:
	 #DEBUG:print "single_conn:run:loop iteration"
	 #try to connect
	 self.connect()
	 #if connected, handle the session
	 if self.connected:self.handler(self.commands,self.recv,self.escape)
	 #DEBUG:else:print "single_conn:run:no connection"
	 #if disconnected, retry in 5 min.
	 if not self.done:time.sleep(self.retrysleep)

class listener(Thread):
   """
   <Purpose>
      Wraps up the host side of the arizonacomm functions (with the help of check_connection below).
   <Author>
      Jason Hardies
   <Side Effects>
      Defaults to running itself in a thread.
   """
   def __init__(self,port,handler=None,resethandler=None,maxpending=5,autostart=True):
      """
      <Purpose>
	 Initializes the class.
      <Arguments>
	 port = port to bind to
	 handler = the method to call when accepting a new socket (defaults to default_handler method)
	 resethandler = the method to call when the listening socket has died (defaults to default_reset_handler method)
	 maxpending = the maximum queue size for incoming connections
	 autostart = whether to start the thread automatically or not (default: True)
      <Exceptions>
	 TypeError if a bad parameter is detected.
      <Side Effects>
	 if autostart is true, will start itself in a thread.
      """
      Thread.__init__(self)
      self.port=port
      self.handler=handler
      self.resethandler=resethandler
      self.maxpending=maxpending
      self.done=False
      self.sock=None
      self.default_nonblocking=True
      if handler is None:self.handler=handler=self.default_handler
      if resethandler is None:self.resethandler=resethandler=self.default_resethandler
      tlist=[[port,int],[handler,[types.FunctionType,types.MethodType]],[resethandler,[types.FunctionType,types.MethodType]],[maxpending,int],[autostart,bool]]
      check_types(tlist,listener.__init__)
      if autostart:self.start()
   def stop(self):
      """
      <Purpose>
	 Called to attempt to stop the listener.
	 Note: this will not stop the socket's accept method, so this will likely not kill the thread."""
      self.done=True
   def default_handler(self,sock,addr):
      """
      <Purpose>
	 The default handler for socket accept events.
      <Arguments>
	 sock = the socket of the new connection
	 addr = the tuple/list of the address
      <Exceptions>
	 TypeError if a bad parameter is detected.
      <Side Effects>
	 Creates/appends to a list attribute (connlist) and sets all sockets to nonblocking if default_nonblocking is true.
      """
      check_types([[sock,socket._socketobject],[addr,[tuple,list]]],listener.default_handler)
      if not hasattr(self,'connlist'):self.connlist=[]
      if self.default_nonblocking:sock.setblocking(0)
      self.connlist.append((sock,addr))
   def default_resethandler(self):
      """
      <Purpose>
	 The default method called when the listening socket must be reset.
      <Side Effects>
	 closes all sockets and empties the connlist attribute if it exists.
      """
      #since we lost the original socket, it's probably a good idea to force everyone to reconnect.
      if hasattr(self,'connlist'):
	 for i in self.connlist:
	    try:i[0].close()
	    except:pass
	 self.connlist=[]
   def default_list_check(self):
      """
      <Purpose>
	 Checks all sockets in the connlist attribute, removing disconnected sockets from the list.
	 Note: this is best used with the default_handler and assumes nonblocking behavior when default_nonblocking is
	    set to true.
      <Side Effects>
	 will add the connlist attribute if it doesn't exist.
      """
      if not hasattr(self,'connlist'):self.connlist=[]
      i=0
      while i<len(self.connlist):
	 if not type(self.connlist[i]) in [list,tuple] or len(self.connlist[i])<2 or self.connlist[i][0] is None:
	    self.connlist=self.connlist[:i]+self.connlist[i+1:]
	    continue
	 if not check_connection(self.connlist[i][0],self.default_nonblocking):
	    self.connlist=self.connlist[:i]+self.connlist[i+1:]
	    continue
	 i+=1
   def run(self):
      """
      <Purpose>
	 The main loop - called by start() as a thread (or with autostart on), or called
	 directly to use the current thread."""
      while not self.done:
	 #attempt to use the port
	 #would do check_connection here, but it doesn't make sense for a listening socket.
	 skiplisten=False
	 if not self.sock is None:
	    try:self.sock.close()
	    except:pass
	    self.sock = None
	 try:
	    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	    self.sock.bind(("127.0.0.1", self.port))
	 except socket.error:skiplisten=True
	 #listen to the port...
	 if not skiplisten:
	    self.sock.listen(self.maxpending)
	    while not self.done:
	       try:
		  comm, addr = self.sock.accept()
	       except socket.error, e:
		  # to handle signal interrupt exceptions
		  if str(e)[:3] == "(4,":
		     continue 
		  else:break #we'll just try resetting
		     #raise IOError, e
	       #call the handler
	       self.handler(comm,addr)
	 #wait 5 minutes if we errored/could not get the port to try again.
	 if not self.sock is None:self.resethandler()
	 if not self.done:time.sleep(600)

def check_connection(sock=None,nonblocking=False):
   """
   <Purpose>
      Checks if a given socket is still 'alive' using the given nonblocking bool value to determine the method to use. 
      If a socket is defined, this will assume to use that socket instead of the global.
   <Arguments>
      sock = the socket to check (will use the global socket by default)
      nonblocking = a bool value indicating whether or not to assume the socket has blocking turned on
   <Exceptions>
      TypeError if a bad parameter is detected.
   <Side Effects>
      if autostart is true, will start itself in a thread.
   <Returns>
      False if not connected, otherwise a true value.  With nonblocking set to true, this may return the
      string received, if any.
   """
   global glo_comm,EOL
   if sock is None and glo_comm is None:return False
   if sock is None and not glo_comm is None:sock=glo_comm
   check_types([[sock,socket._socketobject],[nonblocking,bool]],check_connection)
   if not nonblocking:
      try:
	 sock.sendall("####"+EOL)
	 sock.sendall("####"+EOL)
      except socket.error:
	 return False
   else:
      rd=""
      try:
	 rd=sock.recv(1024)
	 if rd is None or len(rd)==0:return False
	 return rd
      except socket.error,e:
	  if e.args[0]==9:return False 
   return True
      
      
