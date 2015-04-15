#! /usr/bin/env python

# Jeffry Johnston
# Find/Replace Program
# August 16, 2005

#           [option, long option, variable,  action,  data,     default, metavar,  description]
"""arizonaconfig
   options=[["",   "--findstr", "findstr", "store", "string", None,      "TEXT",   "text to find"],
            ["",   "--replacestr", "replacestr", "store", "string", None,      "TEXT",   "replacement text"]]
   includes=[]
"""

import arizonaconfig
import arizonageneral





def main():

   args = arizonaconfig.init_options('replace.py', usage='usage: replace.py [options] FILE...', version='2.0')

   find_text = arizonaconfig.get_option("findstr")
   if find_text == None:
      print "Must specify string to find.  See --help."
      return

   replace_text = arizonaconfig.get_option("replacestr")
   if replace_text == None:
      print "Must specify replacement string.  See --help."
      return

   (status, failed_list) = arizonageneral.text_replace_files_in_fnlist(find_text, replace_text, args)

   if not status:
      print "Cannot locate or access: " + " ".join(failed_list)

   return
   




# Start main
if __name__ == "__main__":
   try:
      main()
   except KeyboardInterrupt:
      print "Exiting via keyboard interrupt..."



