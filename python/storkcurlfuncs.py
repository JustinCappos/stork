#!/usr/bin/python


# provides curl functions for the gui to use
import os
import sys
import tempfile
import shutil
import urllib
import re

import arizonaconfig
import arizonareport

# needs to be set by whatever is using this module. example: "https://stork-repository.cs.arizona.edu"
repository = None

scversion = "$Revision: 1.22 $"

storksite = "http://www.cs.arizona.edu/stork/"


#trys to log the user in
#   returns:
#     true on succussful login
#     false on failure
def login( username, password,site="www.planet-lab.org"):

   print "Using site:",site

   if site == "www.planet-lab.org":
      authtype = "PLauthenticate"
   elif site == "www.planet-lab.eu":
      authtype = "PLEauthenticate"
   else:
      raise ValueError, "Unrecognized site: "+site

   # the curl command to login
   command = arizonaconfig.get_option("curlpath")+" -L -k -d \"%USERINFO%\" -D GetCookie "+repository+":8081/stork/login.php?"

   # build the user info string
   info = "username="+urllib.quote(username)+"&password="+urllib.quote(password)+"&authmethod="+urllib.quote(authtype)
   command  = command.replace( "%USERINFO%", info )

   # try to run the command and see what we get
   (sin, sout, serr) = os.popen3( command )

   outstring = sout.read()
   errstring = serr.read()

   sout.close()
   serr.close()

   if "incorrect username" not in outstring:
      return True

   else:
      return False

# call the autosetup for the user with the specified set of nodes
# (this will add the nodes to the slice and will set the initscript to stork
def autoSetup( username, password, slice, nodes,site="www.planet-lab.org" ):
   if site == "www.planet-lab.org":
      authtype = "PLauthenticate"
   elif site == "www.planet-lab.eu":
      authtype = "PLEauthenticate"
   else:
      raise ValueError, "Unrecognized site: "+site

   command = arizonaconfig.get_option("curlpath")+" -L -k -d \"username="+urllib.quote(username)+"&password="+urllib.quote(password)+"&slice="+urllib.quote(slice)+"&authmethod="+urllib.quote(site)+"&nodes="+urllib.quote_plus(" ".join(nodes))+"\""
   command = command+" "+repository+":8081/stork/autosetup.php"

   #print "DEBUG: about to run", command

   (sin,sout,serr) = os.popen3(command)
   #out = sout.read()




def getslices():
   """Returns an alphabetically sorted list of slices the user has access to.
   """
   
   #TODO this should do some error checking and return none or throw an exception if
   # something goes wrong in retrieving the slices

   command = arizonaconfig.get_option("curlpath")+" -L -k -b GetCookie "+repository+":8081/stork/gui_getslices.php"

   arizonareport.send_out(2, "About to run: "+command)

   (sin, sout, serr) = os.popen3( command )

   outstring = sout.read()
   errstring = serr.read()

   sout.close()
   serr.close()

   slicelist = outstring.rstrip().rstrip("\n").split("\n")
   slicelist.sort()
   return slicelist



# upload a file to the repository.
#  the type of file being uploaded must be specified
#  in the type param and must be one of:
#     package
#     tp
#     pacman
#     pk 
#     conf
def upload_file(username, password, file, type, slice=None):
   arizonareport.send_out(3, "upload_file initiated for file: "+file)

   ok_types = ["package","tp","pacman","pk","conf"]
   if type not in ok_types:
      arizonareport.send_out(2, type+" not in "+str(ok_types)+" , skipping upload")
      return None

   if not login(username,password):
      arizonareport.send_error(2, "ERROR: Not logged in and unable to login. Aborting file upload.")
      return None

   if not os.path.isfile(file):
      arizonareport.send_out(2, file," is not a file, skipping upload.")
      return None

   command = arizonaconfig.get_option("curlpath")+" -L -k -b GetCookie %SLICE% -F \"type=%TYPE%\" -F \"numfiles=1\" -F \"uploadbutton=Upload File\" -F \"file_0=@%FILE%\" "+repository+":8081/stork/upload_handler.php"
   command = command.replace("%FILE%", file).replace("%TYPE%", type)

   if type in ["pk", "conf"]  and slice!=None:
      command = command.replace("%SLICE%", "-F \"slice="+slice+"\"")
   else:
      command = command.replace("%SLICE%", "")
   

   #DEBUG -remove when we go live
   #command  = command.replace("https://stork-repository.cs.arizona.edu", "http://jplichta.ipupdater.com:8080")

   arizonareport.send_out(2, "About to run: "+command)

   (sin, sout, serr) = os.popen3( command )

   outstring = sout.read()
   errstring = serr.read()

   #print outstring



def get_file(relative_path,outputfile):
   tmptuple = tempfile.mkstemp("curldownload")
   tmp      = tmptuple[1]
   try:
      tmptuple[0].close()
   except:
      pass

   command = arizonaconfig.get_option("curlpath")+" -L -w '%{http_code}' -k -o "+tmp+" "+repository+":8081/"+relative_path
 
   arizonareport.send_out(2, "About to run: "+command)

   (sin, sout, serr) = os.popen3( command )

   outline = sout.read()
   sout.close()
   serr.close()

   if outline == "" or outline != "200":
      try:
         os.unlink(tmp)
      except:
         pass
      return False
   else:
      try:
         shutil.move(tmp, outputfile)
      except:
         pass
      return True

def url_exists(relative_path):
   command = arizonaconfig.get_option("curlpath")+" -L -w '%{http_code}' -k --head "+repository+":8081/"+relative_path
 
   arizonareport.send_out(2, "About to run: "+command)

   (sin, sout, serr) = os.popen3( command )

   outline = sout.read()
   sout.close()
   serr.close()

   if outline == "" or outline != "200":
      return False
   else:
      return True




def is_latest_version(version_string):
   """
      Returns a tuple (Boolean,String, String). The first part of the tuple
      is true if this version of the gui is the latest one as reported
      by the website (or newer), the second part of the tuple will always be None if
      the first part is True, if the first part is False it will be a string
      indicating the most recent version from the repository. The third part
      of the tuple will be a string, either storkslicemanager or storkcurlfuncs
      to indicate which file is out of date. If both are out of date, only
      storkslicemanager will be indicated.
   """
   version = "gui-version"
   command = arizonaconfig.get_option("curlpath")+" -L -w '%{http_code}' -k -o "+version+" "+storksite+"gui-version"
   arizonareport.send_out(2, "About to run: "+command)

   (sin, sout, serr) = os.popen3( command )
   outline = sout.read()
   sout.close()
   serr.close()

   if outline == "" or outline != "200":
      # version page did not exist, or could not connect
      return (False, "unknown", "unknown")
   else:
      # try to open the downloaded version page to check the version number
      try:
         f = open(version, "r")
         # Id cvs tag of storkslicemanager should be on first line
         line1 = f.readline().rstrip("\n").rstrip(" ")
         line2 = f.readline().rstrip("\n").rstrip(" ")

         f.close()
 
         current_gui_version = float(version_string.split(" ")[1])
         current_sc_version = float(scversion.split(" ")[1])
         available_gui_version = float(line1.split(" ")[1])
         available_sc_version = float(line2.split(" ")[1])
 
         if current_gui_version >= available_gui_version and current_sc_version >= available_sc_version:
            return (True, None, None)
         else:
            return (False, str(available_gui_version), "storkslicemanager")

      except IOError:
         return (False, "unknown", "unknown")          
      except OSError:
         return (False, "unknown", "unknown")          
 
def update_gui(put_files_here):
   command1 = arizonaconfig.get_option("curlpath")+" -L -o "+os.path.join(put_files_here,"storkslicemanager.py")+" "+storksite+"gui/storkslicemanager.py"
   command2 = arizonaconfig.get_option("curlpath")+" -L -o "+os.path.join(put_files_here,"storkcurlfuncs.py")+" "+storksite+"gui/storkcurlfuncs.py"


   (sin, sout, serr) = os.popen3( command1 )
   (sin, sout, serr) = os.popen3( command2 )
   #SHUTDOWN THE GUI
   # TODO: open it back up for the user again
   sys.exit(0)
   




def fetch_configuration(slicename, defaultconf=False):
   if defaultconf:
       confurl = "http://www.cs.arizona.edu/stork/downloads/sample-stork.conf"
   else:
       confurl = repository+":8081/user-upload/conf/"+slicename+".stork.conf"
       
   destinationfile = slicename+".stork.conf.unsigned"
   command = arizonaconfig.get_option("curlpath")+" -L -w '%{http_code}' -k -o "+destinationfile+" "+confurl
 
   arizonareport.send_out(2, "About to run: "+command)

   (sin, sout, serr) = os.popen3( command )
   outline = sout.read()
   sout.close()
   serr.close()

   if outline == "" or outline != "200":
      os.remove(destinationfile)
      return False
   else:
      return destinationfile



def clean_configuration(conffile):
   """
   Perform mandatory cleaning of the configuration file for proper
   functionality.
   
   """
   writerequired = False
   # read the file in
   lines = []
   try:
      conf = open(conffile, "r")
   except:
      return False
      
   readlines = conf.readlines()
   conf.close()
   for line in readlines:
      origline = line.rstrip("\n")
      pair = read_config_line(line)
      if not pair:
          lines.append(origline)
      else:
          (directive, value) = pair
          # comment out pacmanpackagefile
          if directive == 'pacmanpackagefile':
             lines.append("#pacmanpackagefile = "+value)
             writerequired = True
          # comment out pacmangroupfile
          elif directive == 'pacmangroupfile':
             lines.append("#pacmangroupfile = "+value)
             writerequired = True
          else:
             lines.append(origline)
                        
   # now write file file back, if necessary
   if writerequired:
      try:
         conf = open(conffile, "w")
      except:
         return False
      for line in lines:
         conf.write(line+"\n")

   conf.close()
   return True
  
  

# publickey isn't needed in there anymore
def alter_configuration(conffile, username, publickey, ignoreconflicts=False):
   if not os.path.isfile(conffile): return False

   hasline_requiresignedconf = False

   # read the file in
   lines = []
   try:
      conf = open(conffile, "r")
   except:
      return False
      
   readlines = conf.readlines()
   conf.close()
   for line in readlines:
      origline = line.rstrip("\n")
      pair = read_config_line(line)
      if not pair:
          if origline == 'requiresignedconf':
             hasline_requiresignedconf = True
          lines.append(origline)
      else:
          (directive, value) = pair
          if directive == 'username':
             curuser = value
             if curuser != username and not ignoreconflicts:
                return False
             else:
                lines.append("username = "+username)
          #elif directive == "publickeyfile":
          #   curkey = os.path.basename(value)
          #   if curkey != publickey and not ignoreconflicts:
          #      return False
          #   else:
          #      lines.append("publickeyfile = /usr/local/stork/var/keys/"+publickey)
          else:
               lines.append(origline)
                        
   #TODO detect if username or publickeyfile were completely missing and add
   # them in if the were.
   
   if not hasline_requiresignedconf:
       lines.append("requiresignedconf")
                        
   # now write file file back
   try:
      conf = open(conffile, "w")
   except:
      return False

   for line in lines:
      conf.write(line+"\n")

   conf.close()
   return True
         
         

# returns a tuple (username, pubkey)
def parse_config(conffile):
   try:
      conf = open(conffile, "r")
   except:
      return (None, None)

   username = None
   keyfile  = None

   lines = conf.readlines()
   for line in lines:
      pair = read_config_line(line)
      if pair:
          (directive, value) = pair
          if directive == 'username':
             username = value
          elif directive == "publickeyfile":
             keyfile = os.path.basename(value)  

   conf.close()
   return (username, keyfile)



configlineregex = re.compile(r"(\S+)\s*=\s*(\S+)")

def read_config_line(line):
   """Extract the directive and value from a config file line."""    
   global configlineregex
   if line.find("#") != -1:
       line = line[:line.find("#")]
   matches = configlineregex.match(line.strip())
   if matches:
       return matches.groups()
   else:
       return None
