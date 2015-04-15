#! /usr/bin/env python

"""
<Program Name>
   arizonatransfer_nest.py

<Started>
   November 22, 2005

<Author>
   Programmed by Jeffry Johnston.

<Purpose>
   Shares files via the stork nest
"""

import arizonaconfig
import arizonacomm
import arizonageneral
import storkidentify
import arizonareport
import os

glo_retrievedfiles = []
glo_status = False
glo_nestname = None
glo_comm_ok = False



def init_transfer_program():
   """
   <Purpose>
      Initializes nest transfer by identifying ourselves for the nest.

   <Arguments>
      None.

   <Exceptions>
      TypeError:
         If the types of given arguments are incorrect, then TypeError 
         will be raised.

   <Side Effects>
      Sets glo_nestname

   <Returns>
      None.
   """
   global glo_nestname
   
   try:
      arizonacomm.connect(arizonaconfig.get_option("transhost"), 
                          arizonaconfig.get_option("transport"))
   except IOError: 
      arizonareport.send_error(0, "nest transfer: Could not connect to nest")
      
   glo_nestname = storkidentify.identify()
   
   # if not identified, report an error
   if glo_nestname == None:
      arizonareport.send_error(0, "nest transfer: Could not retrieve nest name (identification failed)")

   storkidentify.verify_exportdir(glo_nestname)
   




def close_transfer_program():
   """
   <Purpose>
      This closes a connection. 

   <Arguments>
      None.
   
   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      True on success, False on error
   """
   try:
      arizonacomm.end_session()
      return True
   except IOError:
      return False   





def retrieve_files(host, filelist, destdir='.', indicator=None):
   """
   <Purpose>
      This retrieves files from a host to a destdir.

   <Arguments>
      host:
          Name of host to retrieve files from.

      filelist:
          List of filenames of files to retrieve.

      destdir:
         (Default is '.')
         String containing a directory name where files should be placed
         upon retrieval.

      indicator:
         (Default is None)
         Download indicator function (to show download progress), or
         None if it is unwanted.

   <Exceptions>
      TODO fix comment
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
      TODO fix comment
      (True, grabbed_list)
      'grabbed_list' is a list of files which are retrieved
   """

   global glo_status
   global glo_retrievedfiles
   global glo_comm_ok

   # init variables
   glo_status = False
   glo_retrievedfiles = []

   # not okay until the operation completes successfully
   glo_comm_ok = False

   arizonacomm.send("retrievefiles", "start")
   arizonacomm.send("retrievehost", host)
   arizonacomm.send("retrievedestdir", destdir)
   if indicator:
      indicator_str = str(indicator.get_width())
   else:
      indicator_str = "0"

   arizonacomm.send("retrieveindicator", indicator_str)
   for file in filelist:
      filename = file['filename']
      hash = file.get('hash', None)
      arizonacomm.send("retrievefile", filename)
      arizonacomm.send("retrievehash", hash)
   arizonacomm.send("retrievefiles", "end")

   arizonacomm.handle_session({"output": __handle_output, \
                               "syslog": __handle_syslog, \
                               "retrievedstatus": __handle_retrievedstatus, \
                               "retrievedfiles": __handle_retrievedfiles, \
                               "retrievedfile": __handle_retrievedfile, \
                               "send_out": __handle_send_out, \
                               "send_out_comma": __handle_send_out_comma, \
                               "send_error": __handle_send_error, \
                               "flush_out": __handle_flush_out, \
                               "flush_error": __handle_flush_error})

   # verify that handle_session exited the expected way
   if not glo_comm_ok:
      # raise an exception so that error reporting will capture output
      arizonareport.send_error(0, "nest transfer: encountered an error, transfer may have failed")

   grabbed_list = []

   # prepend destdir to each filename
   for filename in glo_retrievedfiles:
      found = False
      for file in filelist:
         if file['filename'] == filename:
            grabbed_list.append(file)
            found = True
      if not found:
         arizonareport.send_error(0, "nest transfer: unknown file " + filename + " retrieved")

   return (glo_status, grabbed_list)





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
      'arizona_nest' as an string
   """
   return "arizona_nest"





def __handle_output(data):
   """ 
   <Purpose>
      Outputs data to the screen.  Data must contain \n for a new line to
      be printed.

   <Arguments>
      data:
              Data to display.

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   arizonareport.send_out_comma(2, data)





def __handle_syslog(data):
   pass #TODO




   
def __handle_retrievedstatus(data):
   """ 
   <Purpose>
      Sets whether or not all files were retrieved.

   <Arguments>
      data:
              Status: must be "true" or "false"

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   global glo_status
   __report_handler("retrievedstatus", data)
   data = data.strip().lower()
   if data == "true":
      glo_status = True
   elif data == "false":
      glo_status = False
   else:
      arizonareport.send_syslog(arizonareport.INFO, "__handle_retrievedstatus: expected `true' or `false', data:" + str(data))
      arizonareport.send_error(0, "nest transfer: received unexpected __handle_retrievedstatus response:" + str(data))
      __disconnect("arizonatransfer_nest.__handle_retrievedstatus: received unexpected __handle_retrievedstatus response:" + str(data))





def __handle_retrievedfiles(data):
   """ 
   <Purpose>
      Depends on data:
         "start": Initializes and prepares to receive received files
         "end": Ends the session so download status may be returned

   <Arguments>
      data: 
              Must be "start" or "end".

   <Exceptions>
      None.
   
   <Side Effects>
      Inits retrievedfiles
      On success, sets glo_comm_ok to True.

   <Returns>
      None.
   """
   global glo_retrievedfiles
   global glo_comm_ok
   __report_handler("retrievedfiles", data)
   data = data.strip().lower()
   if data == "start":
      # init variables
      glo_retrievedfiles = []
   elif data == "end":
      arizonacomm.end_session()
      glo_comm_ok = True





def __handle_retrievedfile(data):
   """ 
   <Purpose>
      Adds a file to the retrieved list.

   <Arguments>
      None.

   <Exceptions>
      None.
   
   <Side Effects>
      None.

   <Returns>
      None.
   """
   global glo_retrievedfiles
   __report_handler("retrievedfile", data)
   glo_retrievedfiles.append(data)





def __handle_send_out(data):
   arizonareport.send_out(0, data)
   




def __handle_send_out_comma(data):
   arizonareport.send_out_comma(0, data)





def __handle_send_error(data):
   arizonareport.send_error(0, data)





def __handle_flush_out(junk_data):
   arizonareport.flush_out(0)





def __handle_flush_error(junk_data):
   arizonareport.flush_error(0)





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
   arizonareport.send_syslog(arizonareport.INFO, "Disconnecting from nest.")
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
   arizonareport.send_syslog(arizonareport.INFO, "[" + arizonaconfig.get_option("transhost") + ":" + str(arizonaconfig.get_option("transport")) + "] Handling " + name + ", data: `" + data + "'")
