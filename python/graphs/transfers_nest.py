#! /usr/bin/env python
import sys
import re
import os

def main():

   log = {};
   protocol = [];


   match = re.compile("\{info\}\[arizona_stork2\] Attempting download via\: (.+)\{\/info\}")
   fail = re.compile("\{info\}\[arizona_stork2\] (.*) failed to retrieve any files, trying next method\.\{\/info\}")

   count = 0
   for file in os.listdir(sys.argv[1]):
      print("%d. %s" % (count, file)) 
      os.system("bzcat %s > /tmp/logbuild" % file)
      f = open("/tmp/logbuild")      
      for line in f.readlines():
         m = match.search(line)
         if(m):
            try:
               log[m.group(1)] = log[m.group(1)] + 1
            except KeyError:
               log[m.group(1)] = 1
               protocol.append(m.group(1))
               
         m = fail.search(line)
         if(m):
            try:
               log[m.group(1) + "_fail"] = log[m.group(1) + "_fail"] + 1
            except KeyError:
               log[m.group(1) + "_fail"] = 1
      f.close
      count = count + 1   

   print("%10s\t%s\t%s" % ("Protocol","Uses","Failed"))     
   print("===")
   for i in protocol:
      success = log[i]
      fail = 0
      try:
         fail = log[i + "_fail"]
      except KeyError:
         pass

      print("%10s\t%d\t%d" % (i, success, fail))
         
   
   
if __name__ == "__main__":
   if len(sys.argv) != 2:
      print("Usage: trans.py directory")
      sys.exit()

   main()
