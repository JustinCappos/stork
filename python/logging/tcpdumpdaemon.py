#! /usr/bin/env python

"""
<Program Name>
   tcpdumpdaemon.py

<Started>
   February 3, 2007

<Author>
   Programmed by Jeffry Johnston

<Purpose>
   Collects packet information from tcpdump and saves as files in one hour
   increments.
   
   Note: Planetlab use requires that the following line be included in  
         /etc/passwd:
         
         pcap:x:77:77::/var/arpwatch:/bin/nologin
"""

#           [option, long option,  variable,   action,  data,     default, metavar,   description]
"""arizonaconfig
   options=[
            ["",     "--logdir",   "logdir",   "store", "string", "/tmp",  "DIR",     "log file directory (default: /tmp)"],
            ["",     "--interval", "interval", "store", "int",    3600,    "SECONDS", "wait at least this number of seconds before opening a new log file (default 3600)"]
           ]
   includes=[]        
"""

import arizonaconfig
import signal
import arizonageneral
import os
import sys
import time
import storkerror

done = False
pipe = None





def handler_sighup(signum, frame):
    """
    <Purpose>
       Intercepts the HUP signal.
    """
    global done, pipe
    
    try: 
       pipe.flush()
       pipe.close()
    except:
       pass   
    pipe = None
    done = True





def main(): 
   global done, pipe

   # parse command line and options
   args = arizonaconfig.init_options(module="tcpdumpdaemon.py", version="2.0")

   # run as a daemon 
   arizonageneral.make_daemon("tcpdumpd")
   
   # make it easy to kill the daemon 
   outfile = open("/tmp/tcpdump.pid", "w")
   outfile.write(str(os.getpid()))
   outfile.close()
   
   # set up I/O
   pipe = os.popen("/usr/sbin/tcpdump -tt -v -nn 2> /dev/null", "r")
   
   # set up hangup signal handler
   signal.signal(signal.SIGHUP, handler_sighup)

   lasttime = 0
   
   while not done:
      # is it time to change log file?
      currtime = time.time()
      if currtime - lasttime >= arizonaconfig.get_option("interval"): 
         lasttime = currtime 

         # build filename
         filename = None
         try:
            filename = arizonageneral.gethostname()
         except:
            pass
         if filename == None:
            filename = "unknown_host"
         try:
            username = arizonageneral.getusername()
         except:
            username = "unknown_user"
         filename = arizonaconfig.get_option("logdir") + "/" + filename \
                    + "^" + username + "^" + str(currtime) + "^packetlog" 
         
         # close old file
         try:
            outfile.flush()
         except:
            pass
         try:
            outfile.close()
         except:
            pass
            
         # create current.packetlog file
         try:
            tempfile = open(arizonaconfig.get_option("logdir") + "/current.packetlog", "w")
            tempfile.write(filename)
            tempfile.close()
         except:
            pass   
            
         # open new file   
         try:    
            outfile = open(filename, "a")
         except:   
            pass
   
      # read stdin
      if not done:    
         try:
            line = pipe.readline()
         except:
            done = True
          
      # write to file      
      if not done:    
         try:
            outfile.write(line)
         except: 
            pass   
      if not done:    
         try:
            outfile.flush()
         except: 
            pass   
   
      #dont eat up cycles
      time.sleep(1)

   # clean up
   try:
      outfile.close()
   except: 
      pass   
      
   os.system("/bin/rm -f /tmp/tcpdump.pid &> /dev/null")
   
   
   
     

if __name__ == "__main__":
   # prepare error reporting tool
   storkerror.init_error_reporting("tcpdumpdaemon.py")
      
   # call main
   main()
