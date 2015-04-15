#! /usr/bin/env python

"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: arizonatransfer
Description:   Provides file transferring from host and synchronizing two
               different directories.
"""

"""arizonaconfig
   options=[["",     "--transfermethod",  "transfermethod", "append", "string", ["ftp", "http"], "program", "use this method to transfer files (default ftp, http)"],
            ["",     "--transfertempdir", "transfertempdir", "store", "string", "/tmp/stork_trans_tmp", "PATH", "use this path to save transferd files temporary (default is /tmp/stork_trans_tmp)"],
            ["",     "--metafilecachetime", "metafilecachetime", "store", "int", 60, None, "seconds to cache metafile without re-requesting"]]
   includes=["$MAIN/transfer/*"]
"""

import sys
import os.path
import arizonareport
import arizonaconfig
import securerandom
import arizonageneral
import shutil
import traceback
import arizonacrypt
import storkpackage
import time
import signal

from stat import *

# metafile holds the names of files which need to sync
metafile = "metafile"
signedmetafile_fn = metafile + ".signed"

# it holds what transfer method is imported
global arizonafetch
arizonafetch = None

# indicates importing status. If init_status is -1, then no transfer module has been imported.
init_status = -1
prioritylist = []
modules_failed_install = []

# pass this in a file tuple when the size is unknown
SIZE_UNKNOWN = None





class TransferTimeOutExc(Exception):
    def __init__(self, value = "Timed Out"):
        self.value = value
    def __str__(self):
        return repr(self.value)





def TransferAlarmHandler(signum, frame):
   raise TransferTimeOutExc





glo_oldsignal = None
def __enable_timeout(seconds):
   """
      <Purpose>
          Enable the alarm signal
      <Arguments>
          seconds - number of seconds when alarm will go off
   """
   global glo_oldsignal
   glo_oldsignal = signal.signal(signal.SIGALRM, TransferAlarmHandler)
   signal.alarm(seconds)





def __disable_timeout():
   """
      <Purpose>
          disable the alarm signal
   """
   global glo_oldsignal
   signal.alarm(0)
   if glo_oldsignal!=None:
       signal.signal(signal.SIGALRM, glo_oldsignal)
       glo_oldsignal = None





def __compute_timeout(filelist):
   """
      <Purpose>
          compute a timeout for a file list.
      <Arguments>
          filelist - a list of file tuples (name, hash, size)
      <Returns>
          timeout in seconds
   """
   total_size = 0
   unknown_size = True

   for file in filelist:
      size = file.get('size', SIZE_UNKNOWN)
      if size != SIZE_UNKNOWN:
         unknown_size = False
         total_size = total_size + size

   if unknown_size:
      # if the size is unknown, return 60 minutes
      return 60*60
   else:
      # otherwise, return 10 minutes + 1 minute per megabyte
      return 60*10 + total_size / (1024*1024/60)





def reset_transfer_method():
   """
      <Purpose>
          reset the init_status variable. This will cause arizonatransfer to
          start transfering with the highest priority method again
   """
   global init_status
   init_status = -1




def default_hashfunc(filename):
   return arizonacrypt.get_fn_hash(filename, "sha1")




def initialize_transfer_method(method):
   global arizonafetch
   global prioritylist
   global init_status
   global modules_failed_install;

   if method in modules_failed_install:
       arizonareport.send_error(2, "WARNING: method '" + method + "' previously tried to initialize and failed; skipping...") 
       arizonafetch = None
       return

   try:
      # import a certain transfer method
      # TODO possible security problem?   For example, method="nest as arizonafetch; hostile code...; #"
      exec("import transfer.arizonatransfer_" + method + " as arizonafetch")    

      # crazy and only way to use 'exec'   :)
      globals()['arizonafetch'] = locals()['arizonafetch']

      arizonareport.send_syslog(arizonareport.INFO, "\n" + arizonafetch.transfer_name() + " starting...")

      # initialize the transfer method
      try:
         arizonafetch.init_transfer_program()
      except:
         arizonareport.send_syslog(arizonareport.ERR, "getfiles(): Initializing : Initialization error.")
         arizonareport.send_error(2, "WARNING: Could not initialize " + method + " transfer...")
         arizonafetch = None
         return

      # init_status is set by index number so that it will indicate that something is imported
      init_status = prioritylist.index(method)
   # if module name doesn't exist
   except ImportError, (errno):
      modules_failed_install.append(method)
      arizonareport.send_syslog(arizonareport.ERR, "getfiles(): Initializing : Import error(" + str(errno) + ")")
      arizonafetch = None
      arizonareport.send_error(2, "WARNING: Could not import " + method + " transfer: " + str(errno))



def getfiles(host, filelist, destdir, hashlist=[""], prog_indicator=0, createhashfile=False):
   """ stub for the old getfiles to convert parameters to getfiles1

       XXX this will go away soon

   """
   if hashlist == [""]:
      hashlist = None

   if hashlist != None and len(hashlist) != len(filelist):
      arizonareport.send_syslog(arizonareport.ERR, "getfiles(): The number of files given doesn't match the number of hashes given.")
      return (False, downloaded_files)

   tuples = []

   for (i,file) in enumerate(filelist):
      if hashlist:
         hash = hashlist[i]
      else:
         hash = None

      dict = {"filename": file}
      if hash:
         dict['hash'] = hash

      # XXX this will be going away
      dict['hashfuncs'] = [storkpackage.get_package_metadata_hash, default_hashfunc]

      tuples.append(dict)

   return getfiles1(host, tuples, destdir, prog_indicator, createhashfile)





def getfiles1(host, filelist, destdir, prog_indicator=0, createhashfile=False):
   """
   <Purpose>
      This fetches files from given host, using prioritylist which holds
      transfer methods to fetch files.
      It tries to get files by one method, and if it fails it uses next
      possible method until it gets all files needed.

   <Arguments>
      host:
         'host' holds two things, a server name and download directory.
         For example, if you want to retrieve files from '/tmp/' directory
         in 'quadrus.cs.arizona.edu' server, the 'host' will be
         'quadrus.cs.arizona.edu/tmp'.
         'host' should be a string.

      filelist:
         'filelist' is a list of files which need to be retrieved.
         'filelist' should be a list of dictionaties of the format:
             {"filename": filename,
              "hash": hash,
              "size": size,
              "hashfuncs": list of hashfuncs to try}
             the hash and size parameters can be None if unavailable

      destdir:
         'destdir' is a destination directory where retrieved files will
         be placed. A user should have 'destdir' exist before retrieving
         files. 'destdir' should be a string.

      prog_indicator:
         If it is non-zero, this program will show a progress bar while
         downloading, with the given width. Default value is 0 (no
         indicator is shown).

   <Exceptions>
      None.

   <Side Effects>
      Messes with SIGALRM
      Set init_status

   <Returns>
      True or False to indicate success, and a list of downloaded files
   """

   global init_status
   global arizonafetch
   global prioritylist

   arizonareport.send_out(4, "[DEBUG] getfiles started")
   arizonareport.send_out(4, "host = " + str(host) + ", filelist = " + str(filelist))

   # downloaded files list
   downloaded_files = []

   # check if host is a string
   arizonageneral.check_type_simple(host, "host", str, "arizonatransfer.getfiles")

   # check if destdir is a string
   arizonageneral.check_type_simple(destdir, "destdir", str, "arizonatransfer.getfiles")

   # get username
   username = arizonageneral.getusername()

   # check that the destination directory exists
   if not os.path.isdir(destdir):
      arizonareport.send_syslog(arizonareport.ERR, "\ngetfiles(): The destination directory '" + destdir + "' does not exist...   Aborting...")
      # return false and empty list
      return (False, downloaded_files)

   # transfer method list set by arizonaconfig
   prioritylist = arizonaconfig.get_option("transfermethod")

   # check the method list
   # if prioritylist is None, there's something wrong with configuration
   if prioritylist == None :
      arizonareport.send_syslog(arizonareport.ERR, "getfiles(): No transfer method was given.")
      return (False, downloaded_files)

   # create a temporary directory for the transfer
   arizonareport.send_out(4, "[DEBUG] getfiles creating temp dir")
   try:
      temp_dir = arizonaconfig.get_option("transfertempdir") + str(securerandom.SecureRandom().random())
   except TypeError:
      arizonareport.send_syslog(arizonareport.ERR, "getfiles(): No transfer temp dir is given.")
      return (False, downloaded_files)

   # in the case of destdir has '/' at the end
   # last '/' should go away to make result list(downloaded_files) match
   if len(destdir) > 1 and destdir.endswith('/'):
      destdir = destdir[:len(destdir) - 1]

   # if there is empty strings in the filelist, those will be taken away
   arizonareport.send_out(4, "[DEBUG] checking file list")
   filelist = __checkFileList(filelist)

   arizonareport.send_out(4, "[DEBUG] creating directories")
   for item in filelist:
      filename = item['filename']
      dirname = os.path.dirname(filename)
      if dirname != "":
         arizonageneral.makedirs_existok(os.path.join(temp_dir, dirname))
         arizonageneral.makedirs_existok(os.path.join(destdir, dirname))

   filenames = [item['filename'] for item in filelist]

   # keep the number of the list to compare how many files are downloaded at the end.
   numoflist = len(filelist)

   # if prog_indicator is True, then set it as download_indicator so that it is passed in the transfer method program
   arizonareport.send_out(4, "[DEBUG] importing download_indicator")
   if (prog_indicator > 0):
      try:
         import download_indicator
         prog_indicator_module = download_indicator
         prog_indicator_module.set_width(prog_indicator)
      # if importing fails
      except ImportError:
         arizonareport.send_syslog(arizonareport.ERR, "getfiles(): Error on importing download_indicator.")
         prog_indicator_module = None
   else:
      prog_indicator_module = None

   # if there is no file needing to be fetched
   if filelist == []:
      arizonareport.send_syslog(arizonareport.ERR, "getfiles(): No files needed to be downloaded.")
      return (False, downloaded_files)

   if not os.path.exists(temp_dir):
      arizonageneral.makedirs_existok(temp_dir)

   # With prioritylist provided from configuration, go through transfer method list
   # until download every files requested
   arizonareport.send_out(4, "[DEBUG] prioritylist = " + str(prioritylist))
   for element in prioritylist:
      arizonareport.send_out(3, "[" + username + "] Attempting download via: " + str(element))
      # if no transfer method is initialized
      if init_status == -1:
         initialize_transfer_method(element)

      if arizonafetch == None:
         init_status = -1
         continue

      # try to retrieve files using retrieve_files func of each module
      arizonareport.send_out(3, "[" + username + "] Downloading via " + arizonafetch.transfer_name() + ": " + ", ".join(filenames))
      try:
         __enable_timeout(__compute_timeout(filelist))

         (check, retrieved_files) = arizonafetch.retrieve_files(host, filelist, temp_dir, prog_indicator_module)

         if len(retrieved_files) > 0:
            retrieved_names = [item['filename'] for item in retrieved_files]
            arizonareport.send_out(3, "[" + username + "] Retrieved: " + ", ".join(retrieved_names))
         else:
            arizonareport.send_out(3, "[" + username + "] "+str(element)+" failed to retrieve any files, trying next method.")

         __disable_timeout()
      except:
         __disable_timeout()
         arizonareport.send_out(3, "[" +username+"] "+str(element)+": error: "+ str( sys.exc_info()[0] ) )
         check = False
         retrieved_files = []

      #print "[DEBUG] (arizonatransfer.py) (", check, ",", retrieved_files, ")"

      # check indicates if retrieve_files call succeeded or not
      if not check:
         arizonareport.send_syslog(arizonareport.INFO, "getfiles(): Transfer method failed.")
         # if it fails, move to the next method.
         init_status = -1
         continue
      # now a file has been downloaded
      else :
         # from the list of retrieved files
         for thefile in retrieved_files:
            dest_filename = os.path.join(destdir, thefile['filename'])
            filename = os.path.join(temp_dir, thefile['filename'])
            expected_hash = thefile.get('hash', None)
            hashfuncs = thefile.get('hashfuncs', [default_hashfunc])

            # default to assuming the hash check is ok, reset to false if we
            # find otherwise
            hash_check_flag = 0

            arizonareport.send_error(4, "[DEBUG] hashcode = " + str(expected_hash))
            if not expected_hash:
               # TWH: don't emit this line; we already know this.
               # arizonareport.send_out(3, "[" + username + "] File doesn't have a hash: " + str(filename))
               hash_check_flag = 1
               pass
            else:
               expected_hash = expected_hash.strip()

               # hashfuncs is a list of possible hash functions, so try them all

               actual_hash = None
               for hashfunc in hashfuncs:
                  if not hash_check_flag:
                     try:
                        actual_hash = hashfunc(filename).strip()
                     except:
                        arizonareport.send_error(4, "[DEBUG] arizonatransfer.getfiles: hash func " + str(hashfunc) + " failed: " + "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])))

                     # if we have a match, then break out of the loop
                     if actual_hash == expected_hash:
                        arizonareport.send_out(4, "[DEBUG] hash check succeeded")
                        hash_check_flag = 1

               if not hash_check_flag:
                  arizonareport.send_error(2, "\n   Hash of the downloaded file " + str(filename) + " (" + str(actual_hash) + ") did not match the expected hash (" + str(expected_hash) + ")")
                  hash_check_flag = 0
                  try:
                     os.unlink(filename)
                  except:
                     pass

            if hash_check_flag:
               arizonareport.send_syslog(arizonareport.INFO, '\n"' + filename.split(temp_dir + '/')[1] + '" transferred by ' + arizonafetch.transfer_name())

               # remove downloaded files from fetch_list
               filelist.remove(thefile)

               # remove the destination file, so we can overwrite it
               try:
                  os.remove(dest_filename)
               except:
                  pass

               arizonareport.send_out(4, "[DEBUG] shutil.move(" + filename +  ", " +  dest_filename + ")")
               try:
                  shutil.move(filename, dest_filename)
               except OSError:
                  arizonareport.send_syslog(arizonareport.ERR, "getfiles(): error moving `" + filename + "' to `" + dest + "'")
                  return (False, downloaded_files)

               if createhashfile and actual_hash:
                  try:
                     f = open(dest_filename + ".metahash", "w")
                     f.write(actual_hash)
                     f.close()
                  except:  # TODO: better exception handling
                     arizonareport.send_error(3, "failed to create .metahash file")

               # add downloaded files to downloaded_files
               downloaded_files.append(dest_filename)

      # check whether every file is downloaded
      if filelist == []:
         arizonareport.send_syslog(arizonareport.INFO, "File = " + ", ".join(downloaded_files) + "\ntransfered")
         shutil.rmtree(temp_dir)
         return (True, downloaded_files)
      # still there are files haven't yet downloaded, so move to next method
      elif not len(downloaded_files) == numoflist:
         arizonareport.send_syslog(arizonareport.INFO, "Some files have not been downloaded yet.  Trying the next transfer method.")
         __close_transfer()
         continue
      else:
         arizonareport.send_syslog(arizonareport.ERR, "getfiles(): " + element +
                  " file transfer has failed.  Trying the next transfer method.")
         __close_transfer()
         continue

   # after trying every transfer method
   arizonareport.send_syslog(arizonareport.ERR, "\ngetfiles(): Every transfer method has failed.\n")
   __close_transfer()
   shutil.rmtree(temp_dir)
   return (False, downloaded_files)





def sync_remote_dir(host, destdir, prog_indicator=0, metafile_signature_key=None, hashfuncs=[default_hashfunc]):
   """
   <Purpose>
      This synchronizes files between target directory in host and
      destination directory.

   <Arguments>
      host:
         'host' holds two things, a server name and target directory.
         For example, if you want to retrieve files from '/tmp/' directory
         in 'quadrus.cs.arizona.edu' server, the 'host' will be
         'quadrus.cs.arizona.edu/tmp'.  'host' should be a string.  
         *** The host directory must contain a metafile ***

      destdir:
         'destdir' is a destination directory which will be synchronized.

      prog_indicator:
         If it is non-zero, this program will show a progress bar while
         downloading, with the given width. Default value is 0 (no
         indicator is shown).

      metafile_signature_key:
         The key that is expected to have signed the metafile for this repository.
         If None, then the metafile will not be required to be signed.

   <Exceptions>
      None.

   <Side Effects>
      None

   <Returns>
      A tuple: (result, grabbed_files, all_files)
      
      True or False to indicate success, a list of downloaded files, and a list
      of all files on the server.

      If the metafile_signature_key was provided but the signature is invalid
      or was not signed with this key, then no files will be downloaded and
      result will be False.
   """

   # check to see if we have an existing metafile that is within the cache
   # time limit. If we do, then do not bother to retrieve a new one.
   useCachedMetaFile = False
   metafile_path = os.path.join(destdir, metafile)
   if os.path.exists(metafile_path):
      mtime = os.stat(metafile_path)[ST_MTIME]
      elapsed = abs(int(mtime - time.time()))
      if elapsed < arizonaconfig.get_option("metafilecachetime"):
         arizonareport.send_out(3, "Using cached metafile (" + str(elapsed) + ") seconds old")
         useCachedMetaFile = True

   if not useCachedMetaFile:
      # Fetch a metafile...
      # getfile will check that the validity of host, metafile, and destdir
      # if any of them is incorrect, return_value will be false
      if metafile_signature_key:
         metafile_dict = {"filename": signedmetafile_fn, "hashfuncs": hashfuncs}
         (return_value, file_list) = getfiles1(host, [metafile_dict], destdir, prog_indicator=prog_indicator)
         if not return_value:
            arizonareport.send_syslog(arizonareport.ERR, "sync_remote_dir(): Unable to retrieve " + signedmetafile_fn + " from " + host)
            return (False, [], [])

         signedmetafile_path = os.path.join(destdir, signedmetafile_fn)

         try:
             # verify signature in the sig file
             try:
                arizonacrypt.XML_timestamp_signedfile_with_publickey_fn(signedmetafile_path, None, publickey_string=metafile_signature_key)
             except TypeError:
                arizonareport.send_out(1, "Invalid signature in " + signedmetafile_fn + " from " + host)
                arizonareport.send_syslog(arizonareport.ERR, "sync_remote_dir(): Invalid signature in " + signedmetafile_fn + " from " + host)
                return (False, [], [])

             # extract the metafile
             try:
                metafile_tmp_fn = arizonacrypt.XML_retrieve_originalfile_from_signedfile(signedmetafile_path)
             except TypeError:
                arizonareport.send_out(1, "Unable to extract metafile from " + signedmetafile_fn + " from " + host)
                arizonareport.send_syslog(arizonareport.ERR, "sync_remote_dir(): Unable to extract metafile from " + signedmetafile_fn + " from " + host)
                return (False, [], [])

             f = file(metafile_tmp_fn, 'r')
             sig_file_contents = f.read()
             f.close

         except IOError, (errno, strerror):
             arizonareport.send_syslog(arizonareport.ERR, "sync_remote_dir(): I/O error(" + str(errno) + "): " + str(strerror))
             return (False, [], [])

         arizonareport.send_out(3, "[DEBUG] signed metafile validated from host " + host)

         shutil.copy(metafile_tmp_fn, metafile_path)

      else:
         arizonareport.send_out(2, "No metafile signature key, metafile signature not being checked for " + host)
         metafile_dict = {"filename": metafile, "hashfuncs": hashfuncs}
         (return_value, file_list) = getfiles1(host, [metafile_dict], destdir, prog_indicator=prog_indicator)
         if not return_value:
            arizonareport.send_syslog(arizonareport.ERR, 'sync_remote_dir(): Error in retrieving metafile')
            return (False, [], [])
   
   # Open the file we just retrieved
   arizonareport.send_out(4, "[DEBUG] opening " + metafile_path)
   try:
      dir_file = open(metafile_path)
   # if a file cannot be opened
   except IOError, (errno, strerror):
      arizonareport.send_syslog(arizonareport.ERR, "sync_remote_dir(): I/O error(" + str(errno) + "): " + str(strerror))
      return (False, [], [])

   # files retreived from the server
   grabbed_files = []
   # files available on the server
   all_files = []
   # The list of items to retrieve...
   fetch_list = []

   # for each line in the metafile, check to make sure the local file is okay
   # each line has two string; the first one is filename, and second one is hash
   # go through every file and check if each file exist in the destdir
   # and the hash of files in the destdir match the hash from metafile
   # if it doesn't satisfy, then add the file to fetch_list to be retrieved
   for line in dir_file:       
      # TWH: ignore blank lines
      if len(line.strip()) == 0:
         continue
      # Split the file's line into pieces
      line_dat = line.split()
      if len(line_dat) < 2:
         # invalid line in the meta file
         arizonareport.send_syslog(arizonareport.ERR, "sync_remote_dir(): The format of metafile is incorrect")         
         return (False, grabbed_files, all_files)
  
      # split a line into filename, filehash, and filesize
      filename = line_dat[0]
      expectedhash = line_dat[1].strip()
      if len(line_dat) >= 3:
          filesize = line_dat[2]
      else:
          filesize = None
      localfilename = os.path.join(destdir, filename)
      arizonareport.send_out(4, "[DEBUG] file: " + localfilename)
      arizonareport.send_out(4, "[DEBUG] expected hash: " + expectedhash)

      all_files.append(localfilename)

      # if this file has already been downloaded and checked, it will have
      # a filename.metahash file.. look for it
      if os.path.isfile(localfilename + ".metahash"):
         # open it and compare the hash
         f = open(localfilename + ".metahash")
         precomputedhash = f.read().strip()
         f.close()
         arizonareport.send_out(4, "[DEBUG] precomputed hash: " + precomputedhash)
         if precomputedhash == expectedhash:
            arizonareport.send_out(4, "[DEBUG] precomputed hash matched")
            # The hash matched so try the next file...
            continue
      
      # if a file looking for is in the destination directory
      if os.path.isfile(localfilename):
         # and if it has the same hash 
         # (we tell it to create a filename.metahash file for next time)
         actualhash = storkpackage.get_package_metadata_hash(localfilename, True)
         arizonareport.send_out(4, "[DEBUG] actual hash: " + actualhash)
         if actualhash == expectedhash:
            arizonareport.send_out(4, "[DEBUG] hash matched")
            # The hash matched so try the next file...
            continue

      # add it of the things to get
      arizonareport.send_out(4, "[DEBUG] either hash didn't match or file wasn't found")

      dict = {'filename': filename,
              'hash': expectedhash,
              'hashfuncs': hashfuncs}

      fetch_list.append(dict)

   # if nothing needs to be downloaded
   if fetch_list == []:
      arizonareport.send_syslog(arizonareport.INFO, "\nFetched every requested file.")
   else :
      # get the files which needs to be downloaded
      #TODO pass the expected file sizes and limit the downloads by those sizes
      (return_value, grabbed_files) = getfiles1(host, fetch_list, destdir, prog_indicator, True)
      # fails to get files from host
      if not return_value and grabbed_files == []:
         arizonareport.send_syslog(arizonareport.ERR, "sync_remote_dir(): Failed to retrieve files.")
         return (False, grabbed_files, all_files)

   # if we retrieve every file needed
   if len(fetch_list) == len(grabbed_files):
      return (True, grabbed_files, all_files)
   # if we retrieve some of files
   else:
      arizonareport.send_syslog(arizonareport.ERR, "sync_remote_dir(): Failed to retrieve all files.")
      return (False, grabbed_files, all_files)





def __checkFileList(checklist):
   """
   <Purpose>
      This checks the given list and removes empty elements from the list.

   <Arguments>
      checklist:
         The list to be checked, should contain file tuples.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      The list that empty elements are removed
   """

   checked_list = []
   for item in checklist:
      if (item != None) and ('filename' in item) and (item['filename']):
         checked_list.append(item)

   return checked_list





def __close_transfer() :
   """
   <Purpose>
      This closes the currently using transfer method
   
   <Arguments>
      None

   <Exceptions>
      None

   <Side Effects>
      set init_status as -1

   <Returns>
      None
   """

   global init_status  
   if arizonafetch != None: 
      arizonafetch.close_transfer_program()
   init_status = -1




