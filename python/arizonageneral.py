#! /usr/bin/env python

"""
<Program Name>
   arizonageneral.py

<Started>
   April 27, 2004

<Author>
   Justin Cappos, with new routines added by members of the Stork team.

<Purpose>
   General python routines.
"""

import atexit
import os
import re
import signal
import smtplib
import sys
import traceback
import time
import socket
import select
import inspect
import types
import random

# Justin: This is needed because syslog does not exist on Windows.   We don't 
# use any function that does a syslog on Windows so this should be okay.
try:
  import syslog
except ImportError:
  pass


def uniq(orig_list):
   """ 
   <Purpose>
      Performs "uniq" on a list (returns the unique items in a list), with
      the new list retaining the order of the original list.  Doesn't use 
      sort.

   <Arguments>
      orig_list:
              List or other iterable type from which to collect unique 
              items.  

   <Exceptions>
      TypeError if a bad parameter is detected.
   
   <Side Effects>
      None.

   <Returns>
      Returns a list of the unique items in the original list.
   """
   # check params
   check_type(orig_list, "orig_list", [None, "iterable"], "uniq")
   
   # None returns an empty list
   uniq_list = []
   if not orig_list:
      return uniq_list
      
   # check each item in the original list   
   for item in orig_list:
   
      # if this item wasn't in our new uniq list, add it
      if item not in uniq_list:
         uniq_list = uniq_list + [item]
         
   return uniq_list
      
      
      
      
      
def intersect(list_a, list_b):
   """ 
   <Purpose>
      Performs "intersect" on two lists (returns the unique items in a list), 
      with the new list retaining the order of list_a.  ###If duplicate items 
      appear in list_a, the result may contain duplicate items.  ### 

   <Arguments>
      list_a:
              List or other iterable type from which to collect unique 
              items.  
      list_b:
              List or other iterable type from which to collect unique 
              items.  

   <Exceptions>
      TypeError if a bad parameter is detected.
   
   <Side Effects>
      None.

   <Returns>
      Returns a list containing the intersection of lists a and b
   """
   # check params
   check_type(list_a, "list_a", [None, "iterable"], "intersect")
   check_type(list_b, "list_b", [None, "iterable"], "intersect")
   
   # None returns an empty list
   intersect_list = []
   if not list_a or not list_b:
      return intersect_list
      
   # check each item in list_a
   for item in list_a:
   
      # if this item is in list_b, add it
      if item in list_b:
         intersect_list = intersect_list + [item]
         
   return intersect_list





def subtract(list_a, list_b):
   """ 
   <Purpose>
      Performs "subtract" on two lists (returns the items in list_a that are
      not in list_b)

   <Arguments>
      list_a:
      list_b:

   <Exceptions>
      TypeError if a bad parameter is detected.
   
   <Side Effects>
      None.

   <Returns>
      Returns a list containing the subtraction of lists a and b
   """
   # check params
   check_type(list_a, "list_a", [None, "iterable"], "subtract")
   check_type(list_b, "list_b", [None, "iterable"], "subtract")
   
   # None returns an empty list
   subtract_list = []
   if not list_a or not list_b:
      return subtract_list
      
   # check each item in list_a
   for item in list_a:
      if not item in list_b:
         subtract_list.append(item)
         
   return subtract_list

      
      

      
def recur_depth(func_name):
   """
   <Purpose>
      Returns the number of levels deep in recursion a function is.

   <Arguments>
      func_name:
              Name of the function to find recursive depth for.

   <Exceptions>
      TypeError if a bad parameter is detected.
   
   <Side Effects>
      None.

   <Returns>
      Returns the number of levels deep in recursion a function is.
   """
   # check params
   check_type_simple(func_name, "func_name", str, "recur_depth")
   
   the_list = traceback.extract_stack()
   count = 0

   for the_item in the_list:
      if the_item[2] == func_name:
         count += 1

   return count





def format_list(string_list, separator, head, headnew, tail, width=80):
   """
   <Purpose>
      Builds a string representation of a list of strings, adding newline
      characters to break up long lines, as appropriate.

   <Arguments>
      string_list: 
              The list of strings to combine into a string.
      separator: 
              A string to separate the items.  Any trailing spaces will be
              automatically removed to fit at the end of a line. 
      head: 
              Text to insert before the list.
      headnew: 
              Text to insert before a wrapped line (usually spaces).
      tail: 
              Text to insert after the list.
      width: (default is 80)
              Number of character columns to use.  Wrapping will occur as
              lines grow longer than this.          

   <Exceptions>
      TypeError if a type mismatch or parameter error is detected.
   
   <Side Effects>
      None.

   <Returns>
      String holding the formatted list contents.
   """
   # check params
   check_type_stringlist(string_list, "string_list", "format_list")
   check_type_simple(separator, "separator", str, "format_list", noneok=True)
   check_type_simple(head, "head", str, "format_list", noneok=True)
   check_type_simple(headnew, "headnew", str, "format_list", noneok=True)
   check_type_simple(tail, "tail", str, "format_list", noneok=True)
   
   # set default values when None is passed in
   if separator == None:
      separator = ""
   if head == None:
      head = ""
   if headnew == None:
      headnew = ""   
   if tail == None:
      tail = ""
   
   items = len(string_list) - 1
   maxspace = len(separator)
   separator = separator.rstrip()
   minsep = len(separator)
   maxspace -= minsep
   last = 0   

   # add each item in the list
   string = ""
   line = head  # current line of text we're building
   index = 0
   for item in string_list:
      
      # is the line too long (does it need to be wrapped)?
      if index >= items:
         minsep = 0
         
      if len(line) + len(item) + minsep > width:
         if string != "":
           string += "\n"
         string += line
         last = len(line)
         line = ""
      
      # If new output line.. add any new line header the user gave.   
      # In either case, add a list item to the line.
      if line == "":
         line = headnew + item
      else:
         line += item
         
      # as long as we're not at the end of the list add user's separator
      if index < items:
         line = line + separator
         spaces = width - len(line)
         if maxspace < spaces:
            spaces = maxspace
         line += " " * spaces
      
      # keep track of what index we're at in the list   
      index += 1         
      
   # deal with the last line 
   if line != "":
      if string != "":
         string += "\n"
      string += line
      last = len(line)
   
   # add user's tail text
   if last + len(tail) > width and string != "":
      string += "\n"
   string += tail
   
   return string





glo_child_failed = False

def __child_failed_handler(signum, frame):
   """ Handles SIGUSR1 for system_timeout """
   global glo_child_failed
   glo_child_failed = True
   return signum, frame






def system_timeout(command, tries, wait, kill_signal=15):
   """ 
   <Purpose>
      Runs a command and terminates the command after a predefined time.
      If the command fails to complete within "wait" seconds, it kills it
      and tries again.   

   <Arguments>
      command:
              Command to run.
      tries:
              Number of times to attempt to run the command.
      wait:
              Number of seconds to wait before killing the command. 
      kill_signal:
              Signal number to send to the process to kill it (Default SIGTERM)

   <Exceptions>
      TypeError if a bad parameter is detected.
      
      ValueError if either "tries" or "wait" are negative integers
   
   <Side Effects>
      None.

   <Returns>
      Returns (bool, status)  where bool is True on normal exit, False on 
      error or interruption by a signal.
      
      Status is the exit status of the command, 1 on error or timeout 
      
      If the command returns fail_id then this function will be confused 
      into thinking that it failed to execute.      
   """
   # check params
   check_type_simple(command, "command", str, "system_timeout")
   check_type_simple(tries, "tries", int, "system_timeout")
   check_type_simple(wait, "wait", int, "system_timeout")
   check_type_simple(kill_signal, "kill_signal", int, "system_timeout")

   # make sure that variables "tries" and "wait" are non-negative
   if tries < 0:
       raise ValueError, 'The second argument must be a non-negative integer'
   if wait < 0:
       raise ValueError, 'The third argument must be a non-negative integer'
   
   # set up signal handler for child failure
   global glo_child_failed 
   glo_child_failed = False
   signal.signal(signal.SIGUSR1, __child_failed_handler)   

   time_start = time.time()

   # give more than one try 
   our_tries = tries
   while our_tries > 0:  
      
      time_this = time.time()
      # fork the parent process into a duplicate child process
      try:
         child_pid = os.fork()
      except OSError:
         # Had a problem with fork so bomb out
         syslog.syslog("Error : system_timeout() fork, "+str(sys.exc_info()[0])+" "+str(sys.exc_info()[1])+" "+str(traceback.format_tb(sys.exc_info()[2])))
         raise
         
      # are we the child or the parent?
      if child_pid == 0:
         # child process: execute the command and exit (if I use execv, I have 
         # to reparse the string as bash, etc. would)

         # Justin:  we need to extract the exit status from the command if we
         # let the command status pass through, we will lose the upper 2 bytes
         # and will have the wrong status.
         os._exit(os.WEXITSTATUS(os.system(command)))

      else:
         # parent
         while time.time() - time_this < wait:
            ( ret_pid, status ) = os.waitpid(child_pid, os.WNOHANG)
            if ret_pid == child_pid:
               
               if glo_child_failed:
                  return (False, 0)

               # if exited cleanly...
               if os.WIFEXITED(status):
                  return (True, os.WEXITSTATUS(status))
               elif os.WIFSIGNALED:
                  return (True, os.WTERMSIG(status))
            time.sleep(0)
         else:
            ########## TODO replace with Justin's routine arizonacrypt.sl_to_fn
            # log netstat -altneep output for debugging
            ( junk_in, the_out, the_err ) = os.popen3("netstat -altneep")
            junk_in.close()
            output = the_out.readline()
            while output:
               syslog.syslog("[netstat -altneep] " + output)
               output = the_out.readline()

            # kill the child
            os.kill(child_pid, kill_signal)  
            syslog.syslog("Error : system_timeout() Forced to kill command [" + str(tries) + " tries left] : " + command)

            # wait until the child actually terminates  
            os.waitpid(child_pid, 0)
            our_tries -= 1

   # out of tries.. log failure
   time_elapsed = round(time.time() - time_start, 3) # round to 3 decimal places
   syslog.syslog("Error : system_timeout() Forced to abort command [waited " + str(time_elapsed) + " seconds] :" + command)
   
   return (False, 0)




def system_timeout_backoff(command, tries, wait, kill_signal=15):
   """ 
   <Purpose>
      Runs a command and terminates the command after a predefined time.
      If the command fails to complete within "wait" seconds, it kills it
      and tries again.
      
      [NOTE]
      In this version of the function wait is multiplied by 2 after
      each attempt

   <Arguments>
      command:
              Command to run.
      tries:
              Number of times to attempt to run the command.
      wait:
              Number of seconds to wait before killing the command. 
      kill_signal:
              Signal number to send to the process to kill it.       

   <Exceptions>
      TypeError if a bad parameter is detected.
      
      ValueError if either "tries" or "wait" are negative integers
   
   <Side Effects>
      None.

   <Returns>
      Returns (bool, status)  where bool is True on normal exit, False on 
      error or interruption by a signal.
      
      Status is the exit status of the command, 1 on error or timeout 
      
      If the command returns fail_id then this function will be confused 
      into thinking that it failed to execute.      
   """
   # check params
   check_type_simple(command, "command", str, "system_timeout_backoff")
   check_type_simple(tries, "tries", int, "system_timeout_backoff")
   check_type_simple(wait, "wait", int, "system_timeout_backoff")
   check_type_simple(kill_signal, "kill_signal", int, "system_timeout_backoff")

   # make sure that variables "tries" and "wait" are non-negative
   if tries < 0:
       raise ValueError, 'The second argument must be a non-negative integer'
   if wait < 0:
       raise ValueError, 'The third argument must be a non-negative integer'
   
   # set up signal handler for child failure
   global glo_child_failed 
   glo_child_failed = False
   signal.signal(signal.SIGUSR1, __child_failed_handler)   

   time_start = time.time()

   # give more than one try 
   our_tries = tries
   while our_tries > 0:  
      
      # if this is not the first pass
      # multiply the current waiting time
      # by two. this will cause the exponential
      # backoff
      if not our_tries == tries:
          wait *= 2
      print "trying for the "+str(tries-our_tries+1)+" time, waiting: "+str(wait)
      
      # call the system_timeout command with the
      # specified command and wait time   
      success, status = system_timeout(command, 1, wait)
      
      # if we succeeded then get out of this loop...
      # else continue on
      if success:
          return (success, status)
      
      our_tries -= 1

   # out of tries.. log failure
   time_elapsed = round(time.time() - time_start, 3) # round to 3 decimal places
   syslog.syslog("Error : system_timeout_backoff() Forced to abort command [waited " + str(time_elapsed) + " seconds] :" + command)
   
   return (False, 0)


   

def system2(command):
   """ 
   <Purpose>
      Runs a command and terminates the command after a predefined time.
      Tries multiple times on failure.

   <Arguments>
      command:
              Command to run.

   <Exceptions>
      TypeError if a bad parameter is detected.
   
   <Side Effects>
      Terminates the program if the command fails.

   <Returns>
      Status of the run.  See system_timeout for details.
   """
   # check params
   check_type_simple(command, "command", str, "system2")

   # give 3 tries, wait 5 seconds each, if it times out: kill -9
   (success, status) = system_timeout(command, 3, 5, 9) 
   if not success:
      # Command failed
      os._exit(1)

   return status





def fsystem2(comm, command):
   """ 
   <Purpose>
      Runs a command and terminates the command after a predefined time.
      Tries multiple times on failure.  Prints error messages to given
      file stream.

   <Arguments>
      comm:
              File stream to send error messages to.
      command:
              Command to run.

   <Exceptions>
      TypeError if a bad parameter is detected.
   
   <Side Effects>
      Terminates the program if the command fails.

   <Returns>
      Status of the run.  See system_timeout for details.
   """
   # check params
   check_type_simple(comm, "comm", file, "fsystem2")
   check_type_simple(command, "command", str, "fsystem2")

   # give 3 tries, wait 10 seconds each, if it times out: kill -9
   (success, status) = system_timeout(command, 3, 10, 9) 
   if not success:
      # Command failed
      try:
         comm.sendall("Error: Command '" + command + "' timed out...")
         comm.close()
         syslog.syslog("Error: Command '" + command + "' timed out...")
      except socket.error:
         syslog.syslog("Error: arizonageneral.fsystem2(), Command '" + command + "' timed out (error reporting also failed)...")
         syslog.syslog("Error : arizonageneral.fsystem2() comm call failed")
      os._exit(1)

   return status





def popen0(command):
   """
   <Purpose>
      Runs a command, returning exit code.  The program must exit for this
      function to return.
   
   <Arguments>
      command: 
              A string giving the command to run.
      
   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      Program return status (exit code), or None.
   """
   # check params
   check_type_simple(command, "command", str, "popen0")

   # run command
   return os.system(command + " &>/dev/null")





def popen5(command, tempdir="/tmp"):
   """
   <Purpose>
      Runs a command, returning exit code, stdout, and stderr.  The 
      program must exit for this function to return.
   
   <Arguments>
      command: 
              A string giving the command to run.
      
   <Exceptions>
      IOError if an I/O error occurs (could not write to /tmp).
   
   <Side Effects>
      None.

   <Returns>
      A tuple (out, err, status), containing stdout output, stderr output,
      and the return status, respectively.
   """
   # check params
   check_type_simple(command, "command", str, "popen5")

   # create the tempdir if it doesn't exist
   try:
      os.makedirs(tempdir)
   except OSError:
      pass

   fileout = os.path.join(tempdir, str(random.random()) + "popen5_stdout")
   fileerr = os.path.join(tempdir, str(random.random()) + "popen5_stderr")
   
   # run command
   status = os.system(command + " >" + fileout + " 2>" + fileerr)
   
   # get stdout
   try:
      f = file(fileout)
      out = f.readlines()
      f.close()
      os.remove(fileout)
   except OSError:
      out = []
   
   # get stderr
   try:
      f = file(fileerr)
      err = f.readlines()
      f.close()
      os.remove(fileerr)
   except OSError:
      err = []
      
   # fix status
   if status == None:
      # couldn't get a status code.. have to assume it's okay
      status = 0
   else:
      # for some reason, status is multiplied by 256. we reverse that here
      status = status >> 8         
   
   return (out, err, status)

   



def popen6(command, tempdir="/tmp"):
   """
   <Purpose>
      Runs a command, returning exit code, and stdout/stderr combined.  
      The program must exit for this function to return.
   
   <Arguments>
      command: 
              A string giving the command to run.
      
   <Exceptions>
      IOError if an I/O error occurs (could not write to /tmp).
   
   <Side Effects>
      None.

   <Returns>
      A tuple (out, status), containing stdout/stderr output, and the 
      return status, respectively.
   """
   # check params
   check_type_simple(command, "command", str, "popen6")

   # create the tempdir if it doesn't exist
   try:
      os.makedirs(tempdir)
   except OSError:
      pass

   fileout = os.path.join(tempdir, str(random.random()) + "popen6_stdout")
   
   # run command
   status = os.system(command + " &>" + fileout)
   
   # get stdout/stderr
   try:
      f = file(fileout)
      out = f.readlines()
      f.close()
      os.remove(fileout)
   except OSError:
      out = []
   
   # fix status
   if status == None:
      # couldn't get a status code.. have to assume it's okay
      status = 0
   else:
      # for some reason, status is multiplied by 256. we reverse that here
      status = status >> 8         

   return (out, status)





def split_quoted(text):
   """
   <Purpose>
      Similar to split(), however double-quoted (") text is not split.  
   
   <Arguments>
      text: 
              The string to split.
      
   <Exceptions>
      TypeError if a type mismatch or parameter error is detected.
   
   <Side Effects>
      None.

   <Returns>
      A list containing text split by spaces (unless in double-quotes).

   <Examples>
      split_quoted('a b c') -> ['a', 'b', 'c']
      split_quoted('a "b c"') -> ['a', 'b c']
   """
   # check params
   check_type_simple(text, "text", str, "split_quoted")

   split_list = []
   quote_start = False
   for piece in text.split('"'):
      
      # are we starting a quoted string?
      if quote_start: 
      
         # yes, leave it alone
         split_list.append(piece)
      else:
 
         # no, break up all the spaces
         split_list.extend(piece.split())
         
      # since we split by ", the next thing we will see is a quoted 
      # string, or the end of a quoted string   
      quote_start = not quote_start 
   
   return split_list


   
   
   
def check_type(variable, parameter_name, expected_type, function_name):
   """
   <Purpose>
      Checks the actual type of variable against the expected type, and
      raises a TypeError if variable is of a type other than expected.

   <Author>
      Jeffry Johnston

   <Arguments>    
      variable:
              Variable to check the type of.  Can be anything.
      parameter_name:
              Name of the function parameter being tested, as a string.  
              Used for error reporting.
      expected_type:
              The expected variable type.  
              
                Example (allow only integers): int  
              
              Can be a list, if the variable can be of multiple different 
              types.  Only one type in the list must match for the entire 
              list to match.  
              
                Example (allow integers or strings): [int, str]
              
              A list can include other lists.  These sub-lists are 
              slightly different in use than the previously mentioned 
              list.  The first item in a sub-list must specify an iterable
              type.  The variable will then be checked for an iterable 
              of that type.  Multiple nesting of sub-lists is 
              allowed.  
              
                Example (require a list of strings): [[list, str]].  
                Note: Simply doing [list, str] will not result in the 
                desired check, because it will accept any list or any 
                string, as in the previous section. 

                Example (require a tuple containing lists of integers):
                [[tuple, [list, int]]]

              Use the special string "iterable" to match any iterable 
              type.                
              
                Example (allow any iterable as long as it contains only
                strings): [["iterable", str]]
                
                Example: [None, "iterable"], allow None or any iterable 
                type to pass.  
              
              Use the special string "any" to allow any type, but not to 
              to allow the absence of a type (this is useful to enforce 
              that at least one item be in an iterable type such as a 
              list).  
              
                Example: [list, "any"].  This would match [3], but not [].
                Compare this to simply using: list, which would also match
                [].
                
              Use the special string "empty" to allow an empty iterable 
              type. 
 
                Example: [[list, str, "empty"]].  Allows [], and ["abc"], 
                but not [[]], or [1].   
              
              The special type string "parent" auto-includes all of the 
              types and sub-lists of the list parent.  The parent of the 
              main list is None.  
              
                Example: [int, [list, "parent"]].  This will accept
                any combination of integers and lists with integers in 
                them, for example: 1, [3], [[-5]], [10,[[7],[[[9]]],8]].  
              
              Special strings are case sensitive and must be given in 
              lowercase.
              
              Other examples: file, int, list, [[list, "any"]], None, 
              str, tuple, [type, None], [[list, str]], 
              [["iterable", str]], [float, [tuple, "parent"]].     
      function_name:
              Name of the called function, as a string.  Used for error 
              reporting.
   
   <Exceptions>
      TypeError if a type mismatch or parameter error is detected.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   # first, check parameters passed to this function
   __check_type_internal(expected_type, "expected_type", [type, str, None, ["iterable", "parent"]], "check_type")
   check_type_simple(parameter_name, "parameter_name", str, "check_type")
   check_type_simple(function_name, "function_name", str, "check_type")

   # now perform requested check
   __check_type_internal(variable, parameter_name, expected_type, function_name)





def __check_type_internal(variable, parameter_name, expected_type, function_name, parent=[None], depth=0):
   """
   <Purpose>
      Checks the actual type of variable against the expected type, and
      raises a TypeError if variable is of a type other than expected. 
      Internal helper function to check_type that does the necessary 
      recursive work (so this should never be called directly, use 
      the function check_type instead).

   <Author>
      Jeffry Johnston

   <Arguments>    
      See check_type for full details.
      parent:
              Internal.  Must be None (default) for function to complete.
              Used to know when the recursion is complete. 
      depth:
              Internal.  Used to indent debugging output.
   
   <Exceptions>
      TypeError if a type mismatch or parameter error is detected.
   
   <Side Effects>
      None.

   <Returns>
      True: found a match, False: didn't match
   """      
   # make expected_type a list if it wasn't already
   type_list = expected_type
   if not isinstance(type_list, list):
      type_list = [ type_list ]
      
   # iterate over entries in type_list.  If "parent" is found, replace 
   # it with the parent entry.  
   temp = []
   for item in type_list:
      if item == "parent":
         temp += parent
      else:
         temp.append(item)   
   type_list = temp

   # If they specify [] for the expected type, we need to catch that (fails),
   # so the default behavior is to fail. 
   answer = False
   

   # see if any of the patterns given in expected_type match the type of the variable
   for expected_type in type_list:

      # The type None doesn't actually exist, it is actually called NoneType.
      # We specially allow None here (to be user-friendly). 
      if expected_type == None:
         answer = variable == None
         
      # Special string "parent".  Ignore this, it was already processed above.  
      elif expected_type == "parent":
         answer = False
         
      # Special string "any".  Always matches (passes). 
      elif expected_type == "any":
         answer = True
         
      # Special string "empty".  Ignore this, it was already processed by parent.
      elif expected_type == "empty":
         answer = False
         
      # Special string "iterable".  
      elif expected_type == "iterable":
         # is the type iterable?
         answer = True
         try:
            iter(variable)
         except TypeError:
            answer = False

      # Found a list.  It should be of the form [iterable type, ...]   
      elif isinstance(expected_type, list):
         
         # Are there enough items in the list?  Need at least 2 to match the form.
         if len(expected_type) < 2:
            raise \
                  TypeError, "A sub-list requires an iterable type and " + \
                  "at least one expected type.  Function: '" + \
                  function_name + "', specified '" + str(expected_type) + \
                  "' for expected_type."

         # Is the first element of the expected type? 
         if expected_type[0] != "iterable":
           try: 
              is_inst = isinstance(variable, expected_type[0])
           except TypeError:
              raise \
                    TypeError, "Received a '" + \
                    str(type(expected_type[0])).split("'")[1] + "' (with value: " + \
                    str(expected_type[0]) + ") for the iterable type of the list '" + \
                    str(expected_type) + "'.  The iterable type must consist only of " + \
                    "iterable types or the special string \"iterable\" (case sensitive)."
         
         # special string "iterable", allows any iterable type
         # otherwise, variable needs to be of the type listed      
         if expected_type[0] == "iterable" or is_inst:
            
            # is the type iterable?
            try:
               iter(variable)
            except TypeError:
               answer = False
            else:
               # iterate over the variable, and recursively check each piece (item) of it
               if len(variable) == 0:
                  for item in expected_type[1:]:
                     if item == "empty":
                        answer = True
               else:
                  for item in variable:
                     answer = __check_type_internal(item, parameter_name, expected_type[1:], function_name, type_list, depth + 2)
                     # if we didn't have a match on this piece of the variable, 
                     # there is no reason to check the other pieces
                     if not answer:
                        break
         else:
            # fail, variable we were trying to match wasn't an interable type,
            # or wasn't the interable type that was expected
            answer = False         
      else:
         # This where non-iterable types such as int, str, float, are checked.
         # Note that this also checks list, tuple, etc, when specified as such,
         # (For example, if they didn't care what the list held, they could say
         # '[list, "any"]', or just simply 'list' if the list could be empty).  
         try: 
            answer = isinstance(variable, expected_type)
         except TypeError:
            raise \
                  TypeError, "Received a '" + \
                  str(type(expected_type)).split("'")[1] + "' (with value: " + \
                  str(expected_type) + ") for the parameter 'expected_type'.  " + \
                  "The parameter expected_type must consist only of " + \
                  "types, lists of types, or the special strings " + \
                  "\"iterable\", \"parent\", or \"any\" (case sensitive)."
         
      # If we found a match, then we're done with all of this.. break out   
      if answer:
         break

   # If this is the top level, then a failure generates a TypeError so 
   # that the user may see it.  Otherwise, we're not done yet, so the 
   # True / False result is returned to the parent caller to deal with.  
   if parent == [None]:
      if not answer:
         raise \
               TypeError, "Incorrect type passed to parameter '" + \
               parameter_name + "' of function '" + \
               function_name + "'.  Received the type: '" + \
               str(type(variable)).split("'")[1] + "' (with value: " + \
               str(variable) + \
               "), but expected to receive a type matching the pattern: '" + \
               str(type_list) + "'."
      else:
         return True
   else:
      return answer





def check_types(list, function, modulename=None):
   """
   <Purpose>
      Pass this method a list of data,type pairs of args your function 
      takes along with your function as the second parameter, and this 
      method will attempt to determine the full name of the function, and 
      the names of the variables and pass the information to the 
      check_type method. (note: this will skip over the self parameter for
      class methods)  Using this method could also have the added benefit 
      of making a method slightly more portable.  The method could be
      moved or copied with very little change, if any.
   <Author>
      Jason Hardies
   <Arguments>
      list:
         a list of variable,type pairs (see check_type)
      function:
         the function to use
      modulename: (optional)
         The name to insert as the module name (specifically for use in 
         the case where the method is in a main module)
   <Exceptions,etc.>
      See check_type.
   <Example>
      class Test:
         def myfunc(self, a_str, b_str, c_int):
            check_types([[a_str,str],[b_str,str],[c_int,int]],self.myfunc)
            #should be the same as:
            check_type(a_str,'a_str',str,'a_module.Test.myfunc')
            check_type(b_str,'b_str',str,'a_module.Test.myfunc')
            check_type(c_int,'c_int',int,'a_module.Test.myfunc')
   <Note>
      It is recommended that you use the class name instead of self for 
      class methods (unlike the example above), in case of inheritance 
      (eg: calling the init method of the parent class).
   """
   arglist = inspect.getargspec(function)[0]
   
   # try to divine the full method/function name:
   # note: this should get all the lib.lib.lib.s that might be in the 
   #       module name, but will use the actual module's name
   # also, for the main script, this will be __main__
   function_name = function.__module__ + "."
   if modulename:
      function_name = modulename + "."
   if type(function) == types.MethodType:
      # all class methods are of type method, methods/functions not inside
      # of a class are the function type.
      # since it has a class, we're assuming the first argument (whatever 
      # it may be named), is the self argument)
      arglist = arglist[1:]
      function_name += function.im_class.__name__ + '.'
   function_name += function.__name__
   for i in range(len(arglist)):
      check_type(list[i][0], arglist[i], list[i][1], function_name)   
   
   
   
   
   
def check_type_simple(variable, parameter_name, expected_type, function_name, noneok=False):
   """
   <Purpose>
      Checks the actual type of variable against the expected type, and
      raises a TypeError if variable is of a type other than expected.
      This function accepts only a limited amount of functionality in
      order to increase its speed.  Does not check its own input, so must
      be called correctly.

   <Author>
      Jeffry Johnston

   <Arguments>    
      variable:
              Variable to check the type of.  Can be anything.
      parameter_name:
              Name of the function parameter being tested, as a string.  
              Used for error reporting.
      expected_type:
              The expected variable type (int, str, dict, ...)  
      function_name:
              Name of the called function, as a string.  Used for error 
              reporting.
   
   <Exceptions>
      TypeError if a type mismatch or parameter error is detected.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   if not isinstance(variable, expected_type) and (not noneok or variable != None):
      raise TypeError, "Incorrect type passed to parameter '" + \
            parameter_name + "' of function '" + \
            function_name + "'.  Received the type: '" + \
            str(type(variable)).split("'")[1] + "' (with value: " + \
            str(variable) + \
            "), but expected to receive a type matching the pattern: '" + \
            str(expected_type) + "'."





def check_type_stringlist(variable, parameter_name, function_name):
   """
   <Purpose>
      Checks the actual type of variable to see if it is a list containing
      either nothing, or containing strings (or unicodes) only.  Raises a 
      TypeError if variable is of a type other than expected.  Does not 
      check its own input, so must be called correctly.

   <Author>
      Jeffry Johnston

   <Arguments>    
      variable:
              Variable to check the type of.  Can be anything.
      parameter_name:
              Name of the function parameter being tested, as a string.  
              Used for error reporting.
      function_name:
              Name of the called function, as a string.  Used for error 
              reporting.
   
   <Exceptions>
      TypeError if a type mismatch or parameter error is detected.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   # is it a list?
   if not isinstance(variable, list):
      raise TypeError, "Incorrect type passed to parameter '" + \
            parameter_name + "' of function '" + \
            function_name + "'.  Received the type: '" + \
            str(type(variable)).split("'")[1] + "' (with value: " + \
            str(variable) + \
            "), but expected to receive a string list."
      
   # empty list?   
   if not variable:
      return 

   # iterate over values, check for strings
   for item in variable:
      if not isinstance(item, str) and not isinstance(item, unicode):
         raise TypeError, "Incorrect type passed to parameter '" + \
               parameter_name + "' of function '" + \
               function_name + "'.  Received the type: '" + \
               str(type(variable)).split("'")[1] + "' (with value: " + \
               str(variable) + \
               "), but expected to receive a string list."




def check_running(program):
   """
   <Purpose>
      Checks to see if a deamon is already running

   <Arguments>
      program:
              Filename (not including path) of the program being turned
              into a daemon.  Used to
              read the pid of the daemon from `/var/run/PROGRAM.pid'.

   <Exceptions>
      TypeError if a bad parameter is detected.

   <Returns>
      pid of the daemon or -1 if no daemon is running
   """
   filename = "/var/run/" + program + ".pid"
   try:
      in_file = open(filename, "w")
      pid = int(in_file.read())
      in_file.close()
   except IOError:
      syslog.syslog("[" + program + "] IOError reading: " + filename)
      return -1

   result = os.system("ps -p " + str(pid) + " > /dev/null")

   # XXX: how do we know the pid is the daemon we are interested in, and
   #   not that our demon terminated and some other program is running?

   if result == 0:
      # the process exists
      return pid
   else:
      # the process does not exist
      return -1





def make_daemon(program):
   """
   <Purpose>
      Turns the currently running program into a daemon, detaching it from
      the console so that it runs in the background.

   <Arguments>
      program:
              Filename (not including path) of the program being turned
              into a daemon.  Used for logging, error reporting, and to 
              write the pid of the daemon to `/var/run/PROGRAM.pid'.

   <Exceptions>
      TypeError if a bad parameter is detected.
   
   <Side Effects>
      Terminates the program if the command fails.

   <Returns>
      pid of the daemon
   """
   # check params
   check_type_simple(program, "program", str, "make_daemon")
   
   # log what we're about to do and fork
   syslog.syslog("[" + program + "] Starting daemon...")
   pid = os.fork()

   # if fork was successful, exit the parent process so it returns 
   try:
      if pid > 0:
         os._exit(0) 
   except OSError:
      syslog.syslog("[" + program + "] Error: fork failed, daemon not started")
      sys.exit(1)

   # Print my pid into /var/run/PROGRAM.pid
   pid = str(os.getpid())
   filename = "/var/run/" + program + ".pid"
   try:
      out_file = open(filename, "w")
      out_file.write(pid)
      out_file.close()
   except IOError:
      syslog.syslog("[" + program + "] IOError writing: " + filename)

   # close any open files
   try:
      sys.stdin.close()
   except:
      syslog.syslog("[" + program + "] Error closing stdin")
   try:
      sys.stdout.close()
   except:
      syslog.syslog("[" + program + "] Error closing stdout")
   try:
      sys.stderr.close()
   except:
      syslog.syslog("[" + program + "] Error closing stderr")
   for i in range(1023):
      try:
         os.close(i)
      except OSError:
         pass
         
   # redirect stdin/out/err to /dev/null    
   try:
      sys.stdin = open('/dev/null')       # fd 0
   except:
      syslog.syslog("[" + program + "] Error opening new stdin")
   try:
      sys.stdout = open('/dev/null', 'w') # fd 1
   except:
      syslog.syslog("[" + program + "] Error opening new stdout")
   try:
      sys.stderr = open('/dev/null', 'w') # fd 2  
   except:
      syslog.syslog("[" + program + "] Error opening new stderr")

   # disassociate from parent
   os.chdir("/")
   os.setsid()
   os.umask(0)

   return pid





def mutex_lock(program, lockdir="/var/lock", unlock_on_exit=True):
   """
   <Purpose>
      Checks to see if we can obtain a mutex lock (i.e. is there only one
      copy of the specified program running?), if not, returns False;
      otherwise, sets a mutex lock and returns True.

   <Arguments>
      program:
              Name of the program.
      lockdir: (default: "/var/lock")
              Directory to store the lock file in.
      unlock_on_exit: (default: True)
              Whether the mutex lock should automatically be unlocked on
              program exit.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      None if lock cannot be obtained
      an open file descriptor for the lock if lock can be obtained 
   """
   # Justin: we do this here so that this is imported only in applications that
   # need it
   import fcntl

   # check params
   check_type_simple(program, "program", str, "mutex_lock")
   check_type_simple(lockdir, "lockdir", str, "mutex_lock")
   check_type_simple(unlock_on_exit, "unlock_on_exit", bool, "mutex_lock")

   # create the lockdir if it doesn't exist
   try:
      os.makedirs(lockdir)
   except OSError:
      pass

   # open the lock file for writing
   # we should always be able to open the file, even if it is locked.
   lock = file(lockdir + "/" + program + ".lock", "w")

   try:
      # attempt to obtain the file lock
      fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
   except IOError:
      # lock not obtained, abort
      lock.close()
      return None

   #print "locked " + program

   # obtained the lock
   if unlock_on_exit:
      atexit.register(mutex_unlock, lock)
   return lock



def mutex_unlock(lock):
   """
   <Purpose>
      Releases the mutex lock (if any).

   <Arguments>
      None

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      True or False.
   """
   # Justin: we do this here so that this is imported only in applications that
   # need it
   import fcntl

   if lock != None:
      # if the lock file is closed, then we already released it.
      # if it is still open, then we are still holding the lock and need to
      # release and delete it.
      if not lock.closed:
         filename = lock.name
         fcntl.flock(lock, fcntl.LOCK_UN)
         lock.close()
         if os.path.isfile(filename):
            os.remove(filename)
         #print "unlocked " + str(lock)





class Exception_Data(Exception):
   """
   <Purpose>
      Exception with an extra data field.

   <Parent>
      Exception
   """
   message = None
   data = None

   def __init__(self, message, data):
      """
      <Purpose>
         Exception with string list.

      <Arguments>
         message:
                 Error message.
         data:
                 Error data (tuple, list, etc).

      <Exceptions>
         None.

      <Side Effects>
         None.

      <Returns>
         None.
      """
      Exception.__init__(self)
      self.message = message
      self.data = data





def list_to_args(raw_list):
   """
   <Purpose>
      Converts a list of command line parameters into a space separated 
      list, with special characters escaped for command-line use.  Will
      have a leading space unless len(raw_list) == 0.

   <Arguments>
      raw_list:
              List of strings each contaning a command line argument.

   <Exceptions>
      TypeError:
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      String containing space separated args.
   """
   # check params
   check_type_stringlist(raw_list, "raw_list", "list_to_args")
   
   args = ""
   for item in raw_list:
      args += " " + re.escape(item)
   return args





def gethostname():
   """ Returns hostname, or None on error """
   hostname = None   
   try:
      import socket
   except ImportError:
      pass
   try:
      hostname = socket.gethostname()
   except NameError:
      pass
   
   if hostname == None:   
      try:
         import os
      except ImportError:
         pass
      try:
         nodehost = os.getenv("HOSTNAME", None)
      except NameError:
         hostname = None
         
   return hostname      



def getslicename():
   try:
      if os.path.isfile("/etc/slicename"):
         slicefile = open("/etc/slicename")
         slicename = slicefile.read().strip()
         slicefile.close()
      else:
         return None
   except (NameError, IOError):
      return None

   return slicename



   
def getusername():
   """ TODO comments """
   # refactored 05Feb2007 by Jeffry Johnston to fix very ugly changes that  
   # have been made since my original code was written
   try:
      import os
   except ImportError:
      pass
   try:
      username = os.getlogin()
   except (NameError, OSError):
      username = None   
      
   if username == None or username == "root":
      try:
         username = os.environ.get("USER")
      except (NameError, OSError):
         username = None   
   else:
      return username
            
   if username == None or username == "root":
      try:
         username = os.environ.get("SUDO_USER")
      except (NameError, OSError):
         username = None 
   else:
      return username

   if username == None or username == "root":
      try:
         username = os.environ.get("USERNAME")
      except (NameError, OSError):
         username = None 
   else:
      return username

   if username == None or username == "root":
      try:
         username = os.environ.get("LOGNAME")
      except (NameError,OSError):
         username = None 
   else:
      return username

   if username == None or username == "root":
      try:
         tmp_in, tmp_out, tmp_err = os.popen3("/usr/bin/id -un")
         tmp_in.close()
         tmp_str = "".join(tmp_err.readlines()).strip()
         tmp_err.close()
         if tmp_str != "":
            username = None
         else:
            username = "".join(tmp_out.readlines()).strip()
         tmp_out.close()
      except (IOError, OSError, NameError):
         username = None 
   else:
      return username

   # JRP - 112706
   # last fail over method
   # if username is still root or None at this point, try to read the 
   # /etc/slicename file
   if username == None or username == "root":
      try:
         if os.path.isfile("/etc/slicename"):
            slicefile = open("/etc/slicename")
            username = slicefile.read().strip()    
            slicefile.close()
         elif username == None:
            username = "UNKNOWN USERNAME" 
      except (NameError, IOError):
         if username == None or username == "":  
            username = "UNKNOWN USERNAME" 

   return username





def uniq_string(s):
   """
   <Purpose>
      Remove duplicate lines from a string. Lines in the string are seperated by
      newline characters. Duplicate lines are marked with "previous line
      repeated n times".

   <Arguments>
      s:
         string to remove duplicates
   <Returns>
      string with duplicates removed
   """
   orig_list = s.split("\n")
   new_list = []

   last = None
   last_count = 0

   for line in orig_list:
       if line == last:
          last_count = last_count + 1
       else:
          if last_count == 1:
             # if we only have a single duplicate line, then just output the
             # duplicate line. This avoids printing the 'repeat' message
             # for minor things like when multiple newlines occur.
             new_list.append(line)
          elif last_count >= 2:
             new_list.append("previous line repeated " + str(last_count) + " times")
          last_count = 0
          new_list.append(line)
          last = line

   # catch the case where the last line of the string was a duplicate
   if last_count > 0:
      new_list.append("previous line repeated " + str(last_count+1) + " times")

   return "\n".join(new_list)





def error_report(exc_info, program=None, version=None, output="", email=None, files=[], listdirs=[], savedir="/tmp", title="STORK ERROR REPORT"):
   """
   <Purpose>
      Collects system information for an error report, saves it to disk,
      and optionally e-mails it to the desired recipient.

   <Arguments>
      exc_info:
              Exception information.  May be obtained by calling
              sys.exc_info().
      program:
              (Default: None)
              Name of the program being run.  If None, tries to figure it
              out automatically.
      version:
              (Default: None)
              Version of program being run.
      output:
              (Default: "")
              Program output as a string.  Although there is a default
              option, not providing output really hinders debugging.
      email:
              (Default: None)
              List of email address to send report to, or None to not 
              mail a report.
      files:  
              (Default: [])
              List of filenames (including absolute paths for each) whose 
              contents should be included in the error report.         
      listdirs:
              (Default: [])
              List of directories whose files and subdirectories should be
              recursively listed.
      savedir:
              (Default: "/tmp")
              Directory in which to save the error report, or None to not
              save the report to disk.    
      title:
              (Default: "STORK ERROR REPORT")
              Title of the error report.

   <Author>
      Jeffry Johnston

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      A 3-tuple: mailed, saved, report.
      Where mailed is True if an error report was mailed, False otherwise.
            saved is the name of the saved error report, otherwise None.
            report is the text of the generated error report.
   """
   # Note: I intentionally do not check types up front.  This routine must
   #       continue no matter what.  It does the best it can in the face
   #       of errors.

   # Note: If you must add code to this function please follow these rules:
   #       1) Wrap the new code in try/except blocks.  No exceptions.
   #          If a variable is assigned in the try: block, it must also be
   #          assigned in the except: block.
   #       2) Add a comment so we know what the new code does.
   #       3) DO NOT assume that the new code will always work.  This
   #          includes when building the report string.  Assume the
   #          opposite, in fact.  Pretend that each line of your new code
   #          fails.  Then handle the failures appropriately.
   #       4) Do not put code above the time code.  We need an accurate
   #          reading of the current time.
   #       5) Check your indentation.  Use exactly 3 spaces for
   #          indentation.  Do not use tabs.
   #       6) Be extra careful.  Check your typing, double check the code.
   #          Test that it loads, run it.  Make sure you didn't break it.
   #          If this code generates an exception then error reporting
   #          fails and the user will get an ugly error.  Or worse...

   # Note: All except: blocks in this function are generic, because we do
   #       not want this code to fail under any circumstances.

   # collect information...

   # date and time, DO THIS FIRST SO WE GET A MORE ACCURATE TIME READING
   try:
      import time
   except: # leave this as general exception handler
      pass
   try:
      now = time.localtime()
   except: # leave this as general exception handler
      now = (1980, 1, 1, 0, 0, 0, 0, 1, 0)
   # !!!!!!! DON'T PUT *ANY* NEW CODE ABOVE THIS LINE !!!!!!!!
   try:
      time_str = time.strftime("%a, %d %b %Y %H:%M:%S %Z", now)
   except: # leave this as general exception handler
      time_str = ""

   # exception name
   try:
      except_name = ": " + str(exc_info[1].__class__.__name__)
   except: # leave this as general exception handler
      except_name = ""

   # stack trace
   try:
      trace = "".join(traceback.format_exception(exc_info[0], exc_info[1], exc_info[2]))
   except: # leave this as general exception handler
      trace = "Unable to process stack trace.\n"

   # load averages
   try:
      import os
   except: # leave this as general exception handler
      pass
   try:
      load_avg = str(os.getloadavg())
   except: # leave this as general exception handler
      load_avg = "Unable to determine load averages."

   # process listing
   try:
      tmp = os.popen("ps -wweF")
      ps = "".join(tmp.readlines())
      tmp.close()
   except: # leave this as general exception handler
      ps = "Unable to retrieve process listing.\n"

   # memory info
   try:
      tmp_in, tmp_out, tmp_err = os.popen3("free -t")
      tmp_in.close()
      tmp_str = "".join(tmp_err.readlines()).strip()
      tmp_err.close()
      if tmp_str != "":
         memory = "Unable to retrieve memory information.\n"
      else:
         memory = "".join(tmp_out.readlines())
      tmp_out.close()
   except: # leave this as general exception handler
      memory = "Unable to retrieve memory information.\n"

   # disk info
   try:
      tmp_in, tmp_out, tmp_err = os.popen3("df -ah")
      tmp_in.close()
      tmp_str = "".join(tmp_err.readlines()).strip()
      tmp_err.close()
      if tmp_str != "":
         disk = "Unable to retrieve disk information.\n"
      else:
         disk = "".join(tmp_out.readlines())
      tmp_out.close()
   except: # leave this as general exception handler
      disk = "Unable to retrieve disk information.\n"

   # runtime environment
   try:
      uname = " ".join(os.uname())
   except: # leave this as general exception handler
      uname = ""
   try:
      cwd = os.getcwd()
   except: # leave this as general exception handler
      cwd = ""
   try:
      path = os.getenv("PATH", "Unable to determine path.")
   except: # leave this as general exception handler
      path = "Unable to determine path."
   try:
      username = getusername()
   except: # leave this as general exception handler
      username = "Unable to determine username."
   try:
      hostname = gethostname()
      if hostname == None:
         hostname = "Unable to determine hostname."
   except: # leave this as general exception handler
      hostname = "Unable to determine hostname."
   try:
      cmdline = " ".join(sys.argv[0:])
   except: # leave this as general exception handler
      cmdline = "Unable to determine command line."

   # file contents
   file_contents = ""
   try:
      iter(files)
   except: # leave this as general exception handler
      files = []
   for filename in files:
      if not isinstance(filename, str):
         continue
      try:
         file_contents += "\n" + filename + "\n" + ("-" * len(filename)) + "\n"
         tmp = file(filename, "r")
         file_contents += "".join(tmp.readlines()) + "\n"
         tmp.close()
      except: # leave this as general exception handler
         file_contents += "Unable to read file.\n\n"

   # directory listings
   directory_list = ""
   try:
      iter(listdirs)
   except: # leave this as general exception handler
      listdirs = []
   for directory in listdirs:
      if not isinstance(directory, str):
         continue
      try:
         tmp_out = os.popen("ls -AlFRq " + directory + " 2>&1")
         directory_list += "".join(tmp_out.readlines()) + "\n"
         tmp_out.close()
      except: # leave this as general exception handler
         directory_list += "Unable to read directory tree: " + directory + "\n\n"

   # output
   if not isinstance(output, str):
      output = "No output information given.\n"
   else:
      # remove duplicate strings in the output
      try:
         output = uniq_string(output)
      except: # leave this as general exception handler
         pass

   if not output.endswith("\n"):
      output += "\n"

   # title
   if not isinstance(title, str):
      title = "STORK ERROR REPORT"

   # program
   if not isinstance(program, str):
      try:
         # try to determine the name of the program
         program = os.path.basename(sys.argv[0])
         if program == "":
            # running from the python shell
            program = "Python Interpreter Interface"
      except: # leave this as general exception handler
         program = "Unknown"

   # version
   if version == None:
      version = "Unknown version"

   try:
       subject = title + ": " + hostname + ": " + except_name
   except: # leave this as general exception handler
       subject = "STORK ERROR REPORT: failed to build subject string"

   # build error report
   try:
      report = subject + "\n\n\n" + \
               "Summary\n=======\n" + program + ", " + version + ", " + hostname + "\n\n\n" + \
               "Stack trace\n===========\n" + trace + "\n" + \
               "Time\n====\n" + time_str + "\n\n" + \
               "Program reporting the error\n===========================\n" + program + "\n\n" + \
               "Command line\n============\n" + cmdline + "\n\n" + \
               "Program output\n==============\n" + output + "\n" + \
               "Current directory\n=================\n" + cwd + "\n\n" + \
               "System\n======\n[" + username + "@" + hostname + "] " + uname + "\n\n" + \
               "Path\n====\n" + path + "\n\n" + \
               "Memory usage\n============\n" + memory + "\n" + \
               "Load averages (1, 5, 15 min)\n============================\n" + load_avg + "\n\n" + \
               "Process listing\n===============\n" + ps + "\n" + \
               "Disk usage\n==========\n" + disk + "\n"
      if len(directory_list) > 0:
         report += "Directory listings\n==================\n" + directory_list
      if len(file_contents) > 0:
         report += "File contents\n=============\n" + file_contents
   except: # leave this as general exception handler
      report = "Could not assemble error report string."

   # write to a file
   saved = None
   if savedir != None:
      if not isinstance(savedir, str):
         savedir = "/tmp"
      try:
         os.makedirs(savedir)
      except: # leave this as general exception handler
         pass
      try:
         filename = os.path.join(savedir, program + ".error." + time.strftime("%d%b%Y_%H.%M.%S_%Z", now))
         outfile = file(filename, "w")
         outfile.write(report)
         outfile.close()
         saved = filename
      except: # leave this as general exception handler
         pass

   # send mail
   mailed = False
   if email != None and username != "UNKNOWN USERNAME":
      try:
         iter(email)
      except: # leave this as general exception handler
         email = []
      try:
         import stmplib
      except: # leave this as general exception handler
         pass
      for recipient in email:
         if not isinstance(recipient, str):
            continue

         # TODO FIXME smtplib and sendmail may report that they sent the
         #    mail successfully, even when they didn't.  This happens, for
         #    example, if mail is set up for local delivery only.  In this
         #    situation the mail programs do not give any indication of
         #    error.  To fix this, we will need to investigate the mail
         #    system ourselves, or have some sort of response sent back to
         #    the client.

         # try smtplib first
         try:
            server = smtplib.SMTP("localhost")
            server.sendmail(username + "@" + hostname, recipient, "Subject: " +
               subject + "\n\n" + report)
            server.quit()
            mailed = True
         except: # leave this as general exception handler
            pass

         # if smtplib failed, try sendmail
         if not mailed:
            # make a list of default places to look
            find_dirs = ["/usr/sbin", "/usr/local/sbin", "/sbin", "/usr/bin", "/usr/local/bin", "/bin"]

            # additionally, try other places in the path
            try:
               find_dirs = uniq(find_dirs + os.environ.get("PATH").split(os.pathsep))
            except: # leave this as general exception handler
               pass

            # try finding sendmail in each of the above directories
            for sendmail in find_dirs:
               sendmail = os.path.join(sendmail, "sendmail")
               if os.path.isfile(sendmail):
                  try:
                     p = os.popen(sendmail + " -t", "w")
                     p.write("To: " + recipient + "\n")
                     p.write("Subject: " + subject + "\n")
                     p.write("\n")
                     p.write(report)
                     status = p.close()
                     if status == None or status == 0:
                        mailed = True
                  except: # leave this as general exception handler
                     pass

                  # mail was sent, exit the for loop
                  break

   # return results
   return mailed, saved, report





def valid_fn(filename):
   """
   <Purpose>
      This returns True if filename is a valid file that may be opened for
      reading or False if it is not.

   <Arguments>
      filename:
          The name of the file to be checked

   <Exceptions>
      None

   <Side Effects>
      None

   <Returns>
      True or False (see above)
   """
   # Verify that filename is a valid string 
   if isinstance(filename, str) or isinstance(filename, unicode):

      # If the path is not valid
      if not os.path.exists(filename):
         return False

      # If filename does not refer to a file
      # TODO FIXME /dev/null isn't a file
      #if not os.path.isfile(filename):
      #   print "b"
      #   return False

      # Try to open the file for reading
      try:
         f = open(filename, "r")
         f.close()
      except IOError:
         return False

      return True

   else:
      # filename wasn't even a string...
      return False





def text_replace_files_in_fnlist(find, replace, fn_list):
   """
   <Purpose>
      Performs a find and replace in a list of files

   <Arguments>
      find:
              This is the string that should be located in each file
      replace:
              This should be substituted for the find string
      fn_list:
              This is the list of files to be examined

   <Exceptions>
      TypeError if the arguments are invalid

   <Side Effects>
      Changes the file contents on disk as described

   <Returns>
      A tuple with a boolean that indicates if the operation was performed and 
      a list of files that failed.   This function will not modify any files 
      if it returns False (even the correctly specified files in the list).
   """
   check_type(find, "find", [str, unicode], "text_replace_files_in_fnlist")
   check_type(replace, "replace", [str, unicode], "text_replace_files_in_fnlist")
   check_type_stringlist(fn_list, "fn_list", "text_replace_files_in_fnlist")

   # Check each filename to see if it is valid
   bad_fns = []
   for thisfn in fn_list:
      if not valid_fn(thisfn):
         bad_fns.append(thisfn)

   # Some file names are invalid, return False and a list
   if bad_fns:
      return (False, bad_fns)
   
   # Perform the replace
   for filename in fn_list:
      a_file = open(filename, "r+")
      text = a_file.read().replace(find, replace)
      a_file.seek(0)
      a_file.write(text)
      a_file.truncate()
      a_file.close()

   return (True, [])
   




def text_replace_files_in_fnlist_re(find, replace, fn_list):
   """
   <Purpose>
      Performs a find and replace in a list of files using a regular expression.

   <Arguments>
      find:
              This is the regular expression that should be located in each file
      replace:
              This should be substituted for the find string
      fn_list:
              This is the list of files to be examined

   <Exceptions>
      TypeError if the arguments are invalid

   <Side Effects>
      Changes the file contents on disk as described

   <Returns>
      A tuple with a boolean that indicates if the operation was performed and 
      a list of files that failed.   This function will not modify any files 
      if it returns False (even the correctly specified files in the list).
   """
   check_type(find, "find", [str, unicode], "text_replace_files_in_fnlist")
   check_type(replace, "replace", [str, unicode], "text_replace_files_in_fnlist")
   check_type_stringlist(fn_list, "fn_list", "text_replace_files_in_fnlist")

   # Check each filename to see if it is valid
   bad_fns = []
   for thisfn in fn_list:
      if not valid_fn(thisfn):
         bad_fns.append(thisfn)

   # Some file names are invalid, return False and a list
   if bad_fns:
      return (False, bad_fns)
   
   # Perform the replace
   cfind=re.compile(find,re.DOTALL)
   for filename in fn_list:
      a_file = open(filename, "r+")
      text = cfind.sub(replace,a_file.read())
      a_file.seek(0)
      a_file.write(text)
      a_file.truncate()
      a_file.close()

   return (True, [])





def remote_popen(hostname, command):
   """
   <Purpose>
      Executes a command on a remote node and returns the error and output 
      results.   Pipes, redirection, etc. should be handled correctly by
      this function.

   <Arguments>
      hostname:
              The host to execute the command on
      command:
              The command to be executed (may contain spaces, etc.)

   <Exceptions>
      IOError if the host cannot be located or there is an error with the 
      command

   <Side Effects>
      Nothing other than what command does

   <Returns>
      A tuple containing the standard out and standard error as a list of 
      strings.   
   """
   # Justin: we do this here so that this is imported only in applications that
   # need it
   import fcntl

   check_type(hostname, "hostname", [str, unicode], "remote_popen")
   check_type(command, "command", [str, unicode], "remote_popen")

   (cmd_in, cmd_out, cmd_err) = os.popen3("ssh "+hostname+" "+re.escape(command))

   # Close the input stream
   cmd_in.close()

   # Make stderr and stdout non-blocking so that it doesn't deadlock
   flags = fcntl.fcntl(cmd_out.fileno(), fcntl.F_GETFL)
   fcntl.fcntl(cmd_out.fileno(), fcntl.F_SETFL, flags | os.O_NDELAY)

   flags = fcntl.fcntl(cmd_err.fileno(), fcntl.F_GETFL)
   fcntl.fcntl(cmd_err.fileno(), fcntl.F_SETFL, flags | os.O_NDELAY)

   # I need to use select because of blocking issues if a stream gets too full
   out_str = ''
   err_str = ''

   streams = [ cmd_out, cmd_err ] 
   # Read until they are both at eof
   while streams:
      (read_streams, junk_write_streams, junk_event_streams) = select.select(streams, [], [], 0)

      if cmd_out in read_streams:
         outdata = cmd_out.read()
         out_str = out_str + outdata
         # I'm finished with the output so close the stream.
         if outdata == '':
            streams.remove(cmd_out)
            cmd_out.close()

      if cmd_err in read_streams:
         errdata = cmd_err.read()
         err_str = err_str + errdata
         # I'm finished with the error so close the stream.
         if errdata == '':
            streams.remove(cmd_err)
            cmd_err.close()

      time.sleep(0.1)

   # I split at \n, \r, etc to make the items string lists
   out_list = out_str.splitlines()
   err_list = err_str.splitlines()

   return (out_list, err_list)
   




def stream_to_sl(in_stream):
   """
   <Purpose>
      This returns the string list it reads from a given stream. 
      If an error occurs, the routine simply returns the exception.

   <Arguments>
      in_stream:
            This is a stream that the string list will be extraced from.

   <Exceptions>
      IOError and ValueError as may be returned by file.readline() or 
      TypeError if in_stream is not a file object (stream)

   <Side Effects>
      None

   <Returns>
      True or False (see above)
   """
   # Make sure we're given a file as an argument...
   if not isinstance(in_stream, file):
      raise TypeError, "Invalid stream in stream_to_sl"

   # Start with an empty list
   ret_sl = []

   # add lines to the list (after removing the \r\n characters)
   rawinput = in_stream.readline()
   while rawinput:
      ret_sl.append(rawinput.strip('\r\n'))
      rawinput = in_stream.readline()

   # return the sl
   return ret_sl





def get_main_module_path():
   """
   <Purpose>
      Returns the directory where the main program module exists on disk.
      Should be relatively smart, for example, if the user typed 
      ./stork.py, this should still return /usr/local/stork/bin.  Also 
      works from the python shell.  Also works if the program is in the
      system path.

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      None

   <Returns>
      Directory where the main module exists on disk.
   """
   program = sys.argv[0]
   path = os.path.realpath(program)
   if program != "":
      path = os.path.split(path)[0]
   return path
   
   



def rmdir_recursive(path):
   """
   <Purpose>
      Removes the directory, and all its files and subdirectories.  
      Similar to rm -rf, but does not use an os.system call.

   <Arguments>
      path:
         Directory to remove.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      True on success (all files/dirs removed), False on error (some or 
      all of the files/dirs remain).
   """
   check_type_simple(path, "path", str, "rmdir_recursive")

   success = True

   # generate directory and file listing
   try:
      walk = os.walk(path)
   except OSError:
      return False

   # make a list of directories and remove files
   dirs = []
   for root, junk, files in os.walk(path):
      dirs.append(root)
      for filename in files:
         try:
            os.remove(os.path.join(root, filename))
         except OSError:
            success = False   
         
   # remove the directories (in reverse order, so subdirectories are
   # removed before their parents)  
   dirs.reverse()
   for directory in dirs:
      try:
         os.rmdir(directory)
      except OSError:
         success = False
   
   return success
   




def grep_escape(s, special_star=False):
   """
   <Purpose>
      Escapes a line for use with a grep system call.
      
   <Arguments>
      s:
         String to be escaped.
      
      special_star:   
         If True, any * (asterisk) in s wil become .* (a wildcard match),
         otherwise False indicates the stars wil be escaped and have no
         special meaning.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      The grep-escaped string.
   """
   check_type_simple(s, "s", str, "grep_escape")

   o = ""
   for c in s:
      if c == "<" or c == ">" or c == "|" or c == "(" or c == ")" or \
         c == "=" or c == ";" or c == "!" or c == "`" or c =="?" or \
         c == "&" or c == "'" or c == " " or c == "\"":
         o += "\\"
      elif c == "[" or c == "]" or c == "^" or c == "." or c == "$":  
         # "*" would be in this category, but it is a special case that 
         # is handled separately below
         o += "\\\\"
      elif c == "*":
         if special_star:
            # convert * to .*
            o += "."   
         else:
            o += "\\\\"   
      elif c == "\\":
         # only \\\ here because the 4th will be added below
         o += "\\\\\\"
      o += c
   return o
   




def program_exists(name):
   """
   <Purpose>
      Checks the path for the presence of a file (hopefully executable)

   <Arguments>
      name:
         Program name

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      True if the program was found in the path, False otherwise
   """
   check_type_simple(name, "name", str, "program_exists")
   path = os.environ.get("PATH").split(os.pathsep)
   for loc in path:
      if os.path.isfile(os.path.join(loc, name)):
         return True
   return False





def makedirs_existok(name):
   """
   <Purpose>
      Creates a directory, but does not throw an exception if it already
      exists.

   <Arguments>
      name:
         directory

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      None.
   """
   try:
      os.makedirs(name)
   # if the path already exists then pass
   except OSError, (errno, strerr):
      if errno == 17:
         pass



def lcut(str, substr):
   if str.startswith(substr):
      str = str[len(substr):]
   return str
