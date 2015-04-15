#! /usr/bin/env python
"""
<Program Name>
   storkpackagelist.py

<Started>
   October 6, 2005

<Author>
   Programmed by Justin Cappos.

<Purpose>
   Routines for accessing and querying the package list.
"""

#           [option, long option,               variable,    action,        data,     default,                            metavar,      description]
"""arizonaconfig
   options=[
            ["",     "--localpackageinfo",      "localinfo", "store",       "string", "/usr/local/stork/var/packageinfo", "PACKAGEDIR", "location of local package information (default /usr/local/stork/var/packageinfo)"],
            ["",     "--repositorypackagedir",  "pdir",      "append",      "string", None,                               "dir",        "repository name and location of packages (the switch may appear multiple times)"],
            ["",     "--repositorypackageinfo", "repinfo",   "append",      "string", None,                               "dir",        "repository name and location of information about packages (the switch may appear multiple times)"],
            ["",     "--repositorykey",         "repkey",    "append",      "string", None,                               None,         "repository public key expected to have signed metafile (the switch may appear multiple times)"],
            ["",     "--repositorypackageurl",  "repurl",    "store",       "string", None,                               None,         "optional URL to use when fetching packages"],
            ["",     "--noupdatepackageinfo",   "updatedb",  "store_false", None,     True,                               None,         "do not attempt to update the package database"]]
            ["",     "--repository",     "repositories", "sectionstart", "string",    None,                             "name",      "start repository section"],
            ["",     "--repositoryend",  "junk",         "sectionstop",  None,        None,                              None,        "end repository section"],

   includes=[]
"""

import os
import sys
import tempfile
import arizonageneral
import shutil
import arizonaconfig
import arizonacrypt
import arizonareport
import arizonatransfer
import dircache
import random
import fnmatch
import storkusername
import storkpackage
import storkpoison
#import storktrackusage

# glo_repo_list: a list of repository dictionaries
# each dictionary contains the following entries:
#    'name': the name of the repository
#    'section': the arizonaconfig section the repository was found in
#    'localdir': the local dir of the repository on this node
#    'url': the URL to use when downloading (use None for default)
#    'files': a list of filenames that were downloaded from the repository

glo_repo_list = []
glo_initialized = False

# glo_repo_sections: a list of arizonaconfig sections that contain repository
# information. If it is set to [None], then that indicates a compatibility
# mode where arizonaconfig sections are not used.
glo_repo_sections = []


def init():
   """
   <Purpose>
      Initialize and update repository package list(s).
   """
   global glo_initialized
   global glo_repo_sections

   glo_repo_sections = arizonaconfig.get_option("repositories")
   if not glo_repo_sections:
      # compatibility mode -- None causes arizonaconfig.get_option_section
      #   to default to the same behaviour as arizonaconfig.get_option
      glo_repo_sections = [None]

   # check repinfo
   for repo_section in glo_repo_sections:
      if arizonaconfig.get_option_section("repinfo", repo_section) == None:
         if repo_section:
             arizonareport.send_error(0, "repository " + repo_section + ":")
         arizonareport.send_error(0, "Repository package information locations must be" + \
                                     " specified either on the command line" + \
                                     " or in the configuration file.  See the" + \
                                     " `--repositorypackageinfo' option.")
         sys.exit(1)

      if not arizonaconfig.get_option_section("updatedb", repo_section):
         arizonareport.send_out(1, "Skipping update of package information...")
         update_ok = False
      else:
         arizonareport.send_out(1, "Updating package information...")
         update_ok = True

      # check to see if the user tried to override the localinfo variable for
      # a specific repository. If so, then complain because this is not yet
      # implemented
      # TODO: finish this (see __find_package_fnlist_on_one_criteria)
      if arizonaconfig.get_option_section("localinfo", repo_section) != arizonaconfig.get_option("localinfo"):
         arizonareport.send_error(0, "cannot use localinfo variable inside repository section")
         sys.exit(1)

      download_repositories(repo_section,
                            arizonaconfig.get_option_section("repinfo", repo_section),
                            arizonaconfig.get_option_section("localinfo", repo_section),
                            update_ok)

   # build the list of packageinfo directories
   build_localpdir()

   # uncomment to dump info about repositories to stdout
   # dump_repositories()

   glo_initialized = True


def download_repositories(repo_section, repo_names, local_dir, update_ok):
   """
   <Purpose>
      Download all packageinfo, tpfile, pacman files from all repositories
   <Arguments>
      repo_names
         a list of repository packageinfo names/directories (for example,
            [quiver.cs.arizona.edu/packageinfo, nr06.cs.arizona.edu/packageinfo]
         NOTE: this does not appear to be used. the config value of repinfo is
            used instead.
      local_dir
         local directory to place repository data files in
      update_ok
         True if files should be downloaded
   """
   global glo_repo_list
   global glo_repo_sections

   glo_repo_list = []

   # TODO: finish update_ok

   # download from each repository in our list
   repkeys = arizonaconfig.get_option("repkey")
   for repo_section in glo_repo_sections:
      for i, repo in enumerate(arizonaconfig.get_option("repinfo", repo_section)):
         # assuming config options repkey is a list that is in the same order 
         # as the repinfo, we have a key for this repo only if we have a key
         # at the current index
         if repkeys and len(repkeys) > i:
            repkey = repkeys[i]
         else:
            repkey = None
         try:
            repo_dict = download_repository(repo, local_dir, update_ok, repkey)
            if repo_dict:
               repo_dict['section'] = repo_section
               glo_repo_list.append(repo_dict)
         except IOError, e:
            arizonareport.send_error(1,  \
               "Warning: Failed to update repository " + str(repo) + \
                  " Error :" + str(e))



   

   
def download_repository(repo_name, local_dir, update_ok, repo_key=None):
   """
   <Purpose>
      Download all packageinfo, tpfile, pacman files from a single repository
   <Arguments>
      repo_name
         the name/directory of the repository
      local_dir
         local directory to place repository data files in
      update_ok
         True if files should be downloaded
      repo_key
         The key that is expected to have signed the metafile for this repository.
         If None, then the metafile will not be required to be signed.
   """

   # TODO: finish update_ok
   if not update_ok:
      arizonareport.send_out(0, "* --noupdatepackageinfo not currently implemented *")

   # create a dict to hold this repository's information
   repo_dict = {}
   repo_dict['name'] = repo_name

   # the default URL use when accessing the repository
   repo_dict['repurl'] = arizonaconfig.get_option("repurl")

   # get a directory name we can use for the repository. Do this by replacing
   # /'s with _'s.
   repodir = repo_name
   repodir.replace("/", "_")

   # get a local directory where we will place this repos information
   localdir = os.path.join(local_dir, repodir)

   # make sure localdir exists
   try:
      os.makedirs(localdir)
   except OSError:
      pass

   # if the directory isn't there, then we can't download anything
   if not os.path.isdir(localdir):
      arizonareport.send_error(1, "Cannot create repository data dir: " + localdir)
      return None

   repo_dict['localdir'] = localdir

   # setup paths for downloading files
   source = repo_name
   dest = localdir

   arizonareport.send_out(3, "Retrieving package data files from: " + str(source))
   if arizonareport.get_verbosity() > 1:
      width = arizonareport.console_size()[1]
      if width == None:
         width = 70
   else:
      width = 0

   # TODO: If a file is successfully downloaded and stork crashes before the
   # file can be unpacked, then stork will think the file is up-to-date next
   # time around, and it will never get unpacked. 

   (success, updated_files, all_files) = \
      arizonatransfer.sync_remote_dir(source, dest, width,
                                      metafile_signature_key=repo_key,
                                      hashfuncs = [storkpackage.get_package_metadata_hash, arizonatransfer.default_hashfunc])
                                      
   arizonareport.send_out(3, "Downloaded files: " + ", ".join(updated_files))
   arizonareport.send_out(2, "")

   # we only care about the files on the repository that we have local copies
   # of
   all_files = [file for file in all_files if os.path.exists(file)]

   repo_dict['files'] = all_files

   if not success:
      arizonareport.send_error(2, "Warning: Could not get all repository metadata, from: " + source)

   # extract tarballs to obtain package information
   for tarball in updated_files:
      # TODO NEEDS WORK: currently hardcoded as a bzipped tarball
      # delete old metadata directory, if it exists
      if tarball.endswith(".tar.bz2"):
         # TODO potentially dangerous
         arizonageneral.rmdir_recursive(os.path.join(dest, tarball[:-8]))

      arizonareport.send_out(2, "Unpacking: " + tarball)
      arizonageneral.popen5("tar -C " + dest + " -jxf " + tarball)
      # TODO check for errors

   arizonareport.flush_out(1)

   return repo_dict





def build_localpdir():
   """
   <Purpose>
      Build the list of local packageinfo directories. This is done by looking
      at each repository's file list, comparing them to the repository
      directories we are interested in
   """
   global glo_repo_list

   packageinfo_list = []

   for repo in glo_repo_list:
      # get the patterns that the user wants us to use. If nothing is
      # specified, then assume the user wants everything
      patterns = arizonaconfig.get_option_section("pdir", repo['section'])
      if patterns == None:
         patterns = ["*_packages_*"]

      localdir = repo.get("localdir", "")
      repo_packageinfo_list = []
      for file in repo.get('files', []):
         for pattern in patterns:
            # if pattern is a path, convert it to a filename
            pattern = pattern.replace("/", "_")
            pattern = os.path.join(localdir, pattern) + ".tar.bz2"
            if fnmatch.fnmatch(file, pattern):
               # the directory is the same as the filename, but with .tar.bz2
               # stripped off.
               dir = file
               pos = dir.find(".tar.bz2")
               if pos>0:
                  dir = dir[:pos]

               # now that we have the directory, add it to the list
               repo_packageinfo_list.append(dir)

      # save the info in the repository dict for future use
      repo['packageinfo'] = repo_packageinfo_list

      # add it to the list of all packageinfo directories
      packageinfo_list.extend(repo_packageinfo_list)

   arizonaconfig.set_option("localpdir", packageinfo_list)





def dump_repositories():
   """
   <Purpose>
      Dump our list of repositories to stdout.
   """
   global glo_repo_list
   
   for repo in glo_repo_list:
      print "Repository: " + repo.get("name", "unknown")
      print "   local directory: " + repo.get("localdir", "unknown")
      print "   files: " + ",".join(repo.get("files", []))
      print "   packageinfo: " + ",".join(repo.get("packageinfo", []))
      print ""




def find_file_ts(dir, filename_list, publickey_fn=None, publickey_string=None):
   """
   <Purpose>
      Search for a file from multiple repositories
   <Arguments>
      dir
         type of file to look for, currently "tpfiles" or "pacman"
      filename
         name of the file to look for
      publickey_fn
         filename containing publickey to verify correctness of file
         if publickey_fn == None, use publickey_string instead
      publickey_string
         string containing publickey, if publickey_fn == None
   <Returns>
      a tuple (None, None, None, candidate_count) if the file cannot be found
      a tuple (filename, repo, timestamp, candidate_count) if the file can be found. repo is the dictionary
      for the repository that contained the file and can be used for
      informational purposes (letting the user know where the file came from)
   """
   found = None
   found_timestamp = None
   found_repo = None
   found_dict = None
   found_count = 0

   # check to see if the key is poisoned
   if storkpoison.is_poisoned(file=publickey_fn, string=publickey_string):
      arizoanreport.send_out(3, "rejecting poisoned key " + str(publickey_fn) + " " + str(publickey_string))
      # if the key is poisoned, then don't consider it
      return (None, None, None, 0)

   for filename in filename_list:
      for repo in glo_repo_list:
         arizonareport.send_out(4, "[DEBUG] looking for " + filename + " on " + repo['name'])
         # this_name is the local name of the file we are looking for in the
         # repository's directory
         this_name = os.path.join(os.path.join(repo['localdir'], dir), filename)
   #      storktrackusage.add_file(this_name)
         if os.path.exists(this_name):
            # it exists. Now get the timestamp and compare it to any other
            # candidate that we might have found.
            try:
               this_dict = arizonacrypt.XML_validate_file(this_name, publickey_fn, publickey_string)
            except TypeError: #changed from general exception
               # if we failed to extract the timestamp, then the file is bad.
               # perhaps is has an invalid signature, bad format, missing timestamp...
               arizonareport.send_error(0, "Warning: Unable to validate " + this_name + " using key file " +
                  str(publickey_fn) + " or key string " + str(publickey_string))
               continue

            this_timestamp = this_dict.get("timestamp", 0)

            if storkpoison.is_poison_timestamp(this_timestamp):
               arizonareport.send_out(0, "poisoned timestamp detected in " + str(this_name) + " for key " + str(publickey_fn) + " " + str(publickey_string))
               storkpoison.set_poisoned(file = publickey_fn, string = publickey_string)
               return (None, None, None, 0)

            found_count = found_count + 1
            if (found == None) or (this_timestamp > found_timestamp):
               found = this_name
               found_timestamp = this_timestamp
               found_dict = this_dict
               found_repo = repo

   # check and see if the file we found is expired
   if found_dict:
      if found_dict.get("expired", False):
         arizonareport.send_error(0, "File " + str(found) + " is expired")
         return (None, None, None, 0)

   return (found, found_repo, found_timestamp, found_count)





def find_file(dir, filename, publickey_fn=None, publickey_string=None):
   # Note: this function should probably not be used. find_file_list() or
   # find_file_kind() should probably be used instead, because we now have
   # multiple types of keys (and thus multiple filenames to arbitrate)

   # TODO: args checking

   (found, found_repo, found_timestamp, found_count) = \
       find_file_ts(dir, [filename], publickey_fn, publickey_string)

   if found:
      arizonareport.send_out(4, "[DEBUG] " + filename + " found on " +
                                found_repo['name'] + "(" + str(found_count) +
                                " candidates)")

   return (found, found_repo)





def find_file_list(dir, filename_list, publickey_fn=None, publickey_string=None):
   # TODO: comment

   # TODO: args checking

   (found, found_repo, found_timestamp, found_count) = \
       find_file_ts(dir, filename_list, publickey_fn, publickey_string)

   if found:
      arizonareport.send_out(4, "[DEBUG] " + os.path.basename(found) + " found on " +
                                found_repo['name'] + "(" + str(found_count) +
                                " candidates)")

   return (found, found_repo)





def find_file_kind(dir, kind):
   """
   <Purpose>
      Search for a file from multiple repositories using multiple keys
   <Arguments>
      dir
         type of file to look for, currently "tpfiles" or "pacman"
      kind:
         suffix of file to look for. For example, "tpfile" to look for something
         that ends in .tpfile
   <Returns>
      a tuple (None, None, None) if the file cannot be found
      a tuple (filename, repo, keytuple) if the file can be found. repo is the dictionary
      for the repository that contained the file and can be used for
      informational purposes (letting the user know where the file came from)
   """
   keylist = storkusername.build_key_database()

   try_list = []

   found = None
   found_repo = None
   found_timestamp = None
   found_keytuple = None
   found_filename = None
   found_count = 0

   for keytuple in keylist:
      # keytuple[4] contains the config_prefix (username.key). Put it together
      # with the kind to get a candidate filename
      filename = keytuple[4] + "." + kind

      # keytuple[1] and keytuple[3] contain the filename of the public key file
      # and the public key as a string
      key_fn = keytuple[1]
      key_string = keytuple[3]

      try_list.append(filename)

      # search for this filename
      (this_found, this_found_repo, this_found_timestamp, this_found_count) = \
         find_file_ts(dir, [filename], key_fn, key_string)

      found_count = found_count + this_found_count

      # if we found something and it is better than what we already have, then
      # update our candidate
      if (found == None) or (this_found and (this_found_timestamp > found_timestamp)):
          found = this_found
          found_repo = this_found_repo
          found_timestamp = this_found_timestamp
          found_keytuple = keytuple
          found_filename = filename

   # if we didn't find anything, then fall back to searching for the default,
   # if a default username is available.
   if not found:
      default_keytuple = storkusername.build_default_keytuple()
      if default_keytuple:
         filename = default_keytuple[4] + "." + kind
         try_list.append(filename)

         usernames = arizonageneral.uniq([key[0] for key in keylist])
         if keylist and keylist[0]:
             arizonareport.send_out(0, "unable to find a " + kind + " file that starts with " + str(usernames))
         arizonareport.send_out(0, "reverting default filename: " + filename)

         (found, found_repo, found_timestamp, found_count) = \
            find_file_ts(dir, [filename], None, default_keytuple[3])

         if found:
            found_filename = filename
            found_keytuple = default_keytuple

   if found:
      arizonareport.send_out(4, "[DEBUG] " + found_filename + " found on " +
                                found_repo['name'] + "(" + str(found_count) +
                                " candidates)")
   else:
      arizonareport.send_error(1, "Failed to find a valid " + kind + " file. Tried the following:")
      for fn in try_list:
         arizonareport.send_error(1, "  " + fn)

   return (found, found_repo, found_keytuple)





def package_exists(name):
   """
   <Purpose>
      Checks to see if a particular package exists in the package lists.

   <Arguments>
      name:
              Name of the package.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      True or False, or None on error.
   """

   if name == None:
      return None
   
   # check params
   arizonageneral.check_type_simple(name, "name", str, "storkpackagelist.package_exists")

   # search for packages with the given name
   criteria_dict = {}
   criteria_dict['name'] = name
   mylist = find_packages(criteria_dict)

   # return True if there was at least one entry found, False otherwise
   return len(mylist) > 0





def find_package_name(filename):
   """
   <Purpose>
      Finds the correct package name for the given package filename.

   <Arguments>
      filename:
              Filename of the package.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      Package name, or None if not found.
   """
   # check params
   arizonageneral.check_type_simple(filename, "filename", str, "storkpackagelist.find_package_name")

   retlist = []

   # search for packages matching the given filename   
   criteria_dict = {}
   criteria_dict['filename'] = filename
   mylist = find_packages(criteria_dict)
   
   # go through results, and build a list of package names
   for package in mylist:
      retlist.append(package["name"])
  
   # remove any duplicate entries 
   retlist = arizonageneral.uniq(retlist)

   # return None if there weren't any results
   if len(retlist) < 1:
      return None

   # abort if there was more than one result.  we don't know which one 
   # they want to use.      
   if len(retlist) > 1:
      raise TypeError, "Unable to determine package name for '" + \
                       filename + "'.\n  Multiple matches found: " + \
                       ", ".join(retlist) + "."

   # there was exactly one result, return it   
   return retlist[0]





# Most of the functions are going to return dictionaries (rather than huge 
# tuples).   The dictionary keys are the package information types (like hash,
# size, etc.).   The values are the corresponding values of those types for
# this package.
#
# The fields in the package dictionary are defined in
# storkpackage.get_package_metadata, but described in detail here:
#
# filename      filename as stored on disk, ex: "nano-1.2.3-1.i386.rpm"
# name          package name, not including version or release, ex: "nano"
# version       package version, not including release, ex: "1.2.3"
# release       package release, ex: "1"
# size          unpacked package size, ex: "1026407"
# hash          sha1 hash of the package file,
#               ex: "59bb5f0cd15ee45ffff24a7c45538045608c8632"
# provides      list of dependencies fulfilled, each in the format:
#               "name = version-release"
# requires      list of dependencies required, each in the format:
#               "/filename" or "name OP version[-release]", where OP is
#               one of: =, <, <=, >, >=, and [-release] indicates that
#               the release number is optional.
# files         list of files and directories that will be installed by
#               the package
# URL           list of URLs as provided by the creator of the metadata. See
#               also _URL.
# _valid        set to True if the metadata's hash has been validated
# _repo         repository that this metadata came from
# _metadatahash TODO description
# _URL          list of expected download locations for the package. _URL is
#               generated from URL if it is available. Otherwise a default
#               _URL is generated by using the URL of the repository.
#
# Note that these field names are not hardcoded anywhere in this file
# (with the exception of names starting with _),  so if an improper field 
# name is used, it will just result in an empty search result. 
#
# Any field (key) beginning with an _ (for example, _metadatahash) is not
# stored in the file and is reconstituted on the fly

def find_packages(criteria):
   """
   <Purpose>
      This takes a dict of items and fields and returns a list of 
      corresponding package dicts.  This is essentially a search function 
      for packages given incomplete information

   <Arguments>      
      criteria:
         This is a dictionary where the keys correspond to the fields that
         need to be matched and the fields are the values that must be
         found.   

   <Exceptions>
      TypeError is raised when given an invalid argument.
      IOError may be raised if the package meta files are corrupted

   <Side Effects>
      None

   <Returns>
      a list of dicts corresponding to the matched packages
   """
   arizonageneral.check_type_simple(criteria, "criteria", dict, "find_packages")

   # Find all of the packages that match this key/value pair
   initial = True
   for keyvalpairs in criteria.iteritems():
     cur_filenames = __find_package_fnlist_on_one_criteria(keyvalpairs[0], keyvalpairs[1])
     if initial:
        initial = False
        filenamelist = cur_filenames
     else:
        # If we have more than one criteria, we only want files that match
        # all of the criteria
        filenamelist = arizonageneral.intersect(filenamelist, cur_filenames)

   # Now we build the list of package information dicts
   metadatadicts = []

   for current_fn in filenamelist:
      metadatadicts.append(package_metadata_fn_to_dict(current_fn))

   # TODO Do I want to do a "uniq" operation or combine URLs somehow?

   return metadatadicts
   




def __find_package_fnlist_on_one_criteria(field, value, path=None):
   """
   <Purpose>
      This takes a field and a value and returns a list of corresponding 
      package filenames.  This is essentially a search function for 
      packages given incomplete information.

   <Arguments> 
      field:
                Field to be searched, ex: _metadatahash
      value:
                Value we want to find in the field, ex: 3fa687d23a07cc9...
      path:
                (default: None, for no restriction)
                Restrict search to a certain directory.     

   <Exceptions>
      TypeError is raised when given an invalid argument.
      IOError may be raised if the package meta files are corrupted

   <Side Effects>
      None.

   <Returns>
      A list of package filenames.
   """
   matching_files = []
   
   stars = value.count("*")
   if stars == 1:
      if value[-1] == "*":
         useindex = True
         fuzzy = True
         value2 = value[:-1]
      else:
         useindex = False   
   elif stars > 1:
      useindex = False
   else:
      useindex = True
      fuzzy = False
      value2 = value
   
   # determine which directories to search
   if path == None:
      search_dirs = arizonaconfig.get_option("localpdir")
   else:
      search_dirs = [path]   

   # Handle metadatahash as a special case
   if field == "_metadatahash":
      for package_dir in search_dirs:
         # Currently, each metadatahash is its own file, and all 
         # metadatahash files for a pdir are in one directory.. so what
         # we do is look in that directory for the hash that we want.  If
         # a file by that name (the hash) exists, then we add the filename
         # to the matching files list
         if os.path.exists(os.path.join(arizonaconfig.get_option("localinfo"), package_dir, value)):
            matching_files.append(os.path.join(arizonaconfig.get_option("localinfo"), package_dir, value))
      return matching_files

   # need to search for list items differently than plain strings
   search = arizonageneral.grep_escape("'" + value + "'", True)
   if field == "files" or field == "provides" or field == "requires":
      # search for [anything'value'anything]
      search = "\\\\[.*" + search + ".*\\\\]"

   # now the kitchen sink matcher...
   for package_dir in search_dirs:
      # does an index file exist?  if so, use it (faster!)
      if useindex:
         index = os.path.join(arizonaconfig.get_option("localinfo"), package_dir, field + ".index")
         if os.path.isfile(index):
            return __hashtree_get(index, value2, fuzzy=fuzzy)
      
      # Grab files that match the search format: (start of line)field:(search as above)
      out, err, status = arizonageneral.popen5("grep -rl ^" + field + ":" + search + " " + \
                         os.path.join(arizonaconfig.get_option("localinfo"), package_dir))

      # add all of the files to this list
      for line in out:
         matching_files.append(line.rstrip("\n"))

   return matching_files





def __hashtree_get(filename, key, fuzzy=False, offset=False):
   """
   <Purpose>
      Searches a hashtree file for the specified key and returns either 
      its associated data as a list or its byte offset in the index file.
      
      Hashtree file entries are one line each, and are in the following 
      format:
      key\tdata[\t...]\n

   <Arguments>      
      filename:
         The hashtree file to search.  For this algorithm to work, the 
         keys must be in sorted order, and the sort based on order of 
         ASCII values.
      key:
         The key to look for.
      fuzzy:
         (default: False)
         Find the first item that starts with the given key.  
         Note: only returns a single match of the key, so this is not
               equivalent to a wildcard match.
      offset:
         (default: False)
         If True, returns the byte offset to the beginning of the line 
         where the key was found, rather than returning the data values.

   <Exceptions>
      TODO

   <Side Effects>
      None

   <Returns>
      offset is True:
         Returns the byte offset of the beginning of the line where the
         key was found:
      offset is False:
         Returns a list of strings containing the data items.   
   """
   if offset:
      data = -1
   else:   
      data = []

   # open the file for binary reading
   try:
      f = open(filename, "rb")
   except IOError:
      return data

   low = 0
   high = os.stat(filename).st_size - 1

   # traverse tree
   pos = 0
   last = -1
   while True:   
      # parse line  
      truepos = f.tell() 
      line = f.readline().split("\t")
      if pos == last or not line[0]:
         break 
      last = pos   
    
      # found key?
      if key == line[0] or (fuzzy and line[0].startswith(key)):
         if offset:
            data = truepos
         else:
            # remove trailing newline from last data item
            line[-1] = line[-1].rstrip("\n")
      
            # return only the data 
            data = line[1:]
         break
   
      # didn't find key, determine which direction to look
      if key < line[0]:
         # key is smaller than what we found
         high = pos
         pos = (pos + low) / 2
      else:
         # key is larger than what we found
         low = pos
         pos = (pos + high) / 2
   
      # go to the branch
      f.seek(pos)
      
      # we probably ended up in the middle of a line, find the beginning
      # of the next line
      f.readline()   
   
   # done, close the file and return results
   f.close()
   return data





def __append_index(field, metafile, outputfile, tempdir="/tmp"):
   """
   <Purpose>
      Reads a metadata file and adds any new information it provides to
      the index file.

   <Arguments>      
      field:
         The metadata field to build the index for (ex: "provides")
      metafile:
         The metadata file to be read.
      outputfile:
         The index file to add to.
      tempdir:
         Which directory to use for the writing of temporary data files.      

   <Exceptions>
      TODO

   <Side Effects>
      None

   <Returns>
      None.
   """
   # read dictionary entry for the field we are looking for  
   entry = package_metadata_fn_to_dict(metafile)[field]
   
   # convert a string to a list of a single string 
   # for example the "filename" field won't be a list but "provides" will
   if not isinstance(entry, list):
      entry = [entry]

   # examine each entry in the list
   for item in entry:
      # does the entry already exist?
      metafilepos = __hashtree_get(outputfile, item, offset=True)
      
      if metafilepos < 0:
         # can just create our new line
         newline = [metafile]
      else:
         # yes.. need to extract the line
         tempfile = os.path.join(tempdir, str(random.random()) + "__append_index")
         fin = open(outputfile, "rb")
         fout = open(tempfile, "w")
         newline = []
         while True:
            pos = fin.tell()
            line = fin.readline()
            if line == "":
               break
            if pos == metafilepos:
               # found the line, extract it
               newline = line.rstrip("\n").split("\t")[1:]
            else:   
               # writes all lines of the original file except the one
               # we're extracting
               fout.write(line)
         fout.close()
         fin.close()
         
         # replace original file with our new file 
         os.remove(outputfile)
         os.rename(tempfile, outputfile)
         
         # add our filename to the entry
         newline.append(metafile)
         newline = arizonageneral.uniq(newline)
         
      # open the index file
      f = open(outputfile, "a")
   
      # write the new line
      f.write(item + "\t" + "\t".join(newline) + "\n")

      # close the file
      f.close()       
      
      # sort the file
      tempfile = os.path.join(tempdir, str(random.random()) + "__append_index")
      os.system("LC_ALL=C sort " + outputfile + " >" + tempfile)
      os.remove(outputfile)
      os.rename(tempfile, outputfile)
             




def __build_index(field, path):
   """
   <Purpose>
      Builds an index for the metadata in a particular directory.

   <Arguments>      
      field:
         The metadata field to build the index for (ex: "provides")
      path:
         The directory where the metadata files are located.
         Also, the directory where the index file will be written.  
         It will be named "path/<field>.index"

   <Exceptions>
      TODO
      
   <Side Effects>
      None

   <Returns>
      None.
   """
   outputfile = os.path.join(path, field + ".index")
   
   # remove an existing index 
   if os.path.isfile(outputfile):
      os.remove(outputfile)

   # building the index takes a while, so set up a progress indicator
   if arizonareport.get_verbosity() > 1:
      width = arizonareport.console_size()[1]
      if width == None:
         width = 70
   else:
      width = 0
   import download_indicator
   prog_indicator_module = download_indicator
   prog_indicator_module.set_width(width)

   filenames = dircache.listdir(path)
   n = len(filenames)
   for i, metahash in enumerate(filenames):
      metafile = os.path.join(path, metahash)
      
      # listdir returns subdirectories too, skip them
      if not os.path.isfile(metafile):
         continue

      # add the items in this metahash to the index
      __append_index(field, metafile, outputfile)

      # update progress indicator
      prog_indicator_module.download_indicator(i + 1, 1, n)

   arizonareport.send_out(2, "")




def package_get_default_url(repo_dict, filename, pack):
   """
   <Purpose>
      Generates the default URL of a package in the case that a packages does
      not already have a _URL entry.

     takes a filename such as:
        /usr/local/stork/var/packageinfo/quadrus.cs.arizona.edu_PlanetLab_V3_dist/3fa687d23a07c...
     and changes it to:
        quadrus.cs.arizona.edu/PlanetLab/V3/dist/3fa687d23a07c...
   <Arguments>
      filename - the filename of the package
      pack - the package dictionary; '_URL' will be added to it
   """

   # make sure the package knows what repository it belongs to
   assert('_repo' in pack)

   # build a URL from the packageinfo filename that the repository gave
   # us.

   # remove repository local dir part
   URL = filename[len(pack['_repo']['localdir']):]

   # remove any leading or trailing /'s
   URL = URL.strip("/")

   # change _'s into /'s
   URL = URL.replace("_", "/")

   specUrl = repo_dict['repurl']
   if specUrl:
       slashPos = URL.find("/")
       if slashPos > 0:
           URL = specUrl + URL[slashPos+1:]

   # concatenate the filename onto the end, so we have a complete URL
   URL = os.path.join(URL, pack['filename'])

   pack['_URL'] = [URL]

   return pack





def load_package_metadata_fn(filename):
   """
   <Purpose>
      Loads metadata from a .metadata file or a repository packageinfo metadata
      file.

   <Arguments>
      filename - the filename of the metadata file

   <Returns>
      dictionary containing the metadata entries
   """
   arizonageneral.check_type_simple(filename, "filename", str, "package_metadata_fn_to_dict")

   if not arizonageneral.valid_fn(filename):
      raise IOError, (2, "No such file or directory '" + filename + "' in package_metadata_fn_to_dict")

   ret_dict = {}
   f = file(filename)
   for line in f:
      (key, value) = line.split(':', 1)
      # This is what converts lists, etc. to and from the correct types
      ret_dict[key] = eval(value)
   f.close()

   return ret_dict





def package_metadata_fn_to_dict(filename):
   """
   <Purpose>
      This takes a metadata filename for a package and returns a dict

   <Arguments>
      filename:
         The metadata file that should be retrieved

   <Exceptions>
      TypeError is raised when given an invalid argument.
      IOError may be raised if the package meta files are corrupted

   <Side Effects>
      None

   <Returns>
      A package dict for this metadata file.
   """
   arizonageneral.check_type_simple(filename, "filename", str, "package_metadata_fn_to_dict")

   ret_dict = load_package_metadata_fn(filename)

   # add the metadata hash as a field
   ret_dict['_metadatahash'] = os.path.basename(filename)

   # figure out which repository contains the file. We need to know this so
   # we can strip the repository's local dir out of the filename to make the
   # url.
   for repo in glo_repo_list:
      repo_dir = repo['localdir']
      if filename.startswith(repo_dir):
         ret_dict['_repo'] = repo
         break
   else:
      # we couldn't find the repository that this filename belonged to
      # this should not happen
      arizonareport.send_error(0, "ERROR: " + str(filename) + " does not belong to any repository")
      raise TypeError, "Unable to find repository for " + str(filename)

   # if the package already contains a URL field, then assign _URL=URL.
   # Otherwise, we'll generate _URL.
   if 'URL' in ret_dict:
      ret_dict['_URL'] = ret_dict['URL']
   else:
      package_get_default_url(ret_dict['_repo'], filename, ret_dict)

   return ret_dict



def package_metadata_dict_get_canonical_hash(metadict):
   """
   <Purpose>
      Generate a canonical metadata hash for a package.

      When a user creates a .metadata file that contains his own URL, the
      metadatahash that is generated includes that URL entry. When stork
      downloads a package and extracts the metadata, there is no URL field, and
      therefore the hashes don't match.

      This function takes a metadata and generates the hash that the metadata
      would have with the URL entry removed, so that we can compare it to
      downloaded packages.

   <Arguments>
      metadict - dictionary containing metadata
   """
   # let's assume that we're always dealing with metadicts that include a
   # _metadata hash field (loaded by package_metadata_fn_to_dict)
   assert('_metadatahash' in metadict)

   # check for the easy case first -- no URL entry in metadict, and the hash is
   # already computed -- so we can just return what we already have.
   if not ('URL' in metadict):
      return metadict['_metadatahash']

   # since we are going to be recomputing the metahash, we need to ensure that
   # this metadict is valid, and was not forged.
   if not storkpackage.package_metadata_dict_valid(metadict):
       # the metadict's precomputed metahash is invalid. Report the error to
       # the user.
       arizonareport.send_error(1, "invalid metahash detected: " + str(metadict['filename']) + " " + str(metahash) + " " + str(metadict['_metadatahash']))

       # return the (possibly forged) _metadatahash. This is what we would have
       # used had there been no URL entry to remove.
       return metadict['_metadatahash']

   # remove the URL field from the metadict. Make a copy first, so we don't
   # damage the original.
   metadict = metadict.copy()
   del metadict['URL']

   # compute a new metahash
   metahash = storkpackage.package_metadata_dict_get_hash(metadict)

   return metahash





"""
TODO remove references to these functions
storkbuild:
field_list = ['name', 'version', 'release', 'size', 'hash', 'file', 'requires', 'provides', 'files']

storkbuild:
field_sep = '|'

storkquery:
def cull_database(items, fields):
   ""'Returns a string that may cull the database of unnecessary entries.
      Not clever yet... examine before using""'
   if len(items) != len(fields):
      arizonareport.send_error(1, "Internal error, fields and items of differing length in cull_database")
      sys.exit(1)

   data = []
   for num in range(len(field_list)):
      data.append('.*')
   for num in range(len(items)):
      data[get_field(fields[num])] = items[num]

   ans = 'grep "^' + data[0]
                                                                                
   for dataitem in data[1:]:
      ans += (field_sep + dataitem)
                                                                                
   ans += '$"'
   return ans

storkquery:
def get_db_field(string,field):
   ""'Returns a named field from a string
      ""'
   the_list = string.split(field_sep)
   return the_list[get_field(field)]

storkquery: 
def package_cache_name(pkg_db):
   ""'
   <Purpose>
      Returns the local cache file name associated with a package 
      repository.
   ""'
   pos = pkg_db.find("://")
   if pos == -1:
      return arizonaconfig.get_option("dbdir") + "/" + pkg_db.replace("|", "_").replace("/", "_")
   else:
      return arizonaconfig.get_option("dbdir") + "/" + pkg_db[pos + 3:].replace("|", "_").replace("/", "_")
"""

