#! /usr/bin/env python

"""
<Program Name>
   stracedaemon.py

<Started>
   February 3, 2007

<Author>
   Programmed by Jeffry Johnston

<Purpose>
   Collects packet information from strace and saves as files in one hour
   increments.

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
import arizonareport
import time

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


LOGSUFFIX = "^strac2"
CURRENTFILE = "current.strac2"
DAEMONNAME = "straced"
DAEMONPIDFILE = "/tmp/strace.pid"

# the name of the file that contains the pid that we want to monitor with
# strace
INPUT_PIDFILE = "/var/run/stork_nest_comm.py.pid"

def main():
   global done, pipe

   # parse command line and options
   args = arizonaconfig.init_options(module="stracedaemon.py", version="2.0")

   # run as a daemon
   arizonageneral.make_daemon(DAEMONNAME)

   # make it easy to kill the daemon
   outfile = open(DAEMONPIDFILE, "w")
   outfile.write(str(os.getpid()))
   outfile.close()

   # check to make sure the service we want to monitor exists
   if not os.path.exists(INPUT_PIDFILE):
       # sleep a few seconds and try again, just in case stork_nest_comm
       # was launched, but has not yet written its pidfile
       time.sleep(10)
       if not os.path.exists(INPUT_PIDFILE):
           # raise an exception to generate an error report
           raise Exception, "the stork nest is not running"
           # the following does not happen
           arizonareport.send_error(0, "the stork nest is not running")
           sys.exit(-1)

   # get the pid we want to monitor from INPUT_PIDFILE
   input_pidfile = open(INPUT_PIDFILE)
   input_pid = input_pidfile.read()
   input_pidfile.close()

   arizonareport.send_out(0, "monitoring pid " + str(input_pid))

   command = '(strace -f -ttt -e trace=network -p ' + str(input_pid)+ ' 2>&1 1>/dev/null)' + \
             ' | (egrep "AF_INET")'

#             ' | egrep "connect\([0-9]+, \{sa_family=AF_INET.* = 0" 2>/dev/null' + \
#             ' | fgrep -v "127.0.0.1"' + \
#             ' | awk \'"*" { gsub("(\\[pid )|(\\])|(sin_port=htons\\()|(\\),)|(sin_addr=inet_addr\\(.)|(.\\)\\},)","", $0); print $1 " " $2 " " $5 " " $6; }\''


   arizonareport.send_out(0, "executing: " + command)

   # set up I/O
   # XXX run the command
   pipe = os.popen(command, "r")

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
                    + "^" + username + "^" + str(currtime) + LOGSUFFIX

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
            tempfile = open(arizonaconfig.get_option("logdir") + "/" + CURRENTFILE, "w")
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
      
   os.system("/bin/rm -f " + DAEMONPIDFILE + " &> /dev/null")





if __name__ == "__main__":
   # prepare error reporting tool
   storkerror.init_error_reporting("stracedaemon.py")

   # call main
   main()
