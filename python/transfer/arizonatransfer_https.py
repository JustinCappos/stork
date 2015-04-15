#! /usr/bin/env python
"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: arizonatransfer_https
Description:   Provides a general file transferring by HTTPS
               This is essentially a stub module that calls arizonatransfer_http

"""

import urllib
import urllib2
import os
import time
import arizonareport
import arizonatransfer_http




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

   return arizonatransfer_http.close_transfer_program()



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
   return arizonatransfer_http.init_transfer_program(ignore, ignore2, ignore3, ignore4)




def retrieve_files(host, filelist, destdir='.', indicator=None):
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
   # call arizonatransfer to download the file, specifying the "https"
   # protocol to ensure a secure connection is used.
   return arizonatransfer_http.retrieve_files(host, filelist, destdir, indicator, "https")




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

   return 'arizona_https'

