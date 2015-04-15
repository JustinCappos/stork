#! /usr/bin/env python
"""
<Program Name>
   storkutil.py

<Started>
   November 21, 2005

<Author>
   Programmed by Justin Cappos.

<Purpose>
   General purpose actions that are useful for clients
"""

#           [option, long option,                    variable,            action,        data,     default,                            metavar,    description]
"""arizonaconfig
   options=[
            ["",   "--short",   "short",   "store_true", None,     False,     None,        "Print shorter help message"],
            ["",   "--dontask",   "dontask",   "store_true", None,     False,     None,        "Do not prompt for any questions. Assume 'yes' for everything."],
            ["",   "--no",        "no",        "store_true", None,     False,     None,        "Do not prompt for any questions. Assume 'no' for everything."],
            ["",   "--configurationfile",                 "configurationfile",        "store",       "string", "~/.storkutil.conf",                  "FILE",      "use a different config file (~/.storkutil/storkutil.conf is the default)"],
            ["-u", "--username",      "username",      "store", "string", "",      "USERNAME", "use this username for configuration files"],
            ["",   "--privatekey","tpprivatekey","store","string","","PRIVATEKEYLOCATION","The location of the private key to use."],
            ["",   "--privatekeypasslocation","privatekeypasslocation","store",     "string",    "",    "PRIVATEKEYPASSLOCATION",    "Where to get the private key passphrase from."],
            ["",   "--publickey","tppublickey","store","string","","PUBLICKEYLOCATION","The location of the public key to use."],
            ["",   "--tpfile","tpfileloc","store","string","","TPFILELOCATION","The location of the tpfile to use."],
            ["",   "--pacmanfile","pacfileloc","store","string","","PACMANFILE","The location of the pacman file to use."],
            ["",   "--storkutilsetupcomplete","storkutilsetupcomplete","store","string","False","TRUE/FALSE", "Whether the setup of this utility was completed properly."],
            ["",   "--timestamp",     "timestamp",     "store",      "string", "now",     "TIMESTAMP", "Timestamp for added package."],
            ["",   "--wrappertimestamp", "wrappertimestamp", "store","string", "now",     None,        "Timestamp to use in signature wrapper."],
            ["",   "--wrapperduration",  "wrapperduration",  "store","string", None,      None,        "Duration to use in signature wrapper."],
            ["",   "--orderby",       "orderby",       "store",      "string", "default", "ORDERBY",   "Method (default | timestamp) to prioritize packages in referenced trusted packages file."],
            ["",   "--createblank",   "createblank",   "store_true", None,     False,     None,        "Create a blank trusted packages or pacman files instead of the default"],
            ["",   "--baseurl",       "baseurl",       "store",      "string", None,      None,      "Base URL to use when creating .metadata files"],
            ["",   "--tags",          "tags",          "store",      "string", "",        None,        "Specify tags when adding package"]
           ]
   includes=[]        
"""

import os
import shutil
import sys
import re

import arizonaconfig
import arizonageneral
import arizonareport
import storkerror
import arizonacrypt
import arizonaxml
import storkpackage
import storkpackagelist
import time
import comonscript
import binascii


usage_message = """
storkutil [OPTIONS] keyword

related options:
(all of these options should be automatically defined inside the
  config file with the first use of the program.)
-u USERNAME, --username USERNAME
                            -- The username to use.  Unless specified explicitly,
                            locations of the keyfiles, trusted packages files,
                            and pacman files will be derived from this username.

--privatekey KEYFILENAME -- The explicit file that contains the private key
--privatekeypasslocation LOCATION -- Where to get the private key's password from (e.g. "stdin")
--publickey KEYFILENAME -- The explicit file that contains the public key
--tpfile TPFILENAME -- The explicit trusted packages file to use
--pacfile PACMANNAME -- The explicit pacman group/package file to use
--storkutilsetupcomplete TRUE/FALSE -- Using this option with the False setting
                                       will result in rerunning the initial
                                       setup.

keywords:
hash FILE                       -- lists the sha1 hash for a file
metahash PACKAGE                -- lists the sha1 hash for a package's metadata
signedhash FILE
                                -- lists the signed sha1 hash for a file using privkey
extractpub
                                -- extracts the public key from a private key
genpair PREFIX                  -- creates a public/private RSA pair named
                                    prefix.privatekey and prefix.publickey
setdefault PREFIX [PRIVATEKEY] [PUBLICKEY]
                                -- sets the default public/private RSA pair
sign FILE
                                -- sign the file using the privkey
verify FILE                     -- verify the signature of file using your publickey
extract FILE DESTFILE           -- extract the original data embedded in the signedfile
                                   file to destfile
pubkeyembed FILE
                                -- rename the file so that the publickey is embedded
                                    in the name
addfile FILE [FILE]...
                                -- allow file in the trustedpackages file
removefile FILE [FILE]...
                                -- remove the allow file lines for the specified files.
adduser USER USER.publickey (allow|deny|any) AFFECTEDPACKAGES
                                -- add the listed user to the trustedpackages file
removeuser USER
                                -- remove the specified user from the tpfile.
pacgroups (include|exclude|intersect|remove) GROUP NAME
                                -- change group definitions in a groups.pacman file
                                   to include or exclude a node or group
pacpackages (node|group|slice|all) [NAME] (install|remove|update) PACKAGE
                                -- change action definitions for nodes/group for use
                                   with stork package manager
view (tpfile|groups|packages)   -- display the contents of the trusted packages,
                                   pacman groups, or pacman packages file.
extractmeta --baseurl URL FILE [FILE] ...
                                -- extract the metadata from a package and
                                   generate a .metadata file. URL specifies the
                                   location where the stork client can download
                                   the package
comon (include|exclude|intersect|remove) GROUP \"STORKUTIL-QUERY\". 
                                -- queries storkutil through comon
                                   Make sure your query is surrounded 
                                   by quotation marks, or escape your 
                                   single &'s
pubkeyconvert sshfilein sslfileout 
                                -- convert a publickey from ssh format to ssl format

typical usage:

storkutil [options] addfile mypackage.rpm myotherpackage.rpm

  This will go through the setup options if no previous setup configuration
  is found.  It will also create the tpfile if no associated tpfile is found
  in the ~/.storkutil directory.  This will result in a single signed file in the
  storkutil directory with the new files added.

storkutil --username=MyUsername pacgroups include MyGroup MyNode

  This will create/modify the pacman group definitions that is associated with
  the user name specified under --username.  All files under the related username
  will be used (including the public key, the private key, and the
  MyUsername.groups.pacman file).  The result is a signed filed in the storkutil
  directory with the proper definition.
  """

short_message = """
storkutil [OPTIONS] keyword

Common Keywords:
extractpub
                                -- extracts the public key from a private key
genpair PREFIX                  -- creates a public/private RSA pair
sign FILE                       -- sign the file using the privkey
extract FILE DESTFILE           -- extract the original data embedded in the signedfile
                                   file to destfile
addfile(removefile) FILE [FILE]...
                                -- add/remove file in the trustedpackages file
adduser USER USER.publickey (allow|deny|any) AFFECTEDPACKAGES
                                -- add the listed user to the trustedpackages file
removeuser USER                 -- remove the specified user from the tpfile.
pacgroups (include|exclude|intersect|remove) GROUP NAME
                                -- Change groups in a groups.pacman file
pacpackages (node|group|all) [NAME] (install|remove|update|delete|clear) PACKAGE
                                -- Change actions in packages.pacman file
                                   (delete will remove the entry; clear will
                                   remove all entries in the group)
view (tpfile|groups|packages)   -- Display file contents

For a full listing of options and commands, use the option '--help'
"""






class StorkUtilArgumentError(Exception):
    """An error to be raised if there are invalid command line arguments."""
    pass


def getPrivateKeyPass():
    privatekeypasslocation = arizonaconfig.get_option("privatekeypasslocation")
    if not privatekeypasslocation:
        return None
    elif privatekeypasslocation == 'stdin':
        lines = sys.stdin.readlines()
        return lines[0]
    else:
        raise StorkUtilArgumentError, "Invalid value for --privatekeypasslocation."


privatekeypass = None


# Embed the public key  in a file
def pubKeyEmbed(fn, publickeyfn):
   #should now return the new filename
   # check the file arg for validity
   if not arizonageneral.valid_fn(fn):
      arizonareport.send_error(0, "Invalid file to embed public key in '"+fn+"'")
      sys.exit(1)

   (fndir, fnfn) =os.path.split(fn)
   # figure out the new file name (minus the pubkey)
   fn_list = fnfn.split(".")

   if len(fn_list) ==1:
      # it doesn't have any "." so we'll make it prefix.publickey
      prefix = fnfn+"."
      suffix = ""
   else:
      # Let's see if there is already a public key...
      prefix = ""
      for item_pos in range(len(fn_list)):
   #               possiblepubkey = arizonacrypt.fnstring_to_publickey_sl(fn_list[item_pos])
   #               if arizonacrypt.valid_publickey_sl(possiblepubkey):
   #                  prefix = ".".join(fn_list[:item_pos])+"."
   #                  try:
   #                     suffix = "."+".".join(fn_list[item_pos+1:])
   #                  except IndexError:
   #                     # Was the last element in the filename
   #                     suffix=""
   #                  break


         # see if it's an old style public-key-in-filename
         possiblepubkey = arizonacrypt.fnstring_to_publickey_sl(fn_list[item_pos])
         if arizonacrypt.valid_publickey_sl(possiblepubkey):
             is_a_key_representation = True
         # consider this part a key hash if it has some reasonable hash length and is a valid hex string
         else:
             try:
                 binascii.unhexlify(fn_list[item_pos])
                 is_a_key_representation = len(fn_list[item_pos]) >= 36
             except TypeError:
                 is_a_key_representation = False
         if is_a_key_representation:
            prefix = ".".join(fn_list[:item_pos])+"."
            try:
               suffix = "."+".".join(fn_list[item_pos+1:])
            except IndexError:
               # Was the last element in the filename
               suffix=""
            break
      else:
         #Let's add it to the second field instead
         # # Add the publickey as the second to last field
         # prefix = ".".join(fn_list[:-1])+"."
         # suffix = "."+fn_list[-1]
         prefix = fn_list[0]+"."
         suffix = "."+".".join(fn_list[1:])

   ### AT THIS POINT THERE IS prefix AND suffix.   The filename should
   ### end up as prefix+(hash)+suffix


   # check the pubkey arg for validity
   if not arizonageneral.valid_fn(publickeyfn):
      arizonareport.send_error(0, "Invalid publickey file '"+publickeyfn+"'")
      sys.exit(1)

   pubkey_sl = arizonacrypt.fn_to_sl(publickeyfn)
   if not arizonacrypt.valid_publickey_sl(pubkey_sl):
      arizonareport.send_error(0, "Invalid publickey file '"+publickeyfn+"'")
      sys.exit(1)

   # get the hash we need to add
   pubkeyhash = arizonacrypt.publickey_sl_to_fnstring(pubkey_sl)

   # Get the new filename (prepend the path)
   newfilename = fndir + prefix + pubkeyhash + suffix

   # Move the file to this name
   shutil.copy(fn, newfilename)

   # Inform the user
   arizonareport.send_out(2, "File '"+fn+"' has been copied to '"+newfilename+"'")
   return newfilename







# Make the blank trusted packages file
def makeTPFile(username, createblank):
   try:
      #Obtain the path to place the new tpfile
      path = os.path.dirname(os.path.abspath(sys.argv[0]))
      fh = open(username+".tpfile", 'w')
      
      #If the default.publickey file is found, trust default
      if os.path.exists(os.path.join(path,"default.publickey")) and not createblank:
         arizonareport.send_out(2, "\ndefault user public key found: Adding user to TPFile\n")
      
         key = arizonacrypt.PublicKey(file=os.path.join(path,"default.publickey")).string
      
         fh.write('<?xml version="1.0" encoding="ISO-8859-1" standalone="yes" ?>\n' +
                  '<TRUSTEDPACKAGES>\n'+
                  '<USER PATTERN="*" USERNAME="default" PUBLICKEY="'+key+'" ACTION="ALLOW"/>\n'+                        
                  '</TRUSTEDPACKAGES>\n')
       
       
      #If the default publickey is not found, just make a blank tp file
      else:
         if not createblank:
            arizonareport.send_out(2, "\nWarning: default user publickey not found in storkutil directory, skipping\n")
      
         fh.write('<?xml version="1.0" encoding="ISO-8859-1" standalone="yes" ?>\n<TRUSTEDPACKAGES>\n</TRUSTEDPACKAGES>\n')
         fh.close()
   except IOError:
      arizonareport.send_error(0, "Error accessing file or path '"+username+".tpfile' check that you have write permissions")
      sys.exit(1)








# Sign the trusted package file with the given private keyfile
def signTPFile(tpfile, privkeyfile):

   wrapper_timestamp = arizonaconfig.get_option("wrappertimestamp")
   if wrapper_timestamp == "now":
      wrapper_timestamp = None
   else:
      wrapper_timestamp = int(wrapper_timestamp)

   wrapper_duration = arizonaconfig.get_option("wrapperduration")
   if not wrapper_duration:
      wrapper_duration = None
   else:
      wrapper_duration = int(wrapper_duration)

   #Try to sign the file using ArizonaCrypt
   try:
      arizonacrypt.XML_sign_file_using_privatekey_fn(tpfile, privkeyfile, privatekey_pass=privatekeypass, timestamp=wrapper_timestamp, duration=wrapper_duration)
      
      
   #signing failed, report error to user
   except TypeError, e:
      arizonareport.send_error(0, "Error when XML signing file")
      arizonareport.send_error(0, str(e))
   
      # Give an intelligable message to the end user
      found = False
      if not arizonageneral.valid_fn(tpfile):
         arizonareport.send_error(0, "Error accessing file '"+tpfile+"'")
         found = True
      if not arizonageneral.valid_fn(privkeyfile):
         arizonareport.send_error(0, "Error accessing privatekey file '"+privkeyfile+"'")
         found = True
   
      if not found:
         # I haven't told the user anything yet
         arizonareport.send_error(0, "Check privatekey file '"+privkeyfile+"'")
      sys.exit(1)
   except IOError:
      arizonareport.send_error(0, "Error: Unable to write to file - Check permissions")
      sys.exit(1)
   arizonareport.send_out(2, "File '"+tpfile+"' successfully signed")







# Make the priv/pub keypair with the given username
def makeKeys(username):
   
   #Call arizonacrypt to generate private key
   try:
      arizonacrypt.generate_privatekey_fn(username+".privatekey")
   except IOError:
      arizonareport.send_error(0, "Error accessing file or path '"+username+"' please make sure you have read and write permissions")
      sys.exit(1)
   
   arizonareport.send_out(2, "Generated "+username+".privatekey...")
   
   #Use privatekey to generate public key
   pubk_sl = arizonacrypt.extract_publickey_sl_from_privatekey_fn(username+".privatekey")
   pubk_fn_temp = arizonacrypt.sl_to_fn(pubk_sl)
   
   #rename the key properly
   try:
      shutil.move(pubk_fn_temp, username+".publickey")
   finally:
      try:
         os.remove(pubk_fn_temp)
      except OSError:
         pass
   arizonareport.send_out(2, "Extracted "+username+".publickey...")
     
     



#Open an xml file and view it's contents (works for tpfile, groups, and packages)
def __view(filename):
   """
   <Purpose>
      Views the contents of tpfile, groups.pacman, and packages.pacman files.
   
   <Arguments>   
      filename:
              File location of a valid, signed tpfile, groups.pacman, or
              packages.pacman file
   
   <Exceptions>
      None
   
   <Side Effects>
      Creates and Removes a temporary file

   <Returns>
      None
   """
   
   #Report filename
   arizonareport.send_out(0,"Viewing: " + filename + "\n")
   temp = "/tmp/__"+filename
   
   
   #Extract original file from signed XML
   try:
      arizonacrypt.XML_retrieve_originalfile_from_signedfile(filename,temp)
   except IOError:
      arizonareport.send_error(0, "Unable to write to temporary file")
      sys.exit(1)
   except TypeError:
      arizonareport.send_error(0, "Invalid signedfile '"+filename+"'")
      sys.exit(1)
      
   tempfo = open(temp, 'r')
   lines = tempfo.readlines()
   tempfo.close()
   #os.remove(temp)
   
   #TODO - replace pattern matching with actual XML parsing
   
   #Create regular expressions
   tp_re = re.compile('<TRUSTEDPACKAGES>', re.I)
   tp_file_re = re.compile('(<FILE PATTERN=")(.*)(" HASH=")(.*)(" ACTION=")(.*)("\/>)', re.I)
   tp_user_re = re.compile('(<USER PATTERN=")(.*)(" USERNAME=")(.*)"( PUBLICKEY=")(.*)(" ACTION=")(.*)("\/>)', re.I)
   
   gp_re = re.compile('<GROUPS>', re.I)
   gp_else_re = re.compile('(<)(.*)( NAME=")(.*)("\/?>)', re.I)
   
   pa_re = re.compile("<PACKAGES>", re.I)
   pa_confA_re = re.compile('<CONFIG>', re.I)
   pa_conf_re = re.compile('(<CONFIG )(NODE|GROUP)(=")(.*)(">)', re.I)
   pa_com_re = re.compile('(<)(.*)( PACKAGE=")(.*)("\/>)', re.I)
   
   
   #Scan through the lines and report the files
   for i in lines:
      #print ":::" + i 
      if tp_re.match(i):
         m = tp_re.match(i)
         arizonareport.send_out(0, "TRUSTED PACKAGES FILE")
         
      elif tp_file_re.match(i):
         m = tp_file_re.match(i)
         arizonareport.send_out(0, "\t" + m.group(6) + " " + m.group(2))
         
      elif tp_user_re.match(i):
         m = tp_user_re.match(i)
         arizonareport.send_out(0, "\t" + m.group(8) + " " + m.group(2) + " from " + m.group(4))
         
         
      elif gp_re.match(i):
         m = gp_re.match(i)
         arizonareport.send_out(0, "PACMAN GROUP FILE")
         
      elif gp_else_re.match(i):
         m = gp_else_re.match(i)
         if m.group(2) == "GROUP":
            arizonareport.send_out(0, "\t" + m.group(2) + ":\t" + m.group(4))
         else:
            arizonareport.send_out(0, "\t\t" + m.group(2) + ":\t" + m.group(4))
      
      elif pa_re.match(i):
         m = pa_re.match(i)
         arizonareport.send_out(0, "PACMAN PACKAGES FILE")
         
      elif pa_confA_re.match(i):
         arizonareport.send_out(0, "CONFIG ALL:")
         
      elif pa_conf_re.match(i):
         m = pa_conf_re.match(i)
         arizonareport.send_out(0, "\tCONFIG " + m.group(2) + ":\t" + m.group(4))
      
      elif pa_com_re.match(i):
         m = pa_com_re.match(i)
         arizonareport.send_out(0, "\t\t" + m.group(2) + ":\t" + m.group(4))
         
   arizonareport.send_out(0, "")
   return

   
     
     
     
     
     

########################### MAIN ###############################
def main():
   # process command line and initialize variables
   args = arizonaconfig.init_options('storkutil.py', usage=usage_message, configfile_optvar='configurationfile', version='2.0')
   
   
   # make the private key password available
   global privatekeypass
   privatekeypass = getPrivateKeyPass()
   
   ###### No Args and Short ########
   if len(args)==0 or arizonaconfig.get_option("short"):
     print short_message
     sys.exit(0)
   
   ###### Help #############
   if arizonaconfig.get_option("help"):
     print "Got Here"
     arizonaconfig.print_help()
     if arizonaconfig.get_option("storkutilsetupcomplete").strip().lower()!='true':
             arizonareport.send_out(0,"Stork Enduser Utility has not been setup.\nPlease " + 
                                      "run 'storkutil genpair PREFIX' to create a new " + 
                                      "identity (public/private keys), or 'storkutil setdefault "+ 
                                      "PREFIX' to use an existing identity.")
     sys.exit(0)
   
   
   # take care of the timestamp argument used for the addfile command. 
   # if it is "now", then set it to the current time.
   timestamp = arizonaconfig.get_option("timestamp")
   if timestamp=="now":
       timestamp=str(time.time())
   
   
   
   
   
   #Duy Nguyen: storkutil directory is now the current directory
   #storkutildir=os.path.join(os.environ["HOME"],".storkutil")
   storkutildir="."
   


   #Check the options and make sure there are keys we can use.  If genpair or setdefault is called, ignore this check
   if arizonaconfig.get_option("storkutilsetupcomplete").strip().lower()!='true':
      if args[0] != "genpair" and args[0] != "setdefault":
         arizonareport.send_out(0,"Stork Enduser Utility has not been setup.\nPlease " +
                                  "run 'storkutil genpair PREFIX' to create a new identity "+
                                  "(public/private keys), or 'storkutil setdefault " + 
                                  "PREFIX' to use an existing identity.")
         sys.exit(1)
   
   
   
   #initialize option variables
   username = arizonaconfig.get_option("username")
   createblank = arizonaconfig.get_option("createblank")
   
   
   
   
   
   #public and privatekey, by default, is obtained using the username option
   privatekeyfile = arizonaconfig.get_option("tpprivatekey")
   if not privatekeyfile:
      privatekeyfile = username+".privatekey"
   
   publickeyfile = arizonaconfig.get_option("tppublickey")
   if not publickeyfile:
      publickeyfile = username+".publickey"
   
   
   
   #get tpfile/pacman file locations from the options
   _tpfile = arizonaconfig.get_option("tpfileloc")
   _pacfile = arizonaconfig.get_option("pacfileloc")
   
   
   
   
   
   #hash file                -- lists the sha1 hash for a file
   if args[0] == "hash":
      try:
         #Check arguments
         if len(args) != 2:
            arizonareport.send_error(0, "Error: Bad Number of Arguments: Usage - storkutil hash FILE")
         else:
            #Report hash
            arizonareport.send_out(0, arizonacrypt.get_fn_hash(args[1]))
            
            
            
      except IOError:
         arizonareport.send_error(0, "Error accessing file '"+args[1]+"'")
         sys.exit(1)
      return
   
   
   
   #metahash file            -- lists the sha1 hash for a package's metadata
   if args[0] == "metahash":
      try:
         #Check arguments
         if len(args) != 2:
            arizonareport.send_error(0, "Error: Bad Number of Arguments: Usage - storkutil metahash FILE")
         else:
            #Report metahash
            arizonareport.send_out(0, storkpackage.get_package_metadata_hash(args[1]))
            
            
            
      except IOError:
         arizonareport.send_error(0, "Error accessing file '"+args[1]+"'")
         sys.exit(1)
      except TypeError:
         arizonareport.send_error(0, "File '"+args[1]+"' is not a recognized package type")
         sys.exit(1)
      return
   
   
   
   
   #extractpub [--tpprivatekey KEYFILENAME]      -- extracts the public key from a private key
   elif args[0] == "extractpub":
      privkey=""
      #Check arguments
      if len(args)!=1:
          arizonareport.send_error(0,"Error: Bad Number of Arguments: Usage - storkutil [--username=MYUSER] extractpub")
          sys.exit(1)
      else:
          privkey=privatekeyfile
          
      try:
         #Try to generate publickey from privatekey
         arizonareport.send_out(0, "\n".join(arizonacrypt.extract_publickey_sl_from_privatekey_fn(privkey)))
         
         
      #Error occured, report to user
      except IOError:
         arizonareport.send_error(0, "Error accessing file '"+privkey+"'")
         sys.exit(1)
      except TypeError:
         arizonareport.send_error(0, "Invalid privatekey file '"+privkey+"'")
         sys.exit(1)
      return #publickeyfile = /usr/local/stork/var/keys/PlanetLab.publickey
   
   
   
   
   
   #genpair prefix           -- creates a public/private RSA pair named
   #                            prefix.privatekey and prefix.publickey
   #Note: Why aren't we using the makeKeys() function?
   
   elif args[0] == "genpair":
      try:
      #Check arguments
         if len(args) != 2:
            arizonareport.send_error(0,"Error: Bad Number of Arguments: Usage - storkutil genpair PREFIX")
            sys.exit(1)
         else:
         
            #Make sure pair of keys don't already exist
            if os.path.exists(args[1]+".privatekey") or os.path.exists(args[1]+".publickey"):
               arizonareport.send_error(0, "Error: Key files for '" + args[1] + "' already exist")
               sys.exit(1)
               
            #Create the privatekey
            arizonacrypt.generate_privatekey_fn(args[1]+".privatekey")
      except IOError:
         arizonareport.send_error(0, "Error accessing file or path '"+args[1]+"'")
         sys.exit(1)
         
   
   
      arizonareport.send_out(2, "Generated "+args[1]+".privatekey...")
      
      #Extract publickey from privatekey
      pubk_sl = arizonacrypt.extract_publickey_sl_from_privatekey_fn(args[1]+".privatekey")
      pubk_fn_temp = arizonacrypt.sl_to_fn(pubk_sl)
      try:
         #Rename key to proper name
         shutil.move(pubk_fn_temp, args[1]+".publickey")
      finally:
         #cleanup
         try:
            os.remove(pubk_fn_temp)
         except OSError:
            pass
      arizonareport.send_out(2, "Extracted "+args[1]+".publickey...")
      
      
      #Prompt user if they want to use this new set of keys as their default
      if arizonaconfig.get_option("dontask"):
         _in = "y"
      elif arizonaconfig.get_option("no"):
         _in = "n"
      else:
         print "Would you like to make '" + args[1] +"' your default identity? (y/n) >"
         _in = sys.stdin.readline().strip().lower()
      if _in in ["y", "yes"]:
      
         #Write storkutil config file
         try:
            envHome = ''
            if 'HOME' in os.environ:
               envHome = os.environ['HOME']
            elif 'HOMEDRIVE' in os.environ and 'HOMEPATH' in os.environ:
               envHome = os.path.join(os.environ['HOMEDRIVE'],os.environ['HOMEPATH'])
            fo = open(os.path.join(envHome,".storkutil.conf"), 'w')
            fo.write("username="+args[1]+"\n")
            fo.write("privatekey=%s\n" % os.path.abspath(args[1] + '.privatekey'))
            fo.write("publickey=%s\n" % os.path.abspath(args[1] + '.publickey'))
            fo.write("storkutilsetupcomplete=True\n")
            fo.write("tarpackinfo=.\n")
            fo.close()
            arizonareport.send_out(2, "'" + args[1] + "' is now your default identity")
         except IOError:
            arizonareport.send_error(0, "Error writing '" + envHome + "/.storkutil.conf'")
      return
   
   
   
   
   
   #setdefault PREFIX [PRIVATEKEY] [PUBLICKEY]   -- Set the default identify to be used on storkutil
   elif args[0] == "setdefault":
      #Check arguments
      if len(args) < 2 or len(args) > 4:
         arizonareport.send_error(0,"Error: Bad Number of Arguments: Usage - storkutil setdefault PREFIX")
         sys.exit(1)
      else:
         arizonareport.send_out(0,"Previous Identity: " + username)
   
         #Find path of the files given
         if len(args) == 3:
            privkeypath = os.path.abspath(args[2])
         else:
            privkeypath = os.path.join(os.path.abspath(''), args[1] + ".privatekey")
   
         if len(args) == 4:
            pubkeypath = os.path.abspath(args[3])
         else:
            pubkeypath = os.path.join(os.path.abspath(''), args[1] + ".publickey")  
   
   
         #Report if files are not found, but continue anyway
         if not os.path.exists(privkeypath):
            arizonareport.send_error(1, "Warning: '%s' could not be found" % privkeypath) 
         if not os.path.exists(pubkeypath):
            arizonareport.send_error(1, "Warning: '%s' could not be found" % pubkeypath)
   
   
         #Write the new config file
         try:
            envHome = ''
            if 'HOME' in os.environ:
               envHome = os.environ['HOME']
            elif 'HOMEDRIVE' in os.environ and 'HOMEPATH' in os.environ:
               envHome = os.path.join(os.environ['HOMEDRIVE'],os.environ['HOMEPATH'])
            fo = open(os.path.join(envHome,".storkutil.conf"), 'w')
            fo.write("username="+args[1]+"\n")
            fo.write("privatekey=%s\n" % privkeypath)
            fo.write("publickey=%s\n" % pubkeypath)
            fo.write("storkutilsetupcomplete=True\n")
            fo.write("tarpackinfo=.\n")
            fo.close()
            arizonareport.send_out(2, "'" + args[1] + "' is now your default identity")
         except IOError:
            arizonareport.send_error(0, "Error writing '" + envHome + "/.storkutil.conf'")
      return
   
   
   
   
   
   #signedhash [--tpprivatekey KEYFILENAME] file   -- lists the signed sha1 hash for a file using privkey
   elif args[0] == "signedhash":
      privkey=""
      #Check arguments
      if len(args)!= 2:
          arizonareport.send_error(0, "Error: Bad Number of Arguments: Usage - storkutil [--username=MYUSER] signedhash FILE")
          sys.exit(1)
      else:
          privkey=privatekeyfile
      try:
         arizonareport.send_out(0,arizonacrypt.get_fn_signedhash_using_privatekey_fn(args[1],privkey))
      except IOError:
         arizonareport.send_error(0, "Error when generating signedhash")
   
         # Give an intelligable message to the end user
         found = False
         if not arizonageneral.valid_fn(args[1]):
            arizonareport.send_error(0, "Error accessing file '"+args[1]+"'")
            found = True
         if not arizonageneral.valid_fn(privkey):
            arizonareport.send_error(0, "Error accessing privatekey file '"+privkey+"'")
            found = True
   
         if not found:
            # I haven't told the user anything yet
            arizonareport.send_error(0, "Check privatekey file '"+privkey+"'")
         sys.exit(1)
      except TypeError:
         publickeyfile = "/usr/local/stork/var/keys/PlanetLab.publickey"
         arizonareport.send_error(0, "Invalid privatekey file '"+privkey+"'")
         sys.exit(1)
      return
      
   
   
   
   
   #sign [--tpprivatekey KEYFILENAME] file    -- sign the file using the privkey
   elif args[0] == "sign":
      privkey=""
      #Check arguments
      if len(args)!=2:
          arizonareport.send_error(0, "Error: Bad Number of Arguments: Usage - storkutil [--username=MYUSER] sign FILE")
          sys.exit(1)
      else:
          privkey=privatekeyfile
          
      #Sign the file
      signTPFile(args[1],privkey)
      return
   
   
   
   
   #verify [--tppublickey KEYFILENAME] file  -- verify the signature of file using pubkey
   elif args[0] == "verify":
      pubkey=""
      #Check arguments
      if len(args)!=2:
          arizonareport.send_error(0, "Error: Bad Number of Arguments: Usage - storkutil [--username=MYUSER] verify FILE")
          sys.exit(1)
      else:
          pubkey=publickeyfile


      #Send file to arizonacrypt to have it verified
      try:
         arizonacrypt.XML_timestamp_signedfile_with_publickey_fn(args[1], pubkey)

      #Error occured, report to user
      except TypeError, e:
         arizonareport.send_error(0, "Error when verifying signature")
         arizonareport.send_error(0, str(e))
         # Look for the error
         found = False

         if not arizonageneral.valid_fn(args[1]):
            arizonareport.send_error(0, "Error accessing file '"+args[1]+"'")
            found = True

         if not arizonageneral.valid_fn(pubkey):
            arizonareport.send_error(0, "Error accessing publickey file '"+pubkey+"'")
            found = True

         if not found:
            # I haven't told the user anything yet
            arizonareport.send_error(0, "Check publickey file '"+pubkey+"'")
         sys.exit(1)
      arizonareport.send_out(2, "File '"+args[1]+"' is signed correctly")
      return
   
   
   
   
   
   
   
   #extract file destfile -- extract the original data embedded in the signedfile
   #                            file to destfile
   elif args[0] == "extract":
      #Check arguments
      if len(args) != 3:
          arizonareport.send_error(0, "Error: Bad Number of Arguments: Usage - storkutil extract FILE DESTFILE")
          sys.exit(1)
       
      try:
         #Extract the file
         arizonacrypt.XML_retrieve_originalfile_from_signedfile(args[1],args[2])
         
      #Error occured, report to user
      except IOError:
         arizonareport.send_error(0, "Error opening destination file '"+args[2]+"'")
         sys.exit(1)
      except TypeError:
         arizonareport.send_error(0, "Invalid signedfile '"+args[1]+"'")
         sys.exit(1)
      return
   
   
   
   #extractmeta --baseurl URL FILE [FILE] ... Generate the metadata for a list of files, including a base url
   elif args[0] == "extractmeta":
      #Check arguments
      if len(args) < 2:
         arizonareport.send_error(0, "Error: Bad Number of Arguments: Usage - storkutil extractmeta --baseurl URL FILE [FILE] ...")
         sys.exit(1)
      destdir = '.'
   
      baseurl = arizonaconfig.get_option("baseurl")
      if not baseurl:
         arizonareport.send_error(0, "Error: You must use the --baseurl option. For example: --baseurl http://myserver/packages")
         sys.exit(1)
   
   
      #Iterate through the files and extract the metadata for each one
      filenames=args[1:]
      for filename in filenames:
         try:
            #Get the metadata for the file
            mymeta = storkpackage.get_package_metadata(filename)
         except TypeError, e:
            arizonareport.send_error(1, "Failed to generate metadata for " + filename + " (" + str(e) + ")")
            sys.exit(1)
   
         #Store the url in the metadata
         mymeta['URL'] = [os.path.join(baseurl, os.path.basename(filename))]
   
         #Save metadata
         destfn = os.path.basename(filename) + ".metadata"
         storkpackagelist.package_metadata_dict_to_fn(mymeta, destdir, destfn)
   
         arizonareport.send_out(1, "Metadata saved to: " + destdir + "/" + destfn)
         arizonareport.send_out(1, "Metadata hash: " +
           storkpackagelist.package_metadata_dict_get_hash(mymeta))
   
      return
   
   
   
   
   
   #addfile [--tpfile=file.tpfile] file [file]...    -- allow file in the provided trustedpackages file
   elif args[0] == "addfile":
      if len(args) < 2:
         arizonareport.send_error(0, "Error: Bad Number of Arguments: Usage - storkutil [--username=MYUSER] addfile FILE [FILE]...")
         sys.exit(1)
   
   
      files=args[1:]
      for i in files:
         if not arizonageneral.valid_fn(i):
            arizonareport.send_error(0, "Invalid file '"+i+"'")
            sys.exit(1)
   
   
      tags = arizonaconfig.get_option("tags")
      if tags == None:
         tags = ""
   
   
      #if file does not exist, create it
      filename=""
      if _tpfile[-7:]==".tpfile":
         filename=_tpfile
         if not os.path.isfile(filename):
            arizonareport.send_out(1,"Specified file not found.  Creating new file %s." %(filename))
            makeTPFile(filename[:-7], createblank)
   
      if not filename:
         #find the tp file:
         #now search their storkutil dir
         lst=os.listdir(storkutildir)
         for i in lst:
            if not os.path.isfile(os.path.join(storkutildir,i)):continue
            if i[:len(username)+1]==username+"." and i[-7:]==".tpfile":
              filename=os.path.join(storkutildir,i)
              break
              
              
         if not filename:
            #no tpfile here, so we will make a new one for the user and warn them at the same time.
            arizonareport.send_out(1,  "No tpfile found for %s.  Generating new tpfile." %(username) )
            cwd=os.getcwd()
            if not os.path.isdir(storkutildir):os.makedirs(storkutildir)
            os.chdir(storkutildir)
            makeTPFile(username, createblank)
            tmp=username+".tpfile"
            signTPFile(tmp,privatekeyfile)
            filename=os.path.join(storkutildir,pubKeyEmbed(tmp,publickeyfile))
            arizonareport.send_out(2, "Unembeded trusted packages file '"+tmp+"' removed.")
            os.remove(tmp)#to simplify and prevent confusion
            os.chdir(cwd)
            
            
      arizonareport.send_out(2, "Using trustedpackages file '"+filename+"'.")
   
   
      for i in files:     
         # Work on an unsigned file
         try:
            if i.endswith(".metadata"):
               # the file is a metadata file, so we need to read the
               # metadata file, extract the package filename, and compute
               # the hash of the metadata file.
               metadata_dict = storkpackagelist.load_package_metadata_fn(i)
               pattern = metadata_dict['filename']
               filehash = arizonacrypt.get_fn_hash(i)
            else:
               pattern = os.path.split(i)[1]
               filehash = storkpackage.get_package_metadata_hash(i)
   
            #Write to file
            (success, junk) = arizonageneral.text_replace_files_in_fnlist(
                                 "<TRUSTEDPACKAGES>",
                                 "<TRUSTEDPACKAGES>\n"+
                                 '<FILE PATTERN="'+pattern+
                                    '" HASH="'+filehash+
                                    '" TIMESTAMP="'+str(timestamp)+
                                    '" TAGS="'+tags+
                                    '" ACTION="ALLOW"/>',
                                 [filename])
   
            if not success:
               arizonareport.send_error(0, "Failure accessing file '"+filename+"' while adding file '"+i+"'.")
               sys.exit(1)
   
            # Work on a signed file
            (success, junk) = arizonageneral.text_replace_files_in_fnlist(
                                 arizonaxml.escape("<TRUSTEDPACKAGES>"),
                                 arizonaxml.escape('<TRUSTEDPACKAGES>\n<FILE PATTERN="'+
                                                   pattern+
                                                   '" HASH="'+
                                                   filehash+
                                                   '" TIMESTAMP="'+
                                                   str(timestamp)+
                                                   '" TAGS="'+
                                                   tags+
                                                   '" ACTION="ALLOW"/>'),
                                 [filename])
   
            if not success:
               arizonareport.send_error(0, "Failure accessing file '"+filename+"' while adding file '"+i+"'.")
               sys.exit(1)
            arizonareport.send_out(2, "Successfully added file '"+os.path.split(i)[1]+"'.")
         except TypeError:
            arizonareport.send_error(0, "WARNING: '" + i + "' is not a valid package")
               
      #be nice and sign it again for the user.
      if os.path.isfile(privatekeyfile):signTPFile(filename,privatekeyfile)
      else:arizonareport.send_out(2, "Private key not found.  Be sure to sign your file." )
      return
   
   
   
   
   
   
   
   #removefile [--tpfile=file.tpfile] file [file]...
   #                         -- remove the allow file lines for the specified files.
   elif args[0] == "removefile":
   
      if len(args) == 1:
          arizonareport.send_error(0,"Error: Bad Number of Arguments: Usage - storkutil [--username=MYUSER] removefile FILE [FILE]...")
          sys.exit(1)
   
      files=args[1:]
      #should be no need to check to see if the files still exist.
      
      filename=""
      if _tpfile[-7:]==".tpfile":
         filename=_tpfile
         if not os.path.isfile(filename):
            arizonareport.send_out(1,"Unable to find specified tpfile (%s).  Searching for tpfile for %s." %(filename,username) )
            filename=""      
               
      if not filename:
         #find the tp file:
         #now search their storkutil dir
         lst=os.listdir(storkutildir)
         for i in lst:
            if not os.path.isfile(os.path.join(storkutildir,i)):continue
            if i[:len(username)+1]==username+"." and i[-7:]==".tpfile":
              filename=os.path.join(storkutildir,i)
              break
         if not filename:
            #no tpfile here, so since there's nothing to remove from, just exit.
            arizonareport.send_out(0,  "No tpfile found for %s.  Unable to remove files." %(username) )
            sys.exit(0)
   
      arizonareport.send_out(2, "Using trustedpackages file '"+filename+"'.")
      for i in files:         
         # Work on an unsigned file
         (success, junk) = arizonageneral.text_replace_files_in_fnlist_re('\\<FILE PATTERN="'+
                           os.path.split(i)[1]+'" HASH="[^>]+" ACTION="ALLOW"\\>\n','',[filename])
   
         if not success:
            arizonareport.send_error(0, "Failure accessing file '"+filename+"' while removing file '"+i+"'.")
            sys.exit(1)
   
         # Work on a signed file
         (success, junk) = arizonageneral.text_replace_files_in_fnlist_re(arizonaxml.escape('<FILE PATTERN="'+ 
                              os.path.split(i)[1]+'" HASH="')+"[^&]+" + arizonaxml.escape(' ACTION="ALLOW"/>\n'),'',[filename])
   
         if not success:
            arizonareport.send_error(0, "Failure accessing file '"+filename+"' while removing file '"+i+"'.")
            sys.exit(1)
         arizonareport.send_out(2, "Successfully removed file '"+os.path.split(i)[1]+"'.")
      #be nice and sign it again for the user.
      if os.path.isfile(privatekeyfile):signTPFile(filename,privatekeyfile)
      else:arizonareport.send_out(2, "Private keyfile not found.  Be sure to sign your file." )
      return
   
   
   
   
   #pubkeyembed [--tppublickey KEYFILENAME] file  -- rename the file so that the publickey is embedded
   #                            in the name
   elif args[0] == "pubkeyembed":
      pubkey=""
      if len(args)!=2:
          arizonareport.send_error(0, "Error: Bad Number of Arguments: Usage - storkutil [--username=MYUSER] pubkeyembed file")
          sys.exit(1)
      else:
          pubkey=publickeyfile
      pubKeyEmbed(args[1],pubkey)
      return
   
   
   
   
   
   #pubkeyconvert sshfilein sslfileout -- convert a publickey from ssh format to ssl format
   elif args[0] == "pubkeyconvert":
      if len(args)!=3:
         arizonareport.send_error(0, "Error: Bad Number of Arguments: Usage - storkutl <sshfilename> <sslfilename>")
         sys.exit(1)
      arizonacrypt.convert_ssh_to_ssl(args[1], args[2])
      return
   
   
   
         
   #adduser user user.publickey (allow|deny|any) affectedpackages [tpfile]
   #                         -- add the listed user to the trustedpackages file
   elif args[0] == "adduser":
      
      #Check arguments
      if len(args) != 5:
         arizonareport.send_error(0,"Error: Invalid number of arguments: Usage - storkutil" + 
                                    " [--username=MYUSER] adduser USER USER.publickey (allow|deny|any) AFFECTEDPACKAGES")
         sys.exit(1)
      
      if not arizonageneral.valid_fn(args[2]):
         arizonareport.send_error(0, "Invalid publickey file '"+args[2]+"'")
         sys.exit(1)
   
      pubkey_sl = arizonacrypt.fn_to_sl(args[2])
      if not arizonacrypt.valid_publickey_sl(pubkey_sl):
         arizonareport.send_error(0, "Invalid publickey file '"+args[2]+"'")
         sys.exit(1)
   
      #changed args[-1] to _tpfile: Sept. 30th 2006
      if '.tpfile' == _tpfile[-7:] and not arizonageneral.valid_fn(_tpfile):
         arizonareport.send_error(0, "Invalid trustedpackages file '"+_tpfile+"'")
         sys.exit(1)
      
      #Grab the public key from the pubkey file
      pubkeyhash = arizonacrypt.publickey_sl_to_fnstring(pubkey_sl)
   
      #if file does not exist, create it
      filename=""
      if _tpfile[-7:]==".tpfile":
         filename=_tpfile
         if not os.path.isfile(filename):
            arizonareport.send_out(1,"Specified file not found.  Creating new file %s." %(filename))
            makeTPFile(filename[:-7], createblank)
   
      if not filename:
         #find the tp file:
         #now search their storkutil dir
         lst=os.listdir(storkutildir)
         for i in lst:
            if not os.path.isfile(os.path.join(storkutildir,i)):continue
            if i[:len(username)+1]==username+"." and i[-7:]==".tpfile":
              filename=os.path.join(storkutildir,i)
              break
         if not filename:
            #no tpfile here, so we will make a new one for the user and warn them at the same time.
            arizonareport.send_out(1,  "No tpfile found for %s.  Generating new tpfile." %(username) )
            cwd=os.getcwd()
            if not os.path.isdir(storkutildir):os.makedirs(storkutildir)
            os.chdir(storkutildir)
            makeTPFile(username, createblank)
            tmp=username+".tpfile"
            signTPFile(tmp,privatekeyfile)
            filename=os.path.join(storkutildir,pubKeyEmbed(tmp,publickeyfile))
            arizonareport.send_out(2, "Unembedded trusted packages file '"+tmp+"' removed.")
            os.remove(tmp)#to simplify and prevent confusion
            os.chdir(cwd)
      arizonareport.send_out(2, "Using trustedpackages file '"+filename+"'.")
      
      
      #Write to file
      
      # Work on an unsigned file
      (success, junk) = arizonageneral.text_replace_files_in_fnlist(
                           "<TRUSTEDPACKAGES>",
                           '<TRUSTEDPACKAGES>\n<USER PATTERN="'+
                              args[4]+
                              '" USERNAME="'+
                              args[1]+
                              '" PUBLICKEY="'+
                              arizonacrypt.PublicKey(sl=pubkey_sl).string+
                              '" ORDER-BY="'+
                              arizonaconfig.get_option("orderby")+
                              '" ACTION="'+
                              args[3].upper()+
                              '"/>',
                           [filename])
   
      if not success:
         arizonareport.send_error(0, "Failure accessing file '"+filename+"'")
         sys.exit(1)
   
      # Work on a signed file
      (success, junk) = arizonageneral.text_replace_files_in_fnlist(
                           arizonaxml.escape("<TRUSTEDPACKAGES>"),
                           arizonaxml.escape(
                              '<TRUSTEDPACKAGES>\n<USER PATTERN="'+
                              args[4]+
                              '" USERNAME="'+
                              args[1]+
                              '" PUBLICKEY="'+
                              arizonacrypt.PublicKey(sl=pubkey_sl).string+
                              '" ORDER-BY="'+
                              arizonaconfig.get_option("orderby")+
                              '" ACTION="'+
                              args[3].upper()+'"/>\n'),
                           [filename])
   
      if not success:
         arizonareport.send_error(0, "Failure accessing file '"+filename+"'")
         sys.exit(1)
      arizonareport.send_out(2,"Successfully added user '"+args[1]+"'.")
      #be nice and sign it again for the user.
      if os.path.isfile(privatekeyfile):signTPFile(filename,privatekeyfile)
      else:arizonareport.send_out(2, "Private keyfile not found.  Be sure to sign your file." )
      return
   
   
   
   
   
   
   #removeuser [--tpfile=out.tpfile] username -- remove the specified user from the tpfile.
   elif args[0] == "removeuser":
      if len(args) != 2:
          arizonareport.send_error(0,"Error: Invalid number of arguments: Usage - storkutil [--username=MYUSER] removeuser username")
          sys.exit(1)
   
      #changed args[-1] to _tpfile: Sept 30th, 2006
      if '.tpfile' == _tpfile[-7:] and not arizonageneral.valid_fn(_tpfile):
         arizonareport.send_error(0, "Invalid trustedpackages file '"+_tpfile+"'")
         sys.exit(1)
   
      filename=""
      if _tpfile[-7:]==".tpfile":
         filename=_tpfile
      else:
         #Temporary: To be replaced by storkusername?
         pubkey_sl = arizonacrypt.fn_to_sl(publickeyfile)
         if not arizonacrypt.valid_publickey_sl(pubkey_sl):
            arizonareport.send_error(0, "Invalid publickey file '"+publickeyfile+"'")
            sys.exit(1)
   
         pubkeyhash = arizonacrypt.publickey_sl_to_fnstring(pubkey_sl)
   
         filename = username + "." + pubkeyhash + ".tpfile"
           
      if not os.path.isfile(filename):
         arizonareport.send_out(1,"Unable to find specified tpfile (%s)." %(filename) )
         sys.exit(1)
   
      
      arizonareport.send_out(2, "Using trustedpackages file '"+filename+"'.")
      # Work on an unsigned file
      (success, junk) = arizonageneral.text_replace_files_in_fnlist_re('\\<USER PATTERN="[^>]+" USERNAME="'+
                        args[1]+'" PUBLICKEY="[^>]+" ACTION="[^>]+"\\>\n','',[filename])
   
      if not success:
         arizonareport.send_error(0, "Failure accessing file '"+filename+"'")
         sys.exit(1)
   
      # Work on a signed file
      (success, junk) = arizonageneral.text_replace_files_in_fnlist_re(arizonaxml.escape('<USER PATTERN="')+"[^&]+"+
                        arizonaxml.escape('" USERNAME="'+args[1]+'" PUBLICKEY="')+"[^&]+"+arizonaxml.escape('" ACTION="')+
                        "[^&]+"+arizonaxml.escape('"/>\n'),'',[filename])
   
      if not success:
         arizonareport.send_error(0, "Failure accessing file '"+filename+"'")
         sys.exit(1)
      arizonareport.send_out(2,"Successfully removed user '"+args[1]+"'.")
      #be nice and sign it again for the user.
      if os.path.isfile(privatekeyfile):signTPFile(filename,privatekeyfile)
      else:arizonareport.send_out(2, "Private keyfile not found.  Be sure to sign your file." )
      return
   
   
   #Matt Borgard: March 21, 2007
   #comonscript 
   elif args[0] == "comon":
      if len(args) < 4:
         print ("Error: Bad Number of Arguments - Usage: storkutil [--username=MYUSER] comon (include|exclude|intersect|remove) " + 
               "GROUP \"STORKUTIL-QUERY\". Make sure your query is surrounded by quotation marks, or escape your single &'s.")
         sys.exit(1)
      args[0] = "pacgroups"
      
      #Query Comon
      scriptOutput = comonscript.comon(args[3])
      args[3] = ""
      i = 0
      j = 3
      while( i < len(scriptOutput) ):
         args.append("")
         while( scriptOutput[i] != '\n' ):
            args[j] = args[j] + scriptOutput[i]
            i += 1
         i += 1
         j += 1   
      
      args.remove("")
   
   
   #Duy Nguyen: November 7th, 2006      
   #pacgroups (include|exclude|intersect|remove) GROUP NAME [NAME]...
   #'elif' changed to 'if' so that the comon command can make use of pacgroups -Matt
   if args[0] == "pacgroups":
      if len(args) < 4:
         print "Error: Bad Number of Arguments - Usage: storkutil [--username=MYUSER] pacgroups (include|exclude|intersect|remove) GROUP NAME [NAME]..."
         sys.exit(1)
      
      filename = _pacfile
      #Temporary: To be replaced by storkusername?
      pubkey_sl = arizonacrypt.fn_to_sl(publickeyfile)
      if not arizonacrypt.valid_publickey_sl(pubkey_sl):
         arizonareport.send_error(0, "Invalid publickey file '"+publickeyfile+"'")
         sys.exit(1)
   
      #Get key has from the public key file
      pubkeyhash = arizonacrypt.publickey_sl_to_fnstring(pubkey_sl)
   
      #Check if files exists
      if not filename:
         filename = os.path.join(storkutildir, username + "." + pubkeyhash + ".groups.pacman")
   
      if filename[-14:] != '.groups.pacman':
         arizonareport.send_error(1, "Warning: " + filename + " does not end in .groups.pacman")
   
      arizonareport.send_out(0, "Using groups file: %s\n" % (filename)) 
   
      lines = []
      #Read in existing file
      try:
         #Check to see if input file exists
         open( filename, 'r').close()
     
         try:        
             arizonacrypt.XML_retrieve_originalfile_from_signedfile(filename,filename) 
         except IOError:
             arizonareport.send_error(0, "Error opening destination file '"+filename+"'")
             sys.exit(1)
         except TypeError:
             arizonareport.send_error(0, "Invalid signedfile '"+filename+"'")
             sys.exit(1)
         
         pgfo = open ( filename, 'r')
         lines = pgfo.readlines()
         pgfo.close()
      except IOError:
         arizonareport.send_out(0, "File Not Found, Creating New File")
      
      if len(lines) == 0:
         lines = ["<?xml version=\"1.0\" encoding=\"ISO-8859-1\" standalone=\"yes\" ?>\n","<GROUPS>\n", "</GROUPS>\n"]
      
   
   
      #Edit file
      command = args[1]
      group = args[2]
      names = args[3:]
      if command == "include" or command == "exclude" or command == "intersect":
   
         #search for existing group
         try:
            gstart = lines.index("<GROUP NAME=\""+group+"\">\n") + 1 
            gend = lines[gstart:].index("</GROUP>\n") + gstart
   
         except ValueError:
            #group was not found, create new and add
            lines.insert(-1,"<GROUP NAME=\""+group+"\">\n")
            lines.insert(-1,"</GROUP>\n")
            gstart = len(lines) - 2
            gend = len(lines) - 2
   
         for name in names:
            #find if name is already involved
            found = 0
            dex = 0
            for i in lines[gstart:gend]:
               if i.find("\""+name+"\"") >= 0:
                  lines[gstart+dex] = "<"+command.upper()+" NAME=\""+name+"\"/>\n"
                  found = 1
                  break
               dex = dex + 1
            
            #name not involved, so make new
            if found == 0:
               lines.insert(gend,"<"+command.upper()+" NAME=\""+name+"\"/>\n")
               gend =  gend + 1
   
            
      elif command == "remove":
         #search for group
         try:
            gstart = lines.index("<GROUP NAME=\""+group+"\">\n") + 1
            gend = lines[gstart:].index("</GROUP>\n") + gstart
            
            for name in names:
               #find if name is already involved
               found = 0
               dex = 0
               for i in lines[gstart:gend]:
                  if i.find("\""+name+"\"") >= 0:
                     lines[gstart+dex] = ""
                     found = 1
                     break
                  dex = dex + 1
            
               #name not involved, so prompt
               if found == 0:
                  arizonareport.send_error(0, "Name '"+name+"' is not in group '"+group+"'")
   
            #If no more items in group, remove it
            empty = True
            for line in lines[gstart:gend]:
               if line != "":
                  empty = False               
   
            if empty:
               lines[gstart-1] = ""
               lines[gend] = ""
   
   
         except ValueError:
            arizonareport.send_error(0, "Group '"+group+"' does not exist")
            
      else:
         arizonareport.send_error(0, "Error: Bad command '"+command+"'")
         sys.exit(1)
   
   
      #Open file to write
      try:
         out = open ( filename, 'w')
      except IOError:
         arizonareport.send_error(0, "Unable to access '"+filename+"'")
         sys.exit(1)  
   
      for i in lines:
         out.write(i)
      out.close()        
      signTPFile(filename,privatekeyfile)
      return
   
   
   
   
   
   
   #pacpackages (node|group) NAME (install|remove|update|delete|clear) PACKAGE [PACKAGE]...
   elif args[0] == "pacpackages":
      if len(args) < 4:
         arizonareport.send_error(0,"Error: Bad Number of Arguments - Usage: storkutil [--username=MYUSER] pacpackages "+
                                             "(node|group|all) [NAME] (install|remove|update|delete|clear) PACKAGE")
         sys.exit(1)
   
      filename = _pacfile
   
      #Temporary: To be replaced with storkusername call?
      pubkey_sl = arizonacrypt.fn_to_sl(publickeyfile)
      if not arizonacrypt.valid_publickey_sl(pubkey_sl):
         arizonareport.send_error(0, "Invalid publickey file '"+publickeyfile+"'")
         sys.exit(1)
   
      #Get public key has from file
      pubkeyhash = arizonacrypt.publickey_sl_to_fnstring(pubkey_sl)
   
      if not filename:
         filename = os.path.join(storkutildir, username + "." + pubkeyhash + ".packages.pacman")
   
      if filename[-16:] != '.packages.pacman':
         arizonareport.send_error(1, "Warning: " + filename + " does not end in .packages.pacman")
   
      arizonareport.send_out(0, "Using Package File: %s\n" % (filename))
   
      lines = []
      #Read in existing file
      try:
         #Check to see if input file exists
         open( filename, 'r').close()
   
         try:
            arizonacrypt.XML_retrieve_originalfile_from_signedfile(filename,filename)
         except IOError:
            arizonareport.send_error(0, "Error opening destination file '"+filename+"'")
            sys.exit(1)
         except TypeError:
            arizonareport.send_error(0, "Invalid signedfile '"+filename+"'")
            sys.exit(1)
   
         ppfo = open ( filename, 'r')
         lines = ppfo.readlines()
         ppfo.close()
      except IOError:
         arizonareport.send_out(0, "File Not Found, Creating New File")
   
      if len(lines) == 0:
         lines = ["<?xml version=\"1.0\" encoding=\"ISO-8859-1\" standalone=\"yes\" ?>\n",
                  "<PACKAGES>\n",
                  "<CONFIG>\n",]
   
         if not createblank:
            lines = lines + ["<UPDATE PACKAGE=\"stork-client\"/>\n",
                             "<UPDATE PACKAGE=\"arizona-lib\"/>\n",]
   
         lines = lines + ["</CONFIG>\n",
                          "</PACKAGES>\n"]
   
   
      actiontype = args[1]
      if actiontype == "all":
         command = args[2]
         packs = args[3:]
      else:
         name = args[2]
         command = args[3]
         packs = args[4:]
   
   
      if not command in ["install", "remove", "update", "delete", "clear"]:
         arizonareport.send_error(0, "Error: Invalid command (%s)" % command)
   
      if actiontype == "node" or actiontype == "group" or actiontype == "all" or actiontype == "slice":
        #find existing definition for this type
         if actiontype == "all":
   
            try:
               gstart = lines.index("<CONFIG>\n") + 1
               gend = lines[gstart:].index("</CONFIG>\n") + gstart
   
            except ValueError:
               #Definition was not found, create new definition and add
               lines.insert(-1,"<CONFIG>\n")
               lines.insert(-1,"</CONFIG>\n")
               gstart = len(lines) - 2
               gend = len(lines) - 2
   
         else:
            try:
               gstart = lines.index("<CONFIG "+actiontype.upper()+"=\""+name+"\">\n") + 1
               gend = lines[gstart:].index("</CONFIG>\n") + gstart
   
            except ValueError:
               #Definition was not found, create new definition and add
               lines.insert(-1,"<CONFIG "+actiontype.upper()+"=\""+name+"\">\n")
               lines.insert(-1,"</CONFIG>\n")
               gstart = len(lines) - 2
               gend = len(lines) - 2
   
   
   
         for pack in packs:
            #check if pack is a path instead of a package name
            if pack.find('/') != -1 or pack.find('\\') != -1:
               pack = os.path.basename(pack)
               arizonareport.send_error(2,'Warning: Only the package name should be used.  A path is not needed (%s).' % pack)
   
            if command == "delete":
               #find if package is already defined
               found = 0
               dex = 0
               for i in lines[gstart:gend]:
                  if i.find("\""+pack+"\"") >= 0:
                     #match found
                     lines[gstart+dex] = ""
                     found = 1
                     break
                  dex = dex + 1
            else:
               #find if package is already defined
               found = 0
               dex = 0
               for i in lines[gstart:gend]:
                  if i.find("\""+pack+"\"") >= 0:
                     #match found
                     lines[gstart+dex] = "<"+command.upper()+" PACKAGE=\""+pack+"\"/>\n"
                     found = 1
                     break
                  dex = dex + 1
   
               #name not involved, so make new
               if found == 0:
                  lines.insert(gend,"<"+command.upper()+" PACKAGE=\""+pack+"\"/>\n")
                  gend = gend + 1
   
   
         # for the clear command, remove all entries in this group
         if command == "clear":
            dex = 0
            for i in lines[gstart:gend]:
               lines[gstart+dex] = ""
               dex = dex + 1
   
         #remove group if the definition is empty
         flag = 0
         for i in lines[gstart:gend]:
            if i != "":
               flag = 1
   
         if flag == 0:
            lines[gstart-1] = ""
            lines[gend] = ""
   
      else:
        arizonareport.send_error(2,"Error: Invalid type '"+actiontype+"'")
        sys.exit(1)
   
   
   
      #Open file to write
      try:
         out = open ( filename, 'w')
      except IOError:
         arizonareport.send_error(0, "Unable to access '"+filename+"'")
         sys.exit(1)
   
   
      #Write and sign
      for i in lines:
         out.write(i)
      out.close()
      signTPFile(filename,privatekeyfile)
      return
   
   
   
   
   
   
   #view (tpfile|groups|packages)
   elif args[0] == "view":
      if len(args) < 2:
         arizonareport.send_error(0,"Error: Bad Number of Arguments - Usage: storkutil [--username=MYUSER] view (tpfile|groups|packages)")
         sys.exit(1)
         
      #Temporary: To be replaced by storkusername?
      try:
         pubkey_sl = arizonacrypt.fn_to_sl(publickeyfile)
         if not arizonacrypt.valid_publickey_sl(pubkey_sl):
            arizonareport.send_error(0, "Invalid publickey file '"+publickeyfile+"'")
            sys.exit(1)
      except IOError:
         arizonareport.send_error(0, "Could not find publickey file '%s'" %publickeyfile)
         sys.exit(1)
   
   
      pubkeyhash = arizonacrypt.publickey_sl_to_fnstring(pubkey_sl)
   
      if args[1] == "tpfile":
         if not _tpfile:
            _tpfile = username+"."+pubkeyhash+".tpfile"
             
         __view(_tpfile)
      elif args[1] == "groups":
         if not _pacfile:
            _pacfile = username+"."+pubkeyhash+".groups.pacman"
         
         __view(_pacfile)
      elif args[1] == "packages":
         if not _pacfile:
            _pacfile = username+"."+pubkeyhash+".packages.pacman"
            
         __view(_pacfile)
         
      else:
         arizonareport.send_error(0,"Error: Bad Command - Usage: storkutil [--username=MYUSER] view (tpfile|groups|packages)")
      
      return
   
      
   ###########unknown option sent ################
   else:
      arizonareport.send_out(0, "Unknown option: " + str(args[0]))
      print short_message
      
      sys.exit(2)








# Start main
if __name__ == "__main__":
   try:
      storkerror.init_error_reporting("storkutil.py")
      main()
   except KeyboardInterrupt:
      arizonareport.send_out(0, "Exiting via keyboard interrupt...")
      sys.exit(0)
