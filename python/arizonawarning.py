#! /usr/bin/env python

"""
<Program Name>
   storkphonehome.py

<Started>
   Nov 05, 2007

<Author>
   Scott Baker

<Purpose>
   Support for lightweight error messages / warnings. Errors are reported via
   a http "GET" request to stork-repository.

   NOTE: This code was taken from tools/stork/phonehome.py. A more complete
   version of this code lives there.
"""

import socket
import time
import sys
import os
import arizonaconfig
import arizonageneral




#           [option, long option,               variable,          action,        data, default, metavar, description]
"""arizonaconfig
   options=[
            ["",     "--warningurl",            "warningurl",      "store",       "string", None,    None,    "URL to use when logging warnings"]]
   includes=[]
"""




def get_file_modify_time(fn):
   """ return last-modify-time of a file """
   try:
       return os.stat(fn)[8]
   except OSError:
       return -1





def get_log_time(fn):
   """
   Search for initscript log files in /usr/local/stork/var/log/initscript
   and /tmp. Return the modify time of the newest log file.
   """
   t1 = -1
   t2 = -1
   fn1 = os.path.join("/usr/local/stork/var/log/initscript", fn)
   if os.path.exists(fn1):
       t1 = get_file_modify_time(fn)
   fn2 = os.path.join("/tmp", fn)
   if os.path.exists(fn2):
       t2 = get_file_modify_time(fn2)
   return max(t1, t2)


def phonehome(name, status=0):
   # get the time when the machine was booted
   timeBoot = get_file_modify_time("/var/log/boot.log")

   # get the time when the initscript was started
   timeInitScriptStart = get_log_time("stork_initscript_stage1.log")

   # get the time when the initscript installed the packages, before running
   # stork for the first time
   timeInitScriptPreRunStork = get_log_time("stork_initscript_stage2_prerunstork.log")

   # get the time when the initscript was completed
   timeInitScriptFinish = get_log_time("stork_initscript_stage2_complete.log")

   slicename = arizonageneral.getslicename()
   if not slicename:
      slicename = "unknownslicename"

   # some of these don't really make sense here; they were used for the
   # arizona_stork_install tests
   retryCount = 0
   timeLastInstall = 0
   timeTestStart = time.time()
   timeReport = time.time()

   try:
       warningUrl = arizonaconfig.get_option("warningurl")
   except:
       warningUrl = None

   try:
       status = str(status).replace('"', "'").replace(" ", "_")
   except:
       pass

   if not warningUrl:
       warningUrl = "http://stork-repository.cs.arizona.edu/phonehome/phonehome.php"

   cmd = 'curl "' + warningUrl + \
          "?name=" + str(name) + \
          "&slice=" + str(slicename) + \
          "&host=" + str(socket.gethostname()) + \
          "&timeBoot=" + str(int(timeBoot)) + \
          "&timeNow=" + str(int(timeTestStart)) + \
          "&retryCount=" + str(retryCount) + \
          "&timeLastInstall=" + str(int(timeLastInstall)) + \
          "&timeReport=" + str(int(timeReport)) + \
          "&status=" + str(status) + \
          "&timeInitScriptStart=" + str(int(timeInitScriptStart)) + \
          "&timeInitScriptPreRunStork=" + str(int(timeInitScriptPreRunStork)) + \
          "&timeInitScriptFinish=" + str(int(timeInitScriptFinish)) + \
          "&filenameSuffix=storkwarning" + \
          '"'

   os.system(cmd)





def log_warning(name, status=0):
   try:
      phonehome(name, status)

   except: # leave this as general exception; we don't want to crash in this code
      pass

