#! /usr/bin/env python
"""
<Program Name>
   storklog.py

<Author>
   Programmed by Jeffry Johnston

<Purpose>
   Performs data collection, interpretation, and transfer.
"""

#           [option, long option,     variable,     action,  data,                                         default, metavar, description]
"""arizonaconfig
   options=[
            ["",       "--lockdir",            "lockdir",              "store",       "string", "/var/lock",                        "dir",   "use the specified mutex lock directory (default /var/lock)"],
            ["",     "--logdir",      "logdir",     "store", "string", "/tmp",                             "DIR",   "log file directory (default: /tmp)"],
            ["",     "--uploaddir",   "uploaddir",  "store", "string", "logs",                             "DIR",   "remote host upload directory (default: logs)"],
            ["",     "--uploadhost",  "uploadhost", "store", "string", "logging@stork-log.cs.arizona.edu",      "HOST",  "remote host name (default: logging@nr05.cs.arizona.edu)"],
            ["",     "--identitykey", "idkey",      "store", "string", "/usr/local/stork/bin/logging.key", "FILE",  "private key filename (default: /usr/local/stork/bin/logging.key)"],
            ["",     "--enablelogging","enablelogging","store_true", None, False,                           None,   "enable nest logging (off by default)"]
           ]
   includes=[]        
"""

import os
import syslog
import arizonageneral
import arizonaconfig
import time
import arizonareport
import sys
import storkerror
import random
import re

# globals
nodehost = ""
nodeuser = ""
clienthost = ""
clientip = ""
clientport = ""
clientuser = ""





def set_client(hostname, ip, port, username):
   """ TODO comment """
   global clienthost, clientip, clientport, clientuser
   if hostname != None:
      clienthost = hostname
   if ip != None:
      clientip = ip
   if port != None:
      clientport = port
   if username != None:
      clientuser = user

def get_hostname():
   hostname = None
   try:
      hostname = arizonageneral.gethostname()
   except:
      pass
   if hostname == None:
      hostname = "unknown_host"
   return hostname

def get_username():
   try:
      username = arizonageneral.getusername()
   except:
      username = "unknown_user"
   return username

def get_connect_log_filename():
   hostname = get_hostname()
   return "connect-"+hostname

def log_connect(what, data = None):
   # see if we should log this
   enable = arizonaconfig.get_option("enablelogging")
   logdir = arizonaconfig.get_option("logdir")
   if not enable:
      return

   logfile= logdir + "/" + get_connect_log_filename()

   if data:
      data = " " + data
   else:
      data = ""

   # prepare the string
   writeout = str(os.getpid()) + " " + what + data + "\n"

   # try to append to the file
   try:
      tempfile = open(logfile, "a")
      tempfile.write(writeout)
      tempfile.close()
   except:
      pass


def get_transfer_log_filename():
   hostname = get_hostname()
   return "transfer-"+hostname

def log_transfer(function, pid, timestamp, timestampend):
   """
   <Purpose>
      Log the status of a transfer function. this should
      happen on entry or exit of a function.

   <Arguments>
      function:
          the transfer stub ei: coblitz, http, etc
      pid:
          the pid that this stub is running in
      timestamp:
          a timestamp when this function started transf
      timestampend:
          when this function finished transfering
   """
   # see if we should log this
   enable = arizonaconfig.get_option("enablelogging")
   logdir = arizonaconfig.get_option("logdir")
   if not enable:
      return

   logfile= logdir + "/" + get_transfer_log_filename()

   # prepare the string
   writeout = function + " " + timestamp + " " + timestampend + " " + pid + "\n"

   # try to append to the file
   try:
      tempfile = open(logfile, "a")
      tempfile.write(writeout)
      tempfile.close()
   except:
      pass
   

def log_nest(module, function, tag, subtag, info):
   """
   <Purpose>
      Logging support for data collection.
 
   <Arguments>
      module:
              Calling module name.
      function:
              Calling function name. 
      tag:
              Main category tag.
      subtag:
              Category subtag, or None.
      info:
              Information to be logged.      

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   global nodehost, nodeuser
   
   # determine current time.  ***DO THIS FIRST***
   time1 = time.time()
   time2 = time.gmtime()

   # see if logging is enabled
   enabled = arizonaconfig.get_option("enablelogging")
   if not enabled:
      return
   
   try:
      # collect information
      if nodehost == None or nodehost == "":
         hostname = None
         try:
            hostname = arizonageneral.gethostname()
         except:
            pass
         if hostname == None:
            hostname = ""
            
      if nodeuser == None or nodeuser == "":
         try:
            nodeuser = arizonageneral.getusername()
         except:
            nodeuser = ""

      # normalize params
      if module == None:
         # should always have a module name, but fix regardless
         module = ""

      if function == None:
         # should always have a function name, but fix regardless
         function = ""
         
      if tag == None:
         # should always have a tag, but fix regardless
         tag = ""
      else:
         tag = tag.strip().lower()
         
      if subtag == None:
         subtag = ""
      else:
         subtag = subtag.strip().lower()
         
      if info == None:
         info = ""   

      # build message   
      mesg = "{time1}" + str(time1) + "{/time1}" + \
             "{time2}" + str(time2) + "{/time2}" + \
             "{nodehost}" + str(nodehost) + "{/nodehost}" + \
             "{nodeuser}" + str(nodeuser) + "{/nodeuser}" + \
             "{chost}" + str(clienthost) + "{/chost}" + \
             "{cip}" + str(clientip) + "{/cip}" + \
             "{cport}" + str(clientport) + "{/cport}" + \
             "{cuser}" + str(clientuser) + "{/cuser}" + \
             "{module}" + str(module) + "{/module}" + \
             "{function}" + str(function) + "{/function}" + \
             "{tag}" + str(tag) + "{/tag}" + \
             "{sub}" + str(subtag) + "{/sub}" + \
             "{info}" + str(info) + "{/info}" + \
             "{pid}" + str(os.getpid()) + "{/pid}"
             
      # write to syslog
      syslog.syslog(arizonareport.NOTICE, mesg)
   except:
      # if anything fails, we can't disrupt program operation
      pass   





def parse_line(line):
#   # hour
#   i = line.find(":")
#   hour = int(line[:i])
#   line = line[i + 1:]
#
#   # minute
#   i = line.find(":")
#   minute = int(line[:i])
#   line = line[i + 1:]
#
#   # second
#   i = line.find(".")
#   second = int(line[:i])
#   line = line[i + 1:]
#   
#   # fraction of a second   
#   i = line.find(" ")
#   fraction = hex(int(line[:i]))[2:]
#   line = line[i + 1:]
#
#   time = hex(3600 * hour + 60 * minute + second)[2:] + "." + fraction
   i = line.find(" ")
   time = line[:i]
   line = line[i + 1:]

   # protocol
   i = line.find(", proto ")
   j = line.find(", ", i + 1)
   protocol = line[i + 8:j]
   line = line[j + 2:]
   
   # length
   i = line.find(")")
   length = line[8:i]
   line = line[i + 2:]

   # source
   i = line.find(" > ")
   source = line[:i]
   line = line[i + 3:]
   
   # destination
   i = line.find(":")
   destination = line[:i]

   return time + " " + protocol + " " + length + " " + source + " " + destination + "\n"





def compress_packetlog(filename):
   fi = open(filename)
   filename_out = filename + "_pr"
   fo = open(filename_out, "w")
   for line in fi:
      try:
         pruned = parse_line(line)
      except:
         pruned = "*" + line
      fo.write(pruned)
   fo.close()
   fi.close()
   os.system("/usr/bin/bzip2 " + filename_out)

   return filename_out + ".bz2"


def compress_strace(filename):
   filename_out = filename + "_pr"
   os.system("/usr/local/stork/bin/filter-strac2 " + filename + " " + filename_out)
   os.system("/usr/bin/bzip2 " + filename_out)

   return filename_out + ".bz2"


def compress_bzip2(filename):
   # we use -k to keep the input file to mimic the behavior of the other
   # compress_ functions.
   os.system("/usr/bin/bzip2 -k " + filename)

   return filename + ".bz2"



# quick hack to back off the strace uploads
glo_seeded = False
def should_upload_strace():
    global glo_seeded

    if not glo_seeded:
        random.seed()
        glo_seeded = True

    if random.randint(0,24) == 1:
        return True
    else:
        return False

def upload_logs(suffix, subdir, currentName, compressFunc):
   # get list of files in logdir
   temp = os.listdir(arizonaconfig.get_option("logdir"))

   print "upload_logs " + str(suffix) + " " + str(subdir) + " " + str(currentName)

   # prune list to packetlog filenames only
   filelist = []
   for filename in temp:
      if filename.endswith(suffix):
         filelist.append(arizonaconfig.get_option("logdir") + "/" + filename)

   # remove packetlog file named in current.packetlog
   if currentName:
      try:
         temp = open(arizonaconfig.get_option("logdir") + "/" + currentName)
         current = temp.readline().strip()
         temp.close()
         filelist.remove(current)
      except:
         pass

   print "  filelist = " + str(filelist)

   # strip unneeded information from packet lines
   newlist = []
   for filename in filelist:
      newName = compressFunc(filename)
      newlist.append(newName)

   print "  newlist = " + str(newlist)

   # upload packetlogs to repository
   if len(filelist) > 0:
      #Place the packetlog in the proper folder
      target = __folder_destination(filelist[0])

      os.system("/usr/bin/ssh -o StrictHostKeyChecking=no -o BatchMode=yes -qi " + arizonaconfig.get_option("idkey") + " " + arizonaconfig.get_option("uploadhost") + " mkdir -p " + arizonaconfig.get_option("uploaddir") + "/" + subdir + "/" + target)

      status = os.system("/usr/bin/scp -o StrictHostKeyChecking=no -Bqi " + \
                          arizonaconfig.get_option("idkey") + " " + \
                          " ".join(newlist) + " " + \
                          arizonaconfig.get_option("uploadhost") + ":" + arizonaconfig.get_option("uploaddir") + "/" + subdir + "/" + target + " 1> /dev/null 2> /dev/null")

      # delete packetlogs
      if status == 0:
         for filename in filelist:
            try:
               os.remove(filename)
            except:
               pass

      # delete compressed versions
      for filename in newlist:
         try:
            os.remove(filename)
         except:
            pass

def upload_single_log(filename, suffix, subdir, compressFunc):
   filename = arizonaconfig.get_option("logdir") + "/" + filename

   newname = arizonaconfig.get_option("logdir") + "/" + get_hostname() + \
                                      "^" + get_username() + \
                                      "^" + str(time.time()) + suffix

   if not os.path.exists(filename):
       return

   try:
       os.rename(filename, newname)
   except:
       print "failed to rename " + str(filename) + " to " + str(newname)
       return

   upload_logs(suffix, subdir, None, compressFunc)





def rotate_logs():
   """ TODO comment """
   try:
     upload_logs("^packetlog", "packet", "current.packetlog", compress_packetlog)
   except:
     pass;

   try:
      upload_logs("^strac2", "strac2", "current.strac2", compress_strace)
   except:
      pass;

   try:
      upload_single_log(get_transfer_log_filename(), "^transfe2", "transfe2", compress_bzip2)
   except:
      pass;

   # get hostname, username, and timestamp
   hostname = None
   try:
      hostname = arizonageneral.gethostname()
   except:
      pass
   if hostname == None:
      hostname = "unknown_host"
   try:
      username = arizonageneral.getusername()
   except:
      username = "unknown_user"
   try:
      timestamp = str(time.time())
   except:
      timestamp = "unknown_time"

   # rotate syslog files
   os.system("/usr/sbin/logrotate -f /etc/logrotate.d/syslog 2> /dev/null")

   try:
      # get list of syslog files
      temp = os.listdir(arizonaconfig.get_option("logdir"))

      # prune list to syslog filenames only (and rename)
      oldlist = []
      filelist = []
      for filename in temp:
         if (filename.find("messages.") >= 0):
            oldname = arizonaconfig.get_option("logdir") + "/" + filename

            if oldname.endswith(".bz2"):
               # this file must be left from a previous attempt to upload
               # that crashed. We'll add it to the list to upload again.
               filelist.append(oldname)
            else:
               newname = arizonaconfig.get_option("logdir") + "/" + hostname + "^" + username + "^" + timestamp + "^" + filename + "^syslog"
               try:
                  os.rename(oldname, newname)
               except:
                  pass

               # compress syslog
               if not newname.endswith(".bz2"):
                  os.system("/usr/bin/bzip2 " + newname)

               oldlist.append((newname + ".bz2", oldname + ".bz2"))
               filelist.append(newname + ".bz2")

      ## upload syslogs to repository
      ##if len(filelist) > 0:
      #Upload files one at a time
      
      for file in filelist:
         #Place the packetlog in the proper folder
         target = __folder_destination(file)

         os.system("/usr/bin/ssh -o StrictHostKeyChecking=no -o BatchMode=yes -qi " + arizonaconfig.get_option("idkey") + " " + arizonaconfig.get_option("uploadhost") + " mkdir -p " + arizonaconfig.get_option("uploaddir") + "/syslog/" + target)
        
         status = os.system("/usr/bin/scp -o StrictHostKeyChecking=no -Bqi " + arizonaconfig.get_option("idkey") + " " + file + " " + arizonaconfig.get_option("uploadhost") + ":" + arizonaconfig.get_option("uploaddir") + "/syslog/" + target + " 1> /dev/null 2> /dev/null")

         # delete syslogs
         if status == 0:
            #for filename in filelist:
            try:
               os.remove(file)
            except:
               pass

# Do not restore original name to avoid redundancy, the file will be picked up with this filename
#         else:
#            # restore error report files back to original names
#            for filename in oldlist:
#               try:
#                  os.rename(filename[0], filename[1])
#                  if filename[1].endswith(".bz2"):
#                     os.system("/usr/bin/bzip2 -d " + filename[1])
#               except:
#                  pass
   except:
      pass

   if should_upload_strace():
     try:
        # filter the strace log
        try:
           os.system("/usr/local/stork/bin/filter-strace")
#           os.system("/bin/cp /tmp/transfer-`hostname` /tmp/transferpart-`hostname`.`date +%s`")
        except:
           pass

        # find any filtered strace files
        temp = os.listdir(arizonaconfig.get_option("logdir"))
        filelist = []
        translist = []
        for filename in temp:
           if filename.find("strace") >= 0 and filename.find("raw") < 0:
              name = arizonaconfig.get_option("logdir") + "/" + filename
              filelist.append(name)
           elif filename.find("transferpart") >= 0:
              name = arizonaconfig.get_option("logdir") + "/" + filename
              translist.append(name)

        # upload strace reports to repository
        if len(filelist) > 0:
           #Place the packetlog in the proper folder
           target = __folder_destination(filelist[0])

           os.system("/usr/bin/ssh -o StrictHostKeyChecking=no -o BatchMode=yes -qi " + arizonaconfig.get_option("idkey") + " " + arizonaconfig.get_option("uploadhost") + " mkdir -p " + arizonaconfig.get_option("uploaddir") + "/strace/" + target)

           status = os.system("/usr/bin/scp -o StrictHostKeyChecking=no -Bqi " + arizonaconfig.get_option("idkey") + " " + " ".join(translist) + " " + " ".join(filelist) + " " + arizonaconfig.get_option("uploadhost") + ":" + arizonaconfig.get_option("uploaddir") + "/strace/" + target + " 1> /dev/null 2> /dev/null")

           # delete strace reports
           if status == 0:
              for filename in filelist:
                 try:
                    os.remove(filename)
                 except:
                    pass
              for filename in translist:
                 try:
                    os.remove(filename)
                 except:
                    pass

     except:
        pass


   try: 
      # get list of error report files
      temp = os.listdir(arizonaconfig.get_option("logdir"))
      
      # prune list to error report filenames only (and rename)
      oldlist = []
      filelist = []
      for filename in temp:
         if filename.find(".error.") >= 0:
            oldname = arizonaconfig.get_option("logdir") + "/" + filename
            
            if oldname.endswith(".bz2"):
               # this file must be left from a previous attempt to upload
               # that crashed. We'll add it to the list to upload again.
               filelist.append(oldname)
            else:
               newname = arizonaconfig.get_option("logdir") + "/" + hostname + "^" + username + "^" + filename + "^errorreport"
               try:
                  os.rename(oldname, newname)
               except:
                  pass

               # compress error report
               if not newname.endswith(".bz2"):
                  os.system("/usr/bin/bzip2 " + newname)

               oldlist.append((newname + ".bz2", oldname + ".bz2"))
               filelist.append(newname + ".bz2")

      # upload error reports to repository
      if len(filelist) > 0:
         #Place the packetlog in the proper folder
         target = __folder_destination(filelist[0])

         os.system("/usr/bin/ssh -o StrictHostKeyChecking=no -o BatchMode=yes -qi " + arizonaconfig.get_option("idkey") + " " + arizonaconfig.get_option("uploadhost") + " mkdir -p " + arizonaconfig.get_option("uploaddir") + "/error/" + target)

         status = os.system("/usr/bin/scp -o StrictHostKeyChecking=no -Bqi " + arizonaconfig.get_option("idkey") + " " + " ".join(filelist) + " " + arizonaconfig.get_option("uploadhost") + ":" + arizonaconfig.get_option("uploaddir") + "/error/" + target + " 1> /dev/null 2> /dev/null")

         # delete error reports
         if status == 0:
            for filename in filelist:
               try:
                  os.remove(filename)
               except:
                  pass   
         else:
            # restore error report files back to original names            
            for filename in oldlist:
               try:
                  os.rename(filename[0], filename[1])
                  if filename[1].endswith(".bz2"):
                     os.system("/usr/bin/bzip2 -d " + filename[1])
               except:
                  pass
   except:
      pass   


def __folder_destination(file):
   l = re.compile("\^([0-9]+)")
   m = l.search(file)
   target = ""
   if(m):
      number = m.group(1)
      target = ""
     
      number = number[:-3]
      while len(number) > 3:
         target = number[-3:] + "/" + target
         number = number[:-3]
         
      target = number + "/" + target
   return target

def main():
   # prepare error reporting tool
   storkerror.init_error_reporting("storklog.py")
   
   # parse command line and options
   args = arizonaconfig.init_options(module="storklog.py", version="2.0")

   # check for root
   if os.geteuid() > 0:
      arizonareport.send_error(0, "You must be root to run this program...")
      sys.exit(1)

   # grab the storklog mutex. This prevents multiple copies of storklog from
   # running at the same time.
   storklogLock = arizonageneral.mutex_lock("storklog", arizonaconfig.get_option("lockdir"))
   if not storklogLock:
       arizonareport.send_error(0, "Another copy of storklog is already running...")
       sys.exit(0)

   # rotate, upload, and delete logs
   rotate_logs()





if __name__ == "__main__":
   main()
