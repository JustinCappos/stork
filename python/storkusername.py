#! /usr/bin/env python

"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: storkusername
Description:  Determines the prefix for configuration files
"""

# Use arizonaconfig
#           [option, long option,              variable,               action,  data,     default, metavar,    description]
"""arizonaconfig
   options=[["-u",   "--username",             "username",             "store", "string", "",      "USERNAME", "use this username for configuration files"],
            ["",     "--publickeyfile",        "publickeyfile",        "store", "string", "",      "file",     "use this public key file to determine which configuration files to use.  Recommended: /usr/local/stork/var/keys/[username].publickey"],
            ["",     "--defaultusername",      "defaultusername",      "store", "string", "default",  None,    "default username to use if file starting with username does not exist"],
            ["",     "--defaultpublickey",     "defaultpublickey",     "store", "string", "",  None,           "public key to go with --defaultusername"],
            ["",     "--keydir",               "keydir",               "store", "string", "/usr/local/stork/var/keys", None, "place to store keys"],
            ["",     "--noplckeys",            "noplckeys",            "store_true",  None,     False,      None,    "do not use SSH-keys from PLC"],
            ["",     "--plckeysmethod",        "plckeysmethod",        "store", "string", "nodemanager", None, "method to use to retrieve public keys from PLC ('nodemanager' or 'planetlabAPI')"]]

   includes=[]
"""

import arizonaconfig
import arizonacrypt
import arizonareport
import arizonageneral
import sys
import xmlrpclib
import os
import storkwarning


initialized = False
full_username = None

# this dictionary holds all keys for all slices
glo_all_slice_keys = None

"""
   a list of tuples that specifies public keys that are available. The format
   of the tuple is:
       (username, keyfilename, key_sl, key_string, config_prefix)

       username    - the stork username

       keyfilename - filename of local file containing key

       key_sl - stringlist containing contents of keyfilename

       key_string - key_sl as a single long string

       config_prefix - prefix of config files using this key
"""

glo_keylist = []

def get_planetlab_publickeys(slicename):
   """
   <Purpose>
      Get public keys from planetlab.

   <Arguments>
     slicename:    Slice name.
     
     method:       How to retrieve the keys. Default is to use the nodemanager
                   running at http://localhost:812/. The other option is
                   'planetlabAPI', which will use the planetlabAPI module to
                   query the PLC API (this requires that
                   planetlabAPI.planetlabLogin was called first.)
     
   <Side Effects>
      None

   <Returns>
      A list of tuples (sshusername, publickey_filename), or [] if PlanetLab
      returns an empty keylist.
   """

   # the format of glo_all_slice_keys will vary depending on what plckeysmethod is used
   global glo_all_slice_keys

   method = arizonaconfig.get_option("plckeysmethod")

   # get the key database from the nodemanager or the PLC APU
   # we only need to do this once
   if not glo_all_slice_keys:
       if method == 'nodemanager':
           glo_all_slice_keys = xmlrpclib.ServerProxy('http://localhost:812/').GetSSHKeys()
           arizonareport.send_out(4, "glo_all_slice_keys (retrieved from nodemanager): " + str(glo_all_slice_keys))

       elif method == 'planetlabAPI':
           import planetlabAPI
           # this assumes planetlabAPI.PlanetLablogin has been already called elsewhere
           glo_all_slice_keys = planetlabAPI.doplccall('GetSliceKeys')
           arizonareport.send_out(4, "glo_all_slice_keys (retrieved from PLC API with GetSliceKeys): " + str(glo_all_slice_keys))

   sshkeys = []

   # get a list of keys for the requested slice
   if method == 'nodemanager':
       # the database is indexed by slicename. Each entry is a big string that
       # is seperated by newlines.
       sshkeys = glo_all_slice_keys.get(slicename, None)
       # SMB: if sshkeys == None, it'll fall through and be caught by an
       #      'if' statement below
       if sshkeys:
          sshkeys = sshkeys.split("\n")

   elif method == 'planetlabAPI':
       for keyentry in glo_all_slice_keys:
          if keyentry['name'] == slicename:
              sshkeys.append(keyentry['key'])

   if not sshkeys:
       arizonareport.send_error(0, "Failed to get public keys for slice " + slicename)
       return []

   keydir = arizonaconfig.get_option("keydir")
   # create the keydir if it doesn't exist
   if not os.path.exists(keydir):
       os.mkdir(keydir)

   keylist = []

   for i, sshkey in enumerate(sshkeys):
       #arizonareport.send_out(4, "Convert key " + str(i) + ": " + sshkey)

       # PlanetLab may return blank entries among the keys, so skip those
       sshkey = str(sshkey).strip()
       if len(sshkey) == 0: continue

       # use a different temp file for each. without this was encountering occurrences of
       # the previous key still in the file when keyconvert was called by convert_ssh_to_ssl.
       # not sure why that was happening, but this does fix it.
       sshfn = os.path.join(keydir, str(i) + ".tmp.pub")
       sslfn = os.path.join(keydir, "key_" + slicename + "_" + str(i) + ".publickey")

       sshf = file(sshfn, "w")
       sshf.write(sshkey)
       sshf.close()

       arizonacrypt.convert_ssh_to_ssl(sshfn, sslfn)

       os.remove(sshfn)

       # extract the username from the sshkey. The sshkey is in three parts:
       # "ssh-rsa key username", so split it and take the third part
       # TODO: support for DSA keys (ssh-dss?)
       split_key = sshkey.split(" ")
       if len(split_key) > 2:
          sshuser = split_key[2]
          # get rid of the hostname part of an email address
          sshuser = sshuser.split("@")[0]
       else:
          sshuser = "unspecified"

       keylist.append((sshuser, sslfn))

   return keylist


def build_default_keytuple():
   default_username = arizonaconfig.get_option("defaultusername")
   default_pkstring = arizonaconfig.get_option("defaultpublickey")

   if default_username and default_pkstring:
      keydir = arizonaconfig.get_option("keydir")
      default_sl = arizonacrypt.fnstring_to_publickey_sl(default_pkstring)
      default_fn = os.path.join(keydir, "_default.publickey")

      f = file(default_fn, "w")
      for item in default_sl:
         f.write(item.rstrip('\r\n')+'\n')
      f.close()

      prefix = default_username + "." + default_pkstring

      return (default_username, default_fn, default_sl, default_pkstring, prefix)

   return None

def reset_key_database():
   """
   <Purpose>
      Resets the key database. This should be called if an event occurs that
      would change what public keys are usable -- for example if a new
      publickey is downloaded from the repository.

   <Arguments>
      Slice name.

   <Side Effects>
      glo_keylist is set to an empty list

   <Returns>
      None
   """
   global glo_keylist

   glo_keylist = []

def build_key_database(reset = False, ignore_username = False):
   """
   <Purpose>
      Builds a database of public keys. Keys are downloaded from PLC and
      converted from ssh to openssl format (as long as --noplckeys is not
      used). In addition, the --publickey file is read if it is present.

   <Side Effects>
      glo_keylist is filled with a list of usable publickey tuples

   <Returns>
      glo_keylist
   """
   global glo_keylist

   if reset:
      reset_key_database()

   # see if we are already done
   if glo_keylist:
      return glo_keylist

   slicename = arizonageneral.getslicename()
   if slicename:
      on_planetlab = True
   else:
      on_planetlab = False
      # SMB: set slicename to "noslice" if no slice name is available. This
      # will allow a non-planetlab user to have a default filename for his
      # files.
      slicename = "noslice"

   arizonareport.send_out(4, "[DEBUG] slicename = " + str(slicename))

   if on_planetlab and (not arizonaconfig.get_option("noplckeys")):
      try:
         keylist = get_planetlab_publickeys(slicename)
      except Exception, e:
         arizonareport.send_error(0, "Failed to get public keys from planetlab (exception)")
         # TODO: log the type of exception
         storkwarning.log_warning("warning.noplckeys", str(e))
         sys.exit(-1)

      # If keylist == [], then PLC didn't return any keys. Treat this as
      # an error
      if not keylist:
         arizonareport.send_error(0, "Failed to get public keys from planetlab (no keys)")
         storkwarning.log_warning("warning.noplckeys", "nokeys")
         sys.exit(-1)
   else:
      keylist = []

   arizonareport.send_out(4, "[DEBUG] keylist = " + str(keylist))

   if ignore_username:
      username = None
   else:
      username = arizonaconfig.get_option("username")

   # if they forgot to set the username or the publickeyfile
   if not username:
      # if --username isn't specified, then default to using the slicename
      username = slicename
      # if we still don't know what the username is, then complain
      if not username:
         # Oops, error and remind them...
         arizonareport.send_error(0, "Failed to get username from slicename")
         arizonareport.send_error(0, "Must specify the '--username' option")
         sys.exit(1)

   # the --publickeyfile option is treated like an additional key and is added
   # to the list.
   publickeyfile = arizonaconfig.get_option("publickeyfile")
   if publickeyfile:
      keylist.append(("arizonaconfig", publickeyfile))

   # complain if we didn't come up with a publickey anywhere that we can use
   if not keylist:
      arizonareport.send_error(0, "No public keys available. Try '--publickeyfile'.")
      sys.exit(1)

   for keytuple in keylist:
      (success, publickey_sl) = arizonacrypt.publickey_fn_to_sl(keytuple[1])

      if not success:
         # Oops, error and tell them
         arizonareport.send_error(0, "Invalid or missing publickeyfile: '" + keytuple[1] + "'")
         sys.exit(1)

      # add two entries to the keylist: one using the old filename embedded key format
      # for the publickey, the other using the new system where the hash is embedded

      publickey_string_oldformat = arizonacrypt.publickey_sl_to_fnstring_compat(publickey_sl)
      # SMB: only generate old-style filenames if the publickey is exactly
      #      126 bytes long (same technique as arizonacrypt.fnstring_to_publickey_sl)
      if len(publickey_string_oldformat) == 126:
         prefix = username + "." + publickey_string_oldformat
         glo_keylist.append((username, keytuple[1], publickey_sl, publickey_string_oldformat, prefix))

      publickey_hash = arizonacrypt.publickey_sl_to_fnstring(publickey_sl)
      prefix = username + "." + publickey_hash
      glo_keylist.append((username, keytuple[1], publickey_sl, None, prefix))

   arizonareport.send_out(4, "[DEBUG] glo_keylist = " + str(glo_keylist))

   return glo_keylist

def dump():
   arizonareport.send_out(0, "key database: ")
   for keytuple in build_key_database():
      arizonareport.send_out(0, "  " + keytuple[0] + ": " + keytuple[3])

   arizonareport.send_out(0, "default key (used when none of the above exist):")
   default_tuple = build_default_keytuple()
   if default_tuple:
      arizonareport.send_out(0, "  " + default_tuple[0] + ": " + default_tuple[3])
   else:
      arizonareport.send_out(0, "  None")


def publickey_strings():
   global glo_keylist

   if not glo_keylist:
       build_key_database()

   return [keytuple[4] for keytuple in glo_keylist]


def publickey_string():
   """

   XXX This function is deprecated and will be going away soon

   <Purpose>
      This returns a stringlist containing the publickey

   <Arguments>
      None (all command line arguments)

   <Exceptions>
      TypeError may be returned if the user hasn't specified a username and
      a valid publickeyfile

   <Side Effects>
      None (calls config_prefix())

   <Returns>
      A stringlist containing the publickey
   """
   config_prefix()
   (success, publickey_sl) = arizonacrypt.publickey_fn_to_sl(arizonaconfig.get_option("publickeyfile"))
   publickey_string = arizonacrypt.publickey_sl_to_fnstring(publickey_sl)
   return publickey_string





def config_prefix():
   """

   XXX: This function is deprecated and will be going away soon

   <Purpose>
      This returns the prefix for the configuration files that we want to use.
      This function automatically opens the publickeyfile and embeds that 
      string within the username.

   <Arguments>
      None (all command line arguments)

   <Exceptions>
      TypeError may be returned if the user hasn't specified a username and
      a valid publickeyfile

   <Side Effects>
      Nothing external.   If the publickeyfile is specified as a command line
      arguments it is only parsed the first time this function is called.   
      Every additional time the previous result is returned regardless of 
      changes to this file.

   <Returns>
      A string which contains the prefix for other functions that need signed
      configuration files.   Simply append "."+extension and away you go.
   """
   global initialized
   global full_username

   # Only do this the first time
   if not initialized:

      # if they forgot to set the username or the publickeyfile
      if not arizonaconfig.get_option("username"):
         # Oops, error and remind them...
         arizonareport.send_error(0, "Must specify the '--username' option")
         sys.exit(1)

      if not arizonaconfig.get_option("publickeyfile"):
         # Oops, error and remind them...
         arizonareport.send_error(0, "Must specify the '--publickeyfile' option")
         sys.exit(1)

      # Open the publickeyfile
      (success, publickey_sl) = arizonacrypt.publickey_fn_to_sl(arizonaconfig.get_option("publickeyfile"))

      if not success:
         # Oops, error and tell them
         arizonareport.send_error(0, "Invalid or missing publickeyfile in config_prefix: '" + arizonaconfig.get_option("publickeyfile") + "'")
         sys.exit(1)

      # now set the full username to be username.publickeystring
      full_username = arizonaconfig.get_option("username") + "." + arizonacrypt.publickey_sl_to_fnstring(publickey_sl)

      # Don't go through this mess again...
      initialized = True

   # Return the full username
   return full_username

