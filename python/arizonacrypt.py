#! /usr/bin/env python
"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: arizonacrypt
Description:  Provides cryptographic utility functions and commands

Notes:
Stork's cryptographic features rely on communication with openssl.

The functions used here either take string lists or filenames as 
arguments.  Which it takes can be determined by the function suffix "sl" 
or "fn".  There are also routines sl_to_fn and fn_to_sl to convert between 
the two formats.


"""


# This sets up the options for arizonaconfig
#           [option, long option,  variable,   action,  data,     default,  metavar,    description]#
"""arizonaconfig
   options=[["",     "--keytype",  "keytype",  "store", "string", "rsa",    "KEYTYPE",  "Use this technique to sign files (default is rsa)"],
            ["",     "--keygen",   "keygen",   "store", "string", "genrsa", "GENTYPE",  "Use this option to openssl to generate your public/private keypair (default is genrsa)"],
            ["",     "--numbits",  "numbits",  "store", "string", "1024",   "NUMBITS",  "Use this option to openssl to set the size of key modulus in bits (default is 1024)"],
            ["",     "--xmlsignaturedtd",     "xmlsigndtd",  "store",       "string", "arizonacrypt_signature.dtd", "FILENAME",  "The DTD file for signatures"],
            ["",     "--hashtype", "hashtype", "store", "string", "-sha1",  "HASHTYPE", "Use this algorithm to generate hashes (default is -sha1)"]]
   includes=[]
"""

import sys
import re
import os.path
import tempfile
import shutil
import arizonareport
import arizonaconfig
import arizonageneral
import arizonaxml
import time
import base64
import binascii
import sha

# None means we don't know get; call openssl_supports_passin to find out
glo_openssl_supports_passin = None




def valid_sl(stringlist):
   """
   <Purpose>
      This returns True if stringlist is a list of strings or False if it  
      is not.

   <Arguments>
      stringlist:
          The variable to be checked.

   <Exceptions>
      None

   <Side Effects>
      None

   <Returns>
      True or False (see above)
   """

   try:
      arizonageneral.check_type_stringlist(stringlist, "stringlist", "valid_sl")
      return True
   except TypeError:
      return False

   



def sl_to_fn(stringlist):
   """
   <Purpose>
      This dumps a string list to a tempfile and returns the filename...
      The calling routine *must* remove the tempfile when finished...

   <Arguments>
      stringlist:
            The list that should be dumped to a file.   This must be a
            list of strings.   If it is invalid, it will throw TypeError

   <Exceptions>
      TypeError if stringlist is not a list of strings...

   <Side Effects>
      This function creates the file whose name it returns.

   <Returns>
      The name of the temp file it creates.
   """

   if not valid_sl(stringlist):
      raise TypeError, "Invalid stringlist in sl_to_fn"
      
   # Get a new temp file
   (thisfile,thisfilename) = tempfile.mkstemp(suffix=".sl_to_fn.temp")

   # Write the stringlist into the file
   for item in stringlist:
      os.write(thisfile, item.rstrip('\r\n')+'\n')

   # Close the fd
   os.close(thisfile)

   # Return the file name
   return thisfilename






def fn_to_sl(filename):
   """
   <Purpose>
      This takes a file and reads the contents as a list of strings.
      It returns the list of strings.   This function does not remove
      the file.

   <Arguments>
      filename:
            This is the filename containing the string list.  If it is 
            invalid, it will throw IOError or OSError and set errno, etc. 
            appropriately

   <Exceptions>
      IOError or OSError if filename has errors...   There is basically
      no checking in this routine.   The routines in os should correctly
      throw exceptions...

   <Side Effects>
      None

   <Returns>
      The stringlist containing the file data
   """

   # This should throw an exception if there are problems.   The outer program
   # will catch it...
   fileobj = open(filename, "r")
   
   sl = arizonageneral.stream_to_sl(fileobj)
   fileobj.close()
   return sl





def get_genkey_type(type_of_genkey=None):
   """
   <Purpose>
      This returns the default genkey if given None or the given string 
      otherwise.   

   <Arguments>
      type_of_genkey:
            This is the (possibly) user specified key type.  If the value 
            is not specified then the default is used.

   <Exceptions>
      TypeError if type_of_genkey is not a string, etc.

   <Side Effects>
      None

   <Returns>
      A string containing the genkey function that should be used.
   """


   # Did they specify the argument?
   if type_of_genkey == None:
      ret_val = arizonaconfig.get_option("keygen")
   else:
      ret_val = type_of_genkey

   try:
      return "" + ret_val
   except TypeError:
      raise TypeError, "Invalid genkey type in get_genkey_type"




def get_key_numbits(numbits_of_key=None):
   """
   <Purpose>
      This returns the default numbits if given None or the given string
      otherwise.

   <Arguments>
      numbits_of_key:
            This is the (possibly) user specified key modulus size in bits.
            If the value is not specified then the default is used.

   <Exceptions>
      TypeError if numbits_of_key is not a string, etc.
      ValueError if numbits_of_key is not >= 512.

   <Side Effects>
      None

   <Returns>
      A string containing the numbits value that should be used.
   """

   # Did they specify the argument?
   if numbits_of_key == None:
      ret_val = arizonaconfig.get_option("numbits")
   else:
      ret_val = numbits_of_key

   if int(ret_val) < 512:
       raise ValueError, 'Invalid numbits: must be >= 512'

   try:
      return "" + str(ret_val)
   except TypeError:
      raise TypeError, "Invalid numbits type in get_key_numbits"




def get_key_type(type_of_key=None):
   """
   <Purpose>
      This returns the default key type if given None or the given string 
      otherwise.   

   <Arguments>
      type_of_key:
            This is the (possibly) user specified key type.  If the value 
            is not specified then the default is used.

   <Exceptions>
      TypeError if type_of_key is not a string, etc.

   <Side Effects>
      None

   <Returns>
      A string containing the key function that should be used.
   """


   # Did they specify the argument?
   if type_of_key == None:
      ret_val = arizonaconfig.get_option("keytype")
   else:
      ret_val = type_of_key

   try:
      return "" + ret_val
   except TypeError:
      raise TypeError, "Invalid key type in get_key_type"





def get_hash_type(type_of_hash=None):
   """
   <Purpose>
      This returns the default hash if given None or the given string 
      otherwise.   If necessary it prepends "-" to the string.

   <Arguments>
      type_of_hash:
            This is the (possibly) user specified hash type.  If the value 
            is not specified then the default is used.

   <Exceptions>
      TypeError if type_of_hash is not a string, etc.

   <Side Effects>
      None

   <Returns>
      A string containing the hash function that should be used.
   """


   # Did they specify the argument?
   if type_of_hash == None:
      ret_val = arizonaconfig.get_option("hashtype")
   else:
      ret_val = type_of_hash
   try:
      if not ret_val.startswith('-'):
         ret_val = '-'+ret_val
      return "" + ret_val
   except (TypeError, AttributeError):
      raise TypeError, "Invalid hash type in get_hash_type"








def generate_privatekey_sl(type_of_key=None, numbits_of_key=None):
   """
   <Purpose>
      This creates a privatekey and returns the sl.

   <Arguments>
      type_of_key:
            This is the kind of key that should be generated (genrsa, 
            gendsa, etc.).   If the value is not specified then the 
            default is used.

   <Exceptions>
      As thrown by PrivateKey.generate()

   <Side Effects>
      None

   <Returns>
      A string list with the privatekey.
   """
   
   return PrivateKey.generate(type_of_key=type_of_key, numbits_of_key=numbits_of_key).sl





def generate_privatekey_fn(filename,type_of_key=None):
   """
   <Purpose>
      This creates a file that contains a privatekey.

   <Arguments>
      filename:
            This creates a file with this name
      type_of_key:
            This is the kind of key that should be generated (genrsa, 
            gendsa, etc.).   If the value is not specified then the 
            default is used.

   <Exceptions>
      IOError if filename is a directory.
      Otherwise, as thrown by PrivateKey.generate()

   <Side Effects>
      Creates the file "filename"

   <Returns>
      None
   """

   assert(isinstance(filename,str))

   # Check if the dest is a dir
   if os.path.isdir(filename):
      raise IOError, (21, "Is a directory")

   PrivateKey.generate(type_of_key=type_of_key).save_to_file(filename)

      



def extract_publickey_sl_from_privatekey_fn(privatekey_fn,type_of_key=None):
   """
   <Purpose>
      This gets a sl which contains the publickey from a given privatekey 
      filename

   <Arguments>
      privatekey_fn:
            The filename which contains the private key
      type_of_key:
            This is the type of key (rsa, dsa, etc.).   If the value is 
            not specified then the default is used.

   <Exceptions>
      IOError if privatekey_fn is not readable or does not exist.
      Otherwise, as thrown by PrivateKey() and PrivateKey.get_public_key().

   <Side Effects>
      None

   <Returns>
      The sl that contains the public key
   """

   if not arizonageneral.valid_fn(privatekey_fn):
     raise IOError, "Private key file is not readable or does not exist."

   privatekey = PrivateKey(file=privatekey_fn, type=type_of_key)
   return privatekey.get_public_key().sl





def extract_publickey_sl_from_privatekey_sl(privatekey_sl,type_of_key=None):
   """
   <Purpose>
      This gets a sl which contains the publickey from a given privatekey 
      sl

   <Arguments>
      privatekey_sl:
            The sl which contains the private key
      type_of_key:
            This is the type of key (rsa, dsa, etc.).   If the value is 
            not specified or a string then the default is used.

   <Exceptions>
      TypeError is privatekey_sl is not a valid sl.
      Otherwise, as thrown by PrivateKey() and PrivateKey.get_public_key().

   <Side Effects>
      None

   <Returns>
      None
   """

   if not valid_sl(privatekey_sl):
       raise TypeError, "First parameter must be an sl."

   privatekey = PrivateKey(sl=privatekey_sl, type=type_of_key)

   return privatekey.get_public_key().sl





def publickey_fn_to_sl(filename, key_type=None):
   """
   <Purpose>
      This returns a tuple containing a boolean which specifies whether or
      not the file is valid and a stringlist of the publickey stored in 
      the filename.   

   <Arguments>
      filename:
            This the file name that may contain a public key
      key_type:
            The type of public key that will be fetched.   If it is None, 
            then the default is used

   <Exceptions>
      None

   <Side Effects>
      None

   <Returns>
      A tuple containing a boolean indicating success or failure and 
      string list with the publickey 
   """

   publickey = PublicKey(file=filename, type=key_type)

   if not publickey.is_valid():
       return (False, [])
   else:
       return (True, publickey.sl)







def valid_publickey_sl(publickey_sl, key_type=None):
   """
   <Purpose>
      This returns True or False which specifies whether or not the string
      list contains a valid publickey.

   <Arguments>
      publickey_sl:
            This the string list that may contain a public key
      key_type:
            The type of public key that will be fetched.   If it is None, 
            then the default is used

   <Exceptions>
      TypeError if publickey_sl is not a stringlist.

   <Side Effects>
      None

   <Returns>
      A boolean indicating if the publickey is valid or not
   """

   if not valid_sl(publickey_sl):
       raise TypeError, "First parameter must be an sl."

   publickey = PublicKey(sl=publickey_sl, type=key_type)
   return publickey.is_valid()





##
# Create the hash of the metadata
# Either reads metadata as arg or from stdin
# expects null or filename STRING
# returns hash
#def get_metadata_hash(filename, hash_type=None):
#    print "get_metadata_hash is totally bogus"
#    sys.exit(1)
#    import os
#    
#
#    #print "[DEBUG] filename=" + str(filename), #DEBUG !!!!!!!!!!!!!!!!!!!
#    #print "[DEBUG] hash_type=" + str(hash_type), #DEBUG !!!!!!!!!!!!!!!!!!!
#
#    meta = get_metadata(filename)
#    if meta == None:
#        arizonareport.send_error(4, "[DEBUG] get_metadata_hash: No hash, using file contents")
#        return get_fn_hash(filename)
#        #fh = open(filename)
#        #contentsList = fh.readlines()
#        #meta = contentsList[0]
#        #for i in contentsList[1:]:
#        #    meta += i
#        #fh.close()
#        #arizonareport.send_error(4, "[DEBUG] get_metadata_hash: Done reading file contents")
#
#    # Generate the hash
#    ( junk_in, the_out, the_err ) = os.popen3("echo \""+meta+"\" | openssl dgst "+get_hash_type(hash_type))
#
#    # Close the input stream
#    junk_in.close()
#
#    # Grab the data the command spits on stdout
#    out_data = arizonageneral.stream_to_sl(the_out)
#    the_out.close()
#    
#    # Grab the data the command spits on stderr
#    err_data = arizonageneral.stream_to_sl(the_err)
#    the_err.close()
#
#    # If something was put to stderr then fail
#    if not err_data == []:
#        raise IOError, (22, "Invalid argument: Unable to generate hash in get_fn_hash")
#
#    assert(out_data != [])
#
#    arizonareport.send_error(4, "[DEBUG] get_metadata_hash: Hash = " + str(out_data[0]))
#
#    # return the relevant part of the hash
#    return out_data[0]





#def get_metadata(filename):
#    import os
#    import storkpackage
#
#    # TODO FIXME NEEDS WORK BROKEN.. this code MUST NOT be rpm specific
#    #fields = ['%{NAME}', '%{VERSION}', '%{RELEASE}', '%{SIZE}']
#    info = storkpackage.get_package_info(filename)
#    if info == None:
#       return None
#
#    meta = "Package:\n"
#    # append the file hash
#    for data in info:
#    	meta += data + '|'  
#    meta += get_fn_hash(filename, "-sha1")
#
#    # get what requires
#    requires = storkpackage.get_packages_require([filename])
#    # append what requires
#    meta += "\nRequires:\n"
#    meta += '|' + '|'.join(requires)
#    
#    # get what provides
#    provides = storkpackage.get_packages_provide([filename])   
# 
#    # append what provides
#    meta += "\nProvides:\n"
#    meta += '|' + '|'.join(provides)
#
#    # get what files are in the package
#    files = storkpackage.get_packages_files([filename])
#    shortname = ''
#    for name in files:
#	shortname += "|" + os.path.basename(name)
#
#    # append the filenames
#    meta += "\nFiles:\n"
#    meta += shortname
#
#    return meta



def get_openssl_command():
   """
   <Purpose>
      Determine the command to be used to execute openssl
   <Returns>
      Appropriate command name for windows or linux
   """
   # TODO: verify that openssl exists at the path we think it does
   #       research alternate windows locations (not everyone uses C:)
   if os.path.sep == "\\":
   	return "C:\\OpenSSL\\bin\\openssl.exe"
   else:
   	return "openssl"





def get_openssl_version():
   """
   <Purpose>
      Get the version number of openssl
   <Returns>
      Version number of openssl
   """
   global glo_openssl_version

   # try to only do this once
   if glo_openssl_version:
      return glo_openssl_version

   command = get_openssl_command() + " version"
   (the_in, the_out, the_err) = os.popen3(command)

   the_in.close()
   the_err.close()

   ver_string = the_out.read()
   the_out.close()

   # ver_string will look like "openssl version date"

   glo_openssl_verison = ver_string.split(" ")[1]

   return glo_openssl_version





def openssl_supports_passin():
   """
   <Purpose>
      See if openssl supports -passin
   <Returns>
      True if openssl supports -passin, false otherwise
   """
   global glo_openssl_supports_passin

   # only do this once
   if glo_openssl_supports_passin != None:
       return glo_openssl_supports_passin

   # execute a simple command; it'll fail if -passin is not supported
   command = get_openssl_command() + " dgst -passin pass: < /dev/null >/dev/null 2>&1"
   status = os.system(command)

   glo_openssl_supports_passin = (status == 0)
   return glo_openssl_supports_passin




def get_openssl_passin_arg(privatekey_password):
   """
   <Purpose>
      Generate a -passin argument for an openssl command.
   <Arguments>
      privatekey_password. The password that goes with the privatekey. If None,
      then try to use "-passin pass:" to tell openssl there is no pkey.
   <Returns>
      -passin argument
   """
   if privatekey_password != None:
      # TODO: check openssl_supports_passin(). If it is false, then we have a
      # problem.
      return "-passin stdin "

   # if no password, make sure an empty password is sent, otherwise it will be prompted
   # for on stdin if one is needed and this may cause the running program to hang
   
   elif openssl_supports_passin():
      return " -passin pass: "
   else:
      return ""



def get_fn_hash(filename,hash_type=None):
   """
   <Purpose>
      This returns the hash of a file's contents given the name

   <Arguments>
      filename:
            This the name of the file to generate a hash for
      hash_type:
            The hash function that should be used.   If it is None, then
            the default is used

   <Exceptions>
      IOError will be thrown when the file is invalid or another file 
      related error occurs.   TypeError may also be thrown if hash_type is
      invalid.

   <Side Effects>
      None

   <Returns>
      A string containing the file's hash
   """

   # Check the file name
   if not arizonageneral.valid_fn(filename):
      raise IOError, (2, "Invalid file in get_fn_hash: " + str(filename))

   # Generate the hash
   #os.path.sep == "\\" indicates we are on Windows
   ( junk_in, the_out, the_err ) = os.popen3(get_openssl_command()+" dgst " + get_hash_type(hash_type) + " " + filename)

   # Close the input stream
   junk_in.close()

   # Grab the data the command spits on stdout
   out_data = arizonageneral.stream_to_sl(the_out)
   the_out.close()

   # Grab the data the command spits on stderr
   err_data = arizonageneral.stream_to_sl(the_err)
   the_err.close()

   # If something was put to stderr then fail
   if not err_data == []:
      raise IOError, (22, "Invalid argument: Unable to generate hash in get_fn_hash")

   assert(out_data != [])

   # return the relevant part of the hash
   return out_data[0].split()[1]




def publickey_sl_to_fnstring_compat(publickey_sl):
   """
   <Purpose>
      Used only for compatibility with old fnstrings. A mangled version of
      the public key used to be stored in filenames. This will do such
      mangling.
   
      This removes unnecessary information from a publickey_sl and returns
      only a string containing the characters that form the publickey.   
      Leading and trailing '=' are removed and all '/' are replaced by '_'
      to allow this string to be used as a filename.   The publickey_sl is
      not checked for validity.

   <Arguments>
      publickey_sl:
            This is the stringlist containing the publickey

   <Exceptions>
      TypeError will be thrown

   <Side Effects>
      None

   <Returns>
      A string containing the publickey in the above format
   """

   # Strip out the lines that start with -----
   new_publickey_sl = []
   for item in publickey_sl:
      if not item.startswith('-----'):
         new_publickey_sl.append(item)

   # Make it one string
   publickey_string = "".join(new_publickey_sl)

   # Replace '/' with '_' and remove '='   
   publickey_string = re.sub('/','_',publickey_string)
   publickey_string = publickey_string.strip('=')

   return publickey_string



def publickey_sl_to_fnstring(publickey_sl):
   """
   <Purpose>
      Returns the identifier for the public key for use in filenames.
      Note that since the change to long key support, the returned value
      for use in filenames is just a hash of the key, not a form of the
      key itself.

   <Arguments>
      publickey_sl:
            This is the stringlist containing the publickey

   <Exceptions>
      None

   <Side Effects>
      None

   <Returns>
      A string containing the publickey in the above format
   """

   return PublicKey(sl=publickey_sl).hash





def fnstring_to_publickey_sl(fnstring, force_unmangling=False):
   """
   <Purpose>
      This generates a publickey_sl given a string as would be generated
      by publickey_sl_to_fnstring_compat or just a standard public key string
      (that is, an actual public key as a single string with no newlines).

   <Arguments>
      fnstring:
            This is the string (in either old-mangled-string format or as an
            actual public key as a string with no newlines) to be converted
            to a publickey_sl.
      force_unmangling:
            If true, key is unmangled (to turn old-style mangled key back
            into valid base64) even if it is not 126 characters long in its
            mangled state (126 characters is the length of a mangled
            512 bit key).

   <Exceptions>
      None

   <Side Effects>
      None

   <Returns>
      A stringlist containing the publickey where the strings are at most 64
      characters long (as one might find in an openssl key file). This must
      be checked elsewhere for validity.
   """

   # if the caller gave us a pathname, then we only want to filename part
   # removed 2007-07-12. will cause problems if fnstring is valid base64,
   # which may contain "/" characters
   #(path, fnstring) = os.path.split(fnstring)

   # get just the pub key in the filename, not the whole filename itself
   tmppub  = fnstring.split(".")
   if len(tmppub) > 1:
       fnstring= tmppub[1];

   # check if this is an old key fnstring format and correct
   publickey_string = fnstring
   if force_unmangling or len(publickey_string) == 126:
     # Replace _ by / and append ==
     publickey_string = re.sub('_','/',publickey_string)+"=="

   fnstring = publickey_string

   # Append the leading line
   publickey_sl = ['-----BEGIN PUBLIC KEY-----']

   # split the key into 64-byte lines
   tmp = publickey_string
   while tmp:
       publickey_sl.append(tmp[:64])
       tmp = tmp[64:]

   # Now append the trailing line
   publickey_sl.append('-----END PUBLIC KEY-----')

   return publickey_sl




   
def fnstring_to_publickey(fnstring):
   """
   <Purpose>
      This generates a publickey object from a filename string. Basically a
      wrapper around fnstring_to_publickey_sl that returns objects rather
      than stringlists.

   <Arguments>
      fnstring:
            This is the string (in either old-mangled-string format or as an
            actual public key as a string with no newlines) to be converted
            to a publickey_sl.

   <Exceptions>
      TypeError, when fnstring does not contain a valid public key

   <Returns>
      A publickey object containing the public key
   """
   sl = fnstring_to_publickey_sl(fnstring)
   if not sl:
      raise TypeError, "fnstring '" + fnstring + "' does not contain embedded key"

   pubkey = PublicKey(sl = sl)
   if not pubkey.is_valid():
      raise TypeError, "fnstring '" + fnstring + "' does not contain valid embedded key"

   return pubkey





def get_fn_signedhash_using_privatekey_fn(filename, privatekey_fn, privatekey_password=None, type_of_hash=None):
   """
   <Purpose>
      This takes a file, a private key, private key password, and a hash type and generates a
      hash of the file signed by the private key.  The type of private key
      is not taken as an argument because it is not accepted as an
      argument by openssl.

   <Arguments>
      filename:
            The file which will have a hash, etc. generated for it.
      privatekey_fn:
            The filename which contains the private key
      privatekey_password:
            The password the private key is encrypted with, if any.
      type_of_hash:
            This is the type of hash (sha1, etc.).   If the value is not
            specified then the default is used.

   <Exceptions>
      TypeError is privatekey_fn or type_of_key are invalid.   IOError if 
      the privatekey_fn or filename is invalid or unreadable, etc.

   <Side Effects>
      None

   <Returns>
      A string containing the signed hash of the file.   This is generated 
      using the binascii routine, since the original hash is returned as 
      binary.
   """

   # Does the file exist?
   if not arizonageneral.valid_fn(filename):
      raise IOError, (2, "No such file or directory '"+filename+"' in get_fn_signedhash_using_privatekey_fn (1)")

   # Does the privatekey file exist?
   if not arizonageneral.valid_fn(privatekey_fn):
      raise IOError, (2, "No such file or directory '"+privatekey_fn+"' in get_fn_signedhash_using_privatekey_fn (2)")

   # If they specified the type of hash then listen, otherwise use the default
   command = get_openssl_command() + " dgst "

   command += get_openssl_passin_arg(privatekey_password)

   # the "-passin stdin" has to be before the filename
   command += get_hash_type(type_of_hash)+" -sign "+privatekey_fn+" "+filename

   print command
   (the_in, the_out, the_err) = os.popen3(command)

   if privatekey_password != None:
      the_in.write(privatekey_password)
   the_in.close()

   # get the error output
   err_sl = arizonageneral.stream_to_sl(the_err)
   the_err.close()

   # Check to see if an error occured
   if not err_sl == []:
      raise TypeError, "Could not generate signed hash in get_fn_signedhash_using_privatekey_fn"

   # Get the hash if there isn't a problem.   It returns the whole binary data
   # hash produced on the output stream.
   hash_data = the_out.read()
   the_out.close()

   # Make sure something was returned
   assert(hash_data)

   # Make the hash into a string and return it...
   return binascii.b2a_hex(hash_data)





def verify_fn_signedhash_using_publickey_fn(filename, signedhash, publickey_fn, type_of_hash = None):
   """
   <Purpose>
      This takes a file, a signedhash (string), a file that contains a 
      publickey, and (optionally) a hash type.   It determines if the 
      given signedhash for the file was generated by the privatekey that 
      corresponds to the given publickey.   The type of publickey is not 
      taken as an argument because it is not accepted as an argument by 
      openssl.

   <Arguments>
      filename:
            The file which the hash corresponds to
      signedhash:
            The signed hash for file
      publickey_fn:
            The filename which contains the private key
      type_of_hash:
            This is the type of hash (sha1, etc.).   If the value is not 
            specified then the default is used.

   <Exceptions>
      TypeError is raised if an argument is invalid.   IOError is raised if 
      the privatekey_fn or filename is invalid or unreadable, etc.

   <Side Effects>
      None

   <Returns>
      True if the signedhash is valid or False otherwise.
   """

   
   # Check the hash argument validity
   if not isinstance(signedhash,str) and not isinstance(signedhash, unicode):
      raise TypeError, "signedhash not a string in verify_fn_signedhash_using_publickey_fn"

   # Convert the signedhash to binary and dump it to a file.    This is 
   # unfortunately necessary because openssl doesn't seem to recognize ascii 
   # hash dumps.
   (temp_signedhash_fd, temp_signedhash_fn) = tempfile.mkstemp(suffix=".verify_fn_signedhash_using_publickey.temp")
  
   try:
      os.write(temp_signedhash_fd,binascii.a2b_hex(signedhash))
      os.close(temp_signedhash_fd)
   except (IOError, OSError):
      os.remove(temp_signedhash_fn)
      raise
                                                                                

   # Now try to verify the signedhash and remove the temporary signed hash file
   try:
      ( junk_in, the_out, the_err ) = os.popen3(get_openssl_command()+" dgst "+get_hash_type(type_of_hash)+" -signature "+temp_signedhash_fn+" -verify "+publickey_fn+" "+filename)
   except TypeError:
      print "Option 1"+temp_signedhash_fn, os.path.exists(temp_signedhash_fn)
      os.remove(temp_signedhash_fn)
      raise

   
   # Close extraneous stream
   junk_in.close()


   # Get stringlists corresponding to the out and err streams...
   out_sl = arizonageneral.stream_to_sl(the_out)
   the_out.close()
   err_sl = arizonageneral.stream_to_sl(the_err)
   the_err.close()
   
   # Remove the temporary signedhash file
   os.remove(temp_signedhash_fn)

   # If there was an error...
   if not err_sl == []:
      raise TypeError, "Error verifying signature in verify_fn_signedhash_using_publickey_fn"+ "\n".join(err_sl)

   assert(not out_sl == [])

   # If it worked then verify, else don't
   if out_sl[0].startswith("Verified OK"):
      return True
   else:
      return False




########################################################
########                                        ########
########          XML signature stuff           ########
########                                        ########
########################################################


# This class parses a file that should contain a signature

class SignedFileApplication(arizonaxml.XMLApplication):
   def __init__(self):
      arizonaxml.XMLApplication.__init__(self)
      arizonaxml.CreateAttr(self, 'signedhash', None)
      arizonaxml.CreateAttr(self, 'publickey', None)
      arizonaxml.CreateAttr(self, 'signature_algorithm', None)
      arizonaxml.CreateAttr(self, 'timestamp', None)
      arizonaxml.CreateAttr(self, 'duration', None)
      arizonaxml.CreateAttr(self, 'file_data', '')
      arizonaxml.CreateAttr(self, 'file_data_list', [])
      arizonaxml.CreateAttr(self, 'file_encoding', None)
      arizonaxml.CreateAttr(self, 'file_tag_count', 0)
      arizonaxml.CreateAttr(self, 'filename_prefix', None)
      arizonaxml.CreateAttr(self, 'filename_suffix', None)
      arizonaxml.CreateAttr(self, 'write_certified_filename', True)

   def init_header(self, publickey_string, sig_alg = None, tstamp = None, dur = None, fencode = None, filename = None):
      self.publickey = publickey_string

      # If unset set default
      if self.signature_algorithm == None:
         self.signature_algorithm = "-sha1"
      if not sig_alg == None:
         self.signature_algorithm = sig_alg

      # If unspecified use the current time
      self.timestamp = int(time.time())
      if not tstamp == None:
         self.timestamp = tstamp

      # If unset use the default
      if self.duration == None:
         self.duration = 0
      if not dur == None:
         self.duration = dur

      # If unset use the default
      if self.file_encoding == None:
         self.file_encoding = "native"
      if not fencode == None:
         self.file_encoding = fencode

      if filename:
         fnparts = os.path.basename(filename).split(".")
         if len(fnparts) >= 2:
            self.filename_prefix = fnparts[0]
            self.filename_suffix = fnparts[-1]
         else:
            self.filename_prefix = None
            self.filename_suffix = None



   def get_publickey(self):
      return PublicKey(string = self.publickey)



   def debug_print(self):
      print 'signedhash:', self.signedhash
      if self.publickey is not None:
          print 'publickey:', self.publickey
      else:
          print 'publickey: None'
      print 'signature_algorithm:', self.signature_algorithm
      print 'timestamp:',self.timestamp
      print 'duration:',self.duration
      print 'file_encoding:', self.file_encoding
      print 'file_tag_count:',self.file_tag_count
      #print 'file_data:',self.file_data



   def handle_data(self,data, start, end):
      if self.file_tag_count > 0:
         try:
            # put the data into a string list. We'll join file_data_list into
            # file_data when we're done processing the file tag. This is much
            # faster than repeated string concatenation on large files.
            self.file_data_list.append(data[start:end])
         except:
            self.debug_print()
            print "'"+data[:30]+"'", start, end
            raise

   def handle_start_tag(self, tag, attrs):

      if self.file_tag_count > 0:
         if tag == "FILE":
            self.file_tag_count = self.file_tag_count + 1
	 #Duy Nguyen October 31, 2006
	 #Change: If there is an attribute error, try to continue. Cause of error not clear, but it is
	 # believed to be caused by an older version of PyXML.  Restore by removing try block.
	 try:
            self.file_data = self.file_data + self.get_raw_construct() # TODO profiler complains.. is it ok?
	 except AttributeError:
	 	pass 
         return

      if tag == "SIGNED_FILE":
         self.signedhash = attrs.get("SIGNEDHASH");

         self.publickey = attrs.get("PUBLICKEY")
         if not self.publickey:
             # if the field is "", change it to None
             self.publickey = None

         self.signature_algorithm = attrs.get("SIGNATURE_ALGORITHM");

      elif tag == "HEADER":
         self.timestamp = attrs.get("TIMESTAMP");
         self.duration = attrs.get("DURATION");
         
         self.filename_prefix = attrs.get("PREFIX")
         if not self.filename_prefix:
             # if the field is "", change it to None
             self.filename_prefix = None

         self.filename_suffix = attrs.get("SUFFIX")
         if not self.filename_suffix:
             # if the field is "", change it to None
             self.filename_suffix = None

      elif tag == "FILE":
         self.file_encoding = attrs.get("ENCODING");
         self.file_tag_count = self.file_tag_count + 1

      else:
         # Shouldn't happen if DTD is correct
         raise arizonaxml.XMLError , "invalid element: " + tag


   def handle_end_tag(self,tag):
      if tag == "FILE":
         self.file_tag_count = self.file_tag_count -1
         if self.file_tag_count == 0:
            self.file_data = self.file_data + ''.join(self.file_data_list)
            self.file_data_list = []

      if self.file_tag_count > 0:
	#Duy Nguyen - October 31, 2006
	#Change: Added try catch block. #.get_raw_construct does not exist?
         try:
           self.file_data = self.file_data + self.get_raw_construct() # TODO profiler complains.. is it ok?
         except:
           pass
         return

      if tag == "SIGNED_FILE" or tag == "FILE" or tag == "HEADER":
         return
      else:
         # Shouldn't happen if DTD is correct
         raise arizonaxml.XMLError , "invalid closing element: " + tag



   def __encoded_file_data(self):
      if self.file_encoding == "hex":
         return binascii.b2a_hex(self.file_data)
      if self.file_encoding == "escaped":
         return arizonaxml.escape(self.file_data)
      elif self.file_encoding == "native":
         return self.file_data
      else:
         raise TypeError, "Invalid file encoding type: "+self.file_encoding+" for signed file"



   def __decoded_file_data(self):
      if self.file_encoding == "hex":
         return binascii.a2b_hex(self.file_data)
      if self.file_encoding == "escaped":
         return arizonaxml.unescape(self.file_data)
      elif self.file_encoding == "native":
         return self.file_data
      else:
         raise TypeError, "Invalid file encoding type: "+self.file_encoding+" for signed file"




   def __write_protected_data(self, filefd):
      os.write(filefd, '   <HEADER TIMESTAMP="'+str(self.timestamp)+'" DURATION="'+str(self.duration) + '"')
      if self.write_certified_filename:
         if self.filename_prefix:
            os.write(filefd, ' PREFIX="' + self.filename_prefix + '"')
         if self.filename_suffix:
            os.write(filefd, ' SUFFIX="' + self.filename_suffix + '"')
      os.write(filefd, '/>\n')
      os.write(filefd, '   <FILE ENCODING="'+str(self.file_encoding)+'">'+self.__encoded_file_data())
      os.write(filefd, '</FILE>\n\n')


   def valid_file(self, given_fn):

      b = SignedFileApplication()
      null_obj = file("/dev/null", "w+")
      try:
         # Throw away all of the junk output of the original parser
         arizonareport.redirect_stdout(null_obj)
         arizonareport.redirect_stderr(null_obj)
         # read the file
         try:
            b.__raw_read_file(given_fn)
         finally:
            # Reenable output
            arizonareport.restore_stdout()
            arizonareport.restore_stderr()

         abc = b.file_data
         if abc == b.file_data:
            pass
      except (UnicodeDecodeError, OSError, SystemExit, TypeError, ValueError), e:
         arizonareport.send_error(4, "[DEBUG] valid_file failed: " + str(e))
         return False
      else:
         return True




   def read_file(self, file):
      if self.valid_file(file):
         self.__raw_read_file(file)
      else:
         arizonareport.send_error(4, "[DEBUG] read_file failed")
         raise TypeError, "Invalid signed file '"+file+"'"

   def __raw_read_file(self, file):
      self.file_data= ""
      arizonaxml.XMLParse(self, arizonaconfig.get_option("xmlsigndtd"), file)
      self.timestamp = int(self.timestamp)
      self.duration = int(self.duration)
      self.decode_file_data(self.file_encoding)


   def get_signedhash(self, privatekey_fn, privatekey_password=None):
      # make sure the encoding is okay
      (thistempfd,thistempname) = tempfile.mkstemp(suffix=".xml_get_hash.temp")
      try:
         os.close(thistempfd)
         self.write_file(thistempname)
      finally:
         os.remove(thistempname)

      # Find the correct secure hash for this data
      (thisfilefd,thisfilename) = tempfile.mkstemp(suffix=".xml_get_hash.temp")
      try:
         self.__write_protected_data(thisfilefd)
         os.close(thisfilefd)
         self.signedhash = get_fn_signedhash_using_privatekey_fn(thisfilename, privatekey_fn, privatekey_password=privatekey_password, type_of_hash=self.signature_algorithm)
         return self.signedhash
      finally:
         os.remove(thisfilename)


   def valid_signedhash(self, publickey):
      (thisfilefd, thisfilename) = tempfile.mkstemp(suffix=".xml_valid_signedhash.temp")
      try:
         self.__write_protected_data(thisfilefd)
         os.close(thisfilefd)
         if publickey:
             publickey_to_use = publickey
         else:
             publickey_to_use = PublicKey(string=self.publickey)
         return verify_fn_signedhash_using_publickey_fn(thisfilename, self.signedhash, publickey_to_use.file, type_of_hash = self.signature_algorithm)
      finally:
         os.remove(thisfilename)



   def decode_file_data(self, encodingtype):
      self.file_encoding = encodingtype
      if self.file_encoding == "hex":
         self.file_data = binascii.a2b_hex(self.file_data)
         return
      if self.file_encoding == "escaped":
         self.file_data = arizonaxml.unescape(self.file_data)
         return
      elif self.file_encoding == "native":
         return
      else:
         raise TypeError, "Invalid file encoding type: "+self.file_encoding+" for signed file"




   def raw_write_file(self, destfile):
      # Get a new temp file
      (thisfilefd,thisfilename) = tempfile.mkstemp(suffix=".xml_raw_write_file.temp")
      try:

         # Write the file
         os.write(thisfilefd,'<?xml version="1.0" encoding="ISO-8859-1" standalone="yes" ?>\n\n')
         os.write(thisfilefd,'<SIGNED_FILE'+
                  ' SIGNEDHASH="'+str(self.signedhash)+'"'+
                  ' PUBLICKEY="'+self.publickey+'"'+
                  ' SIGNATURE_ALGORITHM="'+self.signature_algorithm + '">\n')
         self.__write_protected_data(thisfilefd)
         os.write(thisfilefd,'</SIGNED_FILE>\n')

         # Close the fd
         os.close(thisfilefd)
 
         shutil.copy(thisfilename, destfile)
      finally:
         try:
            os.remove(thisfilename)
         except OSError:
            pass



   def write_file(self, destfile):
      
      (thisfilefd,tmp_fn) = tempfile.mkstemp(suffix=".xml_write_file.temp")
      os.close(thisfilefd)
    
      try:
         if self.file_encoding=="native":
            try:
               self.raw_write_file(tmp_fn)
            except UnicodeDecodeError:
               pass
 
            a = SignedFileApplication()

            if a.valid_file(tmp_fn):
               a.read_file(tmp_fn)
               try:
                  if a.file_data == self.file_data:
                     pass
                  else:
                     self.file_encoding="escaped"
                     self.write_file(tmp_fn)
               except UnicodeDecodeError:
                  self.file_encoding="escaped"
                  self.write_file(tmp_fn)
                  
            else:
               self.file_encoding="escaped"
               self.write_file(tmp_fn)
                  
            shutil.copy(tmp_fn, destfile)

         elif self.file_encoding=="escaped":

            try:
               self.raw_write_file(tmp_fn)
            except UnicodeDecodeError:
               pass

            a = SignedFileApplication()

            if a.valid_file(tmp_fn):
               a.read_file(tmp_fn)
               try:
                  if a.file_data == self.file_data:
                     pass
                  else:
                     self.file_encoding="hex"
                     self.write_file(tmp_fn)
               except UnicodeDecodeError:
                  self.file_encoding="hex"
                  self.write_file(tmp_fn)
            else:
               self.file_encoding="hex"
               self.write_file(tmp_fn)

            shutil.copy(tmp_fn, destfile)

         elif self.file_encoding=="hex":

            self.raw_write_file(tmp_fn)
            shutil.copy(tmp_fn, destfile)

      finally:
         try:
            os.remove(tmp_fn)
         except OSError:
            pass


      
   def dump_file_data(self, destfile):
      (thisfilefd,thisfilename) = tempfile.mkstemp(suffix=".xml_dump_original_file.temp")
      try:
         os.write(thisfilefd,self.file_data)
         os.close(thisfilefd)
 
         shutil.copy(thisfilename, destfile)
      finally:
         try:
            os.remove(thisfilename)
         except OSError:
            pass
      

   def read_file_data(self, inputfile):
      self.file_data= ""
      thisfilefd = os.open(inputfile,os.O_RDONLY)

      cur = os.read(thisfilefd,1024)
      self.file_data = cur
      while cur != '':
         cur = os.read(thisfilefd,1024)
         self.file_data = self.file_data + cur

      os.close(thisfilefd)
      
      return self.file_data
      
      
      




def XML_sign_file_using_privatekey_fn(filename, privatekey_fn, privatekey_pass=None,
                                      type_of_hash=None, timestamp=None, duration=None, file_encoding=None,
                                      certify_filename=True):
   """
   <Purpose>
      This takes a target filename and a filename containing a private key.
      It removes any existing signature block for the file and signs the 
      file with the private key.

   <Arguments>
      filename:
         This is the source file (the original message)
      privatekey_fn:
         This is the file that contains the private key
      privatekey_pass:
         The passphrase for the private key
      type_of_hash:
         This is the type of hash function that should be used for the 
         signature
      timestamp:
         This is the timestamp that should be added to the file
      duration:
         This is the timestamp that should be added to the file

   <Exceptions>
      TypeError is raised if any argument is invalid

   <Side Effects>
      The given file is signed with the user's private key and existing 
      signatures are removed.

   <Returns>
      None
   """

   # Make sure it's a valid filename
   if not arizonageneral.valid_fn(filename):
      raise TypeError, "Invalid stringlist in XML_sign_file_using_privatekey_fn"
   
   # Make sure it's a valid filename
   if not arizonageneral.valid_fn(privatekey_fn):
      raise TypeError, "Invalid privatekey_fn in XML_sign_file_using_privatekey_fn"

   if type_of_hash != None and not isinstance(type_of_hash,str):
      raise TypeError, "Invalid hash type in XML_sign_file_using_privatekey_fn"

   if timestamp != None and not isinstance(timestamp,int):
      raise TypeError, "Invalid hash type in XML_sign_file_using_privatekey_fn"

   if duration != None and not isinstance(duration, int):
      raise TypeError, "Invalid hash type in XML_sign_file_using_privatekey_fn"

   if file_encoding != None and not isinstance(file_encoding,str):
      raise TypeError, "Invalid hash type in XML_sign_file_using_privatekey_fn"

   signedfileobj = SignedFileApplication()

   signedfileobj.write_certified_filename = certify_filename
   signedfileobj.signature_algorithm = type_of_hash

   try:
      signedfileobj.read_file(filename)
   except TypeError:
      signedfileobj.read_file_data(filename)

   # Reset any portions of the header that need to be changed...
   publickey_string = PrivateKey(file=privatekey_fn, password=privatekey_pass).get_public_key().string
   signedfileobj.init_header(publickey_string, sig_alg = type_of_hash, tstamp = timestamp, dur = duration, fencode = file_encoding, filename = filename)

   signedfileobj.get_signedhash(privatekey_fn, privatekey_password=privatekey_pass)

   signedfileobj.write_file(filename)






def XML_retrieve_originalfile_from_signedfile(signedfile_fn, dest_file=None):
   """
   <Purpose>
      This takes a filename and returns a filename containing the original
      file.

   <Arguments>
      signedfile_fn:
         This is the sigendfile
      dest_file:
         This is the file we want to put the original contents into

   <Exceptions>
      TypeError is raised if the file name is invalid or is not a valid signed
      file

   <Side Effects>
      The creation of the temp file whose name it returns

   <Returns>
      The name of a tempfile which it returns
   """

   # Make sure it's a valid filename
   if not arizonageneral.valid_fn(signedfile_fn):
      raise TypeError, "Invalid signedfile_fn - does file exist & is it readable?"

   a = SignedFileApplication()

   # May throw TypeError
   a.read_file(signedfile_fn)

   (thisfilefd,thisfilename) = tempfile.mkstemp(suffix=".xml_original_file.temp")
   os.close(thisfilefd)
   a.dump_file_data(thisfilename)
   if dest_file == None:
      return thisfilename
   else:
      try:
         shutil.copy(thisfilename, dest_file)
      finally:
         try:
            os.remove(thisfilename)
         except OSError:
            pass
      return dest_file




def XML_validate_file(signedfile_fn, publickey_fn=None, publickey_string=None, certify_filename=True, real_fn=None):
   """
   <Purpose>
      This takes a filename and returns the timestamp if it is correctly signed
      and timestamped/durationed or throws an exception otherwise.

   <Arguments>
      signedfile_fn:
         This is the signedfile filename
      publickey_fn:
         Name of public key used to verify
      publickey_string:
         String of public key used to verify, only used if publickey_fn == None
      certify_filename:
         True to certify the filename. If the file has been renamed, then an
         exception will be thrown.
      real_fn:
         If signedfile_fn is a temporary filename, then real_fn is what the
         real name of the file should be. This is used when extracting the
         key from the filename. If real_fn==None, then it is assumed to be
         the same as signedfile_fn
      NOTE:
         If neither publickey_fn nor publickey_string is specified, then this
         function will self-certify the file using its embedded public key.

   <Exceptions>
      TypeError is thrown if an argument is invalid

   <Side Effects>
      None

   <Returns>
      A dictionary containing information about the validated signed file.
         dict['timestamp'] == timestamp
   """
   if not arizonageneral.valid_fn(signedfile_fn):
      # Bad signed file name
      raise TypeError, "Signed file `" + str(signedfile_fn) + "' doesn't exist, or cannot be opened."

   if not real_fn:
      real_fn = signedfile_fn

   if publickey_fn:
      publickey = PublicKey(file = publickey_fn)
      arizonareport.send_out(4, "[DEBUG] got key " + str(publickey.string) + " from fn " + publickey_fn)
   elif publickey_string:
      publickey = PublicKey(string = publickey_string)
      arizonareport.send_out(4, "[DEBUG] got key " + str(publickey.string) + " from str " + publickey_string)
   else:
      # finally, try to extract a publickey from the real_fn
      try:
         publickey = fnstring_to_publickey(real_fn)
      except TypeError:
         publickey = None
      except ValueError:
         publickey = None

      # if an error returned, then we fallthrough with publickey == None. We
      # will notice this below and attempt to get the public key that is
      # embedded inside the file.

      if publickey:
         arizonareport.send_out(4, "[DEBUG] got key " + str(publickey.string) + " from embedded fn " + real_fn)

   # read the signed file
   a = SignedFileApplication()
   try:
      a.read_file(signedfile_fn)
   except TypeError, e:
      # not a signed file
      arizonareport.send_error(4, "[DEBUG] xml_validate_file error " + str(e))
      raise TypeError, "Malformed signed file `" + str(signedfile_fn) + "'"

   # if none of then other methods yielded a public key, then attempt to use
   # the publickey at is embedded in the file
   if not publickey:
      publickey = a.get_publickey()

      if publickey:
         arizonareport.send_out(4, "[DEBUG] got key " + str(publickey.string) + " from embedded key")

   # in order to validate the file, a publickey is necessary. If we didn't get
   # one from somewhere, then we need to bail out.
   if not publickey:
      raise TypeError, "No public key was passed, and file did not contain embedded publickey for  `" + str(signedfile_fn) + "'"

   # verify that the file is properly signed
   if not a.valid_signedhash(publickey):
      # Invalid signature
      raise TypeError, "Invalid embedded signature in signed file `" + str(signedfile_fn) + "'"

   # verify that the key/hash contained in the filename matches the public key
   if not publickey.certify_filename(signedfile_fn):
      raise TypeError, "The publickey does not match filename in signed file `" + str(signedfile_fn) + "'"

   # check the timestamp and duration
   expired = False
   if not a.duration == 0:
      if int(time.time()) > a.timestamp + a.duration:
         # expired status will be passed to the caller, rather than
         # throwing an exception here
         expired = True

   # extract the filename prefix and suffic
   fnparts = os.path.basename(real_fn).split(".")
   if len(fnparts)>=2:
      prefix = fnparts[0]
      suffix = fnparts[-1]
   else:
      prefix = None
      suffix = None

   if certify_filename:
      # if a prefix was specified, then make sure it is correct
      if a.filename_prefix and (a.filename_prefix != prefix):
         raise TypeError, "Filename prefix does not match embedded filename prefix for " + signedfile_fn

      # if a suffix was specified, then make sure it is correct
      if a.filename_suffix and (a.filename_suffix != suffix):
         raise TypeError, "Filename suffix does not match embedded filename suffix for " + signedfile_fn

   return {"timestamp": a.timestamp,
           "duration": a.duration,
           "expired": expired,
           "key": publickey}





def XML_timestamp_signedfile_with_publickey_fn(signedfile_fn, publickey_fn=None, publickey_string=None):
   """
   <Purpose>
      This is a stub wrapped around XML_validate_file for compatibility
      reasons. This function is deprecated. Use XML_validate_file instead
   """
   filesig_dict = XML_validate_file(signedfile_fn, publickey_fn, publickey_string)
   return filesig_dict['timestamp']




def convert_ssh_to_ssl(infile, outfile):
   """This takes a SSH public key and converts it into SSL format
   """

   """
      OpenSSH Key File Format
          RSA:
               STRING("ssh-rsa")
               BIGNUM2(e)
               BIGNUM2(n)
          DSA:
               STRING("ssh-dsa")
               BIGNUM2(p)
               BIGNUM2(q)
               BIGNUM2(g)
               BIGNUM2(pub_key)
          STRING:
               UINT32(length),
               CHAR[string]
          BIGNUM2:
               if (value is_zero):
                   UINT32(0)
               else:
                   buf = 0x00, BN_bn2bin(value)
                   if (buf[1] & 0x80) then
                       buf = buf[1:]
                   STRING(buf)
   """

   # We use a C program to do the conversion, so it can link with openssl
   # for generating PEM files
   
   # try to find the location of keyconvert
   keyconvertpath = None
   # directory that the arizonacrypt.py file is in
   directoryofthisfile = os.path.realpath(os.path.dirname(__file__))
   keyconvertdirs = ['/usr/local/stork/bin', directoryofthisfile, directoryofthisfile + '/../c/keyconvert']
   for possibledir in keyconvertdirs:
      if os.path.exists(possibledir + '/keyconvert'):
          keyconvertpath = possibledir + '/keyconvert'
          break

   if not keyconvertpath:
       raise TypeError, "Could not find keyconvert in any of the following directories: " + str(keyconvertdirs)
   
   execstring = keyconvertpath + " " + infile + " " + outfile
   # suppress output of the keyconvert command
   suppressoutput = " >/dev/null 2>&1"
   status = arizonageneral.popen0(execstring + suppressoutput)

   if status != 0:
       # repeat the command without output suppressed so that its output will show
       arizonageneral.popen0(execstring)
       raise TypeError, "Failed to convert key"




########################################################
########                                        ########
########          Key manipulation              ########
########                                        ########
########################################################



class Key(object):
    """Base class which is extended by PrivateKey and PublicKey. Allows specifying
       the key in different formats with the rest of the functionality being
       the same regardless of the initial format in which the key is specified."""
    
    _initialized = False
    _key_type = None
    _original_file = None
    _temp_file = None
    _sl = None
    _string = None
    _password = None # only private keys have passwords, but having this hear made some other parts simpler
    
    def __init__(self, file=None, sl=None, string=None, type=None, password=None):
        """
           <Arguments>
              file:
                 The name of the file which contains the key.
              sl:
                 A stringlist of the key.
              string:
                 The key as a string with no linebreaks.
              
              Note that one and only one of the these named arguments must be specified
              which specifies the key that the instance represents.

              type:
                 The type of key (e.g. "rsa")
                 
              password:
                 The password the key is symmetrically encrypted with, if any. This is
                 really only useful for private keys, but the implemenations simpler and
                 cleaner to allow any key to have a password.
        """
        
        super(Key, self).__init__()
        self._key_type = type
        self._password = password
        if file is not None:
            if sl or string:
                raise ValueError, "Too many initialization methods specified."
            self._load_file(file)
        elif sl is not None:
            if string:
                raise ValueError, "Too many initialization methods specified."
            self._load_sl(sl)
        elif string is not None:
            self._load_string(string)
        else:
             raise ValueError, "Must specify an initialization format for a Key: file, sl, or string."


    def __del__(self):
        """Performs cleanup when a Key instance is deleted or goes out of scope."""

        try:
            os.remove(self._temp_file)
        except:
            pass
        
    
    def __eq__(self, other):
        """Overrides == comparison of Key instance to compare the contents (are
           the keys that are represented the same?)."""
           
        if not isinstance(other, self.__class__):
            return False
        else:
            return self.string == other.string
    
    
    def __ne__(self, other):
        """Overrides != comparison of Key instance to compare the contents (are
           the keys that are represented different?)."""
           
        return not self.__eq__(other)
    
    
    def _load_file(self, file):
        """
           <Purpose>
               Set the file that the Key instance represents.
               Can only be called if none of the _load_* methods
               have been called yet.

           <Exceptions>
               TypeError if key already initialized.
               TypeError if file doesn't exist.
           """
           
        if self._initialized:
            raise TypeError, "Cannot load file '" + str(file) + "', key already initialized."
        
        # verify that the file exists
        if type(file) == type(int) or type(file) == type(float):
           raise TypeError, "Cannot load file, was given a number"
           
        if not os.path.exists(file):
            raise TypeError, "Cannot load file '" + str(file) + "', file doesn't exist."
        
        self._original_file = file
        self._initialized = True


    def _load_sl(self, sl):
        """
           <Purpose>
               Set the stringlist that the Key instance represents.
               Can only be called if none of the _load_* methods
               have been called yet.
           
           <Exceptions>
               TypeError if key already initialized.
               TypeError if stringlist is invalid.
           """
           
        if self._initialized:
            raise TypeError, "Cannot load sl, key already initialized."
        
        if not valid_sl(sl):
            raise TypeError, "Cannot load sl, sl is not valid."

        self._sl = sl
        self._initialized = True
        
        
    def _load_string(self, string):
        """
           <Purpose>
               Set the string that the Key instance represents.
               Can only be called if none of the _load_* methods
               have been called yet.
           
           <Exceptions>
               TypeError if key already initialized.
               TypeError if string is not a string.
           """
           
        if self._initialized:
            raise TypeError, "Cannot load string, key already initialized."
        
        if not isinstance(string, str) and not isinstance(string, unicode):
            raise TypeError, "Cannot load string, string argument is not a string."

        self._string = string
        self._initialized = True


    def _generate_temp_file(self):
        """Ensures that a temp file with the key exists."""

        self._generate_sl()
        self._sl_to_temp_file()


    def get_password(self):
        """Getter for the password."""

        return self._password
    
    
    def set_password(self, password):
        """Setter for the password."""
        
        self._password = password
    
    
    # make it so that when keyinstance.password is called, that the
    # accessor methods are actually used rather than a variable
    # being directly accessed.
    password = property(get_password, set_password)
    
    
    def get_file(self):
        """Getter for the name of a/the file that contains the key."""
        
        if not self._initialized:
            raise TypeError, "Cannot get_file, key is not initialized."

        if self._original_file:
            return self._original_file
        else:
            if not self._temp_file:
                self._generate_temp_file()
            return self._temp_file
    
    
    def set_file(self, file):
        """Setter for the name of a/the file that contains the key. Should
           never be called, here just for completeness of the file property()."""

        raise TypeError, "Cannot set attribute after instantiation."
    
    
    # make it so that when keyinstance.file is called, that the
    # accessor methods are actually used rather than a variable
    # being directly accessed.
    file = property(get_file, set_file)
    
    
    def _generate_string(self):
        """Ensures that a string with the key is available."""
        
        if self._string is None:
            if self._sl is None:
                self._file_to_sl()
            self._sl_to_string() 
    
    
    def get_string(self):
        """Getter for the string representation of the key."""
        
        if not self._initialized:
            raise TypeError, "Cannot get_string, key is not initialized."
        
        self._generate_string()
        return self._string
    
    
    def set_string(self, string):
        """Setter for the string representation of the key. Should
           never be called, here just for completeness of the file property()."""

        raise TypeError, "Cannot set attribute after instantiation."
    
    
    # make it so that when keyinstance.string is called, that the
    # accessor methods are actually used rather than a variable
    # being directly accessed.
    string = property(get_string, set_string)
 
    
    def _generate_sl(self):
        """Ensures that a stringlist with the key is available."""
        
        if self._sl is None:
            if self._string is not None:
                self._string_to_sl()
            else:
                self._file_to_sl()
    
    
    def get_sl(self):
        """Getter for the stringlist representation of the key."""
        
        if not self._initialized:
            raise TypeError, "Cannot get_sl, key is not initialized."
        
        self._generate_sl()
        return self._sl
    
    
    def set_sl(self, sl):
        """Setter for the stringlist representation of the key. Should
           never be called, here just for completeness of the file property()."""
        raise TypeError, "Cannot set attribute after instantiation."
    
    
    # make it so that when keyinstance.sl is called, that the
    # accessor methods are actually used rather than a variable
    # being directly accessed.
    sl = property(get_sl, set_sl)
    

    def save_to_file(self, filename):
       """
       <Purpose>
          This creates a file that contains a privatekey.
    
       <Arguments>
          filename:
                This creates a file with this name
          type_of_key:
                This is the kind of key that should be generated (genrsa, 
                gendsa, etc.).   If the value is not specified then the 
                default is used.
    
       <Exceptions>
          As thrown by generate_privatekey_sl, sl_to_fn, and shutil.move
          (TypeError, ValueError, IOError).
    
       <Side Effects>
          Creates the file "filename"
    
       <Returns>
          None
       """
    
       assert(isinstance(filename, str))

       # Check if the dest is a dir
       if os.path.isdir(filename):
          raise IOError, (21, "Is a directory")
    
       # If this fails, then raise an exception
       assert(self.get_sl() != [])

       # Dump it to disk
       temp_file = sl_to_fn(self.get_sl())
    
       # Move it to the correct filename
       try:
          shutil.move(temp_file, filename)
       except (IOError, OSError):
          # Clean up when an error occurs
          os.remove(temp_file)
          raise
    
    
    def _sl_to_string(self):
        """Internally sets the string representation of the key based on the
           interally stored stringlist representation of the key."""

        # Strip out the lines that start with -----
        new_publickey_sl = []
        for item in self._sl:
           if not item.startswith('-----'):
              new_publickey_sl.append(item)
              
        # Make it one string
        self._string = "".join(new_publickey_sl)


    def _string_to_sl(self):
        """Internally sets the stringlist representation of the key based on the
           interally stored string representation of the key."""

        self._sl = []
        self._sl.append(self._get_sl_begin())
        line_length = 64;
        i = 0
        while i < len(self._string):
            self._sl.append(self._string[i:i + line_length])
            i += line_length
        self._sl.append(self._get_sl_end())


    def _sl_to_temp_file(self):
        """
        <Purpose>
           Internally sets the temp file representation of the key based on the
           interally stored stringlist representation of the key.

        <Exceptions>
           TypeError if internally stored stringlist is not valid.

        <Side Effects>
           Temp file representation of key is available.
        """

        if not valid_sl(self.get_sl()):
           raise TypeError, "Invalid stringlist."

        # Get a new temp file
        (handle, filename) = tempfile.mkstemp(suffix="._sl_to_temp_file.temp")

        # Write the stringlist into the file
        for item in self.get_sl():
           os.write(handle, item.rstrip('\r\n')+'\n')

        # Close the fd
        os.close(handle)

        self._temp_file = filename


    def _file_to_sl(self, key_type=None):
       """
       <Purpose>
          Internally sets the stringlist representation of the key based on the
          interally stored file/temp file representation of the key.

       <Exceptions>
          TypeError, IOError, OSError if problem getting the data from the file.

       <Side Effects>
          Stringlist representation of key is available.
       """
        
       try:
          # Read in a public key in rsa format...
          (junk_in, the_out, junk_err) = os.popen3(self._get_file_stream_command(self.get_file()))
       except (TypeError, IOError, OSError):
          raise
    
       # Close input and error streams
       junk_in.close()
       junk_err.close()
    
       try:
           # Return the string list that results. The openssl stream will be
           # empty if the file is invalid and thus this will return []...
           self._sl = arizonageneral.stream_to_sl(the_out)
       except (TypeError,IOError):
           raise
    
       the_out.close()
       if self._sl == []:
           raise TypeError, "Invalid key file: unable to create sl from key file."
    

    def is_valid(self):
       """
       <Purpose>
          Returns True or False which specifies whether or not the key
          the Key instance represents is valid.
    
       <Exceptions>
          None
    
       <Side Effects>
          None
    
       <Returns>
          A boolean indicating if the key is valid.
       """
    
       try:
           
          command = self._get_file_stream_command(self.get_file())
          command += get_openssl_passin_arg(self._password)

          (the_in, the_out, the_err) = os.popen3(command)

          if self._password != None:
             the_in.write(self._password)
          the_in.close()

       except (TypeError, IOError, OSError):
          return False
    
       the_err.close()
    
       try:
           # Return the string list that results. The openssl stream will be 
           # empty if the file is invalid and thus this will return []...
           temp_sl = arizonageneral.stream_to_sl(the_out)
       except (TypeError,IOError):
           the_out.close()
           return False
    
       the_out.close()
       
       if temp_sl == []:
           return False
       
       return True
    

    def _get_file_stream_command(self):
        """Returns the core of the openssl command that can be run where this key is
           passed to openssl."""
        
        raise NotImplementedError, "Must be implemented by a derived class"

    
    def _get_sl_begin(self):
        """Returns a string that should be the first line of a file this key
           would be stored in."""        
        
        raise NotImplementedError, "Must be implemented by a derived class"
    
    
    def _get_sl_end(self):
        """Returns a string that should be the last line of a file this key
           would be stored in."""
           
        raise NotImplementedError, "Must be implemented by a derived class"
    
    
    
class PublicKey(Key):
    """
       A representation of a PublicKey which extends the Key class.

       Example usages:
          publickey = PublicKey(string=var_that_has_key_string)
          print publickey.hash
       
          publickey = PublicKey(file=var_that_has_pubkey_filename)
          print publickey.sl

          publickey = PublicKey(sl=var_that_has_pubkey_stringlist)
          print publickey.string
          
          # Note: if using the file property, unless a file was used in the
          # constructor [PublicKey(file=some_fn)], the filename that is
          # returned will be a temp file that will be cleaned up when
          # the publickey object goes out of scope or is deleted/removed
          print publickey.file
    """

    _hash = None

    def _generate_hash(self):
        """Ensures that a hash of the key is available."""

        if (self._hash is None):
            self._generate_string()
            self._string_to_hash()


    def get_hash(self):
        """Getter for the hash of the key."""

        self._generate_hash()
        return self._hash


    def set_hash(self, hash):
        """Setter for the hash of the key. Should never be called,
           here just for completeness of the file property()."""

        raise TypeError, "Cannot set a key's hash."


    def certify_filename(self, filename):
       # usually the filename will be split into parts by ".", and the hash/key
       # is in the second part
       test = filename.split(".")
       if len(test) > 1:
          test = test[1]
       else:
          test = filename

       # try to match string without mangling
       string = self.get_string()
       if test == string:
          return True

       # try to match the mangled string
       if (test.replace('_', '/') + "==") == string:
          return True

       hash = self.get_hash
       if test == hash:
          return True

       return True



    # make it so that when keyinstance.hash is called, that the
    # accessor methods are actually used rather than a variable
    # being directly accessed.
    hash = property(get_hash, set_hash)

    def _string_to_hash(self):
       # decode the base64 encoded key string
       try:
           publickey = base64.decodestring(self._string)
       except:
           print "Unable to decode base64 public key string.";
           raise

       # return the sha1 of the public key
       self._hash = sha.new(publickey).hexdigest()



    def _get_file_stream_command(self, filename):
       return get_openssl_command() + " " + get_key_type(self._key_type) + " -pubin -in " + filename

    def _get_sl_begin(self):
        return "-----BEGIN PUBLIC KEY-----"

    def _get_sl_end(self):
        return "-----END PUBLIC KEY-----"



class PrivateKey(Key):
    """
       A representation of a PrivateKey which extends the Key class.

       Example usages:
          privatekey = PrivateKey(file=var_that_has_pubkey_filename)
          publickey = privatekey.get_public_key()
          print publickey.string
       
          privatekey = PrivateKey(file=var_that_has_pubkey_filename, password=var_that_has_password_string)
          
          privatekey = PrivateKey.generate(numbits_of_key=2048)
    """
    
    def _generate(type_of_key=None, numbits_of_key=None):
       """
       <Purpose>
          Creates a new private key.
    
       <Arguments>
          type_of_key:
                This is the kind of key that should be generated (genrsa,
                gendsa, etc.).   If the value is not specified then the
                default is used.
          numbits_of_key:
                The size of the key modulus to generate in bits. If the
                value is not specified then the default is used.
    
       <Exceptions>
          As thrown by stream_to_sl and os.popen3 (TypeError, ValueError,
          IOError).  ValueError is raised if the type_of_key is invalid
    
       <Side Effects>
          None
    
       <Returns>
          A new PrivateKey objects which represents the generated private
          key.
       """
    
       (junk_in, the_out, junk_err) = os.popen3(get_openssl_command() + " " +get_genkey_type(type_of_key)+" "+get_key_numbits(numbits_of_key))
       
       junk_in.close()
       junk_err.close()
    
       # Get the private key from stdout
       privatekey_sl = arizonageneral.stream_to_sl(the_out)
       the_out.close()
    
       assert (privatekey_sl != [])
       
       return PrivateKey(sl=privatekey_sl)


    # make generate a static method which calls the private method _generate
    generate = staticmethod(_generate)


    # TODO make this more efficient by caching the public key after the first time this is called
    def get_public_key(self):
       """
       <Purpose>
          This gets a PublicKey object which contains the public key that
          this corresponds to this private key represented by this PrivateKey
          instance.
    
       <Arguments>
          None
    
       <Exceptions>
          TypeError if the private key this PrivateKey instance represents is
          not valid.
    
       <Side Effects>
          None
    
       <Returns>
          A PublicKey instance that represents the public key.
       """
    
       # Does the file exist?
       if not self.is_valid():
          raise TypeError, (2, "Cannot get public key from invalid private key.")
       
       #os.path.sep == "\\" indicates we are on Windows
       command = get_openssl_command() + " " +get_key_type(self._key_type)+" -in "+self.get_file()+" -pubout"
       command += get_openssl_passin_arg(self._password)

       (the_in, the_out, the_err) = os.popen3(command)
       
       if self._password != None:
           the_in.write(self._password)
           the_in.close()
    
       # get the error output
       err_sl = arizonageneral.stream_to_sl(the_err)
       the_err.close()
    
       # Check to see if an error we were expecting occured
       for line in err_sl:
          if line == "unable to load Private Key":
             raise TypeError, "Invalid private key file in extract_publickey_sl_from_privatekey_fn"
             
       # get the public key from the stream
       publickey_sl = arizonageneral.stream_to_sl(the_out)
       the_out.close()

       assert(publickey_sl != [])
       
       # Return the publickey
       return PublicKey(sl=publickey_sl)
   
    
    def _get_file_stream_command(self, filename):
       """Returns the core of the openssl command that can be run where this key is
          passed to openssl."""

       return get_openssl_command() + " " +get_key_type(self._key_type)+" -in "+filename


    def _get_sl_begin(self):
        """Returns a string that should be the first line of a file this key
           would be stored in."""   
           
        return "-----BEGIN PRIVATE KEY-----"
    
    
    def _get_sl_end(self):
        """Returns a string that should be the klast line of a file this key
           would be stored in."""   
           
        return "-----END PRIVATE KEY-----"

