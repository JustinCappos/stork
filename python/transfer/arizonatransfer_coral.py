#! /usr/bin/env python
"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: arizonatransfer_coral
Description:   Provides a general file transferring by Coral

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
      This closes a connection (dummy function for Coral).

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
      This initializes a connection (dummy function for Coral).

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

      junk_hashlist:
         'junk_hashlist' is a list of the hashes for this list of files.
         It should be a list of strings.

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

   # check if host is a string   
   if not isinstance(host, str):
      arizonareport.send_syslog(arizonareport.ERR, "retrieve_files(): host should be a string")
      # return false and empty list
      return (False, grabbed_list)
   
   # check if filelist contains only strings
   # Later I should just use something like justin.valid_sl   TODO!!!
   # TODO - check for valid tuple list
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

   #don't verify the connection!  it takes way too long to try transferring as it is
   #if not __verify_connection(host):
   #   # return false and empty list
   #   return (False, grabbed_list)


   # go through every file in the file list
   for file in filelist:
      filename = file['filename']
      starttime = time.time()

      # build url which specifies host and filename to be retrieved
      thisurl = __build_url(host,filename)
      # open given url
      try:
         aurl = urllib2.urlopen(thisurl)
         aurl.close()

         # if idicator is passed in
         if (indicator):
            # make indicator_file store a file name which will be used in download_indicator function
            indicator_file = filename
            # make indicator_file hold only filename itself (without directory)
            i = indicator_file.rfind("/")
            if i != -1:
               indicator_file = indicator_file[i + 1:]

            try:
               # set the filename so that indicator module can use the name to show for progress bar
               indicator.set_filename(indicator_file)
               arizonareport.send_out(0, "")
               # download_indicator method of indicator module is passed
               (filename,info) = urllib.urlretrieve(thisurl,destdir+"/"+filename, indicator.download_indicator)
               arizonareport.send_out(0, "")
            # indicator doesn't have method set_filename or download_indicator
            except AttributeError:
               arizonareport.send_syslog(arizonareport.ERR, 'retrieve_files(): indicator module passed in is incorrect')
               return (False, grabbed_list)
            # if indicator_file which used for set_filename is not a string
            except TypeError:
               arizonareport.send_syslog(arizonareport.ERR, 'retrieve_files(): indicator_file is incorrect')
               return (False, grabbed_list)
         else:
            # retrieve a file
            (filename,info) = urllib.urlretrieve(thisurl,destdir+"/"+filename)

         grabbed_list = grabbed_list + [file]
         endtime = time.time()
         log_transfer("coral", str(os.getpid()), str(starttime), str(endtime))
      # if file is not permitted to be retrieved
      except urllib2.HTTPError, (errstr):
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
      'arizona_coral' as an string
   """

   return 'arizona_coral'



def __build_url(host,fname):
   """
   <Purpose>
      This builds a url string with a Coralized address.

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

   # make the host does not contain 'http://' or 'ftp://'
   host = host.replace("ftp://", "")      
   host = host.replace("http://", "")

   #coral requires that the directory be separated from the host name   
   dir=""
   dpos=host.find("/")
   if dpos!=-1:
       dir=host[dpos:]
       host=host[:dpos]

   # if we're specifying a port, we must change it to proper format for coral
   host=host.replace(":",".")
   
   # add '/' at the end of the directory if the file name doesn't begin with one and the directory doesn't end with one, so that file name is added properly
   if (len(fname)>0 and not fname[0] == '/') and not dir[-1] == '/':
      dir = dir + '/'
   # return url which contains host and filename
   return "http://"+ host + ".nyud.net:8090" + dir + fname

          
      
def __verify_connection(host):
   """
   <Purpose>
      This verifies a connection, testing a host and target directory.

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
      True or False (see above)
   """
   
   # split host into server name and directory
   index = host.find('/')
   # set hostname to hold only a server name
   if index != -1:
      hostname = host[:index]
   else :
      hostname = host   

   # checking only host
   checkurl = __build_url(hostname, "")

   # urllib2 is used since urllib doestn't offer a nice way to check the connection is valid
   try :
      urllib2.urlopen(checkurl)
   # incorrect host name or host is dead
   except urllib2.URLError, (msg):      
      arizonareport.send_syslog(arizonareport.ERR, '__verify_connection(): "' + hostname + '" '+ str(msg).split("'")[1])
      return False


   # checking if a directory exists in the server
   checkurl = __build_url(host, "")
   try:
      urllib2.urlopen(checkurl)
   # if a directory doesn't exist in the server
   except urllib2.HTTPError, (strerror):
      arizonareport.send_syslog(arizonareport.ERR, '__verify_connection(): "' + str(strerror) + '" on the url "' + checkurl + '"')
      return False

   # everything is fine       
   return True
   



# TODO: should go away!!!
def valid_sl(stringlist):
   """
   <Purpose>
      This returns True if stringlist is a list of strings or False if it is 
      not.

   <Arguments>
      stringlist:
          The variable to be checked.

   <Exceptions>
      None

   <Side Effects>
      None

   <Returns>
      True or False (see above)
   """

   # If it's a list
   if isinstance(stringlist,list):

      for item in stringlist:
         # If an item in the list isn't a string then False
         if not isinstance(item,str):
            return False
      else:
         # It's a list of strings so True
         return True
   else:
      # Not a list so false
      return False

   
