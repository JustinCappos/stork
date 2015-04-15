#!/usr/bin/env python
#
# pseprpusher.py - Pushes out a given file via PsEPR.

import pseprlib2 as pseprlib
import arizonacrypt as cryptlib
import arizonaxml as xmllib
import sys
import os
import time
import storkerror
import arizonareport
import arizonaconfig

########################### MAIN ###############################
def main():
   arizonaconfig.init_options("*", version="2.0", configfile_optvar="configfile")

   if len(sys.argv)!=4:
      print """Usage:  pseprpusher.py FILENAME NEWFILENAME PRIVATEKEY
      Where FILENAME is the file you wish to push out via PsEPR,
      NEWFILENAME is the filename/path to send via psepr,
      and PRIVATEKEY is the full file path of the private key to use"""
      sys.exit()

   fname=sys.argv[1]

   if not os.path.isfile(fname):
      print fname,"is not a valid file."
      sys.exit(1)

   #copy the file
   fo=open(fname,"r")
   rd=fo.read()
   fo.close()
   tfname="/tmp/"+os.path.split(fname)[1]
   if tfname=="/tmp/":
      print "ERROR: unable to extract filename from path:",fname
      sys.exit(1)
   tfname+=str(time.time())#in case multiple updates are attempted simultaneously
   fo=open(tfname,"w")
   fo.write(rd)
   fo.close()

   #sign it
   try:
      # for compatibility with old versions of Stork not supporting certified
      # filenames, set certify_filename to False
      cryptlib.XML_sign_file_using_privatekey_fn(tfname, sys.argv[3], certify_filename=False)
   except Exception, e:
      print "ERROR: unable to sign message.", e
      if tfname and os.path.isfile(tfname):os.unlink(tfname)
      sys.exit(1)

   #read and delete
   fo=open(tfname,"r")
   fdata=fo.read()
   fo.close()

   os.unlink(tfname)

   #ensure that it's xml safe
   fdata=xmllib.escape(fdata)

   #send it
   pseprlib.SendPsEPRMessage("arizona_stork2","etlk3vXZ23d",sys.argv[2],fdata)





# Start main
if __name__ == "__main__":
   try:
      storkerror.init_error_reporting("pseprpusher.py")
      main()
   except KeyboardInterrupt:
      arizonareport.send_out(0, "Exiting via keyboard interrupt...")
      sys.exit(0)
