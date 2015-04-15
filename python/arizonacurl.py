"""
<Program Name>
   arizonacurl

<Started>
  Oct 20, 2006

<Author>
   Programmed by Jeremy Plichta

<Purpose>
   Fetch a users pubkey files and conf files using curl
"""

import arizonaconfig
import arizonageneral
import arizonareport
import arizonacrypt
import storkpackagelist
import storkusername
import tempfile
import os
import sys
import shutil


#           [option, long option,    variable,     action,        data,     default,                            metavar, description]
"""arizonaconfig
   options=[   
            ["-C",   "--configfile", "configfile", "store",       "string", "/usr/local/stork/etc/stork.conf", "FILE",   "use a different config file (/usr/local/stork/etc/stork.conf is the default)"],
            ["",  "--certificate","certificate","store",       "string", "/usr/local/stork/var/certificates/nr06.certificate", "STRING",    "use a different certificate for downloading conf files from repository. the default is /usr/local/stork/var/certificates/nr06.certificate"],
            ["",  "--repositorypath","repositorypath","store", "string", "https://stork-repository.cs.arizona.edu/user-upload/", "STRING",    "use a different repository to download configuration files from. the default is https://stork-repository.cs.arizona.edu/user-upload/"],
            ["",  "--insecure","insecure","store_true",       None, False, None,    "do not use https for transfering configuration files from the repository using curl"],
            ["",     "--publickeyfile", "publickeyfile", "store", "string", "",      "file",     "use this public key file to determine which configuration files to use.  Recommended: /usr/local/stork/var/keys/[username].publickey"],
            ["",     "--requiresignedconf", "requiresignedconf", "store_true", None, False,      None,     "require downloaded configuration files to be signed. Default: False."]]
   includes=[]
"""






def fetch_conf():
    """ 
    <Purpose>
        This function will attempt to download the users public key
        and configuration file from the stork repository (or whatever
        repository they specified using the repository option

    <Arguments>
        None
        
    <Exceptions>
        None
        
    <Side Effects>
        temp files will be created in /tmp and the the users
        public key file will be replaced. The users configuration
        file will also be replaced with the downloaded one if it
        is succesfull

        if the path to the specied config file does not exist
        it will be created

    <Returns>
      True - if we loaded a new conf file and should reload the
             options
     False - if we did not replace the configuration file
    """

    # try to get the certificate and repositorypath options
    certificate = arizonaconfig.get_option("certificate")
    reppath     = arizonaconfig.get_option("repositorypath")
    useinsecure = arizonaconfig.get_option("insecure")
    conffile = arizonaconfig.get_option("configfile")
    restartFlag = False
    foundNewFile = False

    # filename to use for tmpconf file (this is the one that we will
    # download using curl
    (tmpconffd, tmpconffile) = tempfile.mkstemp(suffix="arizonacurl.temp")
    os.close(tmpconffd)

    # Try finally block to remove the tempfile regardless of outcome
    try:
      if not useinsecure and not certificate:
          arizonareport.send_error(1, "no certificate specified")
          return False
      if not useinsecure and not os.path.isfile(certificate):
          arizonareport.send_error(1, "could not open certificate: "+certificate+" while trying to initiate curl transfer to download configuration file. Use --insecure to transfer without a certificate")
          return False

      if not storkpackagelist.glo_initialized:
          storkpackagelist.init()

      # SMB: make sure we only find config files named after the slicename,
      # not after the username
      storkusername.build_key_database(reset=True, ignore_username = True)

      result = storkpackagelist.find_file_kind("conf", "stork.conf")

      # SMB: the remainer of stork will use files named after the username,
      # so reset the key database that we messed with above
      storkusername.reset_key_database()

      if not result or result[0] == None:
          arizonareport.send_error(3, "Unable to a locate signed conf file in the repository.")
          # if we didn't find a signed file and we are requiring one, then stop here
          if arizonaconfig.get_option("requiresignedconf"):
              arizonareport.send_error(3, "Config options indicate only signed configuration files allowed. Will not look for unsigned conf files.")
              return False
      else:
          arizonareport.send_error(3, "Found signed config file: " + str(result[0]))
          try:
             arizonacrypt.XML_retrieve_originalfile_from_signedfile(result[0], tmpconffile)
             foundNewFile = True
          except TypeError:
             arizonareport.send_error(3, "Unable to extract unsigned file from the signed config file that was found.")
             return False

      # we didn't find a signed file, so look for an (old-style) unsigned file
      # this if block could be removed if/when support for unsigned conf files is removed
      if not foundNewFile:
          # check to make sure that the repository path is / terminated
          if reppath[-1] != '/':
              reppath += '/'

          #build the file we want to download
          #default reppath should be:
          #   https://nr06.cs.arizona.edu/user-upload/
          #so construct the rest of the path to the
          #file we want to download
          # now try to get configuration file
          file = reppath + "conf/" + arizonageneral.getusername() + ".stork.conf"

          #ensure that the directory exists
          condfir   = None
          lastslash = conffile.rfind("/")
          if lastslash > 0:
             try:
                confdir = conffile[:lastslash]
                if not os.path.exists(confdir):
                   os.makedirs(confdir)
             except (OSError, IndexError):
                pass

          arizonareport.send_out(3,"[INFO] Attempting to download unsigned configurations from: "+file)

          if useinsecure:
              execstring = "curl --insecure -w '%{http_code}' " + file + " -o "+tmpconffile
          else:
              execstring = "curl --cacert "+certificate+" -w '%{http_code}' " + file + " -o "+tmpconffile
          out, err, status = arizonageneral.popen5(execstring)
          if len(out) < 1 or out[0] != "200":
              arizonareport.send_error(3,"[INFO]: I was unable to download your configuration file from: "+file+"[USING DEFAULT CONF FILE]: "+conffile)
          else:
              foundNewFile = True
              # JRP: putting in code to get rid of any of the old conffiles
              if os.path.isfile(conffile+".old"):
                  os.system("rm -f "+conffile+"*.old* 2>/dev/null")

      # if we found a new conf file, we'll see if we should install it
      if foundNewFile:

          # if there's an existing conf file, only overwrite it if the downloaded one is different
          if os.path.isfile(conffile):

              # added a try block to catch any IOError that might
              # be raised by the get_fn_hash function, which
              # shouldnt happen unless something really goes wrong,
              # ex: the conffile or .tmpconffile dont exist (maybe
              # there was a problem saving or accessing the tmpconffile?
              try:
                 curhash  = arizonacrypt.get_fn_hash(conffile)
                 newhash  = arizonacrypt.get_fn_hash(tmpconffile)
              except IOError:
                 arizonareport.send_error(3, "There was an error while comparing your old configuration file")
               
                 # try to figure out why this happened
                 if not os.path.isfile(tmpconffile):
                    arizonareport.send_error(3, "There was an error while getting the hash of: "+tmpconffile+\
                                                ", that file does not seem to exist.")
                 elif not arizonageneral.valid_fn(tmpconffile):
                    arizonareport.send_error(3, "There was an error while getting the hash of: "+tmpconffile+\
                                                ", that file exists but cannot be read from.")
               
                 arizonareport.send_error(3, "Aborting update of "+conffile+". It will remain unchanged.") 
                 return False
               
              if curhash != newhash:
                  arizonareport.send_error(3, "Downloaded conf file is different than current file, replacing current file.") 
                  restartFlag = True
                  move_file(conffile)
                  shutil.copy(tmpconffile,conffile)
              else:
                  arizonareport.send_error(3, "Downloaded conf file is the same as the current file.")
          
          # there's no existing conf file
          else:
              restartFlag = True
              shutil.copy(tmpconffile,conffile)

    # clean up the temp file
    finally:
       os.remove(tmpconffile)

    return restartFlag




def fetch_pubkey():
    """
    <Purpose>
         This function will attempt to download the users public key
         from the stork repository (or whatever
         repository they specified using the repository option

    <Side Effects>
         temp files will be created in /tmp and the the users
         public key file will be replaced.

    <Returns>
       True - if we loaded a new public key and need to rebuild key database
      False - if we did not replace the public key
    """
   
    certificate = arizonaconfig.get_option("certificate")
    reppath     = arizonaconfig.get_option("repositorypath")
    useinsecure = arizonaconfig.get_option("insecure")

    restartFlag = False
    
    #check to see if the certificate exists
    if not useinsecure and not os.path.isfile(certificate):
        arizonareport.send_error(1,"could not open certificate: "+certificate+" while trying to initiate curl transfer to download public key file. Use --insecure to transfer without a certificate")
        return False

    #build the file we want to download
    #default reppath should be:
    #   https://nr06.cs.arizona.edu/user-upload/
    #so construct the rest of the path to the
    #file we want to download
    file = reppath + "pubkeys/" + arizonageneral.getusername() + ".publickey"
    
    
    arizonareport.send_out(3,"[INFO] Attempting to download your custom public key from: "+file)

    pubkey = arizonaconfig.get_option("publickeyfile")
    #ensure that the directory exists
    keydir = None
    lastslash = pubkey.rfind("/")
    if lastslash > 0:
       try:
          keydir = pubkey[:lastslash]
          if not os.path.exists(keydir):
             os.makedirs(keydir)
       except (OSError, IndexError):
          pass

    # Generate a temp to hold the public key we'll d/l
    (tmppubkeyfd, tmppubkeyfile) = tempfile.mkstemp(suffix="arizonacurlpub.temp")
    os.close(tmppubkeyfd)

    # Try finally block to remove the temp file
    try:
       if useinsecure:
           execstring = "curl --insecure -w '%{http_code}' " + file + " -o "+ tmppubkeyfile
       else:
           execstring = "curl --cacert "+certificate+" -w '%{http_code}' " + file + " -o "+tmppubkeyfile
       out, err, status = arizonageneral.popen5(execstring)

       if len(out) < 1 or out[0] != "200":
           arizonareport.send_error(3,"[INFO]: I was unable to download your public key from: "+file+" . If you would like to upload one please go to http://quiver.cs.arizona.edu/testphp/upload.php. After you upload your public for your slice it will be automatically distributed when stork starts up. [USING DEFAULT PUBKEY]: "+pubkey)
       else:
           # JRP: putting in code to get rid of any of the old conffiles
           if os.path.isfile(pubkey+".old"):
              os.system("rm -f "+pubkey+"*.old* 2>/dev/null")

           # move the public key file to its new location
           if pubkey != "":
               # I dont think there is a option for key location: at least
               # not that I could find.. Maybe I need to look harder.
               # We really shouldn't be hardcoding paths in here.
               if not os.path.isdir("/usr/local/stork/var/keys"):
                   os.mkdir("/usr/local/stork/var/keys")

               # check to see if the pub key has changed
               if os.path.isfile(pubkey):
                  curhash  = arizonacrypt.get_fn_hash(pubkey)
                  newhash  = arizonacrypt.get_fn_hash(tmppubkeyfile)
                  if not curhash == newhash:
                      restartFlag = True
                      #back up the file if it has changed
                      move_file(pubkey)
                      shutil.copy(tmppubkeyfile, pubkey)
               else:
                  # there was no existing pubkey file
                  restartFlag = True
                  shutil.copy(tmppubkeyfile, pubkey)

    finally:
       # clean up the downloaded file
       try:
          os.unlink(tmppubkeyfile)
       except OSError:
          arizonareport.send_error(3, "[INFO] Could not remove temporary file `" + str(tmppubkeyfile) + "'")

    return restartFlag




def move_file(fn):
    """Renames file fn to have a period and number appended to it, incrementing
       the number as needed so as to not overwrite existing files."""

    lastind = fn.rfind(".")
    num   = 0
    try:
       num = int( fn[lastind+1:] )
       first = fn[:lastind]
    except ValueError:
       first = fn
    
    # [jsamuel] when this gets to backup number 6, this always overwrites number 6, so
    # why bother keeping more than one backup since after a while it will just be one anyways?
    if os.path.exists(first+"."+str(num+1)) and num<5:
        move_file(first + "." + str(num+1))

    shutil.move(fn,first+"."+str(num+1))



# Start main
'''if __name__ == "__main__":
   try:
      # use error reporting tool
      #storkerror.init_error_reporting("stork.py")

      # get command line and config file options
      args = arizonaconfig.init_options("arizona_curl.py", configfile_optvar="configfile", version="2.0")
      main();
   except KeyboardInterrupt:
      arizonareport.send_out(0, "Exiting via keyboard interrupt...")
      sys.exit(0)
'''

