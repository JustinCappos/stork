#!/usr/bin/env python

#           [option, long option,                    variable,            action,        data,     default,                            metavar,    description]
"""arizonaconfig
   options=[   
            ["",   "--managerconf",        "managerconf",        "store",    "string",    "~/.storkmanager.conf",               "FILE",      "use a different config file (~/.storkmanager.conf is the default)"],
            ["",   "--repositoryhost",     "repositoryhost",     "store",    "string",    "stork-repository.cs.arizona.edu",    "FILE",      "use a different repository (among other repository settings) (stork-repository.cs.arizona.edu is the default)"], 
            ["",   "--curlpath",           "curlpath",           "store",    "string",    "/usr/bin/curl",                      "FILE",      "the path to the curl executable (/usr/bin/curl is the default)"]
   ]
   includes=[]        
"""


from Tkinter import *
from tkMessageBox import *
from Tkinter import _setit
import tkFileDialog
import tkFont
import os
import shutil
import sys
import re
import webbrowser

import storkcurlfuncs as sc
import arizonaconfig
import arizonacrypt
import arizonageneral
import arizonareport
import storkpackage
import storkpackagelist
import storkusername as storkusernamepackage
import storkutil
import planetlabAPI



#the version of the gui, this number should be incremented
#whenever there is a change to this file, or a change to 
guiversion = "$Revision: 1.28 $"

checkedforupdate = False

repository = None

debug = False

groupframes = {} 
groups = []
nodes  = {} #a dict of groupname->array of nodes          
actions= {}
to_upload=[]

next_group_row = 0
switch_user = False

# whether the current state is in synch with the repository
synched = True

root = None

topoptions = None
username = None
password = None
#poor choice of name for storkusername variable as it conflicts with the module of the same name
storkusername = None
privatekey = None
publickey = None
slicekeys = None

# copies of these files that are are signed by the key the user selected
# these will be updated from the repository when a slice is selected
localconffile = None
localtpfile = None
localpackagesfile = None
localgroupsfile = None

# copies of the files that are the extracted versions of these files
unsignedconffile = None
unsignedtpfile = None
unsignedpackagesfile = None
unsignedgroupsfile = None

# Flags that will always be passed to storkutil to identify this user. 
# This gets set later, don't add extra flags to this here.
storkutiluserflags = None

# The directory the script is located in.
scriptpath = os.path.realpath(os.path.dirname(sys.argv[0]))

# Path to images used by the GUI.
imagepath = os.path.join(scriptpath, "images")

# filename of the gui config file
config_fn = os.path.expanduser("~/.storkmanager.conf")

# Path to where all non-temp files that are read and created.
# Note: not fully implemented yet. Leave empty to have it be ignored.
# The idea would be to make setting/changing the working directory
# available through the GUI, but this works for testing.
# Example:
#workingpath = "/home/myusername/somedirectory";
#workingpath = "/home/justin/school/research/stork/9-test"
workingpath = ""
commandstub = ""

# Change working directory so files are read from and created there.
# This would be done somewhere else once one can set this from the GUI.
if workingpath:
    arizonareport.send_out(2, "Changing working directory to: "+workingpath)
    os.chdir(workingpath)


# Change the commands for different OS
#HOME is for Linux. Command should be '../storkutil.py' For windows, 
#it is simply 'storkutil.py'
if 'HOME' in os.environ:
    commandstub = '/'


def runCommand(command, stdin_string=None):
    """Executes a shell command.
    
    command:      the shell command to execute
    stdin_string: Optional string containing data to be sent to the command
                  through stdin.
                  
    returns a tuple of (stdout_sl, stderr_sl) 
    """
    arizonareport.send_out(2, "About to run command: " + str(command))
    (the_in, the_out, the_err) = os.popen3(command)
    
    if stdin_string != None:
        the_in.write(stdin_string)
    the_in.close()

    out_sl = arizonageneral.stream_to_sl(the_out)
    the_out.close()

    err_sl = arizonageneral.stream_to_sl(the_err)
    the_err.close()

    arizonareport.send_out(4, "   Last command stdout: " + str(out_sl))
    arizonareport.send_out(4, "   Last command stderr: " + str(err_sl))
    
    return out_sl, err_sl


class StorkGuiException(Exception):
    """Just a quick way to stop using generic exceptions until something better
       is setup for stork exceptions.
    """
    pass


def extractSignedFile(signedfile, extractedfile):
    """Extracts the original file from an signed file.
       
       signedfile: the signed file
       extractedfile: the file where the extracted contents should be saved
    """
    
    global storkutiluserflags
    
    command = scriptpath+commandstub+'storkutil.py extract '+signedfile+' '+extractedfile
    runCommand(command)


def signFile(file):
    """Signs file with the user's key."""
    
    global storkutiluserflags
    
    command = scriptpath+commandstub+'storkutil.py '+storkutiluserflags
    if privatekey.password != None:
       command += " --privatekeypasslocation=stdin "
    command += ' sign '+file
    (out_sl, err_sl) = runCommand(command, privatekey.password)
    
    
def copyFile(src, dst):
    """Copies src to dst, overwriting dst if it exists."""
    
    if os.path.exists(dst):
        os.remove(dst)
    shutil.copy(src, dst)


def removeFile(file):
    """Removes file if it exists."""
    
    if file and os.path.exists(file):
        os.remove(file)


def cleanUpFiles():
    """Cleans up files the GUI created in the working directory."""

    candidates = [localconffile,
                  localtpfile,
                  localpackagesfile,
                  localgroupsfile,
                  unsignedconffile,
                  unsignedtpfile,
                  unsignedpackagesfile,
                  unsignedgroupsfile,
                  "GetCookie"]
    
    for file in candidates:
        removeFile(file)


def createLocalFileFromRepoFile(filetype, repofile):
    """Given a filetype and a signed file from the repository that may be
       signed by a different user's key, creates an unsigned version of the
       file and a version signed by the current user's key.
       
       Returns a tuple of (path to unsigned file, path to signed file).
    """
    
    global storkusername
    global storkutiluserflags
    
    if filetype == 'packages':
        ext = ".packages.pacman"
    elif filetype == 'groups':
        ext = ".groups.pacman"
    elif filetype == 'tpfile':
        ext = ".tpfile"
    elif filetype == 'conf':
        ext = ".stork.conf"
    else:
        raise StorkGuiException, "Unable to create local file from repo file: uknown filetype"
        
    # define the filesnames of the unsigned and signed files
    unsignedfile = storkusername+ext
    signedfile = storkusername+"."+getPubKeyHash()+ext
    
    # extract the repofile, which may be signed by someone else's key
    extractSignedFile(repofile, unsignedfile)
    
    # copy the unsigned file to the location of the signed file
    copyFile(unsignedfile, signedfile)
    
    # create the signed file that is signed by the current user's key
    signFile(signedfile)
    
    return (unsignedfile, signedfile)
    

def isPackage(path):
   """Decides if path is the path to a valid package, checking only its
      file extension for a match with ["tar", "tgz", "tbz","rpm"]."""
      
   # lets try not to tar or rpm in case they are on windows,
   # so we will do 'dummy' checking by filename
   base = os.path.basename(path)
   for foo in ["tar", "tgz", "tbz","rpm"]:
      if foo in base: return True

   return False


def trustPackage(path):
   """Calls storkutil.py addfile ..."""
   
   if not os.path.isfile(path):
      return
   command = scriptpath+'/storkutil.py '+storkutiluserflags
   if privatekey.password != None:
      command += " --privatekeypasslocation=stdin "
   command += ' addfile '+path
   (out_sl, err_sl) = runCommand(command, privatekey.password)
   

def removeTrust(file):
   """Calls storkutil.py removefile ..."""
    
   command = scriptpath+'/storkutil.py '+storkutiluserflags
   if privatekey.password != None:
      command += " --privatekeypasslocation=stdin "
   command += ' removefile '+file
   (out_sl, err_sl) = runCommand(command, privatekey.password)


def uploadPackage(path):
   global repository
   metahash = storkpackage.get_package_metadata_hash(path)
   if not sc.url_exists("metadata/"+repository+"_packages_PlanetLab_V3_Testing/"+str(metahash) ):
      # sense it does not already seem to be on the repository, upload it
      sc.upload_file(username, password, path, "package")
   else:
      print "debug: "+path+" exists on server, not uploading"  


#def makeKey(user):
#   """Generates a keypair for the user using storkutil.py genpair.
#      This isn't used anymore since the change was made to have planetlab keys used
#      rather than dedicated stork keys.
#   """
#   
#   command = scriptpath+commandstub+'storkutil.py --dontask --username='+user+' genpair '+user
#   runCommand(command)
#   # If statusframe is defined, then the main window is open and we want to
#   # change the syched state. Otherwise, we just want to flag that when the
#   # main window opens it should not show as synched.
#   global statusframe
#   try:
#       statusframe
#   except NameError:
#       global synched
#       synched = False
#   else:
#       statusframe.set_in_synch(False)


def getPubKeyHash():
    """Returns the hash of the GUI user's public key."""
    global publickey
    return publickey.hash
  

def getGroups():
   """Returns a list of group names that exist based upon the current groups file.
   """
   # parsing xml by hand not so good, using something like xml.dom.minidom would
   # be much better
    
   # because of the way it's written not using proper xml processing, and I don't feel
   # like fixing it right now, just going to stick with having it process the signed
   # files
   #global unsignedgroupsfile
   #global unsignedpackagesfile
   global localgroupsfile
   global localpackagesfile
   
   grps = []
   grps.append("All")
   if not localgroupsfile or not os.path.isfile(localgroupsfile):
      arizonareport.send_out(2, "No groups file found. No groups will be added.")
   else:
      groupFile = open(localgroupsfile)
      for line in groupFile:
           if line.find("GROUP NAME") != -1:
               groupname = line[16:-6]
               grps.append(groupname)
   # get empty groups that have something set for them in the packages file
   if localpackagesfile and os.path.isfile(localpackagesfile):
       packagesFile = open(localpackagesfile)
       regex = re.compile(r'CONFIG GROUP="(.+?)"')
       for line in packagesFile:
           matches = regex.search(line)
           if matches and matches.group(1) not in grps:
               grps.append(matches.group(1))
   return grps


def getNodes(group):
    """Returns a list of nodes in the group specified, according to the current
       groups file.
    """
    # parsing xml by hand not so good, using something like xml.dom.minidom would
    # be much better
    
    # because of the way it's written not using proper xml processing, and I don't feel
    # like fixing it right now, just going to stick with having it process the signed
    # file
    #global unsignedgroupsfile
    global localgroupsfile
    arizonareport.send_out(4, "Getting nodes for group: " + str(group))
  
    nodeList = []
    if not localgroupsfile or not os.path.isfile(localgroupsfile):
        arizonareport.send_out(2, "Nothing added to nodelist because there is no groups file to read from.")
        return nodeList
    else:
        groupFile = open(localgroupsfile)
   	
    groupstarted = False
    
    for line in groupFile:
        arizonareport.send_out(4, "Current line of groups file: " + str(line).strip())

        # the group is already started and we hit another group, so we're done with the file
        if groupstarted == True and line.find("GROUP") != -1:
            break
        
        # check if this is the start of the group
        if line.find("\""+group+"\"") != -1:
            arizonareport.send_out(4, "Found group " + str(group) + " in groups file.")
            groupstarted = True
            continue
        
        # we haven't found the group yet and we didn't find it on this line, so the contents
        # of this line don't matter
        if groupstarted == False:
            continue
        
        # at this 
        if line.find("INCLUDE") != -1:
            arizonareport.send_out(3, "About to append: "+ str(line[18:-7]) + " to " + str(group))
            nodeList.append(line[18:-7])

    return nodeList


def getSlices():
   """Returns a list of slices that this user has access to, or for some odd reason
      a list containing a single string that says 'Could not fetch slices'.
   """
   
   if debug: return ["arizona_client1"]

   slices = sc.getslices()
   if slices == None:
      return ["Could not fetch slices"]
   else:
      return slices


def getSliceKeys(slicename):
    """Ensures that storkusername's key database is using the keys for 
       slicename.
    """
    
    storkusernamepackage.reset_key_database()
    storkusernamepackage.get_planetlab_publickeys(slicename)


def getActions(group):
   """Returns a list of ??? that has info on the actions (what to install, upgrade, etc.)
      that the GUI should display, based upon the current configuration files.
   """
   
   # parsing xml by hand not so good, using something like xml.dom.minidom would
   # be much better
   
   # because of the way it's written not using proper xml processing, and I don't feel
   # like fixing it right now, just going to stick with having it process the signed
   # file
   #global unsignedpackagesfile
   global localpackagesfile
   
   #Provides tuples of the form (action, package) for the provided group name. actions will be the returned
   #list of tuples, curAct is the current action that needs to be tuplified, preLen is used to parse the 
   #package name from the line
   actions = []
   curAct = ""
   if not localpackagesfile or not os.path.isfile(localpackagesfile):
   	return actions
   else:
        try:
           actionsFile = open(localpackagesfile, "r")
        except:
           return actions
           	
	while(True): #Loop through each line of the packages file
		outerLine = actionsFile.readline()
   		
   		if group == "All":
   			if outerLine.find("CONFIG&gt;") != -1:
   				while(True):
   					innerLine = actionsFile.readline()
   					if innerLine.find("/CONFIG") == -1:
 						if innerLine.find("PACKAGE") != -1:
							if innerLine.find("INSTALL") != -1:
								curAct = "install"
								preLen = 21
							elif innerLine.find("UPDATE") != -1:
								curAct = "update"
								preLen = 20
							elif innerLine.find("REMOVE") != -1:
								curAct = "remove"
								preLen = 20
							curPack = innerLine[preLen:-7]
							actions.append( (curPack, curAct) )
					else:
						break #If we looped through the whole group, stop
				break #If we find the group, stop looping through the file
			if outerLine == "":
				break  						

   		else: #The case where the group IS NOT "All"
			if outerLine.find("CONFIG GROUP=\""+group+"\"") != -1:
				while(True):
					innerLine = actionsFile.readline()
					if innerLine.find("/CONFIG") == -1:
						if innerLine.find("PACKAGE") != -1:
							if innerLine.find("INSTALL") != -1:
								curAct = "install"
								preLen = 21
							elif innerLine.find("UPDATE") != -1:
								curAct = "update"
								preLen = 20
							elif innerLine.find("REMOVE") != -1:
								curAct = "remove"
								preLen = 20
							curPack = innerLine[preLen:-7]
							actions.append( (curPack, curAct) )
					else:
						break #If we looped through the whole group, stop
				break #If we find the group, stop looping through the file
			if outerLine == "":
				break
	actionsFile.close()
	return actions


def createFiles():
    """
	<Purpose>
	Creates pacman files, tpfile, config file and list of packages for upload.

	<Arguments>   
	None

	<Exceptions>
	None

	<Side Effects>
	Deletes and rebuilds the aforementioned files

	<Returns>
	None

	Note: This function is currently done by simply invoking storkutil.py with the appropriate command
	line commands. This can be cleaned up by replacing the "if args=..." statements in storkutil with 
	functions. If this is done, this section will need to be modified.
    """
    
    global localconffile
    global localtpfile
    global localpackagesfile
    global localgroupsfile
    
    global unsignedconffile
    
    global privatekey
    global publickey
   
    if localgroupsfile and os.path.isfile(localgroupsfile):
    	os.remove(localgroupsfile)
    for gp in nodes:
    	nodelist = ''
    	for nd in nodes[gp]:
    		nodelist += nd+' '
    	if nodelist != '':
            command = scriptpath+'/storkutil.py '
            if privatekey.password != None:
               command += " --privatekeypasslocation=stdin "
            # the "--privatekeypasslocation=stdin" has to be at least before "pacgroups" (I think)
            command += storkutiluserflags+' pacgroups include '+"'"+gp+"'"+' '+nodelist
            (out_sl, err_sl) = runCommand(command, privatekey.password)

    localgroupsfile = storkusername+"."+getPubKeyHash()+".groups.pacman"
    
    #Create pacpackages file
    if localpackagesfile and os.path.isfile(localpackagesfile):	
        os.remove(localpackagesfile)
    for gp in actions:
        for act in actions[gp]:
            if(gp == 'All'):
                command = scriptpath+'/storkutil.py '+storkutiluserflags
                if privatekey.password != None:
                   command += " --privatekeypasslocation=stdin "
                command += ' pacpackages all '+act[1]+' '+act[0]
                (out_sl, err_sl) = runCommand(command, privatekey.password)
                
            else:
                command = scriptpath+'/storkutil.py '+storkutiluserflags
                if privatekey.password != None:
                   command += " --privatekeypasslocation=stdin "
                command += ' pacpackages group '+"'"+gp+"'"+' '+act[1]+' '+act[0]
                (out_sl, err_sl) = runCommand(command, privatekey.password)
                
	localpackagesfile = storkusername+"."+getPubKeyHash()+".packages.pacman"
        
	#Create a tpfile if one doesn't exist
    if not localtpfile:
        #storkutil.makeTPFile(storkusername, False)
        storkutil.makeTPFile(storkusername, True) # createblank set to True for testing no default key trusted
        arizonacrypt.XML_sign_file_using_privatekey_fn(storkusername+'.tpfile', privatekey.file, privatekey.password)
        storkutil.pubKeyEmbed(storkusername+'.tpfile', publickey.file)
        os.remove(storkusername+'.tpfile')
        localtpfile = storkusername+'.'+getPubKeyHash()+'.tpfile'
    
    # download a fresh config file if we don't have any at all
    if not unsignedconffile:
       localconffile = sc.fetch_configuration(topoptions.get_slice(), defaultconf=True)
       if not localconffile:
           #arizonareport.send_out(2, "Could not fetch default configuration file.")
           raise StorkGuiException, " Could not fetch a configuration file, even a default one."
       extractSignedFile(localconffile, unsignedconffile)
        
    # change the configuration file
    #pubkey (last argument) probably isn't needed to be passed along anymore, alter_configuration will need to have signature changed
    if not sc.alter_configuration(unsignedconffile, storkusername, "", True):
        arizonareport.send_error(1, "[ERROR] There was an error changing the configuration file.")
       #if we are about to change some values then
       #warn the user here with a pop-up, and ask them wether to try again, this time overwriting
       #any values

#       (susername, pk) = sc.parse_config(localconffile)
#       if susername == None: susername = "unknown"
#       #if pk       == None: pk       = "unknown"
#       
#       # the key is only being compared in name
#       #if susername == 'default' and pk == 'default.publickey':
#       if susername == 'default':
#           changeidentity = True
#       elif storkusername != susername:
#           changeidentity = askyesno('Verify', "Slice '"+topoptions.get_slice()+"' \nis currently managed by \nuser '"+susername+"'.\n\nDo you want to change it to your current user '"+storkusername+"'?")
#       #else:
#       #    changeidentity = askyesno('Verify', "Slice '"+topoptions.get_slice()+"' \ncurrently uses public key '"+pk+"'.\n\nDo you want to change it to your current public key '"+pubkey+"'?") 
#       if changeidentity:
#          #pubkey (3rd argument) probably isn't needed to be passed along anymore, alter_configuration will need to have signature changed
#          if not sc.alter_configuration(localconffile, storkusername, "", True):
#              arizonareport.send_error(1, "[ERROR] There was an error changing the configuration file.")

    # clean up and make any other required changes to the configuration file
    if not sc.clean_configuration(unsignedconffile):
        arizonareport.send_error(1, "[ERROR] There was an error cleaning the configuration file.")
        
    # create a signed conf file
    localconffile = createSignedConfFile(unsignedconffile)
        
    # upload files
    if not debug:
       showwarning("About to upload new files", "About to upload new files to the repository. This may take a while. During the upload, the GUI will be unresponsive.")
       sc.upload_file(username, password, localgroupsfile, "pacman")
       sc.upload_file(username, password, localpackagesfile, "pacman")
       sc.upload_file(username, password, localtpfile, "tp")
       sc.upload_file(username, password, localconffile, "conf", topoptions.get_slice())

       # upload any packages we need to
       if len(to_upload) > 0:
           short = []
           for foo in to_upload: 
              short.append( os.path.basename(foo) )
           for foo in to_upload:
              uploadPackage(foo)

       # call the auto update page with a list of all the possible nodes to add to this slice
       nodestoadd = []
       for group in groups:
          for node in nodes[group]:
             if node not in nodestoadd:
                nodestoadd.append(node)

       sc.autoSetup(username,password,topoptions.get_slice(),nodestoadd,wheretologin); 


nodes["All"] = []
actions["All"] = []


def setSlice(slicename):
    """This is called when the user selects a slice in the GUI's dropdown menu. This
       will make sure everything that needs to be changed is changed. Currently
       it will set the 'username' arizonaconfig option, change the flags we pass
       to all of the storkutil command line calls made here within this module,
       and update the keys that are considered administrator keys for the slice.
    """
    
    global storkusername
    global storkutiluserflags
    global publickey
    global privatekey
    
    arizonareport.send_out(3, "Setting slice to: " + str(storkusername))
    storkusername = slicename
    arizonaconfig.set_option("username", storkusername)
    storkutiluserflags = '--username='+storkusername+' --publickey='+publickey.file+' --privatekey='+privatekey.file
    
    # update the keys we consider administrators for the slice
    getSliceKeys(slicename)


def updateFromRepository():
     """Downloads all of the latest files from the repository.
        We'll need these files to determine which tpfile and pacman files to use.
     """
   
     global localconffile
     global localtpfile
     global localpackagesfile
     global localgroupsfile
    
     global unsignedconffile
     global unsignedtpfile
     global unsignedpackagesfile
     global unsignedgroupsfile

     # clear the key database as its old value will be reused if we don't
     storkusernamepackage.reset_key_database()

     # clear what is displayed in the gui
     depopulate()
     
     # make sure the latest files are downloaded from the repository
     storkpackagelist.init()
   
     # for each type of file, find the latest in the repository that is signed
     # by an administrator of this slice
     result = storkpackagelist.find_file_kind("pacman", "packages.pacman")
     if result and result[0] != None:
         (unsignedpackagesfile, localpackagesfile) = createLocalFileFromRepoFile("packages", result[0])
     else:
         (unsignedpackagesfile, localpackagesfile) = (None, None)
         
     result = storkpackagelist.find_file_kind("pacman", "groups.pacman")
     if result and result[0] != None:
         (unsignedgroupsfile, localgroupsfile) = createLocalFileFromRepoFile("groups", result[0])
     else:
         (unsignedgroupsfile, localgroupsfile) = (None, None)
         
     result = storkpackagelist.find_file_kind("tpfiles", "tpfile")
     if result and result[0] != None:
         (unsignedtpfile, localtpfile) = createLocalFileFromRepoFile("tpfile", result[0])
     else:
         (unsignedtpfile, localtpfile) = (None, None)
         
     result = storkpackagelist.find_file_kind("conf", "stork.conf")
     if result and result[0] != None:
         (unsignedconffile, localconffile) = createLocalFileFromRepoFile("conf", result[0])
     else:
         (unsignedconffile, localconffile) = (None, None)
         
     # refresh what the gui displays
     populate()
     
     # we should be showing what's current in the repository at this point
     global statusframe
     statusframe.set_in_synch(True, upload_files=False)


def createSignedConfFile(unsigned_file):
    """Takes the to the unsigned file and creates a file in the current directory
       called [storkusername].[pubkeyhash].stork.conf that is a signed version of
       the same file.
    """
    
    global storkusername
    global publickey
    signed_file = storkusername + "." + publickey.hash + ".stork.conf"

    copyFile(unsigned_file, signed_file)
    signFile(signed_file)
    
    #TODO should check if error occurrsed in signing
    
    return signed_file


def depopulate():

     global topblock
     topblock.remove_all_groups()


def populate():

     #initialize the nodes/groups/packages
     global groups
     global nodes
     global actions
     global topblock
     global frm
     
     groups = getGroups()
     for group in groups:
        nodes[group] = getNodes(group)
        actions[group] = getActions(group)

     group = Group(frm, "All", topblock)
     group.grid(pady=3, columnspan=2, sticky=NW)
     groupframes["All"] = group
    
     for groupname in groups:
        if groupname == "All": continue
        group = Group(frm, groupname, topblock)
        group.config(relief=GROOVE)
        group.grid(pady=3,columnspan=2, sticky=NW) 
        groupframes[groupname] = group
    
     groups.append("All")


class StatusFrame(Frame):
    
   def __init__(self, parent=None):
      Frame.__init__(self, parent)
      self.parent = parent

      self.goodimage = PhotoImage(file=os.path.join(imagepath, "in-synch-1.gif"))   
      #self.badimage  = PhotoImage(file=os.path.join(imagepath, "out-of-synch-1.gif"))   
      self.upload    = PhotoImage(file=os.path.join(imagepath, "upload-1.gif"))   

      self.helv36 = tkFont.Font ( family="Helvetica",\
        size=14, weight="bold" )

      self.helv10 = tkFont.Font ( family="Helvetica",\
        size=10 )

      self.helv9 = tkFont.Font ( family="Helvetica",\
        size=9, )

      self.linktext = tkFont.Font ( family="Helvetica",\
        size=9, underline=1, weight=tkFont.BOLD)

      self.statusimage = Label(self, image=self.goodimage)

      self.statustext  = Label(self, text="In synch with repository.")
      self.uploadtext  = Label(self, text="Files added or changed.\nSynch with repository.", fg="blue")
      self.uploadimage = Button(self, image=self.upload, command=lambda: self.set_in_synch(True) )

      #self.statusimage.bind("<Button-1>", lambda event: self.set_in_synch(False) )
      self.uploadtext.bind("<Button-1>", lambda event: self.set_in_synch(True))
      
      global synched
      if synched:
          self.statustext.grid(row=1, column=0, sticky=E)
          self.statusimage.grid(row=1, column=1, sticky=E)
      else:
         self.uploadtext.grid(row=0, column=0, sticky=E)
         self.uploadimage.grid(row=0, column=1, sticky=E) 


   def set_in_synch(self, new_synched_status, upload_files=True):
      global synched
      if new_synched_status:
         # if already synched, let user know no synch necessary
         if synched == True and upload_files:
            showwarning("No synch necessary", "You are already synched with the repository.")
         else:
            if not topoptions.get_slice() and upload_files:
               showwarning("Select slice", "You must select a slice before synchronizing with the repository.")
               return
            if upload_files:
                createFiles()
            self.uploadtext.grid_forget()
            self.uploadimage.grid_forget()
            self.statustext.grid(row=0, column=0, sticky=E)
            self.statusimage.grid(row=0, column=1, sticky=E)
      else:
         self.statustext.grid_forget()
         self.statusimage.grid_forget()
         self.uploadtext.grid(row=0, column=0, sticky=E)
         self.uploadimage.grid(row=0, column=1, sticky=E)
      synched = new_synched_status
     

class TopOptions(Frame):

   def __init__(self, parent=None, root=None):
      Frame.__init__(self, parent)
      self.root = root
      self.helv36 = tkFont.Font ( family="Helvetica",\
        size=14, weight="bold" )

      #self.userimage = PhotoImage(file=os.path.join(imagepath, "user-1.gif"))

      managingslice_label = Label(self, text="is managing") 
      self.username       = Label(self, text="",font=self.helv36)
      if username:
         self.username.config(text=username)

      self.username.bind("Button-1", lambda event: self.quit() )

      #self.changeframe = Frame(self)
      #self.changetext  = Label(self.changeframe, text="Switch User")
      #self.changeimage = Button(self.changeframe, image=self.userimage, command=self.switchuser)

      self.slicevar       = StringVar()
      self.slicemenu      = OptionMenu(self, self.slicevar, None)
      self.slicemenu["menu"].config(font=self.helv36)
      self.slicemenu["menu"].delete(0, END)
      
      slices = getSlices()
      #if len(slices)>0:
      #   self.slicevar.set(slices[0])
      self.selectsliceprompttext = "[select slice]"
      self.slicevar.set(self.selectsliceprompttext)
      
      def set_active_slice(who_knows_maybe_some_tkinter_thing):
         global synched
         global storkusername
         
         # check if they didn't actually change what was selected
         if storkusername == self.get_slice():
             return
         
         # if they have changes that will be lost, give them a chance to abort the change
         if synched or askokcancel("Change slice without synching?", "You have changes that are not synched with the repository. These changes will be lost if you change the slice right now. \n\nClick OK to change slice without synching.", default=CANCEL):
             setSlice(self.get_slice())
             updateFromRepository()
         else:
             # they decided not to change the slice, so set the select box back to what it was
             self.slicevar.set(storkusername)
      
      for slicename in slices:
         self.slicemenu["menu"].insert('end','command', label=slicename, command=_setit(self.slicevar, slicename, set_active_slice)) 
      
      self.username.grid(row=0, column=0, sticky=W)
      managingslice_label.grid(row=0, column=1, sticky=E)
      self.slicemenu.grid(row=0, column=2, sticky=W)
      #self.changetext.grid(row=0, column=0,sticky=W)
      #self.changeimage.grid(row=0, column=1) 
      #self.changeframe.grid(row=1, column=2, sticky=E)

   
   def get_slice(self):
      """Returns the name of the slice that is currently selected in the dropdown
         menu, or None if no slice is selected.
      """
      if self.slicevar.get() == self.selectsliceprompttext:
          return None
      else:
          return self.slicevar.get()


   #def switchuser(self):
   #   """Supposed clear all state and reset the application. This never really worked
   #      and I think it's a bit useless compared with other more pressing needs and
   #      the importance of a bug-free gui, so removed by jsamuel."""
   #      
   #   global statusframe
   #   statusframe.set_in_synch(False)
   #   #TODO -actually clear the state out
   #   global switch_user
   #   switch_user = True
   #   arizonareport.send_out(4, "About to switch user to: " + str(switch_user))
   #   close_window_callback()


class TopBlock(Frame):
   def __init__(self, parent=None):
      Frame.__init__(self, parent)
      self.parent=parent
      self.linktext = tkFont.Font ( family="Helvetica",\
        size=9, underline=1, weight=tkFont.BOLD)
      self.helv10 = tkFont.Font ( family="Helvetica",\
        size=10, weight="bold" )

      self.var = StringVar()

      #addnew   = Label(self, text="Add/Remove group: ")
      self.newfield = Entry(self, textvariable=self.var)
      self.add_group= Button(self, text="Ok", font=self.helv10, command=self.add_group )
      self.cancel   = Button(self, text="Cancel", font=self.helv10, command=self.hide_addfields)
      self.newfield.bind("<Return>", lambda event: self.add_group.invoke() )

      self.addgroup_label = Label(self, text="add group", font=self.linktext, fg="blue", cursor="hand2")
      self.addgroup_label.bind("<Button-1>", lambda event: self.show_addfields() )
      self.addgroup_label.grid(column=0, row=0, sticky=NW) 


   def hide_addfields(self):
      self.addgroup_label.grid(column=0, row=0, sticky=NW)
      self.newfield.grid_forget()
      self.add_group.grid_forget()
      self.cancel.grid_forget()


   def show_addfields(self):
      # only let them add groups if they have selected a slice
      # that is, when the gui first starts up no slice is selected, and it was easier
      # to do this then to try to make this only show up after they selected a slice
      global storkusername
      if not storkusername:
          showwarning("Please select a slice", "You must select a slice before you can add groups.")
          return
       
      self.addgroup_label.grid_forget()    
      self.newfield.grid(column=0, row=0, sticky=W)
      self.add_group.grid(column=1, row=0, sticky=W)
      self.cancel.grid(column=2, row=0, sticky=W)
      self.var.set("")
      self.newfield.focus()


   def add_group(self) :
      group = self.newfield.get().strip()
      if len(group) == 0: return
      if re.search(r"[^a-zA-Z0-9_-]", group):
          showwarning("Invalid group name", "Group names can only contain the characters a-z, A-Z, 0-9, underscores, and hyphens.")
          return

      if group not in groups:
         groups.append(group)
         nodes[group] = []
         actions[group] = []
         #create a new group
         newgroup = Group(self.parent, group, self)
         newgroup.grid(pady=3,columnspan=2, sticky=W)
         groupframes[group]=newgroup
         self.set_group(group)
         self.grid_forget()
         self.grid(column=0,pady=10, sticky=NW)
         global statusframe
         statusframe.set_in_synch(False)
         
      self.hide_addfields()


   def remove_group(self):
      if self.var.get() != None and self.var.get() != "":
         # make sure the thing we are trying to move actually exists
         toremove = self.var.get()
         if toremove not in groups: return

         # remove it
         groupframes[toremove].destroy()
         groups.remove(toremove)
         nodes[toremove] = []

         if len(groups) > 0:
            self.set_group( groups[-1] )
         else:
            self.set_group("")
            
         global statusframe
         statusframe.set_in_synch(False)


   def remove_all_groups(self):
       arizonareport.send_out(3, "Removing all groups.")
       while len(groups):
           arizonareport.send_out(4, "Removing group: " + str(groups[0]))
           self.set_group(groups[0])
           self.remove_group()


   def set_group(self, groupname):
      if groupname != None:
         self.var.set(groupname)


class Group(Frame):
    
   nodelist = [] 
   actions  = []
   removenow= (None, None) # the event handler for the node remove button will store its parameters in here
   tempfile = None

   def __init__(self, parent=None, groupname=None, top=None ):
      Frame.__init__(self, parent)
      self.collapsed=1
      self.top = top
      self.group_name = groupname
      self.next_action_row = 0
      self.config(bd=2, relief=RIDGE)
      
      self.ximage = PhotoImage(file=os.path.join(imagepath, "xbutton-1.gif"))   
      #self.addimage=PhotoImage(file=os.path.join(imagepath, "addbutton-1.gif"))

      self.helv36 = tkFont.Font ( family="Helvetica",\
        size=14, weight="bold" )

      self.helv10 = tkFont.Font ( family="Helvetica",\
        size=10 )

      self.helv9 = tkFont.Font ( family="Helvetica",\
        size=9, )

      self.linktext = tkFont.Font ( family="Helvetica",\
        size=9, underline=1, weight=tkFont.BOLD)


      nodelist = nodes[groupname]
      arizonareport.send_out(4, "nodelist for group " + str(groupname) + ": " +  str(nodelist))
      if nodelist != None:
         numnodes = str( len(nodelist) )
      else:
         nodelist = []
         numnodes = "0"

      actionlist = actions[groupname]
      arizonareport.send_out(4, "actionlist for group " + str(groupname) + ": " +  str(actionlist))
      if actionlist == None:
         actionlist = []
      

      if groupname == None:
         groupname = "None"

      group_label_frame = Frame(self)
      inner_group_label_frame = Frame(group_label_frame)
      group_label_frame.grid(row=0, column=0, rowspan=2,  sticky=NW)

     
      remove_group = Button(inner_group_label_frame, image=self.ximage,borderwidth=0, command=self.remove_group)
      self.group= Label(inner_group_label_frame, text=groupname+" ("+numnodes+")", width=30, anchor=W, font=self.helv36)
      if groupname == "All":
         self.group.config(text=groupname+" nodes")

      if groupname != "All":
         remove_group.grid(column=0, row=0, sticky=W)
      
      self.group.grid(column=1, row=0, sticky=W )

      inner_group_label_frame.grid(row=0, column=0, sticky=W)

      self.expandgroup = Label(group_label_frame, text="expand", font=self.linktext, fg="blue", cursor="hand2")
      if groupname != "All":
         self.expandgroup.grid(column=0, row=1, sticky=NW)
         self.expandgroup.bind('<Button-1>', self.expand_group) 

      #self.sbar = Scrollbar(self)
      #self.lbox = Listbox(self, height=5, width=40, relief=SUNKEN)
      self.lbox = Frame(group_label_frame, width=40, relief=GROOVE)

      #construct the box for adding new nodes
      self.addbox = Frame(group_label_frame, bg="#7AFFA4")
      self.add_label    = Label(self.addbox, text="Add:", font=self.helv10, bg="#7AFFA4")
      self.addmethodvar = StringVar()
      self.addmethodvar.set("single node")
      self.optionmenu = OptionMenu(self.addbox, self.addmethodvar, "single node", "CoMon query", "set operation")

      def onchange(name, index, mode):
         if self.addmethodvar.get() == "single node":
	    self.use_singlenode()
         elif self.addmethodvar.get() == "CoMon query":
            self.use_comon()
         elif self.addmethodvar.get() == "set operation":
            self.use_set()

      remember = self.addmethodvar.trace_variable('w', onchange)
      #self.optionmenu["menu"].config(command=onchange)

      self.singlenode_ex = Label(self.addbox, justify=LEFT,width=35,height=2, text="Type in the hostname of a node in \nthe box, ex: planetlab-1.cs.princeton.edu", font=self.helv9, bg="#7AFFA4")
      #self.comon_ex      = Label(self.addbox, justify=LEFT,width=50,height=3, text="Type in a well formed CoMon query to return a set of nodes. \nWARNING: the nodes returned from the query will \nreplace any nodes that are currently in this group.", font=self.helv9, bg="#7AFFA4")
      #self.set_ex        = Label(self.addbox, justify=LEFT,width=25,height=2, text="Union or Intersect this group \nwith another existing group.", font=self.helv9, bg="#7AFFA4")
      self.comon_ex      = Label(self.addbox, justify=LEFT,width=50,height=3, text="Comon support is currently not functional", font=self.helv9, bg="#666666")
      self.set_ex        = Label(self.addbox, justify=LEFT,width=50,height=3, text="Set support is currently not functional", font=self.helv9, bg="#666666")


      self.node_entry    = Entry(self.addbox, width=25 )
      self.node_label    = Label(self.addbox, text="Node:", font=self.helv10, bg="#7AFFA4")

      self.comon_query   = Text(self.addbox, height=4, width=30 , relief=SUNKEN)
      self.comon_label   = Label(self.addbox, text="Query:", font=self.helv10, bg="#7AFFA4")

      self.set_label     = Label(self.addbox, text="Operation:", font=self.helv10, bg="#7AFFA4")
      self.set_option    = StringVar()
      self.set_option.set("intersect")
      self.set_menu      = OptionMenu(self.addbox, self.set_option, "intersect", "union")
      self.set_with      = Label(self.addbox, text="With", font=self.helv10, bg="#7AFFA4")
      self.set_groupvar   = StringVar()
      self.set_grouplist  = OptionMenu(self.addbox, self.set_groupvar, None)
      self.set_grouplist["menu"].delete(0, END)
      self.add_label.grid(row=0, column=0, sticky=NE)
      self.optionmenu.grid(row=0, column=1,sticky=NW)
      self.singlenode_ex.grid(row=1, column=1,sticky=NW)
      self.node_label.grid(row=2, column=0, sticky=NE)
      self.node_entry.grid(row=2, column=1, sticky=NW)

      self.node_buttons = Frame(self.addbox, bg="#7AFFA4")
      self.node_ok        = Button(self.node_buttons, text="Ok", font=self.helv9,  command=self.add_node)
      self.node_cancel    = Button(self.node_buttons, text="Cancel", font=self.helv9,  command=self.hide_addnodes)
      self.node_entry.bind("<Return>", lambda event: self.node_ok.invoke() ) 


      self.node_cancel.grid(row=0, column=0, sticky=NE)
      self.node_ok.grid(row=0, column=1, sticky=NE)
      self.node_buttons.grid(row=3, column=1, sticky=NE)
      
     
      self.addnode_label = Label(group_label_frame, text="add node(s)", font=self.linktext, fg="blue", cursor="hand2")
      self.addnode_label.bind("<Button-1>", lambda event: self.show_addnodes() )
      if groupname != "All":
         self.addnode_label.grid(row=3, column=0, sticky=NW)


      self.actionframe = Frame(self)
      self.action=Label(self.actionframe, text="Actions",width=38,anchor=W, font=self.helv36)
      self.action.grid(column=0, row=0,columnspan=2,  padx=1, sticky=NW)


      self.actionbox = Frame(self.actionframe, width=39, relief=SUNKEN)
      self.actionbox.grid( column=0, row=1, rowspan=1, sticky=NW )

      self.actionframe.grid(column=1, row=0, sticky=NW )

      for i,foo in enumerate(nodelist):
         n = Label(self.lbox,text=foo, font=self.helv9)
         x = Button(self.lbox, image=self.ximage, borderwidth=0 )
         x['command'] = lambda param=(x,n): self.remove_node(param)

         self.nodelist.append(n)
         x.grid(column=0, row=i, sticky=W, pady=0 ) 
         n.grid(column=1, row=i, sticky=W, pady=0 ) 

      for foo in actionlist:
         n = Label(self.actionbox, text="    "+foo[0]+" ("+foo[1]+")", font=self.helv9, anchor=W)
         x = Button(self.actionbox, image=self.ximage, borderwidth=0)
         x["command"]= lambda param=(n,x,foo): self.remove_action(param)
         self.actions.append(n)
         x.grid(column=0, row=self.next_action_row, padx=0,  sticky=NW)
         n.grid(column=1, row=self.next_action_row, padx=0,  sticky=NW)
         self.next_action_row += 1

      #create the addaction button
      self.add_action_area = Frame(self.actionbox, bg="#7AFFA4", relief=SUNKEN)
      self.add_action_label = Label( self.actionbox, text="add action", font=self.linktext, fg="blue", cursor="hand2")
      self.add_action_label.bind("<Button-1>", lambda event: self.show_actionbuttons() )

      self.action_explenation = Label( self.add_action_area,  text="Either type the name of a package in the text box\nor browse for a package on your filesystem.", font=self.helv9, fg="black", height=2, bg="#7AFFA4")

      self.var = StringVar()
      self.var.set("install")
      self.optionmenu = OptionMenu(self.add_action_area, self.var, "install", "update", "remove")


      self.action_var= StringVar()
      self.add_action= Entry(self.add_action_area,textvariable=self.action_var, width=22, relief=SUNKEN)
      self.add_action.bind("<Return>", lambda event: self.add_action_to_list() )
      self.browse    = Button(self.add_action_area,text="Browse...", font=self.helv10, command=self.browse_for_file)

      self.cancel    = Button(self.add_action_area,text="Cancel", font=self.helv10, command=lambda: self.hide_actionbuttons() )
      self.ok        = Button(self.add_action_area,text="Ok", font=self.helv10,command=lambda: self.add_action_to_list() )
      
      self.action_explenation.grid(column=0, row=0,columnspan=2,  sticky=NW)
      self.add_action.grid(column=0, row=2, sticky=NW)
      self.browse.grid(column=1,  row=2, sticky=NW)
      self.optionmenu.grid(column=0, row=3, sticky=NE)
      self.cancel.grid(column=0, row=4, sticky=NE)
      self.ok.grid(column=1, row=4, sticky=NW)
      
      self.add_action_label.grid(column=0, columnspan=2, sticky=W)


   def browse_for_file(self):
      filename = tkFileDialog.askopenfilename()
      if not filename: return
      if not isPackage(filename):
            showerror("Package not understood", "The package must be an rpm or a tar.")
            self.action_var.set("")
            return

      arizonareport.send_out(4, "Selected file: " + str(filename))
      if (self.var.get() == "update" or self.var.get() == "install") and os.path.isfile(filename):
         self.tempfile = filename
         self.action_var.set( os.path.basename( filename ) )


   def show_addnodes(self):
      self.addnode_label.grid_forget()
      self.addbox.grid(row=4,column=0, sticky=NW)
      self.addmethodvar.set("single node")
      self.node_entry.delete(0, len(self.node_entry.get()))
      #self.use_singlenode()


   def hide_addnodes(self):
      self.addbox.grid_forget()
      self.addnode_label.grid(row=3,column=0, sticky=NW)


   def use_singlenode(self):
      self.node_buttons.grid_forget()
      self.comon_ex.grid_forget()
      self.comon_label.grid_forget()
      self.comon_query.grid_forget()

      self.set_ex.grid_forget()
      self.set_label.grid_forget()
      self.set_menu.grid_forget()
      self.set_with.grid_forget()
      self.set_grouplist.grid_forget()     

      self.singlenode_ex.grid(row=1, column=1,sticky=NW)
      self.node_label.grid(row=2, column=0, sticky=NE)
      self.node_entry.grid(row=2, column=1, sticky=NW)
      self.node_cancel.grid(row=3, column=0, sticky=NE)
      self.node_ok.grid(row=3, column=1, sticky=NE)
      self.node_buttons.grid(row=3, column=1, sticky=NE)
      self.node_entry.focus() 
  
  
   def use_comon(self):
      self.node_buttons.grid_forget()
      self.singlenode_ex.grid_forget()
      self.node_label.grid_forget()
      self.node_entry.grid_forget()

      self.set_ex.grid_forget()
      self.set_label.grid_forget()
      self.set_menu.grid_forget()
      self.set_with.grid_forget()
      self.set_grouplist.grid_forget()     

      self.comon_ex.grid(row=1, column=1, sticky=NW)
      self.comon_label.grid(row=2, column=0, sticky=NE)
      self.comon_query.grid(row=2, column=1, sticky=NW)
      self.node_buttons.grid(row=3, column=1, sticky=NE)
      self.comon_query.focus()


   def use_set(self):
      self.node_buttons.grid_forget()
      self.singlenode_ex.grid_forget()
      self.node_label.grid_forget()
      self.node_entry.grid_forget()

      self.comon_ex.grid_forget()
      self.comon_label.grid_forget()
      self.comon_query.grid_forget()

      self.set_ex.grid(row=1, column=1,  sticky=NW)
      self.set_label.grid(row=2, column=0, sticky=NE)
      self.set_menu.grid(row=2, column=1,sticky=NW)
      self.set_with.grid(row=3, column=0, sticky=NE)
      self.set_grouplist.grid(row=3, column=1, sticky=NW)
      self.node_buttons.grid(row=4, column=1, sticky=NE)

      try:
         self.set_grouplist["menu"].delete(0,END)
      except: pass

      def nothing(junk): pass

      for foo in groups:
         if foo == 'All': continue
         if foo!=self.group_name:
            self.set_grouplist["menu"].insert('end','command', label=foo, command=_setit(self.set_groupvar, foo, nothing)) 
            self.set_groupvar.set(foo)
      
   

   def add_node(self):
      """this function will add a node to the current group,
         how that node or nodes is/are added depends on the
         method the user choose, eg: single node, comon, set op
      """
   
      method = self.addmethodvar.get()

      if method == "single node":
         node = self.node_entry.get().strip()
         if len(node) == 0: return
         # TODO separately check valid for hostname, IPv4, or IPv6
         if re.search(r"[^a-zA-Z0-9:.-]", node):
            showwarning("Invalid group name", "Node names can only contain the characters a-z, A-Z, 0-9, periods, hyphens, and colons.")
            return
         arizonareport.send_out(4, "About to add single node: " + str(node))
         if node != None and node != "" and node not in nodes[self.group_name]: 
            # add this node to the group
            i = len(nodes[self.group_name])
            nodes[self.group_name].append(node)

            n = Label(self.lbox,text=node, font=self.helv9)
            x = Button(self.lbox, image=self.ximage, borderwidth=0 )
            x['command'] = lambda param=(x,n): self.remove_node(param)
            
            self.nodelist.append(n)
            x.grid(column=0, row=i, sticky=W, pady=0 ) 
            n.grid(column=1, row=i, sticky=W, pady=0 ) 
            #update label
            self.group.config(text=self.group_name+" ("+str(len(nodes[self.group_name]))+")" )
            global statusframe
            statusframe.set_in_synch(False)

         pass #TODO stub
      elif method == "CoMon query":
         pass #TODO stub
      elif method == "set operation":
         pass #TODO stub

      self.hide_addnodes(); 


   def hide_actionbuttons(self):
      self.add_action_area.grid_forget()
      self.add_action_label.grid(column=0)

       
   def show_actionbuttons(self):
      self.add_action_label.grid_forget()
      self.add_action_area.grid(column=0, columnspan=2 )
      self.add_action.focus()
      self.add_action.delete(0, len(self.add_action.get()))


   def add_action_to_list(self):
       #param is (package, type)
       param = ( self.add_action.get().strip(), self.var.get() )
       if len(param[0]) == 0:
          return
       for existingparam in actions[self.group_name]:
          if param[0] == existingparam[0]:
             showwarning("Action already exists", "An action already exists for this package. To change the action for this package, remove the current action and then add the new one.")
             return
       if re.search(r"[^a-zA-Z0-9._-]", param[0]):
          showwarning("Invalid package name", "Package names can only contain the characters a-z, A-Z, 0-9, periods, underscores, and hyphens.")
          return
      
       arizonareport.send_out(3, "addactin param=" + str(param))
       arizonareport.send_out(4, "actions[self.group_name]: " + str(actions[self.group_name]))
       arizonareport.send_out(4, "going to add new action to row=" + str(self.next_action_row))

       n = Label(self.actionbox, text="    "+param[0]+" ("+param[1]+")", font=self.helv9)
       x = Button(self.actionbox, image=self.ximage, borderwidth=0)
       x["command"]= lambda param=(n,x,param): self.remove_action(param)
       self.actions.append(n)
       x.grid(column=0, row=self.next_action_row, sticky=NW)
       n.grid(column=1, row=self.next_action_row, sticky=NW)
       self.next_action_row += 1

       actions[self.group_name].append( param )
       self.hide_actionbuttons()
       global statusframe
       statusframe.set_in_synch(False)
    
       # see if we have to add this to the trusted packages file (that is,
       # if the user just selected a package on their file system
       if self.tempfile != None:
         global to_upload
         if self.tempfile not in to_upload:
            trustPackage(self.tempfile)
            to_upload.append(self.tempfile) 

       self.tempfile = None
       

   def remove_action(self, param):
      self.actions.remove(param[0])
      param[0].destroy()
      param[1].destroy()
      #TODO Error, the tuple is not being removed from the action list correctly
      arizonareport.send_out(3, "remove_action param=" + str(param))

      actiontuple = param[2]
      for foo in actions[self.group_name]:
         if foo[0] == actiontuple[0] and foo[1] == actiontuple[1]:
            arizonareport.send_out(4, "Removing action: " + str(foo))
            actions[self.group_name].remove(foo)
            global statusframe
            statusframe.set_in_synch(False)


   def remove_node(self, param):
      node = param[1]["text"]
      if node in nodes[self.group_name]:
         nodes[self.group_name].remove(node)
      param[0].destroy()
      param[1].grid_forget()
      param[1].destroy()
      self.group.config(text=self.group_name+" ("+str(len(nodes[self.group_name]))+")" )
      global statusframe
      statusframe.set_in_synch(False)
      
      
   def collapse_group(self, event):
      #do everything needed to make most items "hidden"
      if self.collapsed: return

      self.lbox.grid_forget()
      
      self.collapsed = 1       
      self.expandgroup.bind('<Button-1>', self.expand_group)
      self.expandgroup.config(text="expand") 
  

   def expand_group(self, event):
      #do everything needed to make things visible again
      if not self.collapsed: return

      self.lbox.grid( column=0, row=2, sticky='nw', pady=0 ) 

      self.collapsed = 0
      self.expandgroup.bind('<Button-1>', self.collapse_group )
      self.expandgroup.config(text="collapse")


   def remove_group(self):
      #TODO put hook into storkutil to remove this group
      groups.remove(self.group_name)
      nodes[self.group_name] = []
      self.destroy()
      global statusframe
      statusframe.set_in_synch(False)


def authenticate(username, password,site):
   """Attempt to login to the repository with the provided user/pass."""
   
   return sc.login(username, password,site)
 

# initially the user is not authenticated
authenticated = False

def makeloginwindow():
   """Displays the window that prompts for PL/repo login info and
      selection of private key file."""
      
   login = Tk()
   login.title('Stork Slice Manager')
   login.width=1100
   login.height=800
   helv10 = tkFont.Font ( family="Helvetica",\
        size=10, weight="bold" )
   
   text_content = "Please enter your Planetlab username and password. \n"
   text_content += "This information will only be transmitted over a secure connection \n"
   text_content += "and is needed to identify the slices you have access to.\n"
   text_content += "\n"
   text_content += "Your PlanetLab key is also needed in order to sign files that will be\n"
   text_content += "uploaded to the Stork repository."
   text_content += "\n"
   ex_label       = Label(login,width=60, height=8, justify=LEFT, text=text_content)

   username_label = Label(login,width=20,text="Planetlab Username:")
   password_label = Label(login,width=20,text="Planetlab Password:")
   storkusername_label = Label(login,width=20,text="Slice Name:")
   
   privatekeyfile_label = Label(login,width=20,text="Private key:")
   privatekeypassword_label = Label(login,width=20,text="Private key password:")

   wheretologin_label = Label(login,width=20,text="PlanetLab account type:")


   username_field = Entry(login)
   password_field = Entry(login, show="*")
   storkusername_field = Entry(login)
   wheretologin_field = Entry(login)
   wheretologin_field.insert(0,"www.planet-lab.org")

   def browse_for_key():
      """Opens a file selection dialog to allows user to select private key file."""
      
      filename = tkFileDialog.askopenfilename(title='Select your private key file...', initialdir=(os.path.expanduser('~/.ssh')))
      if not filename:
          return None
      arizonareport.send_out(3, "Selected privatekey: " + str(filename))
      privatekeyfile_var.set(filename)

   privatekeyfile_var = StringVar()
   privatekeyfile_field = Entry(login, textvariable=privatekeyfile_var, width=22, relief=SUNKEN)
   #privatekeyfile_field.bind("<Return>", lambda event: self.add_action_to_list() )
   privatekeyfile_browse = Button(login, text="Browse...", command=browse_for_key)
   
   privatekeypassword_field = Entry(login, show="*")


   def trylogin():
      """Attempt to login to planetlab with the provided login info, and also verify that
         the chosen private key file is a valid private key (and that the password for
         that key is valid, if necessary).
      
         This function will also use planetlabAPI.PlanetLablogin to ensure the user is
         authenticated with the PLC API, as planetlabAPI calls will later need to be
         made to get the keys for this user's slices.
      """
         
      global username
      global password
      global privatekey
      global publickey
      global slicekeys
      global wheretologin
      username = username_field.get().strip()
      password = password_field.get()
      privatekeyfile = privatekeyfile_var.get()
      privatekeypassword = privatekeypassword_field.get()
      wheretologin = wheretologin_field.get()
      if not privatekeypassword:
          privatekeypassword = None
      
      if len(username) == 0:
         ex_label.config(text="Please enter your PlanetLab username.", fg="red")
         return
      if len(password) == 0:
         ex_label.config(text="Please enter your PlanetLab password.", fg="red")
         return
      if len(privatekeyfile) == 0:
         ex_label.config(text="Please select your private key file.", fg="red")
         return
      privatekey = arizonacrypt.PrivateKey(file=privatekeyfile, password=privatekeypassword)
      if not privatekey.is_valid():
         ex_label.config(text="Invalid or encrypted private key.\nPlease reselect your private key or enter its password.", fg="red")
         return
      if wheretologin != "www.planet-lab.org" and wheretologin != "www.planet-lab.eu":
         ex_label.config(text="Invalid authentication site\nPlease use www.planetlab-org or www.planet-lab.eu", fg="red")
         return
      publickey = privatekey.get_public_key() # we can do this because we now know the privatekey is valid
      if authenticate(username, password,wheretologin):
         authenticated=True

         # user is now logged in and has a valid key
         
         # login to the PLC API so later usage of planetlabAPI with calls the require
         # being authenticated work (specifically, GetSliceKeys)
         planetlabAPI.PlanetLablogin(username, password, authsite=wheretologin)

         # this public key will get added to the key database in storkusername even
         # if this key isn't an administrator of a slice. This could result in differeng
         # files being loaded by the gui than would be used by stork
         #arizonaconfig.set_option("publickeyfile", publickey.file)
         #arizonaconfig.set_option("defaultplanetlabkeys", [publickey.string])

         # we don't know the slice name yet, so make this empty
         arizonaconfig.set_option("username", "")

         login.destroy()
      else:
         ex_label.config(text="Invalid username/password. Please try again", fg="red")

   button_frame   = Frame(login)
   ok_button      = Button(button_frame,text="Ok", command=trylogin)
   cancel_button  = Button(button_frame,text="Cancel",command=lambda: sys.exit(0) )
   cancel_button.grid(row=0, column=0, sticky=E)
   ok_button.grid(row=0, column=1, sticky=E)

   ex_label.grid(row=0, column=0, columnspan=2, sticky=NW)
   username_label.grid(row=1, column=0, sticky=W)
   username_field.grid(row=1, column=1, sticky=W)
   password_label.grid(row=2, column=0, sticky=W)
   password_field.grid(row=2, column=1, sticky=W)
   privatekeyfile_label.grid(row=3, column=0,sticky=W)
   privatekeyfile_field.grid(row=3, column=1,sticky=W)
   privatekeyfile_browse.grid(row=3, column=2,sticky=W)
   privatekeypassword_label.grid(row=4, column=0,sticky=W)
   privatekeypassword_field.grid(row=4, column=1,sticky=W)
   wheretologin_label.grid(row=5,column=0,sticky=W)
   wheretologin_field.grid(row=5,column=1,sticky=W)
   
   button_frame.grid(row=6, column=0, columnspan=2, sticky=E)

   username_field.bind("<Return>", lambda event: password_field.focus())
   password_field.bind("<Return>", lambda event: privatekeyfile_field.focus())
#   storkusername_field.bind("<Return>", lambda event: privatekeyfile_field.focus())
   privatekeyfile_field.bind("<Return>",lambda event: privatekeypassword_field.focus())
   privatekeypassword_field.bind("<Return>",lambda event: wheretologin_field.focus())
   wheretologin_field.bind("<Return>", lambda event: ok_button.invoke())
   username_field.focus()

   login.geometry("+%d+%d" % (300, 300))

   arizonareport.send_out(2, "Checking for GUI updates...")
   check_for_update()

   login.mainloop() 


def close_window_callback():
   """This function is called when the user attempts to exit out of the GUI.
      If the GUI isn't synced with the repo, the user will be warned.
   """

   global synched
   if synched or askokcancel("Exit without synching?", "You have changes that are not synched with the repository. These changes will be lost if you exit. \n\nClick OK to exit without synching.", default=CANCEL):
      global root
      root.destroy()
      cleanUpFiles()


def check_for_update():
   """Checks for a newer version of GUI-related files and, if any are found, asks
      the user if they want to update them. If files are updated, the GUI
      will close without restarting (user needs to manually restart).
   """
      
   global checkedforupdate
   if not checkedforupdate:
      uptodate, version, component = sc.is_latest_version(guiversion)

      if not uptodate and version != "unknown":
         showstring = "The "+str(component)+" module is currently at version \n"
         if component == "storkslicemanager":
	    showstring = showstring + guiversion
         elif component == "storkcurlfuncs": 
            showstring = showstring + sc.scversion

         showstring = showstring + "\nand can be autoupdated to\n"+version+"\n"
         showstring = showstring + "Would you like to update?\n"

         if askyesno("Out of date", showstring):
            sc.update_gui(scriptpath)

      checkedforupdate = True


def addOptionToConfigFileIfMissing(option, defaultvalue=None, comments=None):
    """Adds option to ~/.storkmanager.conf if it is missing from that file.
       If defaultvalue is supplied, the option will be added as:
           option = defaultvalue
       otherwise, a non-valued option will be added as:
           option
        
       Returns True if option was added, False if it already existed.
    """
    
    global config_fn
    
    configfile = file(config_fn, "r")
    optionexists = False
    for line in configfile:
        if line.find("#") != -1:
            line = line[:line.find("#")]
        line = line.strip()
        if line.find("=") == -1:
            currentoption = line
        else:
            configpair = sc.read_config_line(line)
            if configpair != None:
                currentoption = configpair[0]
            else:
                currentoption = ""
        # if currentoption == option, the option is already in the file so we're done
        if currentoption == option:
            configfile.close()
            return False

    # if we get to this point, then the option isn't in the file
    # append the option to the end of the file
    configfile.close()
    configfile = file(config_fn, "a")
    configfile.write("\n")
    if comments:
        for comment in comments:
            configfile.write("# " + comment + "\n")
    if defaultvalue != None:
        configfile.write(option + " = " + defaultvalue)
    else:
        configfile.write(option)
    
    return True


def main():
   # if the config file doesn't exist, create it
   global config_fn
   if not os.path.isfile(config_fn):
       configfile = file(config_fn, "w")
       configfile.write("# Set the verbosity.\n")
       configfile.write("# Options are: veryquiet, quiet, verbose, veryverbose, or ultraverbose\n")
       configfile.write("quiet\n")
       configfile.close()
       
#      try:
#         f = open( os.path.expanduser("~/.storkmanager.conf"), "w")
#         #TODO probably add other settings
#         f.write("localpackageinfo = /tmp/packageinfo\n")
#         f.write("tarpackinfo = /tmp/tarinfo\n")
#         f.write("keydir = /tmp/slicekeys\n")
#         f.write("metafilecachetime = 0\n\n")
#         f.write("# use the PLC API rather than the nodemanager to get slice keys.\n")
#         f.write("plckeysmethod = planetlabAPI\n")
#         f.write("# Set the verbosity.\n")
#         f.write("# Options are: veryquiet, quiet, verbose, veryverbose, or ultraverbose\n")
#         f.write("veryverbose\n\n")
#         f.write("# Configure the repository to use. See stork --help for more info.\n")
#         f.write("repositoryhost = stork-repository.cs.arizona.edu\n")
#         f.write("repositorypath = https://stork-repository.cs.arizona.edu/user-upload/\n")
#         f.write("repositorypackageinfo = stork-repository.cs.arizona.edu/packageinfo\n\n")
#         f.write("# Methods to use, in order of preference, to transfer files.\n")
#         f.write("transfermethod = coblitz,coral,http,ftp\n")
#         f.close()
#      except:
#         pass

   # for any required options that don't exist in ~/.storkmanager.conf, add them
   # to the file using the default values the gui should use
   options = []
   options.append(("localpackageinfo", "/tmp/packageinfo", ["Directory in which to store temporary files of package information."]))
   options.append(("tarpackinfo", "/tmp/tarinfo", ["Directory in which to store temporary archive files."]))
   options.append(("keydir", "/tmp/slicekeys", ["Directory in which to store temporary key files."]))
   options.append(("metafilecachetime", "0", ["How long to cache the metafile for. 0 is never."]))
   options.append(("plckeysmethod", "planetlabAPI", ["How to access slice keys."]))
   # too annoying to try to make this type of option work, so just making it written to the default file
   # and that's it. maybe a future world wouldn't have config options that don't have values and something
   # like ConfigParser could be used for much of this
   #options.append((["veryquiet","quiet","verbose","veryverbose","ultraverbose"], None, 
   #                 ["Set the verbosity.", "Options are: veryquiet, quiet, verbose, veryverbose, or ultraverbose"]))
   options.append(("repositoryhost", "stork-repository.cs.arizona.edu", ["Configure the repository to use. See stork --help for more info."]))
   #options.append(("repositorypath", "https://stork-repository.cs.arizona.edu/user-upload/", None))
   options.append(("repositorypackageinfo", "stork-repository.cs.arizona.edu/packageinfo", None))
   options.append(("transfermethod", "coblitz,coral,http,ftp", ["Methods to use, in order of preference, to download files from the repository."]))

   for (option, defaultvalue, comments) in options:
       addOptionToConfigFileIfMissing(option, defaultvalue=defaultvalue, comments=comments)

   # load the options, using the cobfug file
   arizonaconfig.init_options('storkslicemanager.py', usage="", configfile_optvar='managerconf', version='2.0')

   # if we can't find curl and we expect to use it, print a message and exit
   if not os.path.isfile(arizonaconfig.get_option("curlpath")) and 'HOME' in os.environ:
       arizonareport.send_error(0, "Could not find required curl executable at " + arizonaconfig.get_option("curlpath")
                                + "\nTo fix this, supply the proper --curlpath setting or set curlpath in "
                                + arizonaconfig.get_option("managerconf"))
       sys.exit(1)
   
   global repository
   repository = arizonaconfig.get_option("repositoryhost")
   sc.repository = "https://" + repository

   if not debug:
      makeloginwindow()
     
   global switch_user
   switch_user = False

   global root
   root = Tk()
   root.title('Stork Slice Manager')
   root.width=800
   root.height=600
   root.grid_propagate(True)

   #create main scrollable canvas
   cnv = Canvas(root, width=root.width-20, height=600)
   cnv.grid(row=0, column=0, sticky='nswe')
   vScroll = Scrollbar(root, orient=VERTICAL, command=cnv.yview)
   vScroll.grid(row=0, column=1, sticky='ns')
   cnv.configure(yscrollcommand=vScroll.set)
   #make a frame to put in the canvas
   global frm
   frm = Frame(cnv)
   #put the frame in the canvas's scrollable area
   cnv.create_window(0,0, window=frm, anchor='nw')

   global statusframe
   statusframe= StatusFrame(frm)

   global topblock
   topblock   = TopBlock(frm)

   global topoptions
   topoptions = TopOptions(frm,root)

   #groupframes.append(group)
   #group.config(bd=2, relief=GROOVE)
   
   # place it somewhere on the screen that makes sense
   #frm.geometry("%dx%d" % (300, 500) )
   root.geometry("%dx%d+%d+%d" % (800, 600, 50, 50))
   
   # setup some event handlers

   def somethinghappened(event):
      frm.update_idletasks()
      cnv.configure(scrollregion=(0, 0, frm.winfo_width(), frm.winfo_height()))

   def scrollDown(event):
      cnv.yview_scroll(2, 'units')
      
   def scrollUp(event):
      cnv.yview_scroll(-2, 'units')

   root.bind('<Button-4>', scrollUp)
   root.bind('<Button-5>', scrollDown)

   frm.bind("<Configure>", somethinghappened)

   frm.grid_propagate(True)
   frm.update_idletasks()
   cnv.configure(scrollregion=(0, 0, 800, frm.winfo_height()))

   
   topoptions.grid(pady=10,row=0, column=0, sticky=NW)
   statusframe.grid(pady=10,row=0,column=1, sticky=NW)
  
#   group = Group(frm, "All", topblock)
#   group.grid(pady=3, columnspan=2, sticky=NW)
#   groupframes["All"] = group
#
#   for foo in groups:
#      if foo == "All": continue
#      group = Group(frm, foo, topblock)
#      group.config(relief=GROOVE)
#      group.grid(pady=3,columnspan=2, sticky=NW) 
#      groupframes[foo] = group
#
#   groups.append("All")
#
#   if len(groups) > 0:
#      topblock.set_group( groups[-1] )  
 
   topblock.grid(pady=20, sticky=NW)
   
   # assign a callback function for when the user closes the window        
   root.protocol("WM_DELETE_WINDOW", close_window_callback)

   # setup the menu bar
   menubar = Menu(root)
   # File menu
   filemenu = Menu(menubar, tearoff=0)
   filemenu.add_command(label="Exit", command=close_window_callback)
   menubar.add_cascade(label="File", menu=filemenu)
   # User menu
#   usermenu = Menu(menubar, tearoff=0)
#   usermenu.add_command(label="Switch user", command=topoptions.switchuser)
#   menubar.add_cascade(label="User", menu=usermenu)
   # Repository menu
   repositorymenu = Menu(menubar, tearoff=0)
   repositorymenu.add_command(label="Synch with repository", command=lambda: statusframe.set_in_synch(True))
   menubar.add_cascade(label="Repository", menu=repositorymenu)
   # Help menu
   helpmenu = Menu(menubar, tearoff=0)
   helpmenu.add_command(label="Stork website", command=lambda: webbrowser.open("http://www.cs.arizona.edu/stork/"))
   helpmenu.add_command(label="Stork forum", command=lambda: webbrowser.open("http://cgi.cs.arizona.edu/projects/stork/forum/"))
   menubar.add_cascade(label="Help", menu=helpmenu)
   # display the menu
   root.config(menu=menubar)

   root.mainloop()


if __name__ == "__main__":

   while True:  
      main()
      arizonareport.send_out(2, "Exiting.")
      if not switch_user:
         break 
