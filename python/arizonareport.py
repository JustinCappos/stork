# /usr/bin/env python

"""
<Program Name>
   storkreport.py

<Started>   
   February 4, 2005

<Author>
   sethh@cs.arizona.edu
   Justin Cappos
   Jeffry Johnston

<Purpose>
   Provides Error Reporting/Logging Utility Functions.

   The functions are named loosely based on the syslog levels.  However,
   because syslog has 7 priority levels, and stork only has 4, the 
   send_error and send_out_* series only contain debug, info, warning, and
   err (notice, alert, and emergency were omitted).  send_syslog supports 
   all seven levels, however.

   Current syslog implementation assumes local syslog (no remote servers),
   and a facility of LOG_USER (defaults from the syslog module).  

   On July 10th, 2007, Justin is doing a pretty substantial rewrite.   Blame
   him for any resulting cruft.
"""

#           [option, long option,      variable,  action,        data,  default, metavar, description]
"""arizonaconfig
   options=[["-Q",   "--veryquiet",    "verbose", "store_const", 0,     2,       None,    "be very quiet"],
            ["-q",   "--quiet",        "verbose", "store_const", 1,     2,       None,    "be quiet"],
            ["-v",   "--verbose",      "verbose", "store_const", 2,     2,       None,    "be verbose (default)"],
            ["-V",   "--veryverbose",  "verbose", "store_const", 3,     2,       None,    "be very verbose (useful for debugging)"],
            ["",     "--ultraverbose", "verbose", "store_const", 4,     2,       None,    "be extremely verbose (might be useful for debugging)"] ]
   includes=[]        
"""

import arizonaconfig
import struct
import sys
import traceback

# Justin: This is needed because syslog does not exist on Windows.   We don't
# use any function that does a syslog on Windows so this should be okay.
try:
  import syslog
except ImportError:
  pass



# syslog severity levels
EMERG = 0
ALERT = 1
CRIT = 2
ERR = 3
WARNING = 4
NOTICE = 5
INFO = 6
DEBUG = 7 

# aliases for the above (why remember cryptic names?)
EMERGENCY = 0
CRITICAL = 2
ERROR = 3
WARN = 4
INFORM = 6
INFORMATION = 6
INFORMATIONAL = 6

class capture_handler:
   """
   <Purpose>
      An object that can be used to capture the output of arizonalib. See
      start_capture and stop_capture.
   """
   
   def __init__(self):
      self.verb = 0
      self.output = ""
      pass

   def flush(self, verb):
      pass

   def send_out(self, verb, msg):
      self.send(verb, msg + "\n")

   def send_out_comma(self, verb, msg):
      self.send(verb, msg + " ")

   def send_error(self, verb, msg):
      self.send(verb, msg + "\n")

   def send(self, verb, msg):
      if verb >= self.verb:
         self.output = self.output + msg

# a list of capture objects that can be used to capture the output
glo_captures = []

def start_capture():
   """
   <Purpose>
      Adds a capture object to capture the output of arizonareport. Multiple
      capture objects may be used by different callers at the same time. Capture
      is stopped by passing the capture object to stop_capture()

   <Returns>
      Capture object of type capture_handler
   """
   capture = capture_handler()
   glo_captures.append(capture)
   return capture

def stop_capture(capture):
   """
   <Purpose>
      Removes a capture object.

   <Returns>
      String containing output that was captured
   """
   glo_captures.remove(capture)
   return capture.output



# This contains the list of output functions that will be called (see
# set_output_function() for more information).
output_function_list = []

def set_output_function(func):
   """
   <Purpose>
      Sets a function that is called with all output.   The function must take
      take three arguments:

        call_type: This is either "syslog", "send_out", "send_out_comma", "send_error",
                   or "send_error_comma"

        call_verbosity: This is the verbosity the print statement was called
                        with.

        outputstring: This is the string which would have been output

      Multiple functions can be set using this and they will be "chained"
      in a first set, first called fashion.   The output from the first 
      function will be used as the outputstring for the second, and so on...

   <Arguments>   
      func -- The above mentioned function
   
   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """

   global output_function_list

   output_function_list.append(func)






def unset_output_function(func):
   """
   <Purpose>
      Unsets an output function 

   <Arguments>   
      func -- The output function to be removed
   
   <Exceptions>
      ValueError (when the function isn't in the list)
   
   <Side Effects>
      None.

   <Returns>
      None.
   """

   global output_function_list

   output_function_list.remove(func)




def __get_output_string(call_type,call_verbosity,outputstring):
   """
   <Purpose>
      Constructs the output string by calling all of the output functions. 
      The arguments are passed to the output_functions.

   <Arguments>   
      call_type: This is either "syslog", "send_out", "send_out_comma", or 
                 "send_error"

      call_verbosity: This is the verbosity the output statement was called
                      with.

      outputstring: This is the string which would have been output

   <Exceptions>
      Any exceptions caused by the output functions
   
   <Side Effects>
      Any side effects caused by the output functions

   <Returns>
      The output string
   """

   for function in output_function_list:
     outputstring = function(call_type,call_verbosity,outputstring)

   return outputstring















def get_verbosity():
   """
   <Purpose>
      Returns the current verbosity level:
        4 - ULTRAVERBOSE aka DEBUG
        3 - VERYVERBOSE aka DEBUG
        2 - VERBOSE
        1 - QUIET
        0 - VERYQUIET
       -1 - ABSOLUTE SILENCE
 
   <Arguments>   
      None. 
   
   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      Returns the current verbosity level.  See "Purpose", above.
   """
   verbosity = arizonaconfig.get_option("verbose")
   if verbosity == None:
      arizonaconfig.init_options("arizonareport")
      # stork default (--verbose)
      return 2            
   else: 
      return verbosity  





def set_verbosity(verbosity):
   """
   <Purpose>
      Sets the current verbosity level.

   <Arguments>   
      verbosity:
              The new verbosity level:
                4 - ULTRAVERBOSE aka DEBUG
                3 - VERYVERBOSE aka DEBUG
                2 - VERBOSE
                1 - QUIET
                0 - VERYQUIET
               -1 - ABSOLUTE SILENCE
   
   <Exceptions>
      None.
   
   <Side Effects>
      Changes the storkconfig "verbose" setting. 

   <Returns>
      None.
   """
   # check params
   if not isinstance(verbosity, int): 
      raise TypeError, "The parameter 'verbosity' of the function 'set_verbosity' must be an integer."
   if verbosity < -1 or verbosity > 4:
      raise TypeError, "The parameter 'verbosity' of the function 'set_verbosity' must be from -1 to 4, inclusive."

   if arizonaconfig.get_option("verbose") == None:
      arizonaconfig.init_options("arizonareport")
      
   arizonaconfig.set_option("verbose", verbosity)





def console_size():
   """ 
   <Purpose>
      Finds the current console width and height using ioctl.

   <Arguments>
      None.

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      (height, width), or (None, None) on error
   """

   # Justin: we do this here so that this is imported only in applications that
   # need it
   import fcntl
   import termios

   try:
      size = struct.unpack("hhhh", fcntl.ioctl(0, termios.TIOCGWINSZ, "\000" * 8))[0:2]
   except IOError:
      size = (None, None)
   return size





original_stdout = []
def redirect_stdout(stream):
   """
   <Purpose>
      Redirects the standard output stream (stdout) to a new file stream.
      If this is the first time that output has been redirected, the
      original stdout stream will be saved for use with the restore_stdout
      function.

   <Arguments>
      stream:
              The new file stream for stdout.

   <Exceptions>
      TypeError on bad parameters.

   <Side Effects>
      Changes sys.stdout.

   <Returns>
      None.
   """
   global original_stdout
   
   # save the original stdout 
   original_stdout.insert(0, sys.stdout)
   
   # redirect stdout to new stream  
   sys.stdout = stream   





def restore_stdout():
   """
   <Purpose>
      Restores the standard output stream (stdout) to the original file 
      stream.  This function only has an effect if stdout was previously 
      redirected with redirect_stdout.
 
   <Arguments>   
      None.
   
   <Exceptions>
      None.
   
   <Side Effects>
      Changes sys.stdout.

   <Returns>
      None.
   """
   global original_stdout
   
   if len(original_stdout) > 0:
      sys.stdout = original_stdout[0]
      del original_stdout[0]
   else:
      raise ValueError   
      




original_stderr = []
def redirect_stderr(stream):
   """
   <Purpose>
      Redirects the standard error stream (stderr) to a new file stream. 
      If this is the first time that output has been redirected, the 
      original stderr stream will be saved for use with the restore_stderr
      function.
 
   <Arguments>   
      stream:
              The new file stream for stderr.
   
   <Exceptions>
      TypeError on bad parameters.
   
   <Side Effects>
      Changes sys.stderr.

   <Returns>
      None.
   """
   global original_stderr

   # save the original stderr
   original_stderr.append(sys.stderr)
   
   # redirect stderr to new stream  
   sys.stderr = stream




def restore_stderr():
   """
   <Purpose>
      Restores the standard error stream (stderr) to the original file 
      stream.  This function only has an effect if stderr was previously 
      redirected with redirect_stderr.
 
   <Arguments>   
      None.
   
   <Exceptions>
      None.
   
   <Side Effects>
      Changes sys.stderr.

   <Returns>
      None.
   """
   global original_stderr
   
   if len(original_stderr) > 0:
      sys.stderr = original_stderr[0]
      del original_stderr[0]
   else:
      raise ValueError   



   
  
def __verbosity_is_sufficient(required_verbosity):
   """
   <Purpose>
      Checks given verbosity against current verbosity level.  If the 
      current verbosity level is greater than or equal to the required
      verbosity level, returns True, otherwise returns False.
 
   <Arguments>   
      required_verbosity:
              The verbosity level required:
                4 - ULTRAVERBOSE aka DEBUG
                3 - VERYVERBOSE aka DEBUG
                2 - VERBOSE
                1 - QUIET
                0 - VERYQUIET
   
   <Exceptions>
      TypeError on bad parameters.
   
   <Side Effects>
      None.

   <Returns>
      True if current verbosity level is sufficient for operation, 
      False otherwise.
   """
   # check params
   if not isinstance(required_verbosity, int): 
      raise TypeError, "The parameter 'required_verbosity' of the function '__verbosity_is_sufficient' must be an integer."
   if required_verbosity < 0 or required_verbosity > 4:
      raise TypeError, "The parameter 'required_verbosity' of the function '__verbosity_is_sufficient' must be from 0 to 4, inclusive."
   
   # if they requested silence, be sure that request is honored
   if get_verbosity() < 0:
      return False   
   
   return get_verbosity() >= required_verbosity
      
   



def flush_out(required_verbosity):
   """
   <Purpose>
      Flushes stdout if the current verbosity level is greater than
      or equal to required_verbosity.
 
   <Arguments>   
      required_verbosity:
              The verbosity level required:
                4 - ULTRAVERBOSE aka DEBUG
                3 - VERYVERBOSE aka DEBUG
                2 - VERBOSE
                1 - QUIET
                0 - VERYQUIET
   
   <Exceptions>
      TypeError on bad parameters.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   if __verbosity_is_sufficient(required_verbosity):
      sys.stdout.flush()

   for capture in glo_captures:
      capture.flush(required_verbosity)





def flush_error(required_verbosity):
   """
   <Purpose>
      Flushes stderr if the current verbosity level is greater than
      or equal to required_verbosity.

   <Arguments>
      required_verbosity:
              The verbosity level required:
                4 - ULTRAVERBOSE aka DEBUG
                3 - VERYVERBOSE aka DEBUG
                2 - VERBOSE
                1 - QUIET
                0 - VERYQUIET

   <Exceptions>
      TypeError on bad parameters.

   <Side Effects>
      None.

   <Returns>
      None.
   """
   if __verbosity_is_sufficient(required_verbosity):
      sys.stderr.flush()

   for capture in glo_captures:
      capture.flush(required_verbosity)



# The purpose of this variable is to be able to check the messages sent by other modules.
# This is used in tests.
message = None

def send_out(required_verbosity, mesg):
   """
   <Purpose>
      Sends mesg to stdout if the current verbosity level is greater than
      or equal to required_verbosity.

   <Arguments>
      required_verbosity:
              The verbosity level required:
                4 - ULTRAVERBOSE aka DEBUG
                3 - VERYVERBOSE aka DEBUG
                2 - VERBOSE
                1 - QUIET
                0 - VERYQUIET
      mesg:
              The message to display via stdout.

   <Exceptions>
      TypeError on bad parameters.

   <Side Effects>
      None.

   <Returns>
      None.
   """
   mesg = __get_output_string("send_out",required_verbosity,mesg)
   if __verbosity_is_sufficient(required_verbosity):
      print >> sys.stdout, mesg
      sys.stdout.flush()

   for capture in glo_captures:
      capture.send_out(required_verbosity, mesg)

   global message
   message = mesg





def send_out_comma(required_verbosity, mesg):
   """
   <Purpose>
      Sends mesg to stdout if the current verbosity level is greater than
      or equal to required_verbosity.  Does not output a newline after the
      message, similar to Python's "print ,".

   <Arguments>
      required_verbosity:
              The verbosity level required:
                4 - ULTRAVERBOSE aka DEBUG
                3 - VERYVERBOSE aka DEBUG
                2 - VERBOSE
                1 - QUIET
                0 - VERYQUIET
      mesg:
              The message to display via stdout.

   <Exceptions>
      TypeError on bad parameters.

   <Side Effects>
      None.

   <Returns>
      None.
   """
   mesg = __get_output_string("send_out_comma",required_verbosity,mesg)
   if __verbosity_is_sufficient(required_verbosity):
      sys.stdout.write(mesg)
      sys.stdout.flush()

   for capture in glo_captures:
      capture.send_comma(required_verbosity, mesg)

   global message
   message = mesg





def send_error(required_verbosity, mesg, program=None):
   """
   <Purpose>
      Sends mesg to stderr if the current verbosity level is greater than
      or equal to required_verbosity.  Also sends the mesg to the syslog,
      with type ERR.

   <Arguments>
      required_verbosity:
              The verbosity level required:
                4 - ULTRAVERBOSE aka DEBUG
                3 - VERYVERBOSE aka DEBUG
                2 - VERBOSE
                1 - QUIET
                0 - VERYQUIET
      mesg:
              The message to display via stderr.
      module:
              (default: None)
              An optional string giving the name of the program or module
              where the error occurred.  This will be prepended to the
              syslog message in the form "program mesg".

   <Exceptions>
      TypeError on bad parameters.

   <Side Effects>
      None.

   <Returns>
      None.
   """
   mesg = __get_output_string("send_error",required_verbosity,mesg)
   # check params
   if not isinstance(program, str) and program != None:
      raise TypeError, "The parameter 'program' of the function 'send_error' must be either a string or None."

   # prepend module name, function and line no from the function that called us
   (module_name, lineno, function, junk_text) = traceback.extract_stack()[-2]

   # prepend "[program] " to syslog output, and log more info for debugging
   syslog_mesg = "An error occurred in module " + module_name + ", on line " + str(lineno) + " of function " + function + ": " + mesg
   if program != None:
      syslog_mesg = program + " " + syslog_mesg

   # always syslog, regardless of verbosity
   send_syslog(ERR, syslog_mesg)

   # output mesg to stderr
   if __verbosity_is_sufficient(required_verbosity):
      print >> sys.stderr, mesg
      sys.stderr.flush()

   for capture in glo_captures:
      capture.send_error(required_verbosity, mesg)

   global message
   message = mesg





def send_syslog(severity, mesg):
   """
   <Purpose>
      Adds "debug" mesg to the syslog.  For debug-level messages.
 
   <Arguments>
      severity:
              The type of message to send:
                0 or arizonareport.EMERG 
                  System is unusable. 
                1 or arizonareport.ALERT
                  Action must be taken immediately. 
                2 or arizonareport.CRIT
                  Critical conditions. 
                3 or arizonareport.ERR
                  Error conditions. 
                4 or arizonareport.WARNING
                  Warning conditions. 
                5 or arizonareport.NOTICE
                  Normal, but significant, condition. 
                6 or arizonareport.INFO
                  Informational message. 
                7 or arizonareport.DEBUG
                  Debug-level message. 
      mesg:
              The message to add to the syslog.
   
   <Exceptions>
      TypeError on bad params.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   mesg = __get_output_string("send_syslog",severity,mesg)
   # check params
   if not isinstance(severity, int): 
      raise TypeError, "The parameter 'severity' of the function 'send_syslog' must be an integer."
   if severity < 0 or severity > 7:
      raise TypeError, "The parameter 'severity' of the function 'send_syslog' must be from 0 to 7, inclusive."

   global message
   message = mesg
   
   # prepend module name, function and line no from the function that called us
   (module_name, lineno, function, junk_text) = traceback.extract_stack()[-2]
   mesg = "In module: " + module_name + " line " + str(lineno) + " of function " + function + ": " + mesg
   try:
   	syslog.syslog(severity, mesg)
   except NameError:
   	pass

