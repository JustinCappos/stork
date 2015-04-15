#! /usr/bin/env python

"""
<Program Name>
   stork_proper.py

<Author>
   Justin Cappos.  Rewritten by Jeffry Johnston.

<Purpose>
   Wrapper for Proper calls.
"""

import arizonareport
import arizonageneral
import os
import Proper
import storklog

def is_proper_error(output):
    if (output.find("System error") >= 0) or (output.find("No such file") >= 0):
        return True
    else:
        return False

def get_flags(name):
    """
    <Purpose>
       Gets the flags for a file
    <Arguments>
       names: filename
    <Returns>
       False on error, str containing mask, otherwise
    """
    # import Proper.py; if it is already imported, then this is a no-op
    arizonareport.send_syslog(arizonareport.INFO, "Stork_proper: get_flags " + str(name))

    try:
        import Proper
    except:
        arizonareport.send_syslog(arizonareport.ERROR, "Stork_proper: failed to import Proper.py")
        return False

    # call proper to set the file flags
    try:
        output = Proper.get_file_flags(name)
    except:
        arizonareport.send_syslog(arizonareport.ERROR, "Stork_proper: Exception")
        return False

    if is_proper_error(output):
        arizonareport.send_syslog(arizonareport.ERROR, "Stork_proper: Error")
        return False

    output = output.strip(" \n")
    if not output.startswith("OK: "):
        arizonareport.send_syslog(arizonareport.ERROR, "Stork_proper: Not Ok")
        return False

    result = output[4:].strip()

    arizonareport.send_syslog(arizonareport.INFO, "Stork_proper: " + str(result))

    return result





def mount_dir(sourcefinal, targetfinal, flags):
    arizonareport.send_syslog(arizonareport.INFO, "Stork_proper: mount " + str(sourcefinal) + " " + str(targetfinal) + " " + str(flags))

    #uncomment this to call via os.popen instaed of importing proper directly
    #return call(["mountdir", sourcefinal, targetfinal, flags])

    # import Proper.py; if it is already imported, then this is a no-op
    try:
        import Proper
    except:
        arizonareport.send_syslog(arizonareport.ERROR, "Stork_proper: failed to import Proper.py")
        return False

    # call proper to set the file flags
    try:
        output = Proper.mount_dir(sourcefinal, targetfinal, flags)
    except:
        arizonareport.send_syslog(arizonareport.ERROR, "Stork_proper: Exception in Proper call")
        return False

    if is_proper_error(output):
        arizonareport.send_syslog(arizonareport.ERROR, "Stork_proper: Error")
        return False

    arizonareport.send_syslog(arizonareport.INFO, "Stork_proper: Success")

    return True




def unmount(path):
    arizonareport.send_syslog(arizonareport.INFO, "Stork_proper: unmount " + str(path))

    #uncomment this to call via os.popen instaed of importing proper directly
    #return call(["mountdir", sourcefinal, targetfinal, flags])

    # import Proper.py; if it is already imported, then this is a no-op
    try:
        import Proper
    except:
        arizonareport.send_syslog(arizonareport.ERROR, "Stork_proper: failed to import Proper.py")
        return False

    # call proper to set the file flags
    try:
        output = Proper.unmount(path)
    except:
        arizonareport.send_syslog(arizonareport.ERROR, "Stork_proper: Exception in Proper call")
        return False

    if is_proper_error(output):
        arizonareport.send_syslog(arizonareport.ERROR, "Stork_proper: Error")
        return False

    arizonareport.send_syslog(arizonareport.INFO, "Stork_proper: Success")

    return True




def set_flags(name, value):
    """
    <Purpose>
       Sets the flags for a file (or mask)
    <Arguments>
       names: filename or mask
       value: usually "1"
    """

    arizonareport.send_syslog(arizonareport.INFO, "Stork_proper: get_flags " + str(name))

    #uncomment this to call via os.popen instead of importing proper
    #directly
    #return call(["setflags", '"' + name + '"', value]):

    # import Proper.py; if it is already imported, then this is a no-op
    try:
        import Proper
    except:
        arizonareport.send_syslog(arizonareport.ERROR, "Stork_proper: failed to import Proper.py")
        return False

    # call proper to set the file flags
    try:
        output = Proper.set_file_flags(name, value)
    except:
        arizonareport.send_syslog(arizonareport.ERROR, "Stork_proper: Exception in Proper call")
        return False

    if (output.find("System error") >= 0) or (output.find("No such file") >= 0):
        arizonareport.send_syslog(arizonareport.ERROR, "Stork_proper: Error")
        return False

    arizonareport.send_syslog(arizonareport.INFO, "Stork_proper: Success")

    return True



def call(cmdline_args):
   """
   <Purpose>
      Calls proper with the given cmdline_args, and returns success or
      failure.  Syslogs the call attempt.  If call failed, adds an
      additional syslog error message.

   <Arguments>
      cmdline_args:
              A list of strings comaining the command line arguments.  
              Must contain at least one string.

   <Exceptions>
      TypeError if a type mismatch or parameter error is detected.
   
   <Side Effects>
      Calls proper: The file system state may change as a result.

   <Returns>
      True on success, False on failure (error in syslog).
   """
   # check params
   arizonageneral.check_type_stringlist(cmdline_args, "cmdline_args", "call")

   # syslog the attempt
   arizonareport.send_syslog(arizonareport.INFO, "Proper call: `" + \
                                str(cmdline_args) + "'.")
   storklog.log_nest("stork_proper", "call", "args", "", cmdline_args)

   # issue the Proper call
   # TODO add timeout code?
   (fi, fo, fe) = os.popen3("/usr/local/stork/bin/Proper.py " + " ".join(cmdline_args))
   error = fe.read().strip()
   if len(error) > 0:
      error += "\n"
   error += fo.read().strip()
   result = (error.find("System error") == -1) and (error.find("No such file") == -1)
   fe.close()
   fo.close()
   fi.close()

   # log errors
   if not result:
      arizonareport.send_syslog(arizonareport.ERROR, "Proper call: `" + \
                                      str(cmdline_args) + "' failed with error: `" + \
                                      str(error) + "'.")
   else:
      # smbaker: log success too...
      arizonareport.send_syslog(arizonareport.INFO, "Proper call: `" + \
                                str(cmdline_args) + "' success.")
   storklog.log_nest("stork_proper", "call", "result", str(result), error)

   return result
