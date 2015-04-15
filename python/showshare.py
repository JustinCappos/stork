#! /usr/bin/env python

"""
<Program Name>
   showshare.py

<Started>
   Feb 13, 2007

<Author>
   Programmed by Scott Baker.

<Purpose>
   Given the name of an RPM package, tells which files are shared. Used for 
   diagnosing issues with nest sharing. Shared files are determined by hard-
   link count. If a file has '1' link, then it is not shared. If a file has
   '2' or more links, then it _might_ be shared. 

   TODO: We could get accurate information if we asked the nest to compare
         inode numbers.

   TODO: Do things like this belong in the main stork/arizonalib distribution?
         should we create a seperate place for small tools?
"""

#           [option, long option,    variable,     action,        data,     default,                            metavar, description]
"""arizonaconfig
   options=[
            ["-C",   "--configfile", "configfile", "store",       "string", "/usr/local/stork/etc/stork.conf", "FILE",   "use a different config file (/usr/local/stork/etc/stork.conf is the default)"]]
   includes=[]
"""

import os
import arizonageneral
import arizonareport
import storkerror
import arizonaconfig
import storkversion
import sys

# for ST_NLINK
from stat import *

def get_installed_files(pack_list):
   """
   <Purpose>
      Given a string list of packages, return a string list of installed
      files.

   <Arguments>
      pack_list:
              String list of installed packages

   <Exceptions>
      TypeError:
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      String list of installed files
   """
   # check params
   arizonageneral.check_type_stringlist(pack_list, "pack_list", "get_installed_files")

   if not pack_list:
      return []

   out = os.popen("rpm -ql" + arizonageneral.list_to_args(pack_list) + " 2>/dev/null")
   retlist = []
   for line in out:
      line = line.rstrip()
      if line.endswith("is not installed"):
         arizonareport.send_out(0, "ERROR: " + line)
      else:
         retlist.append(line)
   out.close()
      
   return retlist




   
def showsharing(pack_list):
   file_list = get_installed_files(pack_list)

   unsharecount = 0
   sharecount = 0
   missingcount = 0

   for file in file_list:
      if not os.path.exists(file):
         arizonareport.send_out(0, "M " + file)
         missingcount = missingcount + 1
      else:
         links = os.stat(file)[ST_NLINK]

         if links == 1:
            arizonareport.send_out(0, "  " + file)
            unsharecount = unsharecount + 1 
         elif links >= 2:
            arizonareport.send_out(0, "S " + file)
            sharecount = sharecount + 1

   arizonareport.send_out(0, "# 'S' indicates a file is shared or multiply hard-linked")
   arizonareport.send_out(0, "# " + str(missingcount) + " files missing")
   arizonareport.send_out(0, "# " + str(sharecount) + " files shared (or otherwise hard-linked)")
   arizonareport.send_out(0, "# " + str(unsharecount) + " files not shared")





def main(args):
   """ TODO comment """

   global glo_exitstatus;

   # check params
   arizonageneral.check_type_stringlist(args, "args", "showsharing.main")

   if not args:
      print "This program is used to determine which files in a package are"
      print "shared. It does this by looking at the number of hard links"
      print "for each file in an rpm."
      print ""
      print "syntax: showshare [rpm_name...]"
      sys.exit(0)

   # process command line and initialize variables
   showsharing(args)

   sys.exit(0)

   



# Start main
if __name__ == "__main__":
   try:
      # use error reporting tool
      storkerror.init_error_reporting("stork.py")

      # get command line and config file options
      args = arizonaconfig.init_options("showshare.py", configfile_optvar="configfile", version=storkversion.VERREL)

      main(args)
   except KeyboardInterrupt:
      arizonareport.send_out(0, "Exiting via keyboard interrupt...")
      sys.exit(0)
