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
   return True




def retrieve_files(host, filelist, destdir='.', indicator=None, protocol="http"):
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

      protocol:
         either "http" or "https"

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      (True, grabbed_list)
      'grabbed_list' is a list of files which are retrieved
   """
   arizonareport.send_out(4, "[DEBUG] arizonatransfer_http.retrieve_files: started")

   # set grabbed_list as a empty list. Later it will be appended with retrieved files
   grabbed_list = []

   # check if host is a string   
   if not isinstance(host, str):
      arizonareport.send_syslog(arizonareport.ERR, "retrieve_files(): host should be a string")
      # return false and empty list
      return (False, grabbed_list)

   # TODO - check for tuple list
   #if not valid_sl(filelist):
   #   arizonareport.send_syslog(arizonareport.ERR, "retrieve_files(): filelist should be a list of strings")
   #   # return false and empty list
   #   return (False, grabbed_list)
   
   # check if destdir is a string
   if not isinstance(destdir,str):
      arizonareport.send_syslog(arizonareport.ERR, "retrieve_files(): destdir should be a string")
      # return false and empty list
      return (False, grabbed_list)

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
      starttime = time.time()

      # build url which specifies host and filename to be retrieved
      thisurl = __build_url(host, filename, protocol)
      # open given url
      try:
         aurl = urllib2.urlopen(thisurl)

         blocknum = 0
         blocksize = 8192

         # get the size of the file from the HTTP headers
         size = int(aurl.info().get("content-length", -1))

         # tell the download indicator the filename and size
         if indicator:
            indicator.set_filename(os.path.basename(filename))
            indicator.download_indicator(blocknum, blocksize, size)

         # read from the aurl object and write to the destination file,
         # updating the download indicator as necessary
         outfile = open(os.path.join(destdir, filename), "w")
         while True:
            data = aurl.read(blocksize)
            if not data:
               break
            outfile.write(data)
            blocknum += 1
            if indicator:
               indicator.download_indicator(blocknum, blocksize, size)

         # put a newline at the end of the indicator
         if indicator:
            arizonareport.send_out(0, "")

         outfile.close()
         aurl.close()

         grabbed_list = grabbed_list + [file]
         endtime = time.time()
         log_transfer("http", str(os.getpid()), str(starttime), str(endtime))

      # if file is not permitted to be retrieved
      except urllib2.HTTPError, (errstr):
         # TODO: we may wish to catch errors that indicate the server is down
         # and abort all remaining files rather than wasting time on them
         arizonareport.send_syslog(arizonareport.ERR, 'retrieve_files(): "' + str(errstr) + '" on the file "' + filename + '"')

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

   return 'arizona_http'






def __extract_hostname(host):
   """
   <Purpose>
      Extracts the hostname from a host string

   <Arguments>
       host:
         'host' holds two things, a server name and target directory.
         For example, if you want to retrieve files from '/tmp/' directory
         in 'quadrus.cs.arizona.edu' server, the 'host' will be
         'quadrus.cs.arizona.edu/tmp'.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      The hostname
   """

   # remove the protocol if there is one
   host = arizonageneral.lcut(host, "http://")
   host = arizonageneral.lcut(host, "https://")
   host = arizonageneral.lcut(host, "ftp://")

   index=host.find("/")

   # set hostname to hold only a server name
   if index != -1:
      hostname = host[:index]
   else :
      hostname = host

   return hostname





def __build_url(host, fname, protocol="http"):
   """
   <Purpose>
      This builds a url string with Http address.

   <Arguments>
       host:
         'host' holds two things, a server name and target directory.
         For example, if you want to retrieve files from '/tmp/' directory
         in 'quadrus.cs.arizona.edu' server, the 'host' will be
         'quadrus.cs.arizona.edu/tmp'.
      fname:
         A file name to be retrieved

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      A whole url string created
   """

   host = arizonageneral.lcut(host, "http://")
   host = arizonageneral.lcut(host, "https://")
   host = arizonageneral.lcut(host, "ftp://")

   if (protocol != "http") and (protocol != "https"):
      return TypeError, "unknown protocol"

   # add '/' at the end of the host if there is not, so that file name is added properly
   if not host.endswith("/"):
      host = host + '/'

   # return url which contains host and filename
   return protocol + "://" + host + fname




