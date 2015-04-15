#! /usr/bin/env python

"""
<Program Name>
   storkverifysignedfile.py

<Started>
   June 18, 2006

<Author>
   Programmed by Jeremy Plichta

<Purpose>
   Uses functions from arizonacrypt to take a signed file and
   verify it using the public key in its file name. This program
   will mainly be called from the PHP/Webpage end to verify the
   authenticity of a non-packagefile after upload.
   
   This program should be used for newly uploaded tp files.
   If the uploaded tp is valid it will check to see if there
   is already a tp file named the same in tpfiledir. If a
   file is found in there it will only overwrite it if the
   timestamp on the uploaded file is newer then the timestamp
   on the file that was already in the repository
   
   Added: This program will also be used to verify 
   signitures on pacman configuration files. In fact
   this can be used to check the authenticity on any file
   that has been wrapped and signed using storkutil.
   
   This program will look in tmpuploaddir for the file you specify,
   then if it is signed correctly and is newer than any existing file
   in endfiledir it will move the file to movefiledir

   Possible exit codes:
-1 (255)  means that there was an internal error (dir doesnt exist, oserror, etc)
0 - should not get this
1 - error/file not signed correctly
2 - overwriting old file with newer file
3 - tried to upload older, or same ver of file, will not overwrite
4 - brand new file

"""

#           [option, long option,      variable,       action,  data,     default,                           metavar, description]
"""arizonaconfig
   options=[["-C",   "--configfile",   "configfile",   "store", "string", "/usr/local/stork/etc/stork.conf", "FILE", "use a different config file (/usr/local/stork/etc/stork.conf is the default)"],
            ["",     "--endfiledir",    "endfiledir",    "store", "string", "/repository/user-upload/tpfiles",             "DIR",  "use the specified directory where the signed files are stored upon upload (default is /repository/user-upload/tpfiles)"],
            ["",     "--tmpuploaddir", "tmpuploaddir", "store", "string", "/repository/user-upload/tmp",                 "DIR",  "use the specified temp non-package upload directory (default is /repository/user-upload/tmp)"]]
   includes=[]        
"""

import sys
import os
import arizonacrypt
import arizonageneral
import arizonaconfig
import arizonareport
import storkpackage


def main():
   
   #get command line options
   args = arizonaconfig.init_options("storkverifysignedfile.py", configfile_optvar="configfile", version="2.0")
   if len(args) != 1:
      arizonareport.send_error(1, "Usage: storkverifysignedfile.py [OPTION(s)] signedfile")
      sys.exit(-1)
   
   
   tmpuploaddir = arizonaconfig.get_option("tmpuploaddir")
   endfiledir    = arizonaconfig.get_option("endfiledir")
   

   if tmpuploaddir[-1] != "/": # add trailing slash if there isn't one
      tmpuploaddir += "/" 
   if not os.path.isdir(tmpuploaddir): 
       arizonareport.send_out(1, tmpuploaddir + " does not exist, could not verify authenticity of "+args[0])
       sys.exit(-1);
   if endfiledir[-1] != "/": # add trailing slash if there isn't one
      endfiledir += "/" 
   if not os.path.isdir(endfiledir): 
       arizonareport.send_out(1, endfiledir + " does not exist, could not verify authenticity of "+args[0])
       sys.exit(-1);
   
       
   filename = args[0];
   
   timestamp1 = verify_file(filename, tmpuploaddir)
   if timestamp1 > 0:
       arizonareport.send_out(2, "File " + filename + " has been verified.")
   else:
       arizonareport.send_out(2, "File " + filename + " has a bad signature.")
       sys.exit(1)

   #check to see if there is another copy of
   #this tp file in the tp file dir
   if os.path.isfile(endfiledir+filename):
       #there is another copy, get the timestamp
       timestamp2 = verify_file(filename,endfiledir)
       if timestamp2 < 0:
           #something is wrong... once validily signed tp file
           #is no longer valid... should I report this to someone?
           arizonareport.send_out(0, "Once valid signed file " + endfiledir+filename + " is no longer valid.")
           sys.exit(-1)
       
       # now check to see if the new file has a newer timestamp then the old
       # file... if it does, replace it
       if timestamp1 > timestamp2:
           arizonareport.send_out(2,"Overwriting " + filename + " with newer version of tp file...")
           move_file(tmpuploaddir+filename,endfiledir+filename)
           sys.exit(2);
       # the file they tried to upload is older then then the file in the repository... so dont
       # replace it
       else:
           arizonareport.send_out(2,"Will not overwrite " + filename + " with older or same version of uploaded file.")
           sys.exit(3)
   else:               
       # this tp file is not in the repository yet.... move it there now
       arizonareport.send_out(2,"Moving " + filename + " to the tp file dir now...")
       move_file(tmpuploaddir+filename,endfiledir+filename)
       sys.exit(4)       
   
   
def move_file(src,dst):
    try:
       os.rename(src,dst)
    except OSError:
       if not os.path.isdir(dst):
           arizonareport.send_out(0, "dir: " + arizonaconfig.get_option("endfiledir") + " does not exist")
           sys.exit(-1)
       elif not os.access(dst,os.W_OK):
           arizonareport.send_out(0, "Not enough permissions to move tp file to " + dst)
	   sys.exit(-1)
       else:
           arizonareport.send_out(0, "Error while replacing file: " + src)
           sys.exit(-1)

#take a filename and a path and verify it using the functions
#in arizonacrypt.py
def verify_file(filename, path):
   try:
       file_dict = arizonacrypt.XML_validate_file(os.path.join(path, filename))
   except TypeError:
       arizonareport.send_out(0, "Error when verifying signature")

       if not arizonageneral.valid_fn(os.path.join(path, filename)):
           arizonareport.send_out(0, "Error accessing file '"+path+filename+"'")

       # -1 seems to be treated as an exit status
       return -1

   timestamp = file_dict.get("timestamp", 0)
   expired = file_dict.get("expired", False)

   if expired:
       arizonareport.send_out(0, "Expired file detected")
       timestamp = -1

   return timestamp
           


if __name__ == "__main__":
    main()
