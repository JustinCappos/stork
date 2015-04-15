#! /usr/bin/env python
"""
<Program Name>
   stork_nest_comm.py

<Author>
   Programmed by Jeffry Johnston

<Purpose>
   Handles nest side communications with client slices, coordinates
   client identification, downloads and sharing of files.
"""

#           [option, long option,     variable,      action,        data,     default,                           metavar,     description]
"""arizonaconfig
   options=[
            ["-C",   "--configfile",  "configfile",  "store",       "string", "/usr/local/stork/etc/stork.conf", "FILE",      "use a different config file (/usr/local/stork/etc/stork.conf is the default)"],
            ["",     "--listenport",  "listenport",  "store",       "int",    648,                               "PORT",      "bind to this port (default 648)"],
            ["",     "--bindfiles",   "bindfiles",   "store",       "string", "/share/base",                     "DIRECTORY", "location of the files to copy to the client upon binding"],
            ["",     "--retrievedir", "retrievedir", "store",       "string", "/usr/local/stork/var/packages",   "DIRECTORY", "location to put retrieved files (default /usr/local/stork/var/packages)"],
            ["",     "--not-daemon",  "daemon",      "store_false",  None,    True,                              None,        "specify that program should not attempt to detach from the terminal"],
            ["",     "--localoutput", "localoutput", "store_true",   None,    False,                             None,        "display output locally, do not send to client"]]
   includes=[]
"""

# JUSTIN TODO bindfiles -- think about it ??

import arizonaconfig
import arizonareport
import arizonacomm
import os
import glob
import sys
import arizona_share
import arizonatransfer
import stork_prepare
import tempfile
import arizonacrypt
import arizonageneral
import traceback
import storkpackage
import socket
import storklog
import storkerror
import time
import stork_nest_version

# global variables
glo_connection = ""

# global variables used for storing file transfer information
glo_retrievefiles = None
glo_retrievesubdirs = None
glo_retrievehashes = None
glo_retrievehost = None
glo_retrievedestdir = None
glo_retrieveindicator = None


glo_linestart = True
def output_func_pid(type, verbosity, output):
    global glo_tstart
    global glo_linestart

    if glo_linestart:
        time_str = "[%2d] " % os.getpid()
        output = time_str + output

    if (type == "send_out") or (type == "send_error") or (type == "send_syslog"):
        glo_linestart = True
    elif (type == "send_out_comma") or (type == "send_error_comma"):
        glo_linestart = False

    return output

def handle_connection(ip, port):
   """ 
   <Purpose>
      Handles a new client connection.  Receives incoming client messages
      and sends them to the correct handler

   <Arguments>
      ip:
              IP address of the connecting client.
      port:    
              Port the client is connected on.

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   global glo_connection
   global glo_host
   if os.fork():
      # Parent
      arizonacomm.disconnect("stork_nest_comm.handle_connection: disconnecting parent")

      # Clean up if there are any dead child processes
      try:
         os.waitpid(-1, os.WNOHANG)
         os.waitpid(-1, os.WNOHANG)
      except OSError: 
         pass

      # Start accepting connections again...
      return
   else:
      # Handle this connection...
      arizonareport.send_syslog(arizonareport.INFO, "Connected by: " + ip + " " + str(port) + "\n")
      if not arizonaconfig.get_option("daemon"):
         print "Connected by: " + ip + " " + str(port)
      glo_connection = ip + ":" + str(port)
      try:
         hostname = socket.gethostbyaddr(ip)[0]
      except:
         hostname = ""
      storklog.set_client(hostname, ip, port, None)
      storklog.log_nest("stork_nest_comm", "handle_connection", "connected", "", "")

      #storklog.log_connect("connected")

      #arizonareport.set_verbosity(-1)
      arizonacomm.handle_session({"bindscript HTTP/1.0": __handle_bindscript, \
                                  "hello": __handle_hello, \
                                  "version": __handle_version, \
                                  "verbosity": __handle_verbosity, \
                                  "identify": __handle_identify, \
                                  "identifyready": __handle_identifyready, \
                                  "retrievefiles": __handle_retrievefiles, \
                                  "retrievehost": __handle_retrievehost, \
                                  "retrievedestdir": __handle_retrievedestdir, \
                                  "retrieveindicator": __handle_retrieveindicator, \
                                  "retrievefile": __handle_retrievefile, \
                                  "retrievehash": __handle_retrievehash, \
                                  "prepare": __handle_prepare, \
                                  "share": __handle_share, \
                                  "end": __handle_end, \
                                  "info": __handle_info})

      #storklog.log_connect("disconnected")

      # Since the parent accepts connections again, the child MUST exit...
      storklog.log_nest("stork_nest_comm", "handle_connection", "disconnected", "", "")
      arizonareport.send_syslog(arizonareport.INFO, "Disconnected")
      os._exit(0)





def __handle_identify(data):
      storklog.log_nest("stork_nest_comm", "__handle_identify", "start", "data", data)
      #storklog.log_connect("identify", data)
      result = arizona_share.identify(data)

      if result:
          storklog.log_nest("stork_nest_comm", "__handle_bindscript", "end", "ok", "")
      else:
          storklog.log_nest("stork_nest_comm", "__handle_bindscript", "end", "error", "")

      return result





def __handle_identifyready(data):
      storklog.log_nest("stork_nest_comm", "__handle_identifyready", "start", "data", data)
      #storklog.log_connect("identifyready", data)
      result = arizona_share.identifyready(data)

      if result:
          storklog.log_nest("stork_nest_comm", "__handle_bindscript", "end", "ok", "")
      else:
          storklog.log_nest("stork_nest_comm", "__handle_bindscript", "end", "error", "")

      return result


      


def __handle_info(data):
   """
   <Purpose>
      Responds to info command, which logs the data that was sent

   <Arguments>
      data:
              Data to log onto nest

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      None.
   """
   if data[:data.find(':')] == "version":
        storklog.log_nest("stork_nest_comm", "__handle_info", "identify", "nest_version", arizonaconfig.get_version())


   storklog.log_nest("stork_nest_comm", "__handle_info", "identify", data[:data.find(':')], data[data.find(':')+1:])

   # JRP: 4/3/07: commented out the below code because we should
   # not exit at this point because it would break the connection
   # with the client

   # Since the parent accepts connections again, the child MUST exit...
   #storklog.log_nest("stork_nest_comm", "handle_connection", "disconnected", "", "")
   #os._exit(0)





def __handle_bindscript(data):
   """ 
   <Purpose>
      Responds to the \bindscript command by copying files to the 
      client slice

   <Arguments>
      data:
              Client slice name.

   <Exceptions>
      IOError if socket communications fails.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   storklog.log_nest("stork_nest_comm", "__handle_bindscript", "start", "data", data)
   __report_handler("bindscript", data)

   # get client name
   client = data.strip().split()[1].strip()[1:]

   # log the request
   arizonareport.send_syslog(arizonareport.INFO, "client: `" + client + "'")

   # check for bad client name
   if client == '.' or client == '..' or client.find('/') != -1:
      arizonacomm.send("", "stork nest: error")
      arizonareport.send_syslog(arizonareport.ERR, "__handle_bindscript: bad client name `" + client + "'")
      
      __disconnect("stork_nest_comm.__handle_bindscript: bad client name `" + client + "'")
      storklog.log_nest("stork_nest_comm", "__handle_bindscript", "end", "error", "")
      return

   arizonacomm.sendraw("HTTP/1.1 202 OK\r\nContent-Length: " + str(len(client) + 3) + "\r\nConnection: Keep-Alive\r\nContent-Type: text/plain\r\n\r\n" + str(client) + "\r\n\n")

   arizona_share.init_client(client)

   # Now copy files, etc. for setup
   files = glob.glob(arizonaconfig.get_option("bindfiles") + "/*")
   for filename in files:
      name = os.path.split(filename)[1]
      arizona_share.copy_file(arizonaconfig.get_option("slicename"), filename, client, "/tmp/stork/" + name)

   # Tell the client to proceed...
   arizona_share.copy_file(arizonaconfig.get_option("slicename"), "/dev/null", client, "/tmp/stork/stork_says_go")
   arizonareport.send_syslog(arizonareport.INFO, "Done...")
   storklog.log_nest("stork_nest_comm", "__handle_bindscript", "end", "ok", "")

   
   
   
   
def __handle_end(data):
   """ 
   <Purpose>
      Responds to the \end command by terminating the connection.

   <Arguments>
      data:
              Unused.         # to log the time taken
         time_before = time.time()


   <Exceptions>
      IOError if socket communications fails.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   storklog.log_nest("stork_nest_comm", "__handle_bindscript", "start", "data", data)
   __report_handler("end", data)
   arizonareport.send_syslog(arizonareport.INFO, "Client requested disconnect.")
   #print "[DEBUG] client requested disconnection, disconnecting"
   arizonacomm.disconnect("Client requested disconnect (sent end command)")
   storklog.log_nest("stork_nest_comm", "__handle_bindscript", "end", "ok", "")
   
   
   


def __handle_hello(data):
   """ 
   <Purpose>
      Responds to the \hello command.

   <Arguments>
      data:
              Unused.

   <Exceptions>
      IOError if socket communications fails.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   storklog.log_nest("stork_nest_comm", "__handle_hello", "start", "data", data)
   __report_handler("hello", data)
   arizonareport.send_syslog(arizonareport.INFO, "Sending hello response")
   arizonacomm.send("response", "hello")
   storklog.log_nest("stork_nest_comm", "__handle_hello", "end", "ok", "")





def __handle_version(data):
   """ 
   <Purpose>
      Responds to the \version command.

   <Arguments>
      data:
              Unused.

   <Exceptions>
      IOError if socket communications fails.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   storklog.log_nest("stork_nest_comm", "__handle_version", "start", "data", data)
   __report_handler("version", data)
   arizonareport.send_syslog(arizonareport.INFO, "Sending version response")
   arizonacomm.send("response", arizonaconfig.get_version())
   storklog.log_nest("stork_nest_comm", "__handle_version", "end", "ok", "")
   




# for __handle_verbosity
glo_verbosity_set = False

def __handle_verbosity(data):
   """ 
   <Purpose>
      Handles the \verbosity command, then sends local stdout/err messages
      to the client for remote display.  See data argument for details.

   <Arguments>
      data:
              New verbosity level (-1 to 4, inclusive).  Default verbosity
              level is -1, which is silence (no messages are sent).  
              Normal verbosity levels are 0=quiet to 3=very verbose.  
              Verbosity level 4 prints raw debug messages.

   <Exceptions>
      IOError if socket communications fails.

   <Side Effects>
      Sets arizonareport verbosity, to be used when this module prints.
      Redirects/restores stdout/err

   <Returns>
      None.
   """
   global glo_verbosity_set

   storklog.log_nest("stork_nest_comm", "__handle_verbosity", "start", "data", data)
   __report_handler("verbosity", data)
   
   # check verbosity value
   try:
      verbosity = int(data)
      if verbosity < -1 or verbosity > 4:
         raise ValueError
   except ValueError:
      arizonareport.send_syslog(arizonareport.INFO, "__handle_verbosity: bad verbosity value `" + str(data) + "', must be from -1 to 4")
      arizonareport.send_error(0, "nest: bad verbosity value `" + str(data) + "', must be from -1 to 4")
      __disconnect("stork_nest_comm.__handle_verbosity: bad verbosity value `" + str(data) + "', must be from -1 to 4")
      storklog.log_nest("stork_nest_comm", "__handle_verbosity", "end", "error", "")
      return
   
   if verbosity > 0 and not glo_verbosity_set and not arizonaconfig.get_option("localoutput"):
      # turn on output redirection
      arizonareport.redirect_stdout(arizonacomm_out())       
      arizonareport.redirect_stderr(arizonacomm_err()) 
      glo_verbosity_set = True
   """elif verbosity < 0 and glo_verbosity_set:
      # turn off output redirection      
      arizonareport.restore_stdout()       
      arizonareport.restore_stderr() """      

   arizonareport.set_verbosity(verbosity)
   storklog.log_nest("stork_nest_comm", "__handle_verbosity", "end", "ok", "")



   
   
def __handle_retrievefiles(data):
   """ 
   <Purpose>
      Depends on data:
         "start": Initializes and prepares to receive needed transfer data 
         "end": Checks data completeness and retrieves the requested files

   <Arguments>
      data: 
              Must be "start" or "end".

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   global glo_retrievefiles
   global glo_retrievesubdirs
   global glo_retrievehashes
   global glo_retrievehost
   global glo_retrievedestdir
   global glo_retrieveindicator
   storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "start", "data", data)
   __report_handler("retrievefiles", data)
   if not __identified():
      storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "end", "error", "0")
      return
   data = data.strip().lower()
   if data == "start":
      # init variables
      glo_retrievefiles = None
      glo_retrievesubdirs = None
      glo_retrievehashes = None
      glo_retrievehost = None
      glo_retrievedestdir = None
      glo_retrieveindicator = None
   elif data == "end":
      # check that everything was given
      if glo_retrievefiles == None or len(glo_retrievefiles) < 1:
         arizonareport.send_syslog(arizonareport.INFO, "__handle_retrievefiles: missing retrievefile")
         arizonareport.send_error(0, "nest: missing retrievefile, disconnecting")
         __disconnect("stork_nest_comm.__handle_retrievefiles: missing retrievefile")
         storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "end", "error", "1")
         return
      if glo_retrievesubdirs == None or len(glo_retrievesubdirs) != len(glo_retrievefiles):
         arizonareport.send_syslog(arizonareport.INFO, "__handle_retrievefiles: internal error, file count / subdirectory count mismatch")
         arizonareport.send_error(0, "nest: internal error, file count / subdirectory count mismatch, disconnecting")
         __disconnect("stork_nest_comm.__handle_retrievefiles: internal error, file count / subdirectory count mismatch")
         storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "end", "error", "2")
         return
      if glo_retrievehashes == None or len(glo_retrievehashes) < 1:
         arizonareport.send_syslog(arizonareport.INFO, "__handle_retrievefiles: missing retrievehash")
         arizonareport.send_error(0, "nest: missing retrievehash, disconnecting")
         __disconnect("stork_nest_comm.__handle_retrievefiles: missing retrievehash")
         storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "end", "error", "3")
         return
      if len(glo_retrievefiles) != len(glo_retrievehashes):
         arizonareport.send_syslog(arizonareport.INFO, "__handle_retrievefiles: different number of filenames and hashes")
         arizonareport.send_error(0, "nest: different number of filenames and hashes, disconnecting")
         __disconnect("stork_nest_comm.__handle_retrievefiles: different number of filenames and hashes")
         storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "end", "error", "4")
         return
      if glo_retrievehost == None:
         arizonareport.send_syslog(arizonareport.INFO, "__handle_retrievefiles: missing retrievehost")
         arizonareport.send_error(0, "nest: missing retrievehost, disconnecting")
         __disconnect("stork_nest_comm.__handle_retrievefiles: missing retrievehost")
         storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "end", "error", "5")
         return
      if glo_retrievedestdir == None:
         arizonareport.send_syslog(arizonareport.INFO, "__handle_retrievefiles: missing destdir")
         arizonareport.send_error(0, "nest: missing destdir, disconnecting")
         __disconnect("stork_nest_comm.__handle_retrievefiles: missing destdir")
         storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "end", "error", "6")
         return
      if glo_retrieveindicator == None:
         arizonareport.send_syslog(arizonareport.INFO, "__handle_retrievefiles: missing retrieveindicator")
         arizonareport.send_error(0, "nest: missing retrieveindicator, disconnecting")
         __disconnect("stork_nest_comm.__handle_retrievefiles: missing retrieveindicator")
         storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "end", "error", "7")
         return
   
      # TWH: create the retrieve directory
      retrieve_dir = arizonaconfig.get_option("retrievedir")
      if len(retrieve_dir) > 1 and not retrieve_dir.endswith('/'):
         retrieve_dir += '/'
      if not os.path.isdir(retrieve_dir):
         try:
            os.mkdir(retrieve_dir)
         except OSError:
            arizonareport.send_syslog(arizonareport.INFO, "__handle_retrievefiles: error creating directory: " + retrieve_dir)
            arizonareport.send_error(0, "nest: error creating directory: " + retrieve_dir + ", disconnecting.")
            __disconnect("stork_nest_comm.__handle_retrievefiles: error creating directory: " + retrieve_dir)
            storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "end", "error", "8")
            return
			
      # do not re-download existing files
      downloaded_ok = []
      downloaded_ok_hashes = []
      downloaded_ok_subdirs = []
      to_download = []
      to_download_hashes = []
      to_download_subdirs = []
      for i, filename in enumerate(glo_retrievefiles):
         # if there is no hash, pretend that the hash is "no_hash"
         file_hash = glo_retrievehashes[i]
         if file_hash == "":
           file_hash = glo_retrievehashes[i] = "no_hash"
         
         # check for the file  
         file_subdir = glo_retrievesubdirs[i]
         # If we didn't download it or it has no hash
         if os.path.isfile(retrieve_dir + file_hash + "/" + filename) and not file_hash == "no_hash":
            downloaded_ok.append(filename)
            downloaded_ok_hashes.append(file_hash)
            downloaded_ok_subdirs.append(file_subdir)
            storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "need_dl", filename, "no")
         else:
            to_download.append(filename)
            to_download_hashes.append(file_hash)
            to_download_subdirs.append(file_subdir)
            storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "need_dl", filename, "yes")

      if downloaded_ok == []:
        arizonareport.send_out(3, "[" + arizonageneral.getusername() + "] Nest Downloading on your behalf:")
      else:
        arizonareport.send_out(3, "[" + arizonageneral.getusername() + "] Previously downloaded: " + ", ".join(downloaded_ok))

      # True = everything retrieved, protected, and shared without error, False = otherwise      
      retrieve_status = True    

      # set up download indicator if they requested it
      # TWH: this logic already exists in arizonatransfer
      #if glo_retrieveindicator > 0:
      #   import download_indicator
      #   prog_indicator_module = download_indicator
      #   prog_indicator_module.set_width(glo_retrieveindicator)
      #else:
      #   prog_indicator_module = None

      # retrieve files
      # TODO We are forced to download files one at a time because 
      #      arizonatransfer.getfiles doesn't return the hashes of 
      #      successful downloads.  For example, if there are two 
      #      identically named files foo.rpm, but with different hashes,
      #      and only one is in the list returned by getfiles, we will not
      #      know which of the two was successfully downloaded.   
      for i, filename in enumerate(to_download):
         #print "[DEBUG] downloading file:", filename
         file_hash = to_download_hashes[i]
         
         #if file_hash == "":
         #   arizonareport.send_syslog(arizonareport.INFO, "__handle_retrievefiles: file `" + filename + "' had no hash, skipping")
         #   arizonareport.send_error(0, "nest: file `" + filename + "' had no hash, skipping...")
         #   retrieve_status = False
         #   status = False
         #else:

         # download
         if file_hash == "no_hash":
            temp_hash = ""
         else:
            temp_hash = file_hash
         # TWH: let arizonatransfer decide how to use the progress indicator
         status, downloaded = arizonatransfer.getfiles(glo_retrievehost, [filename], retrieve_dir, [temp_hash], glo_retrieveindicator)

         # check download result status         
         if status:
            downloaded_ok.append(filename)
            downloaded_ok_hashes.append(file_hash)
            downloaded_ok_subdirs.append(to_download_subdirs[i])
            
            # create directory: (...)/hash
            link = retrieve_dir + file_hash + "/"
            if not os.path.isdir(link):
               try:
                  os.mkdir(link)
               except OSError:
                  arizonareport.send_syslog(arizonareport.INFO, "__handle_retrievefiles: error creating directory: " + retrieve_dir + str(file_hash) + "/")
                  arizonareport.send_error(0, "nest: error creating directory: " + str(arizonaconfig.get_option("retrievedir")) + "/" + str(file_hash) + "/, disconnecting.")
                  __disconnect("stork_nest_comm.__handle_retrievefiles: error creating directory: " + str(arizonaconfig.get_option("retrievedir")) + "/" + str(file_hash) + "/")
                  storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "end", "error", "9")
                  return
            
            try:
               # move downloaded file to (...)/hash
               os.rename(retrieve_dir + filename, link + filename)
            except OSError:
               arizonareport.send_syslog(arizonareport.INFO, "__handle_retrieve_files: error moving file: " + retrieve_dir + str(filename) + " to: " + str(link))
               arizonareport.send_error(0, "nest: error moving file: " + retrieve_dir + str(filename) + " to: " + str(link) + ", disconnecting.")
               __disconnect("stork_nest_comm.__handle_retrievefiles: error moving file: " + retrieve_dir + str(filename) + " to: " + str(link))
               storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "end", "error", "10")
               return
            
            try:
               # create (...)/filename-hash link to source: (...)/hash/filename
               if not os.path.islink( retrieve_dir+filename+"-"+file_hash):
                    os.symlink(link + filename, retrieve_dir + filename + "-" + file_hash)
            except OSError:
               arizonareport.send_syslog(arizonareport.INFO, "__handle_retrieve_files: error creating symlink, source: " + str(link) + str(filename) + ", dest: " + retrieve_dir + str(filename) + "-" + str(file_hash))
               arizonareport.send_error(0, "nest: error creating symlink, source: " + str(link) + str(filename) + ", dest: " + retrieve_dir + str(filename) + "-" + str(file_hash) + ", disconnecting.")
               __disconnect("stork_nest_comm.__handle_retrievefiles: error creating symlink, source: " + str(link) + str(filename) + ", dest: " + retrieve_dir + str(filename) + "-" + str(file_hash))
               storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "end", "error", "11")
               return
         else:
            retrieve_status = False
         
      to_download = None
      to_download_hashes = None
      to_download_subdirs = None
      
      # to log the time taken
      time_before = time.time()

      # protect/share the package files
      shared_ok = []
      for i, filename in enumerate(downloaded_ok):
         #print "[DEBUG] sharing file:", filename
         file_hash = downloaded_ok_hashes[i]
         file_subdir = downloaded_ok_subdirs[i]
         
         name = retrieve_dir + file_hash + "/" + filename  
         filename = file_subdir + filename
         #print "[DEBUG] nest file:", name   
         #print "[DEBUG] client file:", glo_retrievedestdir + "/" + filename  
         
         # protect files that are located in my fs
         if not arizona_share.protect_file(arizonaconfig.get_option("slicename"), name):
            arizonareport.send_syslog(arizonareport.INFO, "__handle_retrieve_files: error protecting file: arizona_share.protect_file(" + str(arizonaconfig.get_option("slicename")) + "," + name + ")")
            arizonareport.send_error(0, "nest: error protecting file: `" + name + "'")
            retrieve_status = False
            continue
         # link binaries, etc. to a requesting client
         if not arizona_share.link_file(arizonaconfig.get_option("slicename"), name, arizona_share.get_identified_clientname(), glo_retrievedestdir + "/" + filename):
            arizonareport.send_syslog(arizonareport.INFO, "__handle_retrieve_files: error sharing file: arizona_share.link_file(" + arizonaconfig.get_option("slicename") + "," + name + "," + arizona_share.get_identified_clientname() + "," + glo_retrievedestdir + "/" + filename + ")")
            arizonareport.send_error(0, "nest: error sharing file: `" + name + "'")
            retrieve_status = False
            continue
         shared_ok.append(filename)
         
      # inform client about the transfer
      arizonacomm.send("retrievedstatus", str(retrieve_status).lower())
      arizonacomm.send("retrievedfiles", "start")
      for filename in shared_ok:
         arizonacomm.send("retrievedfile", filename)
         try:
            filesize = str(os.stat(filename).st_size)
         except:
            filesize = "unknown"
         storklog.log_nest("stork_nest_comm", "__handle_retrieve_files", "shared", filename, filesize)
      arizonacomm.send("retrievedfiles", "end")

      # log time taken to protect/share
      time_after = time.time()
      storklog.log_nest("stork_nest_comm", "__handle_retrieve_files", "share_time", ",".join(downloaded_ok), str(time_after - time_before))

      # init variables
      glo_retrievefiles = None
      glo_retrievehashes = None
      glo_retrievehost = None
      glo_retrievedestdir = None
      glo_retrieveindicator = None
   else:
      arizonareport.send_syslog(arizonareport.INFO, "__handle_retrievefiles: expected `start' or `end', data:" + str(data))
      arizonareport.send_error(0, "nest: retrievefiles expected `start' or `end', data: `" + str(data) + "', disconnecting")
      __disconnect("stork_nest_comm.__handle_retrievefiles: retrievefiles expected `start' or `end', data: `" + str(data))
      storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "end", "error", "12")
      return
   storklog.log_nest("stork_nest_comm", "__handle_retrievefiles", "end", "ok", "")

      
      

      
def __handle_retrievehost(data):
   """ 
   <Purpose>
      Sets the host for the the current retrieve.  

   <Arguments>
      data: 
              Hostname.

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   global glo_retrievehost
   storklog.log_nest("stork_nest_comm", "__handle_retrievehost", "start", "data", data)
   __report_handler("retrievehost", data)
   if not __identified():
      storklog.log_nest("stork_nest_comm", "__handle_retrievehost", "end", "error", "")
      return
   glo_retrievehost = data
   storklog.log_nest("stork_nest_comm", "__handle_retrievehost", "end", "ok", "")
   




def __handle_retrievedestdir(data):
   """ 
   <Purpose>
      Sets the destination directory for the the current retrieve.  

   <Arguments>
      data: 
              Destination directory for client.

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   global glo_retrievedestdir
   storklog.log_nest("stork_nest_comm", "__handle_retrievedestdir", "start", "data", data)
   __report_handler("retrievedestdir", data)
   if not __identified():
      storklog.log_nest("stork_nest_comm", "__handle_retrievedestdir", "end", "error", "")
      return
   glo_retrievedestdir = data
   storklog.log_nest("stork_nest_comm", "__handle_retrievedestdir", "end", "ok", "")





def __handle_retrieveindicator(data):
   """ 
   <Purpose>
      Sets whether or not the download indicator is displayed.

   <Arguments>
      data:
              Indicator: must be an int (as a string)

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   global glo_retrieveindicator
   storklog.log_nest("stork_nest_comm", "__handle_retrieveindicator", "start", "data", data)
   __report_handler("retrieveindicator", data)
   if not __identified():
      storklog.log_nest("stork_nest_comm", "__handle_retrieveindicator", "end", "error", "")
      return
   data = data.strip()
   try:
      glo_retrieveindicator = int(data)
   except ValueError:
      arizonareport.send_syslog(arizonareport.INFO, "__handle_retrieveindicator: expected an integer value, data: `" + str(data) + "'")
      arizonareport.send_error(0, "nest: retrieveindicator expected an integer value, data: `" + str(data) + "', disconnecting")
      __disconnect("stork_nest_comm.__handle_retrieveindicator: retrieveindicator expected an integer value, data: `" + str(data) + "'")
   storklog.log_nest("stork_nest_comm", "__handle_retrieveindicator", "end", "ok", "")


      
      
      
def __handle_retrievefile(data):
   """ 
   <Purpose>
      Adds a file to the retrieve list.

   <Arguments>
      None.

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   global glo_retrievefiles
   global glo_retrievesubdirs
   
   __report_handler("retrievefile", data)
   storklog.log_nest("stork_nest_comm", "__handle_retrievefile", "start", "data", data)
   if not __identified():
      storklog.log_nest("stork_nest_comm", "__handle_retrievefile", "end", "error", "")
      return
      
   # check filename
   # TODO need other checks?  probably a security bug here  ~ . ..  
   if data[0] == "/" or data.find("../") != -1 or data.find("~/") != -1:  
      arizonareport.send_syslog(arizonareport.INFO, "__handle_retrievefile: Illegal filename path")
      arizonareport.send_error(0, "nest: retrievefile detected an illegal filename path, disconnecting")
      __disconnect("stork_nest_comm.__handle_retrievefile: retrievefile detected an illegal filename path")
      storklog.log_nest("stork_nest_comm", "__handle_retrievefile", "end", "error", "")
      return

   if glo_retrievesubdirs == None:
      glo_retrievesubdirs = []   

   # strip subdirectories from filename
   clip = data.rfind("/")
   if clip != -1:
      # need to modify destdir to include subdirectory
      glo_retrievesubdirs.append(data[: clip + 1])
         
      # remove extra path from filename
      data = data[clip + 1:]
   else:
      glo_retrievesubdirs.append("")  
 
   if glo_retrievefiles == None:
      glo_retrievefiles = []   
      
   glo_retrievefiles.append(data)
   storklog.log_nest("stork_nest_comm", "__handle_retrievefile", "end", "ok", "")





def __handle_retrievehash(data):
   """ 
   <Purpose>
      Adds a hash to the hash list.

   <Arguments>
      None.

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   global glo_retrievehashes
   storklog.log_nest("stork_nest_comm", "__handle_retrievehash", "start", "data", data)
   __report_handler("retrievehash", data)
   if not __identified():
      storklog.log_nest("stork_nest_comm", "__handle_retrievehash", "end", "error", "")
      return
      
   if glo_retrievehashes == None:
      glo_retrievehashes = []   
      
   glo_retrievehashes.append(data)
   storklog.log_nest("stork_nest_comm", "__handle_retrievehash", "end", "ok", "")





def __handle_prepare(data, flags = stork_prepare.PREPARE_COPY + \
                                   stork_prepare.PREPARE_LINK):
   """ 
   <Purpose>
      Prepares a package by unpacking, protecting, and sharing files.

   <Arguments>
      data:
             Filename of the package.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      None.
   """
   # prepare/install the requested file
   #(comm, info_string, client_name):
   storklog.log_nest("stork_nest_comm", "__handle_prepare", "start", "data", data)
   __report_handler("prepare", data)
   if not __identified():
      storklog.log_nest("stork_nest_comm", "__handle_prepare", "end", "error", "")
      return

   # TODO is there a security risk if they specify some weird filename?
   filename = data

   i = filename.rfind("/")
   if i == -1:
      plainfilename = filename 
   else:
      plainfilename = filename[i + 1:]

   (os_handle, temp_fn) = tempfile.mkstemp("handle_prepare")
   os.close(os_handle)

   # share the client's file with us as a temp name (so we can get the hash)
   if not arizona_share.link_file(arizona_share.get_identified_clientname(), filename, arizonaconfig.get_option("slicename"), temp_fn):
      # TODO syslog
      arizonareport.send_error(0, "nest: unable to access client file: `" + str(filename) + "', disconnecting.")
      __disconnect("stork_nest_comm.__handle_prepare: unable to access client file: `" + str(filename) + "'")
      storklog.log_nest("stork_nest_comm", "__handle_prepare", "end", "error", "")
      return
   
   # protect the file
   if not arizona_share.protect_file(arizonaconfig.get_option("slicename"), temp_fn):
      # TODO syslog
      arizonareport.send_error(0, "nest: unable to protect client file: `" + str(filename) + "', disconnecting.")
      __disconnect("stork_nest_comm.__handle_prepare: unable to protect client file: `" + str(filename) + "'")
      storklog.log_nest("stork_nest_comm", "__handle_prepare", "end", "error", "")
      return

   # get hash of now-protected file
   try:
      try:
         # TWH: use the original file name for getting the hash
         arizonareport.send_syslog(4, "[DEBUG] stork_nest_comm: get_metadata_hash=" + str(storkpackage.get_package_metadata_hash(temp_fn, False, plainfilename)))
      except:
         arizonareport.send_error(4, "[DEBUG] stork_nest_comm: get_metadata_hash=" + "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])))
      try:
         arizonareport.send_syslog(4, "[DEBUG] stork_nest_comm: get_fn_hash=" + str(arizonacrypt.get_fn_hash(temp_fn, "sha1")))
      except:
         arizonareport.send_error(4, "[DEBUG] stork_nest_comm: get_fn_hash=" + "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])))
      #file_hash = arizonacrypt.get_fn_hash(temp_fn)
      file_hash = storkpackage.get_package_metadata_hash(temp_fn, False, plainfilename)
   except IOError, e:
      # TODO syslog
      arizonareport.send_error(0, "nest: unable to get hash of client file: `" + filename + "', reason:`" + str(e) + "', disconnecting.")
      __disconnect("stork_nest_comm.__handle_prepare: unable to get hash of client file: `" + str(filename) + "', reason:`" + str(e) + "'")
      storklog.log_nest("stork_nest_comm", "__handle_prepare", "end", "error", "")
      return
      
   #print "[DEBUG] filename =", filename # /tmp/59bb5f0cd15ee45ffff24a7c45538045608c8632/nano-1.2.3-1.i386.rpm
   #print "[DEBUG] temp_fn =", temp_fn # /tmp/tmpRfE6Gthandle_prepare
   #print "[DEBUG] file_hash =", file_hash # empty hash... da39a3ee5e6b4b0d3255bfef95601890afd80709
   #print "[DEBUG] arizonaconfig.get_option(\"retrievedir\") =", arizonaconfig.get_option("retrievedir")
   # /usr/local/stork/var/packages
   
   """
   # split filename-hash into filename and hash components
   i = data.rfind("-")
   if i != -1:
      filename = data[0: i]
      file_hash = data[i + 1: ]
   """
   localdir = arizonaconfig.get_option("retrievedir") + "/" + file_hash
   local = localdir + "/" + plainfilename

   # create the path if it does not exist. This can happen if the file
   # was provided by the client, rather than retrieved by the nest?
   if not os.path.exists(localdir):
      try:
         #arizonareport.send_out(0, "nest: creating directory " + localdir)
         os.makedirs(localdir)
      except:
         arizonareport.send_error(0, "nest: unable to create dir `" + localdir + "', disconnecting.")
         __disconnect()
         storklog.log_nest("stork_nest_comm", "__handle_prepare", "end", "error", "")
         return

   if not os.path.exists(temp_fn):
      arizonareport.send_error(0, "nest: __handle_prepare: file " + temp_fn + " does not exist, disconnecting.")
      __disconnect()
      storklog.log_nest("stork_nest_comm", "__handle_prepare", "end", "error", "")
      return
       
   # move temp file to new location (and name), based on file hash
   try:
      os.rename(temp_fn, local)
   except OSError, e:
      arizonareport.send_error(0, "nest: unable to move `" + temp_fn + "' to `" + local + "', disconnecting.")
      __disconnect()
      storklog.log_nest("stork_nest_comm", "__handle_prepare", "end", "error", "")
      return

   if not stork_prepare.prepare_package(local, arizona_share.get_identified_clientname(), flags):
      # TODO syslog
      arizonareport.send_error(0, "nest: failed to prepare `" + str(local) + "', disconnecting.")
      __disconnect("stork_nest_comm.__handle_prepare: failed to prepare `" + str(local) + "'")
      storklog.log_nest("stork_nest_comm", "__handle_prepare", "end", "error", "")
      return
   
   arizonacomm.send("prepared", "")
   storklog.log_nest("stork_nest_comm", "__handle_prepare", "end", "ok", "")





def __handle_share(data):
   """ 
   <Purpose>
      Share is like 'Prepare', except that it verifies that files are identical
      before linking them, and does not copy configuration files. It is used
      when a package is already installed in a client slice, and we want to
      overwrite the package's files with links. 

   <Arguments>
      data:
             Filename of the package.

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   __handle_prepare(data, stork_prepare.PREPARE_LINK + \
                          stork_prepare.PREPARE_VERIFY_SAME)   




def __identified():
   """ 
   <Purpose>
      Terminates the connection unless the client is identified.

   <Arguments>
      None.

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      True is identified, False if not.
   """
   client = arizona_share.get_identified_clientname()
   if client == None:
      arizonareport.send_syslog(arizonareport.INFO, "__identified: Not identified")
      arizonareport.send_error(0, "nest: identify failed, disconnecting")
      __disconnect("stork_nest_comm.__identified: identify failed")
   return client != None   
      
      
      
      
      
def __disconnect(reason):
   """ 
   <Purpose>
      Terminates the connection.

   <Arguments>
      reason:
          Reason for the disconnection.

   <Exceptions>
      IOError if socket communications fails.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   arizonareport.send_syslog(arizonareport.INFO, "Disconnecting client.")
   arizonacomm.disconnect(reason)
            




def __report_handler(name, data):
   """ 
   <Purpose>
      Syslogs the connection, handler name, and data.

   <Arguments>
      None.

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   arizonareport.send_syslog(arizonareport.INFO, "[" + glo_connection + "] Handling " + name + ", data: `" + data + "'")


   


def __overwrite_file(filename, text):
   """ 
   <Purpose>
      Overwrites filename with the given text.

   <Arguments>
      filename:
              File to write to.
      text:
              Text to write.

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   try:
      out_file = open(filename, "w")
      out_file.write(text)
      out_file.close()
   except IOError:
      arizonareport.send_syslog(arizonareport.ERR, "IOError writing " + filename)
      os._exit(0)
   return





class arizonacomm_out:
   """
   <Purpose>
      Alternate stdout stream that sends output to the connected client.

   <Parent>
      object
   """
   def __init__(self):
      pass
   
   def flush(self):
      arizonacomm.send("flush_out", "")
      
   def write(self, s):
      if s.endswith("\n"):
         arizonacomm.send("send_out", s[0:len(s) - 1])
      else:
         arizonacomm.send("send_out_comma", s)





class arizonacomm_err:
   """
   <Purpose>
      Alternate stderr stream that sends error output to the connected 
      client.

   <Parent>
      object
   """
   def __init__(self):
      pass
   
   def flush(self):
      arizonacomm.send("flush_error", "")
      
   def write(self, s):
      if s.endswith("\n"):
         arizonacomm.send("send_error", s[0:len(s) - 1])
      else:
         arizonacomm.send("send_error", s)





########################### MAIN ###############################
def main():
   # use error reporting tool
   storkerror.init_error_reporting("stork_nest_comm.py")

   # process command line and initialize variables
   args = arizonaconfig.init_options('stork_nest_comm.py', configfile_optvar='configfile', version=stork_nest_version.VERREL)

   arizonareport.set_output_function(output_func_pid)

   # there should not be any leftover options
   if args:
      arizonareport.send_error(0, "Arguments not understood: " + str(args))
      sys.exit(1)

   arizona_share.init()

   # run as a daemon
   if arizonaconfig.get_option("daemon"):
      arizonageneral.make_daemon("stork_nest_comm.py")

   # display ready message
   if not arizonaconfig.get_option("daemon"):
      print "Ready for connections..." 
      
   # infinite loop (daemon must keep running)
   #while True:
      # Handle incoming connections
      #try:
   arizonacomm.listen("localhost", arizonaconfig.get_option("listenport"), handle_connection) 
      #except: # the daemon must be able to report ANY problem
         #arizonareport.send_syslog(arizonareport.ERR, "Error : " + str(sys.exc_info()[0]) + " " + str(sys.exc_info()[1]) + " " + str(traceback.format_tb(sys.exc_info()[2])))





#-------------------------------------------------------------------------
# Start main
#-------------------------------------------------------------------------
if __name__ == "__main__":
   main()
