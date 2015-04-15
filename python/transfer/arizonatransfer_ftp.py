#! /usr/bin/env python
"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: arizonatransfer_ftp
Description:   Provides a general file transferring by FTP

"""


import urllib
import urllib2
import arizonaconfig
import arizonareport
import os
import time
import socket
import getpass

"""arizonaconfig
   options=[["", "--transuser", "transuser", "store", "string", None, "user", "use this user to transfer files (the default is up to the transfer program)"]]
   includes=[]
"""


slicename = getpass.getuser()

# TODO: need to use arizona_config
username="anonymous"
password=slicename+"_AT_"+socket.gethostname()
port=21
#arizonaconfig.set_option("username", "anonymous")
#arizonaconfig.set_option("password", arizonaconfig.get_option("xyz") + "_AT_" + socket.gethostname())

def log_transfer(function, pid, timestamp, timestampend):
   try:
      import storklog
      storklog.log_transfer(function, pid, timestamp, timestampend)
   except:
      pass

def close_transfer_program():
   """
   <Purpose>
      This closes a connection.

   <Arguments>
      None.
   
   <Exceptions>
      None.

   <Side Effects>
      Set username, password, and port as default.

   <Returns>
      True
   """

   # TODO: need to use arizona_config instead
   username="anonymous"
   password=slicename+"_AT_"+socket.gethostname()
   port=21
   
   return True





# TODO: since basically everything is set by arizona_config,
#        there's actually nothing to do here...
def init_transfer_program(uname=None,passwd=None,prt=None,ignore4=None):
   """
   <Purpose>
      This sets username, password, and port for a ftp connection.

   <Arguments>
      uname:
         User name. It should be a string, otherwise it raises TypeError.
         default: 'anonymous'

      passwd:
         password. It should be a string, otherwise it raises TypeError.
         default: slicename_AT_hostname

      prt:
         port number. It should be an int, otherwise it raises TypeError.
         default: 21

      ignore4:
         It is just used to be matched with return value of other transfer 
         methods. Always None for 'storkftp'

   <Exceptions>
      TypeError:
         If the types of given arguments are incorrect, then TypeError 
         will be raised.

   <Side Effects>
      Set username, password, and port.

   <Returns>
      (True, username, password, port, ignore)
   """

   arizonareport.send_out(4, "[DEBUG] arizonatransfer_ftp.init_transfer_program: started")

   arizonaconfig.set_option("transuser", "anonymous")

   # if username is given, but incorrect type
   if not uname == None and not isinstance(uname, str):
      arizonareport.send_syslog(arizonareport.ERR, "username should be a string")
      raise TypeError, "init_transfer_program(): Invalid type of username(should be a string)"

   # if passwd is given, but incorrect type
   if not passwd == None and not isinstance(passwd, str):
      arizonareport.send_syslog(arizonareport.ERR, "passwd should be a string")
      raise TypeError, "init_transfer_program(): Invalid type of passwd(should be a string)"

   # if port is given, but incorrect type
   if not prt == None and not isinstance(prt, int):
      arizonareport.send_syslog(arizonareport.ERR, "port should be an integer")
      raise TypeError, "init_transfer_program(): Invalid type of prt(should be an int)"


   global username
   global password
   global port
   
   # default settings
   username = arizonaconfig.get_option("transuser")
   password=slicename+"_AT_"+socket.gethostname()
   port=21

   # set username with given username
   if uname!=None:
      username=uname
   # set password with given password
   if passwd!=None:
      # if passwd has @, then replace @ to _AT_
      if "@" in passwd:
         arizonareport.send_syslog(arizonareport.ERR, "init_transfer_program(): Warning, replacing @ in password with _AT_")
         password=passwd.replace("@","_AT_")
      else:
         password=passwd
   # set port with given port
   if prt!=None:
      port=prt

   # return result
   return (username, password, port, ignore4)





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
      AttributeError:
         If 'indicator' doesn't have functions such as set_filename, 
         download_indicator, or 'indicator' is not a module, then 'False'
         and an empty list will be returend.
      
      TypeError:
         If 'indicator_file' is not a string, then 'False' and an empty 
         list will be returend.

   <Side Effects>
      None.

   <Returns>
      (True, grabbed_list)
      'grabbed_list' is a list of files which are retrieved
   """
      
   arizonareport.send_out(4, "[DEBUG] arizonatransfer_ftp.retrieve_files: started")

   # set grabbed_list as a empty list. Later it will be appended with retrieved files
   grabbed_list = []

   # check if host is a string   
   if not isinstance(host, str):
      arizonareport.send_syslog(arizonareport.ERR, "retrieve_files(): host should be a string")
      # return false and empty list
      return (False, grabbed_list)
   
   # check if filelist contains only strings
   # Later I should just use something like arizonageneral.valid_sl   TODO!!!
   # TODO - check if valid list of tuples
   #if not valid_sl(filelist):
   #   arizonareport.send_syslog(arizonareport.ERR, "retrieve_files(): filelist should be a list of strings")
   #   # return false and empty list
   #   return (False, grabbed_list)
   
   # check if destdir is a string
   if not isinstance(destdir,str):
      arizonareport.send_syslog(arizonareport.ERR, "retrieve_files(): destdir should be a string")
      # return false and empty list
      return (False, grabbed_list)
   
   # if destdir is a empty string, then make it as a current directory
   if destdir == '':
      destdir = '.'

   # check that the destination directory exists  
   if not os.path.isdir(destdir):
      arizonareport.send_syslog(arizonareport.ERR, "\nretrieve_files(): The destination directory '" + destdir + "' for a requested does not exist")
      # return false and empty list
      return (False, grabbed_list)


   # check host is valid
   arizonareport.send_out(4, "[DEBUG] arizonatransfer_ftp.retrieve_files: verifying connection")
   if not __verify_connection(host):
      # return false and empty list
      return (False, grabbed_list)
      
   # go through every file in the file list
   arizonareport.send_out(4, "[DEBUG] arizonatransfer_ftp.retrieve_files: filelist = " + str(filelist))
   for file in filelist:
      filename = file['filename']
      starttime = time.time()

      arizonareport.send_out(4, "[DEBUG] arizonatransfer_ftp.retrieve_files: filename = " + str(filename))


      # build url which specifies host and filename to be retrieved
      thisurl = __build_url(host,filename)
         
      # open given url
      arizonareport.send_out(4, "[DEBUG] arizonatransfer.ftp: thisurl = " + str(thisurl)) 
      aurl = urllib.urlopen(thisurl)         
      # check the info of opened url if it have 'Content-Length' 
      # if it doesn't have, it means either a user has no permission to read the file, 
      # or it's a directory, not a file. Either way, we won't retrieve it
      if (str(aurl.info()).split().count('Content-Length:')) :   
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
         log_transfer("ftp", str(os.getpid()), str(starttime), str(endtime))
      else:
         aurl.close()
         arizonareport.send_syslog(arizonareport.ERR, 'retrieve_files(): Cannot retrieve "' + filename + '"')
  
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
      'arizona_ftp' as an string
   """

   return 'arizona_ftp'





def __build_url(host,fname):
   """
   <Purpose>
      This builds a url string with host, username, password, port and
      file name.

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

   # if host doesn't contain 'ftp://' or contains 'http://'
   # add 'ftp://' at the beginning or replace to 'ftp://'
   if not "ftp://" in host:
      host = host.replace("http://", "")      
      host = "ftp://" + host
   
   # return url which contain all info
   return host.replace("//","##"+username+":"+password+"@",1).replace("/",":"+str(port)+"/",1).replace("##","//",1)+"/"+fname




def __verify_connection(host):
   """
   <Purpose>
      This verifies a connection, testing a host, username, password, port

   <Arguments>
      host:
         'host' holds two things, a server name and target directory.
         For example, if you want to retrieve files from '/tmp/' directory
         in 'quadrus.cs.arizona.edu' server, the 'host' will be
         'quadrus.cs.arizona.edu/tmp'.
            
   <Exceptions>
      URLError:
         If host name is incorrect or host is dead, then return False

      IOError:
         If given username, password, port, or target directory is 
         incorrect, then return False

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
   # incorrect username, or password
   except IOError, (errno, strerror):     
      arizonareport.send_syslog(arizonareport.ERR, '__verify_connection(): ' + str(strerror))
      close_transfer_program()
      return False

   # checking if either a directory exist in the server, or a port is correct
   checkurl = __build_url(host, "")
   try:
      urllib2.urlopen(checkurl)
   # if either a directory doesn't exist in the server, or a port is incorrect
   except IOError, (errno, strerror):
      arizonareport.send_syslog(arizonareport.ERR, '__verify_connection(): ' + str(strerror))
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



