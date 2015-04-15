#! /usr/bin/env python

import sys
import os
import securerandom
import arizonacomm
import arizonageneral
import arizonareport
import arizonaconfig
import shutil
import stork_proper
import storklog
import filecmp


"""arizonaconfig
   options=[
            ["",     "--slicename",   "slicename",   "store", "string", "arizona_stork",                   "NAME",      "our slice name (default arizona_stork)"],
            ["",     "--verifyprotect", "verifyprotect", "store_true", None, False, None, "verify that files are protected when sharing"]]

   includes=[]
"""




glo_identified = False
glo_state = None
glo_randdir = None
glo_client = None





# This will be called before any other routines
def init_sharing_program():

   # Check that we know who we are...
   if arizonaconfig.get_option('slicename') == None:
      arizonareport.send_error(0, "--slicename must be set")
      arizonareport.send_syslog(arizonareport.ERR, "slicename hasn't been set")
      sys.exit(1)
   
   



def identify(data):
   """ TODO comments """
   global glo_identified
   global glo_state
   global glo_randdir
   global glo_client
   
   storklog.log_nest("planetlab_share", "identify", "start", "data", data)

   # if the client is already identified, we're done
   if glo_identified:
      arizonacomm.send("identified", arizonaconfig.get_option("slicename"))
      storklog.log_nest("planetlab_share", "identify", "end", "yes", "")
      return
   
   # clean up after any previous attempts
   glo_identified = False
   if glo_randdir != None:
      try:
         os.rmdir(glo_randdir)
      except:
         pass    

   # create test directories and start the identification process rolling
   glo_client = data
   glo_randdir = "/tmp/" + str(securerandom.SecureRandom().random())
   os.mkdir(glo_randdir)
   os.mkdir(glo_randdir + "/identify")
   glo_state = 0
   arizonacomm.send("createdirectory", glo_randdir)
   storklog.log_nest("planetlab_share", "identify", "end", "ok", "")


      


def identifyready(junk_data):
   """ TODO comments """
   global glo_identified
   global glo_state
   global glo_randdir
   
   storklog.log_nest("planetlab_share", "identifyready", "start", "", "")

   if glo_state == 0:
      arizonacomm.send("createfile", glo_randdir + "/.exportdir")
      glo_state = 1      
   elif glo_state == 1:
      arizonacomm.send("appendactive", arizonaconfig.get_option("slicename") + "\n")
      glo_state = 2
   elif glo_state == 2:  
      # Try to mount their directory onto ours.  If the /tmp/.../identify 
      # directory disappears, then they are identified, otherwise not.
      __share_directory(glo_client, glo_randdir, arizonaconfig.get_option("slicename"), glo_randdir, "")
      glo_identified = not os.path.exists(glo_randdir + "/identify")
      # clean up... 
      unshare_directory(arizonaconfig.get_option("slicename"), glo_randdir)
      # BUG TODO FIXME NEEDS WORK 
      # There is a bug that gets triggered here...   Sometimes the above unmount
      # call fails silently (acts like success) and then these fail.   I will wrap
      # in try: except OSError: until I figure out
      # NOTE: I copied these comments from the previous authenticate code.. 
      #       It is possible that the bug has been fixed due to the refactoring.
      try:
         os.rmdir(glo_randdir + "/identify")
         os.rmdir(glo_randdir)
      except OSError:
         arizonareport.send_syslog(arizonareport.INFO, "Triggered known BUG in identifyready()\n")
         arizonareport.send_syslog(arizonareport.INFO, "BUG trying to rmdir(" + glo_randdir + "/identify)\n")
         arizonareport.send_syslog(arizonareport.INFO, "BUG trying to rmdir(" + glo_randdir + ")\n")
         arizonareport.send_syslog(arizonareport.INFO, "BUG Exception: " + str(sys.exc_info()[0]) + " " + str(sys.exc_info()[1]) + " " + str(sys.exc_info()[2]))
         arizonareport.send_syslog(arizonareport.INFO, "End BUG ")
      arizonacomm.send("removefile", glo_randdir + "/.exportdir")
      glo_state = 3
   elif glo_state == 3:      
      arizonacomm.send("removedirectory", glo_randdir)
      glo_randdir = None
      glo_state = 4
   elif glo_state == 4:  
      glo_state = None
      if glo_identified:
         arizonacomm.send("identified", arizonaconfig.get_option("slicename"))
         storklog.log_nest("planetlab_share", "identifyready", "identified", "yes", "")
      else:
         arizonacomm.send("identifyfailed", "")
         storklog.log_nest("planetlab_share", "identifyready", "identified", "no", "")
   storklog.log_nest("planetlab_share", "identifyready", "end", "ok", "")

            
      
      
      
def get_identified_clientname():
   if glo_identified:
      return glo_client
   return None 




def share_directory(source_slice, source_dir, target_slice, target_dir, flags):
   """
   <Purpose>
      Share a directory between two slices. It uses Proper.py in planetlab
      servers.   It assumes that source_slice and target_slice have both bound.
      If this is not the case, use __share_directory instead.

   <Arguments>
      source_slice: 
         A slice name that you want to share a directory to.

      source_dir: 
         Directory that you want to share.
       
      target_slice:
         A slice name that you want to share a directory to.

      target_dir: 
         Directory to which you want to share source_dir.
         
      flags:
         If it is not empty string, then share a directory with protection.
         
   <Exceptions>
      OSError:
         If it fails to create directories.

   <Side Effects>
      None.
      
   <Returns>
      True if it succeeds to share, otherwise return False.
   """
   
   # Make sure the slices have bound
   if not __verify_shared(source_slice):
      return False
   if not __verify_shared(target_slice):
      return False

   # Create the source dir if missing
   if not os.path.exists(__path(source_slice, "/" + source_dir)):
      try:		
         os.makedirs(__path(source_slice, "/" + source_dir))
      except OSError, (errno, strerror):
         arizonareport.send_syslog(arizonareport.ERR, "OS error(%s): %s" % (errno, strerror))	
         return False
   elif not os.path.isdir(__path(source_slice, "/" + source_dir)):
      arizonareport.send_syslog(arizonareport.ERR, "Trying to share_dir on with a non-dir as a source "+__path(source_slice, "/" + source_dir))	
      return False

   # Create the target dir if missing
   if not os.path.exists(__path(target_slice, "/" + target_dir)):
      try:		
         os.makedirs(__path(target_slice, "/" + target_dir))
      except OSError, (errno, strerror):
         arizonareport.send_syslog(arizonareport.ERR, "OS error(%s): %s" % (errno, strerror))	
         return False
   elif not os.path.isdir(__path(target_slice, "/" + target_dir)):
      arizonareport.send_syslog(arizonareport.ERR, "Trying to share_dir on with a non-dir as a target "+__path(target_slice, "/" + target_dir))	
      return False

   # Prepare the source for sharing
   __write_file(__path(source_slice,source_dir+"/.exportdir"),arizonaconfig.get_option('slicename'))

   # Make sure we can unmount this later...
   __write_file(__path(source_slice,source_dir+"/.unmountdir"),arizonaconfig.get_option('slicename'))


   # Prepare the target for mounting onto
   __write_file(__path(target_slice,target_dir+"/.importdir"),arizonaconfig.get_option('slicename'))

   # If they set flags, they meant ro, we assume
   if not flags == "":
      flags = "ro"

   return __share_directory(source_slice, source_dir, target_slice, target_dir, flags)
   




def __share_directory(source_slice, source_dir, target_slice, target_dir, flags):
   """
   <Purpose>
      Help function which calls stork_proper to use Proper.py to share a
      directory.
      
   <Arguments>
      source_slice: 
         A slice name that you want to share a directory of.

      source_dir:
         Directory that you want to share.
       
      target_slice:
         A slice name that you want to share a directory to.

      target_dir: 
         Directory to which you want to share source_dir.
       
      flags:
         If it is not empty string, then share a directory with protection.

   <Exceptions>
      None.

   <Side Effects>
      None.
      
   <Returns>
      True if it succeeds to share, otherwise return False.
   """
   # Get correct directories for Proper call
   sourcefinal = __cpath(source_slice, source_dir)
   targetfinal = __cpath(target_slice, target_dir)

   # We need to check if the directory can be mounted.  The absense of the .. directory means that there
   # is a problem with the directory, and it needs to be unmounted before we can continue.
   if os.path.exists(targetfinal): 
      result = os.system("ls -al " + targetfinal + " | grep \\\\.\\\\. > /dev/null 2> /dev/null") 
      if result != 0:
         unshare_directory(target_slice, target_dir)

   return stork_proper.mount_dir(sourcefinal, targetfinal, flags)
#   return stork_proper.call(["mountdir", sourcefinal, targetfinal, flags])


def unshare_directory(source_slice, source_dir):
   """
   <Purpose>
      Unshare a directory in source slice if it's shared. It uses Proper.py
      to do so.
      
   <Arguments>
      source_slice: 
         A slice name in which you want to unshare a directory. 

      source_dir: 
         Directory that you want to unshare.

   <Exceptions>
      None.
      
   <Side Effects>
      None.
      
   <Returns>
      True if it succeeds to unshare, otherwise return False.
   """

   return stork_proper.unmount(__cpath(source_slice, source_dir))
   #return stork_proper.call(["unmount", __cpath(source_slice, source_dir)])

#import planetlab_share as k
#import arizonaconfig as o
#o.init_options()
#o.set_option("slicename", "arizona_stork")  
#o.set_option("nesttype", "planetlab")  
#k.share_directory("", "/tmp/share1", "", "/tmp/share2", "")





def copy_file(source_slice, source_file, target_slice, target_file):
   if not __verify_shared(source_slice):
      return False
   if not __verify_shared(target_slice):
      return False

   # Get the source and dest
   sourcefinal = __path(source_slice, source_file)
   targetfinal = __path(target_slice, target_file)

   # Note what we are doing
   arizonareport.send_syslog(arizonareport.INFO, 'Copy "' + source_file + '" to "' + targetfinal + '"') 

   # Does the source file exist?
   if not arizonageneral.valid_fn(sourcefinal):
      arizonareport.send_syslog(arizonareport.ERR, sourcefinal + " doesn't exist")
      return False   
      
   # Build the target path if it doesn't exist
   if not os.path.exists(os.path.dirname(targetfinal)):
      os.makedirs(os.path.dirname(targetfinal))

   # Copy the file
   try:
      shutil.copyfile(sourcefinal, targetfinal)
   except IOError, (errno, strerror):
      arizonareport.send_syslog(arizonareport.ERR, "IO error(%s): %s" % (errno, strerror))
      return False	

   return True






def link_file(source_slice, source_file, target_slice, target_file, verify_same):

   if not __verify_shared(source_slice):
      return False
   if not __verify_shared(target_slice):
      return False

   # Find out where things should be placed
   sourcefinal = __path(source_slice,source_file)
   targetfinal = __path(target_slice,target_file)
   
   # TODO FIXME  create destdir if it doesn't exist???

   arizonareport.send_syslog(arizonareport.INFO, 'Link a file "' + sourcefinal + '" to "' + targetfinal + '"') 
  
   try: 
      storklog.log_nest("planetlab_share", "link_file", "file-hash-size", "", sourcefinal + " " + str(os.path.getsize(sourcefinal)))
   except:
      pass

   # Is the source valid?
   if not arizonageneral.valid_fn(__path(source_slice,source_file)):
      arizonareport.send_syslog(arizonareport.ERR, "In planetlab_share.link_file, '"+sourcefinal+"' is invalid")
      return False

   if verify_same:
      # verify_same is used by stork_prepare to only link files that are
      # identical. A different file is not an error so do not return False. We
      # want to return True so that arizona_share continues to link the other
      # files in the package. 
      
      # can't be the same if the target doesn't exist
      if not os.path.exists(targetfinal):
         return True

      if not filecmp.cmp(sourcefinal, targetfinal):
         return True

   # If it exists, remove and relink because os.link fails if the target exists...
   if os.path.exists(targetfinal):
      if os.path.isfile(targetfinal):
         os.unlink(targetfinal)
      else:
         arizonareport.send_syslog(arizonareport.ERR, "In planetlab_share.link_file, '"+targetfinal+"' exists and is not a file")
         return False
   
   # Check for the dir and create if missing
   if not os.path.exists(os.path.dirname(targetfinal)):
      os.makedirs(os.path.dirname(targetfinal))

   try:
      os.link(sourcefinal, targetfinal)
   except OSError, (errno, strerror):
      arizonareport.send_syslog(arizonareport.ERR, \
          "planetlab_share.link_file('" + sourcefinal + "','" + \
          targetfinal + "') OS error(%s): %s" % (errno, strerror))
      return False

   return True




def unlink_file(target_slice, target_file):

   # Make sure the slice has bound
   if not __verify_shared(target_slice):
      return False

   targetfinal = __path(target_slice, target_file)

   arizonareport.send_syslog(arizonareport.INFO, 'Unlink a file "' + targetfinal + '"')

   # TODO FIXME Below we should catch FNF, is dir, etc. errors
   try:
      os.unlink(targetfinal)
   except OSError, (errno, strerror):
      arizonareport.send_syslog(arizonareport.ERR, "OS error(%s): %s" % (errno, strerror))
      return False

   return True





def __count_subdirectory_depth(path):
   # if there is a trailing slash, get rid of it, as it will mess up our
   # count
   path = path.rstrip("/")

   pathLen = len(path.split("/"))
   longest = 0
   for root, dirs, files in os.walk(path):
      cur = len(root.split("/"))
      if cur > longest:
         longest = cur

   # longest is the length of the longest full pathname, so subtrace the
   # components that were in the base path we were searching
   return longest - pathLen




def protect_directory(target_slice, target_dir):
   """ protect all subdirectories and files of the given directory """
   arizonageneral.check_type_simple(target_slice, "target_slice", str, "planetlab_share.protect_directory")
   arizonageneral.check_type_simple(target_dir, "target_dir", str, "planetlab_share.protect_directory")

   arizonareport.send_syslog(arizonareport.INFO, 'Protect dir "' + target_dir + '" on slice "' + str(target_slice) + '"')

   # Make sure the slice has bound
   if not __verify_shared(target_slice):
      return False

   # Uncomment the following to switch to fallback method
   """
   for root, dirs, files in os.walk(target_dir):
      for name in files:
         if not protect_file(target_slice, os.path.join(root, name)):
            return False
   return True
   """

   path = target_dir
   # note: add 1 to count_subdirectory_depth, so we include a mask for the
   # filenames themselves
   for x in xrange(0, __count_subdirectory_depth(target_dir) + 1):
      path += "/*"
      targetfinal = __path(target_slice, path)

      # TODO FIXME Should catch FNF, etc. errors
      if not stork_proper.set_flags(targetfinal, "1"):
         arizonareport.send_out(1, 'Protect dir: failed to protect ' + targetfinal)
         arizonareport.send_syslog(arizonareport.INFO, 'Protect dir: failed to protect ' + targetfinal)
         return False

   # verification
   if arizonaconfig.get_option("verifyprotect"):
      for root, dirs, files in os.walk(target_dir):
         for name in files:
            __verify_protected_file(target_slice, os.path.join(root, name))

   return True


def __verify_protected_file(target_slice, target_file):
   """ verifies that a file had the NOCHANGE bit set """

   arizonageneral.check_type_simple(target_slice, "target_slice", str, "planetlab_share.protect_file")
   arizonageneral.check_type_simple(target_file, "target_file", str, "planetlab_share.protect_file")

   # Make sure the slice has bound
   if not __verify_shared(target_slice):
      return False

   targetfinal = __path(target_slice, target_file)

   flags = stork_proper.get_flags(targetfinal)

   if (not flags) or (flags != "00000001"):
      arizonareport.send_syslog(arizonareport.ERR, "file " + targetfinal + " was not protected (flags=" + flags + ")")
      arizonareport.send_out(1, "file " + targetfinal + " was not protected (flags=" + flags + ")")
      return False
   else:
      arizonareport.send_syslog(arizonareport.INFO, "file " + targetfinal + " verified protection")
      arizonareport.send_out(1, "file " + targetfinal + " verified protection")
      return True


def protect_file(target_slice, target_file):

   arizonageneral.check_type_simple(target_slice, "target_slice", str, "planetlab_share.protect_file")
   arizonageneral.check_type_simple(target_file, "target_file", str, "planetlab_share.protect_file")

   arizonareport.send_syslog(arizonareport.INFO, 'Protect file "' + target_file + '" on slice "' + str(target_slice) + '"')

   # Make sure the slice has bound
   if not __verify_shared(target_slice):
      return False

   targetfinal = __path(target_slice, target_file)

   # TODO FIXME Should catch FNF, etc. errors
   result = stork_proper.set_flags(targetfinal, "1")

   if arizonaconfig.get_option("verifyprotect"):
       __verify_protected_file(target_slice, target_file)

   return result



## from Jeffry's code
def __write_file(filename, text):
   arizonageneral.check_type_simple(filename, "filename", str, "planetlab_share.__write_file")
   arizonageneral.check_type_simple(text, "text", str, "planetlab_share.__write_file")

   try:
     thefile = open(filename, "w")
     thefile.write(str(text) + '\n')
     thefile.close()
   except IOError:
      arizonareport.send_syslog(arizonareport.ERR, "IOError writing " + filename)
   return
	



def init_client(client_name):
   try:
      os.makedirs(__path(client_name,"/"))
   except OSError:
      # If the directory exists, this is okay...
      pass
   result = __share_directory(client_name, '/', arizonaconfig.get_option('slicename'), __path(client_name,"/"), "")		
   return result




# Returns the location of an item given a slice name and a fully qualified path
# NEEDS WORK TODO FIXME (Should NOT follow symlinks or at least should do so in
# the users FS instead)
def __path(slice, fqpn):
   if not slice or slice == arizonaconfig.get_option('slicename'):
      return fqpn
   else:
      return "/children/"+slice+fqpn


# Returns the location of an item given a slice name and a fully qualified path
def __cpath(slice, fqpn):
   if not slice or slice == arizonaconfig.get_option('slicename'):
      return fqpn
   else:
      return slice+":"+fqpn



def share_name():
   return 'planetlab'


# See if a slice is shared
def __verify_shared(slice):

   # It's us!
   if not slice or slice == arizonaconfig.get_option('slicename'):
      return True

   # Is there already a dir for this client
   if not os.path.exists(__path(slice,"/")):
      arizonareport.send_syslog(arizonareport.ERR, slice + " hasn't been shared")
      return False
      
   # We init to test (because the dir may exist but it can't be bound).   
   # If it isn't bound but could be then we'll bind here (not necessarily good)
   return init_client(slice)
