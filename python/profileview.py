#! /usr/bin/env python
"""
<Program Name>
   profileview.py

<Started>
   June 21, 2006

<Author>
   Programmed by Jeffry Johnston.

<Purpose>
   Display profiler statistics.
   
   To gather statistics
   --------------------
   import hotshot
   output_filename = "stork.profile"
   p = hotshot.Profile(output_filename)
   
   # the following performs a main(args) call, change as needed
   p.runcall(main, args) 
   p.close()
   
   #COMMENT THE ORIGINAL CALL
   #main(args)  
"""


#           [option, long option,  variable,   action,  data,  default, metavar, description]
"""arizonaconfig
   options=[   
            ["",     "--numstats", "numstats", "store", "int", 0,      "NUM",   "number of lines of statistics to show (default: 0, print all)"]]
   includes=[]        
"""

import sys
import arizonaconfig
import hotshot.stats



def main():
   # get command line and config file options
   args = arizonaconfig.init_options("profileview.py", usage="profileview.py [options] filename", version="2.0")

   if len(args) != 1:
      arizonaconfig.print_help()
      sys.exit(1)
   
   stats = hotshot.stats.load(args[0])
   stats.strip_dirs()
   stats.sort_stats("time", "calls")
   numstats = arizonaconfig.get_option("numstats")
   if numstats == 0:
      stats.print_stats()
   else:
      stats.print_stats(numstats)



if __name__ == "__main__":
   main()
