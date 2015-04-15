#! /usr/bin/env python

"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: storktrackusage
Description:  Tracks usage of files
"""

# Use arizonaconfig
#           [option, long option,       variable,        action,  data,     default, metavar,    description]
"""arizonaconfig
   options=[["",     "--tempusagefilename", "tempUsageFileName", "store", "string", "/usr/local/stork/var/filesopened.temp",      None, "track usage of stork files (this session)"],
            ["",     "--permusagefilename", "permUsageFileName", "store", "string", "/usr/local/stork/var/filesopened.perm",      None, "track usage of stork files (last session)"]]
   includes=[]
"""

import arizonaconfig
import arizonacrypt
import arizonareport
import sys
import os

file_list = []

def reset():
   tempUsageFileName = arizonaconfig.get_option("tempUsageFileName")
   if os.path.exists(tempUsageFileName):
      os.remove(tempUsageFileName)

def add_file(filename):
   if filename in file_list:
       return

   # get the hash of the file
   if os.path.exists(filename):
      hash = arizonacrypt.get_fn_hash(filename)
   else:
      hash = "doesnotexist"

   file_list.append(filename)

   try:
       tempUsageFileName = arizonaconfig.get_option("tempUsageFileName")
       file = open(tempUsageFileName, "a")
       if file:
           file.write(filename + " " + hash + "\n")
           file.close()
   except IOError:
       arizonareport.send_error(0, "failed to write to usage file ")
   except OSError:
       arizonareport.send_error(0, "failed to write to usage file ")

def commit():
   permUsageFileName = arizonaconfig.get_option("permUsageFileName")
   tempUsageFileName = arizonaconfig.get_option("tempUsageFileName")
   if os.path.exists(permUsageFileName):
      os.remove(permUsageFileName)
   if os.path.exists(tempUsageFileName):
      os.rename(tempUsageFileName, permUsageFileName)

def verify():
   result = True

   permUsageFileName = arizonaconfig.get_option("permUsageFileName")

   # open and read the file
   file = open(permUsageFileName, "r")
   lines = file.readlines()

   # there could be duplicate lines because multiple copies of stork may have
   # been invoked from one run of pacman
   lines = uniq(lines)

   for line in lines:
       splitline = line.split(" ")
       (filename, last_hash) = (splitline[0], splitline[1])

       # get the hash of the file
       if os.path.exists(filename):
          hash = arizonacrypt.get_fn_hash(filename)
       else:
          hash = "doesnotexist"

       if (hash != last_hash):
          arizonareport.send_out("hash mismatch file " + filename + " last=" + last_hash + " cur =" + hash)
          result = False

   return result





