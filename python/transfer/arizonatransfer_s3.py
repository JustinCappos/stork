#! /usr/bin/env python
"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: arizonatransfer_http
Description:   Provides a general file transferring by HTTP

"""

import urllib
import urllib2
import os
import time
import arizonareport
import arizonageneral
import storks3

def log_transfer(function, pid, timestamp, timestampend):
   try:
      import storklog
      storklog.log_transfer(function, pid, timestamp, timestampend)
   except:
      pass

      
def close_transfer_program():
   """
   <Purpose>
      This closes a connection (dummy function for HTTP).

   <Arguments>
      None.
   
   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      True.
   """
 
   return True



def init_transfer_program(ignore=None, ignore2=None, ignore3=None, ignore4=None):
   """
   <Purpose>
      This initializes a connection (dummy function for HTTP).

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      True.
   """
   # import the stork S3 module
   storks3.init()
   return True




def retrieve_files(junk_host, filelist, destdir='.', indicator=None):
   """
   <Purpose>
      This retrieves files from a host to a destdir.

   <Arguments>
      host:
         'host' holds two things, a server name and target directory.
         For example, if you want to retrieve files from '/tmp/' directory
         in 'quadrus.cs.arizona.edu' server, the 'host' will be
         'quadrus.cs.arizona.edu/tmp'.

      filelist:
         'filelist' is a list of files which need to be retrieved.

      destdir:
         'destdir' is a destination directory where retrieved files will
         be placed. A user should have 'destdir' exist before retrieving
         files. 'destdir' should be a string. Default is a current dir.

      indicator:
         'indicator' is a module which has set_filename and
         download_indicator functions. 'indicator' will be passed in
         'urlretrieve' function so that progress bar will be shown
         while downloading files. Default is 'None'.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      (True, grabbed_list)
      'grabbed_list' is a list of files which are retrieved
   """
   # set grabbed_list as a empty list. Later it will be appended with retrieved files
   grabbed_list = []

   # TODO - check type of filelist

   arizonageneral.check_type_simple(destdir, "destdir", str, "arizonatransfer_s3.init")

   # check that the destination directory exists
   if not os.path.isdir(destdir):
      arizonareport.send_syslog(arizonareport.ERR, "\nretrieve_files(): The destination directory '" + destdir + "' for a requested does not exist")
      # return false and empty list
      return (False, grabbed_list)

   # if destdir is a empty string, then make it as a current directory
   if destdir == '':
      destdir = '.'

   # go through every file in the file list
   for file in filelist:
      filename = file['filename']
      hash = file.get('hash', None)

      starttime = time.time()

      destfilename = os.path.join(destdir, filename)
      remotename = filename + '-' + hash

      try:
         arizonareport.send_out(1, "arizonatransfer_s3: attempting to retrieve " + remotename)

         storks3.get_file(remotename, destfilename)

         grabbed_list.append(file)
         endtime = time.time()
         log_transfer("s3", str(os.getpid()), str(starttime), str(endtime))

      # if file is not permitted to be retrieved
      except TypeError, e:
         arizonareport.send_syslog(arizonareport.ERR, 'retrieve_files(): "' + str(e) + '" on the file "' + filename + '"')

   if (grabbed_list) :
      return (True, grabbed_list)
   # if nothing in grabbed_list
   else:
      return (False, grabbed_list)



def transfer_name():
   """
   <Purpose>
      This gives the name of this transfer method.

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      'arizona_http' as an string
   """

   return 'arizona_s3'


   
