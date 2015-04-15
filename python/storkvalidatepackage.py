#! /usr/bin/env python

"""
<Program Name>
   storkvalidatepackage.py

<Started>
   July 9th, 2006

<Author>
   Programmed by Jeremy Plichta

<Purpose>
   This program is meant to be called from the php/webapp side to verify if 
   a uploaded package is indeed valid (or that is a package that stork
   currently understands. It does this by simply taking in a package name 
   as a argument and using storkpackage.py to validate it.
   
"""

#           [option, long option,      variable,       action,  data,     default,                           metavar, description]
"""arizonaconfig
   options=[["-C",   "--configfile",   "configfile",   "store", "string", "/usr/local/stork/etc/stork.conf", "FILE", "use a different config file (/usr/local/stork/etc/stork.conf is the default)"],
            ["",     "--updir",    "updir",            "store", "string", "/tmp",             "DIR",  "use the specified directory where files are uploaded (default: /tmp) "],
            ["",     "--metadata", "metadata",         "store_true", None, False,                            None, "check validity of a metadata file, not a package"]]
   includes=[]        
"""

import sys
import os
import arizonareport
import arizonaconfig
import storkpackage

def is_valid_metadatafile(filepath):
   # TODO: finish me
   return True

def main():
       #get command line options
   args = arizonaconfig.init_options("storkvalidatepackage.py", configfile_optvar="configfile", version="2.0")
   if len(args) != 1:
      arizonareport.send_error(1, "Usage: storkvalidatepackage.py [OPTION(s)] <packagename>")
      sys.exit(1)

   dir = arizonaconfig.get_option("updir")

   filepath = dir + '/' + args[0]
   if not os.path.isfile(filepath):
       arizonareport.send_error(1, "[storkvalidatepackage.py] " + filepath + " is not a valid file.")
       sys.exit(1)
       

   # check to see if the user has uploaded a metadata file
   if arizonaconfig.get_option("metadata"):
      if is_valid_metadatafile(filepath):
         arizonareport.send_out(1, filepath + " is a valid metadata file.")
         sys.exit(0)
      else:
         arizonareport.send_out(1, filepath + " is NOT a valid metadata file.")
         sys.exit(1)

   if storkpackage.is_package_understood(filepath):
       arizonareport.send_out(1, filepath + " is a valid package.")
       sys.exit(0)
   else:
       arizonareport.send_out(1, filepath + " is NOT a valid package.")
       sys.exit(1)





if __name__ == "__main__":
    main()
