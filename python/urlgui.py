#!/usr/bin/python


# provides curl functions for the gui to use
import os
import sys
import tempfile
import shutil
import urllib
import urllib2
import re
import cookielib

loginCookie = None
headers = {'User-agent' : "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)"}
COOKIEFILE = 'cookies.lwp'
if os.path.isfile(COOKIEFILE):
	os.remove(COOKIEFILE)

urlopen = urllib2.urlopen
Request = urllib2.Request
cj = cookielib.LWPCookieJar()

opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
urllib2.install_opener(opener)











rep = "https://stork-repository.cs.arizona.edu/"

scversion = "$Revision: 1.3 $"

storksite = "http://www.cs.arizona.edu/stork/"


#trys to log the user in
#   returns:
#     true on succussful login
#     false on failure
def login( username, password ):
	values = {'username' : username,
		  'password' : password}
	usrdata = urllib.urlencode(values)
	theurl = "https://stork-repository.cs.arizona.edu/stork/login.php?"

	req = Request(theurl,usrdata,headers)
	handle = urlopen(req)
	for index, cookie in enumerate(cj):
		loginCookie = cookie
		
	if "incorrect username" not in handle.read():
		return True
	else:
		return False
	

# call the autosetup for the user with the specified set of nodes
# (this will add the nodes to the slice and will set the initscript to stork
def autoSetup( username, password, slice, nodes ):
   command = "/usr/bin/curl -k -d \"username="+urllib.quote(username)+"&password="+urllib.quote(password)+"&slice="+urllib.quote(slice)+"&nodes="+urllib.quote_plus(" ".join(nodes))+"\""
   command = command + " https://stork-repository.cs.arizona.edu/stork/autosetup.php"

   #print "DEBUG: about to run", command

   (sin,sout,serr) = os.popen3(command)
   #out = sout.read()



# gets the slices for the user
# this will automatically call the login functino
# and will return None if it cannot login

# if it can login it will return a list of slices 
# that the user has access to
def getslices( username, password ):

   if not login(username, password):
      return None


   #command = "/usr/bin/curl -k -b GetCookie https://stork-repository.cs.arizona.edu/stork/gui_getslices.php"
 
   #DEBUG -remove when we go live
   #command  = command.replace("https://stork-repository.cs.arizona.edu", "http://jplichta.ipupdater.com:8080")

   #print "DEBUG: about to run: "+command

   #(sin, sout, serr) = os.popen3( command )

   #outstring = sout.read()
   #errstring = serr.read()

   #sout.close()
   #serr.close()

   #print "DEBUG: "+outstring
   #print "ERROR: "+errstring

   #return outstring.rstrip().rstrip("\n").split("\n") 
   
   theurl = "https://stork-repository.cs.arizona.edu/stork/gui_getslices.php"
   req = Request(theurl,None,headers)
   handle = urlopen(req)
   return handle.read().rstrip().rstrip("\n").split("\n")



# upload a file to the repository.
#  the type of file being uploaded must be specified
#  in the type param and must be one of:
#     package
#     tp
#     pacman
#     pk 
#     conf
def upload_file(username, password, file, type, slice=None):
   #print  "upload_file initiated for file: "+file

   ok_types = ["package","tp","pacman","pk","conf"]	
   if type not in ok_types:
      print type+" not in "+str(ok_types)+" , skipping"
      return None

   if not login(username,password):
      print "ERROR: Not logged in and unable to login. Aborting file upload."
      return None

   if not os.path.isfile(file):
      print "WARNING: ",file," is not a file, skipping."
      return None
      
   values = {'slice' : slice,
   	     'type' : type,
	     'numfiles' : 1,
	     'uploadbutton' : 'Upload File',
	     'file_0' : '@'+file}
	     
   print values
	
   usrdata = urllib.urlencode(values)
   print usrdata
   theurl = "https://stork-repository.cs.arizona.edu/stork/upload_handler.php"

   req = Request(theurl,usrdata,headers)
   handle = urlopen(req)
   for index, cookie in enumerate(cj):
	loginCookie = cookie
	
   #print handle.read()

   #command = "/usr/bin/curl -k -b GetCookie %SLICE% -F \"type=%TYPE%\" -F \"numfiles=1\" -F \"uploadbutton=Upload File\" -F \"file_0=@%FILE%\" https://stork-repository.cs.arizona.edu/stork/upload_handler.php"
   #command = command.replace("%FILE%", file).replace("%TYPE%", type)

   #if type in ["pk", "conf"]  and slice!=None:
   #   command = command.replace("%SLICE%", "-F \"slice="+slice+"\"")
   #else:
   #   command = command.replace("%SLICE%", "")
   

   #DEBUG -remove when we go live
   #command  = command.replace("https://stork-repository.cs.arizona.edu", "http://jplichta.ipupdater.com:8080")

   #print "DEBUG: about to run: "+command

   #(sin, sout, serr) = os.popen3( command )

   #outstring = sout.read()
   #errstring = serr.read()

   #print outstring



def get_file(relative_path,outputfile):
   tmptuple = tempfile.mkstemp("curldownload")
   tmp      = tmptuple[1]
   try:
      tmptuple[0].close()
   except:
      pass

   command = "/usr/bin/curl -w '%{http_code}' -k -o "+tmp+" "+rep+"/"+relative_path
 
   print "DEBUG: about to run: ",command

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
   command = "/usr/bin/curl -w '%{http_code}' -k --head "+rep+"/"+relative_path
 
   print "DEBUG: about to run: ",command

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
      by the website, the second part of the tuple will always be None if
      the first part is True, if the first part is False it will be a string
      indicating the most recent version from the repository. The third part
      of the tuple will be a string, either storkslicemanager or storkcurlfuncs
      to indicate which file is out of date. If both are out of date, only
      storkslicemanager will be indicated.
   """
   version = "gui-version"
   command = "/usr/bin/curl -w '%{http_code}' -k -o "+version+" "+storksite+"gui-version"
   print "DEBUG: about to run: ",command

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
 
         if line1 == version_string and line2 == scversion:
            return (True, None, None)
         elif line1 == version_string and line2 != scversion:
            return (False, line2, "storkcurlfuncs")
         elif line1 != version_string and line2 == scversion:
            return (False, line1, "storkslicemanager")
         else:
            return (False, line1, "storkslicemanager")

      except IOError, OSError:
         return (False, "unknown", "unknown")          
 
def update_gui(put_files_here):
   command1 = "/usr/bin/curl -o "+os.path.join(put_files_here,"storkslicemanager.py")+" "+storksite+"gui/storkslicemanager.py"
   command2 = "/usr/bin/curl -o "+os.path.join(put_files_here,"storkcurlfuncs.py")+" "+storksite+"gui/storkcurlfuncs.py"


   (sin, sout, serr) = os.popen3( command1 )
   (sin, sout, serr) = os.popen3( command2 )
   #SHUTDOWN THE GUI
   # TODO: open it back up for the user again
   sys.exit(0)
   




def fetch_configuration(slicename, defaultconf=False):
   if defaultconf:
       confurl = "http://www.cs.arizona.edu/stork/downloads/sample-stork.conf"
   else:
       confurl = rep+"user-upload/conf/"+slicename+".stork.conf"
       
   print confurl    
   destinationfile = slicename+".stork.conf.unsigned"
   command = "/usr/bin/curl -w '%{http_code}' -k -o "+destinationfile+" "+confurl
  
   if os.path.isfile(destinationfile):
   	os.remove(destinationfile)
   req = Request(confurl,None,headers)
   handle = urlopen(req)
   newFile = open(destinationfile,"w")
   newFile.writelines(handle.read())
   newFile.close()
   newFile = open(destinationfile,"r")

 
   #print "DEBUG: about to run: ",command

   #(sin, sout, serr) = os.popen3( command )
   #outline = sout.read()
   #sout.close()
   #serr.close()

   if "not found on this server" in newFile:
      newFile.close()
      os.remove(destinationfile)
      return False
   else:
      return destinationfile



def clean_configuration(conffile):
   """
   Perform mandatory cleaning of the configuration file for proper
   functionality.
   
   """
   print conffile
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
   line = line[:line.find("#")]
   matches = configlineregex.match(line.strip())
   if matches:
       return matches.groups()
   else:
       return None
