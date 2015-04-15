#! /usr/bin/env python

"""
<Program Name>
   storkerror.py

<Started>   
   November 4, 2005

<Author>
   Jeffry Johnston

<Purpose>
   Error reporting routines used by stork.  
   See also: arizonageneral.error_report()
"""

import sys
import arizonaconfig
import arizonageneral
import traceback
import arizonawarning




#           [option, long option,               variable,          action,        data, default, metavar, description]
"""arizonaconfig
   options=[   
            ["",     "--disableerrorreporting", "senderrorreport", "store_false", None, True,    None,    "disable sending of error reports to the Stork team"],
            ["",     "--debug",                 "debug",           "store_true",  None, False,   None,    "disable catching errors and generation/sending of error reports"],
            ["",     "--filtererror",           "filtererror",     "append",      "string", None, None,   "filter error messages from emailed error reports"]
           ]
   includes=[]        
"""





glo_program = None
glo_output = ""
glo_orig_stdout = None
glo_orig_stdout = None
glo_last_stream = None
glo_traceback = False

glo_developer_email = "stork@cs.arizona.edu"
glo_report_email = "stork.errors@gmail.com"




class copy_out:
   def __init__(self):
      pass
   
   def flush(self):
      global glo_output
      glo_orig_stdout.flush()
      if not glo_output.endswith("\n"):
         glo_output += "\n"

   def write(self, s):
      global glo_output
      global glo_last_stream
      if s.endswith("\n"):
         print >> glo_orig_stdout, s[0:len(s) - 1]
         glo_orig_stdout.flush()
      else:
         glo_orig_stdout.write(s)
         glo_orig_stdout.flush()
      if glo_output.endswith("\n") or glo_last_stream != 1:
         glo_output += "[out]"
         glo_last_stream = 1
      glo_output += s          

   # Jeremy 3/7/07:
   # added this stub so it can be
   # called in the case someone
   # tries to close stdout inorder
   # to make a daemon
   def close(self):
      pass 





class copy_err:
   def __init__(self):
      pass
   
   def flush(self):
      global glo_output
      glo_orig_stderr.flush()
      if not glo_output.endswith("\n"):
         glo_output += "\n"

   def write(self, s):
      global glo_output
      global glo_last_stream
      global glo_traceback
      if s.startswith("Traceback (most recent call last)") and not arizonaconfig.get_option("debug"):
         glo_traceback = True
      # if traceback is set: save the output, but do not display it   
      if not glo_traceback:   
         if s.endswith("\n"):
            print >> glo_orig_stderr, s[0:len(s) - 1]
            glo_orig_stderr.flush()
         else:
            glo_orig_stderr.write(s)
            glo_orig_stderr.flush()
      if glo_output.endswith("\n") or glo_last_stream != 2:
         glo_output += "[err]"
         glo_last_stream = 2
      glo_output += s          

   # Jeremy 3/7/07:   
   # added this stub so it can be
   # called in the case someone
   # tries to close stderr inorder
   # to make a daemon
   def close(self):
      pass





def init_error_reporting(program):
   """
   <Purpose>
      Sets up a handler to report errors to the Stork team

   <Arguments>
      program:
              Name of the program being run.
   
   <Exceptions>
      None.
   
   <Side Effects>
      Inits glo_program, glo_output, glo_last_stream
      Sets new stdout/err, originals in glo_orig_stdout, glo_orig_stderr

   <Returns>
      None.
   """
   global glo_program
   global glo_output
   global glo_orig_stdout
   global glo_orig_stderr
   global glo_last_stream
   global glo_traceback

   glo_program = program
   glo_output = ""
   glo_last_stream = None
   glo_traceback = False
   
   # create new stdout and stderr to capture a copy of all output
   glo_orig_stdout = sys.stdout
   glo_orig_stderr = sys.stderr
   sys.stdout = copy_out()
   sys.stderr = copy_err()

   sys.excepthook = __error_report_hook




def __error_report_hook(exc, value, trace):
   """
   <Purpose>
      Catches an exception and passes it to the error reporting routine.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      None.
   """
   exc_info = [exc, value, trace]

   try:
      debug = arizonaconfig.get_option("debug")
   except:
      debug = False

   # if --debug is used, don't report, just print a normal trace and exit
   if debug:
      traceback.print_exception(exc, value, trace)
      sys.exit(1)

   # determine config file name
   try:
      configfile = arizonaconfig.get_option("configfile")
   except:
      configfile = "/usr/local/stork/etc/stork.conf"

   # build list of e-mail recipients
   try:
      if arizonaconfig.get_option("senderrorreport"):
         # SMB: changed to gmail error reporting account
         mailto = [glo_report_email]
      else:
         mailto = None
   except:
      mailto = None

   # SMB: filter out the following error messages
   try:
      str = value.__str__()

      filters = arizonaconfig.get_option("filtererror")

      # if the user didn't specify filter, then apply our defaults
      if not filters:
         filters = ["No buffer space available",
                    "No space left on device",
                    "Read-only file system",
                    "Connection reset by peer"]

      for filter in filters:
         if str.find(filter) > 0:
            mailto = None
            print "filtered out error report for " + str
            warning = "warning." + filter
            arizonawarning.log_warning(warning.replace(" ","_"))
   except:
      # ignore anything that went wrong above
      pass

   # restore original output streams
   try:
      sys.stdout.flush()
      sys.stdout = glo_orig_stdout
      sys.stdout.flush()
   except:
      pass
   try:
      sys.stderr.flush()
      sys.stderr = glo_orig_stderr
      sys.stderr.flush()
   except:
      pass

   # generate the error report
   mailed, saved, report = \
      arizonageneral.error_report(exc_info,
                                  glo_program,
                                  arizonaconfig.version_string,
                                  glo_output,
                                  mailto,
                                  [configfile],
                                  ["/usr/local/stork/bin", "/usr/local/stork/etc"])
   
   # display error report status
   print >> sys.stderr, ""
   print >> sys.stderr, ""
   if mailed:
      # report was mailed
      print >> sys.stderr, "This program has encountered an internal error."
      print >> sys.stderr, "An error report has been generated and automatically sent to the developers."
      if saved != None:
         print >> sys.stderr, "A copy of the error report has been saved to:\n\t" + saved
      print >> sys.stderr, "If you wish to inquire further, please mail " + glo_developer_email
   elif saved != None:
      # requested that the report not be mailed
      print >> sys.stderr, "This program has encountered an internal error."
      if mailto == None:
         print >> sys.stderr, "An error report has been generated, but it was not sent to the developers."
      else:
         print >> sys.stderr, "An error report has been generated, but it could not be automatically sent to the developers."
      print >> sys.stderr, "A copy of the error report has been saved to:\n\t" + saved
      print >> sys.stderr, "Please send a copy of the report to " + glo_developer_email
   else:
      # something is very wrong.. print to screen
      print >> sys.stderr, report
      print >> sys.stderr, "This program has encountered an internal error."
      if mailto == None:
         print >> sys.stderr, "An error report has been generated, but it was not sent to the developers, per your request."
      else:
         print >> sys.stderr, "An error report has been generated, but it could not be automatically sent to the developers."
      print >> sys.stderr, "Please send the above error report to " + glo_developer_email

