#!/usr/bin/python

"""
<Program Name>
   storkpseprattempt.py

<Started>
    Oct 20th, 2006

<Author>
   Programmed by Jeremy Plichta

<Purpose>
    The purpose of this program is to try to call pseprpusher.py to push a file
    via psepr, but have a timeout. This is a workaround because we know that 
    pseprpusher.py is hanging sometimes.
   
"""


"""arizonaconfig
   options=[["-C",   "--configfile",   "configfile",   "store", "string", "/usr/local/stork/etc/stork.conf", "FILE", "use a different config file (/usr/local/stork/etc/stork.conf is the default)"],
            ["",     "--updir",    "updir",    "store", "string", "/tmp",             "DIR",  "use the specified directory where files are uploaded (default: /tmp) "]]
   includes=[]        
"""

import sys
import os
import arizonareport
import arizonaconfig
import storkpackage
import arizonageneral


def main():
     args = arizonaconfig.init_options("storkpseprattempt.py", configfile_optvar="configfile", version="2.0")
     # SMB: doubled it to 32 seconds
     wait = 32;
     global pid_file;

     # SMB: changed filename to psepr.pid to disambiguate from other pid files
     pid_file =  "/repository/psepr.pid"

     # SMB: removed check for existing pid file, since it appears to be done
     # already by attemptpsepr.init
     pid = os.getpid()
     pid_file_obj = open(pid_file, "w")
     pid_file_obj.write(str(pid))
     pid_file_obj.close()
     
     if len(args) < 3:
         print "incorrect usage."
         os.unlink(pid_file)
         sys.exit(-1)
         
    # print args[0]
    # print args[1]
    # print args[2]
     
     pseprpath = "/usr/local/stork/bin/pseprpusher.py"
     
     if not os.path.isfile(pseprpath):
         print "could not find "+pseprpath
         
     command = pseprpath + " " + args[0] + " " + args[1] + " " + args[2]

     finished_ok = False

     finished_ok ,status = arizonageneral.system_timeout_backoff(command, 5, wait, 9)

     if finished_ok:
         print command + " FINISHED OK"
     else:
         print command + " FAILED"
    
     os.unlink(pid_file)
     
     

if __name__ == "__main__":
    try:
        main();
    except KeyboardInterrupt:
        print "exiting via interrupt"
        os.unlink(pid_file)
        sys.exit(-1)








