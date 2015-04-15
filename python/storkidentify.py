"""
<Program Name>
   storkidentify.py

<Started>
   November 29, 2005

<Author>
   Programmed by Jeffry Johnston.

<Purpose>
   Handles client side of the nest identification process 
"""

#           [option, long option,      variable,       action,  data,     default,     metavar,     description]
"""arizonaconfig
   options=[["",     "--nesthostname", "transhost",    "store", "string", "localhost", "hostname", "use this host to transfer files"], 
            ["",     "--nestport",     "transport",    "store", "int",    648,         "port",     "use this port to transfer files"]] 
   includes=[]
"""

import storkpackagelist
import storkusername
import arizonacomm
import arizonaconfig
import arizonareport
import arizonageneral
import os
import sys

glo_active = ""
glo_identified = None
glo_slicename = None



# TODO comments for all functions




def verify_exportdir(nestname):
   """
   <Purpose>
      Checks to see if /.exportdir exists. Creates it if it does not.

      TODO: This should be integrated into planetlab_share. Right now, 
      planetlab_share asks the client ot create .exportdir files in a 
      subdirectory for  identification purposes rather than in the root 
      directory (for sharing purposes)

      TODO: The initscript creates /.exportdir, so in theory this code can be
      removed once all stork clients have been upgraded (legacy stork clients
      remove /.exportdir after using the nest)

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      None
   """
   if not os.path.exists("/.exportdir"):
     arizonareport.send_out(1, "/.exportdir is missing; recreating")
     try:                         
        f = file("/.exportdir", "w+")
        f.write(nestname + "\n")
        f.close()
     except OSError:
        arizonareport.send_error(0, "nest transfer: error creating /.exportdir containing: " + str(nestname))

        

        

def identify():
   global glo_identified
   global glo_slicename
   #print "[DEBUG] identify()"
   glo_identified = None


   glo_slicename = arizonageneral.getusername()
  

   # report data to be logged at the nest
   ##Send Version
   arizonacomm.send("info", "version:" + arizonaconfig.get_version())
   
   ##Send command line
   try:
      cmdline = " ".join(sys.argv[0:])
   except IndexError:                     #changes general except to IndexError
      cmdline = "Unable to determine command line."
   arizonacomm.send("info", "command_line:" + cmdline)
   
   #Send Options
   arizonacomm.send("info", "options:" + repr(arizonaconfig.program_variables.__dict__))

   # TODO: The following code fails if storkpackagelist.init() has not
   # completed. This happens whenever stork downloads new packageinfo, because
   # identify() is called from inside storkpackagelist.

   # SMB: I added the test of storkpackagelist.glo_intialized to prevent the
   # user from being confused by the error messages. We probably need to
   # seperate the logging code out of identify()

   if not storkpackagelist.glo_initialized:
      arizonacomm.send("info", "tpfile:storkpackagelist not initialized::")
   else:
      ##Send tpfile
      (tpfilename, tprepo, tpkeytuple) = storkpackagelist.find_file_kind("tpfiles", "tpfile")

      if not tpfilename:
         tpfilename = "Failed to locate trusted package file"
      tpfile = ""
      if os.path.exists(tpfilename):
         f = open(tpfilename)
         tpfile = f.read()
         f.close()
      arizonacomm.send("info", "tpfile:" + tpfilename + "::" + tpfile)

 
  
  
   
   
   # report our verbosity level so that nest side messages may be displayed    
   arizonacomm.send("verbosity", str(arizonareport.get_verbosity()))
      
   arizonacomm.send("identify", glo_slicename)

   #print "[DEBUG] calling arizonacomm.handle_session"
   arizonacomm.handle_session({"createdirectory": __handle_createdirectory, \
                               "removedirectory": __handle_removedirectory, \
                               "createfile": __handle_createfile, \
                               "removefile": __handle_removefile, \
                               "appendactive": __handle_appendactive, \
                               "overwriteactive": __handle_overwriteactive, \
                               "readactive": __handle_readactive, \
                               "setactive": __handle_setactive, \
                               "identifyfailed": __handle_identifyfailed, \
                               "identified": __handle_identified, \
                               "send_out": __handle_send_out, \
                               "send_out_comma": __handle_send_out_comma, \
                               "send_error": __handle_send_error, \
                               "flush_out": __handle_flush_out, \
                               "flush_error": __handle_flush_error})
   #print "[DEBUG] arizonacomm.handle_session RETURNED"
   #print "[DEBUG] glo_identified =", glo_identified 

   # make sure we identified
   if not glo_identified:                           
      # raise an exception so that error reporting will capture output
      raise IOError, "nest: encountered an error, unable to identify"
      
      
   return glo_identified





def __handle_createdirectory(data):
   global glo_active 
   try:
      glo_active = data
      os.mkdir(data)
      arizonacomm.send("identifyready", "")
   except (TypeError, IOError, OSError):  
      arizonareport.send_syslog(arizonareport.ERR, "storkidentify.__handle_createdirectory(): Could not create directory: `" + str(data) + "'")
      arizonareport.send_error(2, "ERROR: Could not create directory: `" + str(data) + "'") 
      __identify_done(None)
   
   
   
   
def __handle_removedirectory(data):
   try:
      os.rmdir(data)
      arizonacomm.send("identifyready", "")
   except (TypeError, IOError, OSError): #changed from catching a general exception
      arizonareport.send_syslog(arizonareport.ERR, "storkidentify.__handle_removedirectory(): Could not remove directory: `" + str(data) + "'")
      arizonareport.send_error(2, "ERROR: Could not remove directory: `" + str(data) + "'") 
      __identify_done(None)


    
        
            
def __handle_createfile(data):  
   global glo_active 
   try:
      glo_active = data
      f = open(data, "w+")
      f.close()
      arizonacomm.send("identifyready", "")
   except (IOError, TypeError): #changed from catching a general exception
      arizonareport.send_syslog(arizonareport.ERR, "storkidentify.__handle_createfile(): Could not create file: `" + str(data) + "'")
      arizonareport.send_error(2, "ERROR: Could not create file: `" + str(data) + "'") 
      __identify_done(None)

   

         
                           
def __handle_removefile(data):
   try:
      os.remove(data)
      arizonacomm.send("identifyready", "")
   except (TypeError, IOError, OSError): #changed from catching a general exception
      arizonareport.send_syslog(arizonareport.ERR, "storkidentify.__handle_removefile(): Could not remove file: `" + str(data) + "'")
      arizonareport.send_error(2, "ERROR: Could not remove file: `" + str(data) + "'") 
      __identify_done(None)


     
          
                    
def __handle_appendactive(data):
   try:
      f = open(glo_active, "a")
      f.write(data)
      f.close()
      arizonacomm.send("identifyready", "")
   except (TypeError, IOError): #changed from catching a general exception
      arizonareport.send_syslog(arizonareport.ERR, "storkidentify.__handle_appendactive(): Could not append: `" + str(data) + "' to active file: `" + str(glo_active) + "'")
      arizonareport.send_error(2, "ERROR: Could not append: `" + str(data) + "' to active file: `" + str(glo_active) + "'") 
      __identify_done(None)





def __handle_overwriteactive(data):
   try:
      f = open(glo_active, "w")
      f.write(data)
      f.close()
      arizonacomm.send("identifyready", "")
   except (IOError, TypeError): #changed from catching a general exception
      arizonareport.send_syslog(arizonareport.ERR, "storkidentify.__handle_overwriteactive(): Could not overwrite active file: `" + str(glo_active) + "' with: `" + str(data) + "'")
      arizonareport.send_error(2, "ERROR: Could not overwrite active file: `" + str(glo_active) + "' with: `" + str(data) + "'") 
      __identify_done(None)





def __handle_readactive(data):
   try:
      f = open(glo_active, "r")
      data = f.read()
      f.close()
      arizonacomm.send("identifyready", data)
   except (IOError, TypeError): #changed from catching a general exception
      arizonareport.send_syslog(arizonareport.ERR, "storkidentify.__handle_readactive(): Could not read active file: `" + str(glo_active) + "'")
      arizonareport.send_error(2, "ERROR: Could not read active file: `" + str(glo_active) + "'") 
      __identify_done(None)





def __handle_setactive(data):
   try:
      global glo_active 
      glo_active = data
      arizonacomm.send("identifyready", "")
   except (IOError, TypeError): #changed from catching a general exception
      arizonareport.send_syslog(arizonareport.ERR, "storkidentify.__handle_setactive(): Could not set file: `" + str(data) + "' as the active file")
      arizonareport.send_error(2, "ERROR: Could not set file: `" + str(data) + "' as the active file") 
      __identify_done(None)
          
               

                            

def __handle_identifyfailed(junk_data):
   #print "[DEBUG] identify failed"
   __identify_done(None)





def __handle_identified(data):
   #print "[DEBUG] identified !!!!"
   __identify_done(data)





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





def __identify_done(identified):
   global glo_identified 
   glo_identified = identified
   arizonacomm.end_session()
