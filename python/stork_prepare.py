#! /usr/bin/env python

import sys
import arizonaconfig
import arizona_share
import arizonareport
import arizonacrypt
import storkpackage # imported for arizonaconfig options
import arizonacrypt
import os
import traceback


"""arizonaconfig
   options=[
            ["",     "--prepare_sharedir", "prepare_sharedir", "store", "string", "/share/package_dir", "PATH", "use this path for prepared package dir (default is /share/package_dir)"],   
            ["",     "--packagepreparers", "packagepreparers", "append", "string", ["rpm"], "packagepreparers", "use these programs to prepare packages on the nest (default rpm)"]]

   includes=[]        
"""

PREPARE_COPY = 1
PREPARE_LINK = 2
PREPARE_VERIFY_SAME = 4


chosen_packman = None

def __initialize_preparer(packman_type):
   """
   <Purpose>
      Initialize given type of package prepare manager.

   <Arguments>
      packman_type: 
         The name of package prepare manager.

   <Exceptions>
      ImportError:
         If given package prepare manager can not be found. 
         
   <Side Effects>
      Set chosen_packman by the package prepare manager name given as an
      argument.

   <Returns>
      None.
   """
   global chosen_packman
   try:
      # import packman_type
      # TODO possible security problem here
      exec ('import prepare.stork_' + packman_type + '_prepare as chosen_packman')
      globals()['chosen_packman'] = locals()['chosen_packman']
   except ImportError, (errno):
      arizonareport.send_error(0, "initialize_preparer: Import error(%s)" % (errno))	





def prepare_package(packagename, client_slice, flags):
   """
   <Purpose>
      Prepare given package. To do so, it extracts given package to a
      directory with copy and link subdirectories. Files in copy directory 
      will be copied to target_dir and files in link directory will be
      linked to target_dir.      

   <Arguments>
      packagename: 
         The name of package that needs to be prepared.
         
      client_slice: 
         The slice name to which extracted files will be copied and linked.

      flags:
         One or more of PREPARE_LINK, PREPARE_COPY, and PREPARE_VERIFY_SAME

   <Exceptions>
      TypeError:
         Invalid type for packagename and client_slice.
         
      ImportError:
         If 'packagepreparers' or 'prepare_sharedir' has not been set. 
         
   <Side Effects>
      None.
      
   <Returns>
      If it succeeds to prepare given package, then return True.
      Otherwise, return False.
   """
   arizonareport.send_syslog(4, "[DEBUG] stork_prepare.prepare_package: packagename=" +packagename+ " slice=" +client_slice);
   
   # get a list of strings which indicate what package manages are available   
   packmanagers = arizonaconfig.get_option("packagepreparers")
   prepare_base_dir = arizonaconfig.get_option("prepare_sharedir")

   # if there is no setting for packagepreparers option in arizonaconfig
   if packmanagers ==  None:
      # raise importError
      raise ImportError, "prepare_package: no setting for packagepreparers in arizonaconfig"
   
   # if there is no setting for prepare_sharedir option in arizonaconfig
   if prepare_base_dir ==  None:
      # raise importError
      raise ImportError, "prepare_package: no setting for prepare_sharedir in arizonaconfig"

   # if the base dir(/share/package_dir for default) doesn't exist
   if not os.path.exists(prepare_base_dir):
      os.makedirs(prepare_base_dir)

   # dir where the package will be prepared
   #print "[DEBUG] packagename =", packagename
   #print "[DEBUG] prepare_base_dir =", prepare_base_dir
   
   try:
      arizonareport.send_syslog(4, "[DEBUG] stork_prepare: get_metadata_hash=" + str(storkpackage.get_package_metadata_hash(packagename)))
   except TypeError: #changed from a general exception
      arizonareport.send_error(4, "[DEBUG] stork_prepare: get_metadata_hash=" + "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])))
   try:
      arizonareport.send_syslog(4, "[DEBUG] stork_prepare: get_fn_hash=" + str(arizonacrypt.get_fn_hash(packagename, "sha1")))
   except TypeError: #changed from a general exception
      arizonareport.send_error(4, "[DEBUG] stork_prepare: get_fn_hash=" + "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])))
   #target_dir = prepare_base_dir + "/" + arizonacrypt.get_fn_hash(packagename, "sha1").strip()
   target_dir = prepare_base_dir + "/" + storkpackage.get_package_metadata_hash(packagename).strip()   

   # check if the package is prepared in given target_dir
   check_prepared = False
   
   # if the package is already prepared by having the same target directory
   if os.path.exists(target_dir):
      check_prepared = True
   else:
      # create the target_dir
      os.makedirs(target_dir)
      # go through every possible package prepare manager
      for apackman in packmanagers: 
         try:
            # TWH: we should not bomb out if we fail to find a prepare manager
            __initialize_preparer(apackman)  
            #print "[DEBUG] chosen_packman =", chosen_packman
            #print "[DEBUG] chosen_packman.prepare(", packagename, ",", target_dir, ")"
            chosen_packman.prepare(packagename, target_dir)      
            #print "[DEBUG] chosen_packman.prepare() returned"
         # fail to prepare the package, using current package prepare manager
         # move to the next manager
         except IOError:
            #print "[DEBUG] chosen_packman.prepare() ERROR"
            continue
         # now the package is prepared
         check_prepared = True
   
   # it fails to prepare the given package
   if not check_prepared:
      #print "[DEBUG] Failed to prepare: stork_prepare_package.prepare_package returning False"
      os.rmdir(target_dir)
      return False
   
   if flags and PREPARE_COPY:
      #print "[DEBUG] arizona_share.copy_directory(\"\",", target_dir + "/copy/", ",", client_slice, ",", "/", ")"
      arizona_share.copy_directory("", target_dir + "/copy/", client_slice, "/")

   if flags and PREPARE_LINK:
      #print "[DEBUG] arizona_share.protect_directory(\"\",", target_dir + "/link/", ")"
      arizona_share.protect_directory("", target_dir + "/link/")
   
      #print "[DEBUG] arizona_share.link_directory(\"\"", ",", target_dir + "/link/", ",", client_slice, ",\"/\")"
      arizona_share.link_directory("", target_dir + "/link/", client_slice, "/", flags and PREPARE_VERIFY_SAME)
   
   # TODO error and return status checking for the 3 functions above
   return True
   
   
   
