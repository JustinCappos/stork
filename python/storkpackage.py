#! /usr/bin/env python

import arizonareport
import arizonaconfig
import arizonageneral
import arizonacrypt
import os
import tempfile
import shutil



# global list that holds (a package manager name as a string, package manager module itself)
inited_packmanager_list = []
possible_packmanagers = None

# list of all dependencies satisfied by the package managers themselves
glo_packagemanagers_provide = []


#           [option, long option,         variable,          action,   data,     default,        metavar,           description]
"""arizonaconfig
   options=[["",     "--packagemanagers", "packagemanagers", "append", "string", ["rpm", "tar"], "packagemanagers", "use these programs to manage packages (default rpm, tar)"]]
   includes=["$SELF/package/*"]
"""




def initialize():
   """
   <Purpose>
      Check whether package managers have been initialized or not.
      If not, initializes every package manager at once

   <Arguments>
      None.

   <Exceptions>
      ImportError:
         If given package manager cannot be found.
         Or, there is no packagemanager setting in configuration.

   <Side Effects>
      Set inited_packmanager_list and possible_packmanagers.
      Build glo_packagemanagers_provide

   <Returns>
      None.
   """
   global possible_packmanagers
   global glo_packagemanagers_provide
   global inited_packmanager_list

   # if it hasn't been initialized
   if possible_packmanagers == None:
      inited_packmanager_list = []
   
      # get a list of strings which indicate what package manages are available   
      packmanagers = arizonaconfig.get_option("packagemanagers")
  
      # if there is no setting for packagemanagers option in arizonaconfig
      if packmanagers == None:
         # raise exception
         raise arizonageneral.Exception_Data("ERROR: missing --packagemanagers setting", ([], []))

      possible_packmanagers = packmanagers
 
      # reset internal provides list
      glo_packagemanagers_provide = []     

      # for each package manager
      for manager in possible_packmanagers:
         arizonareport.send_out(4, "[DEBUG] Trying to install package manager '" + manager + "'");
         # import each package manager
         try:
            # TODO possible security problem?   For example, method="rpm as chosen_packmanager; hostile code...; #"
            exec('import package.stork' + manager + ' as chosen_packmanager')
            provides = chosen_packmanager.initialize()

            # handle initialization errors
            if provides == None:
               arizonareport.send_error(2, "WARNING: Package manager `" + manager + "' failed initialization, skipping.")
               continue

            glo_packagemanagers_provide += provides

            # store package manager name and package manager module into a list
            inited_packmanager_list.append(('stork' + manager, chosen_packmanager))
         # if given manager is invalid
         except ImportError, (sterr):
            arizonareport.send_error(2, "WARNING: Package manager `" + manager + "' could not be imported, skipping.")
            continue
         # storknestrpm tends to throw IOErrors when there are problems
         except IOError, e:
            arizonareport.send_error(2, "WARNING: Package manager `" + manager + "' generated IO error, skipping.")
            continue
         except Exception, e:
            arizonareport.send_error(2, "WARNING: Package manager `" + manager + "' generated exception " + str(e))
            continue

      # did we end up having any package managers?
      if len(inited_packmanager_list) < 1:
         # raise exception
         raise arizonageneral.Exception_Data("ERROR: no usable package managers.", ([], []))
         




def get_packagemanagers_provide():
   """
   <Purpose>
      Returns a string list of all dependencies fulfilled internally
      by the installed package managers.

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      String list of all dependencies fulfilled internally by the 
      installed package managers.
   """
   # initialize package managers
   initialize()

   return glo_packagemanagers_provide   




  
def is_package_understood(filename): 
   """
   <Purpose>
      Given a filename, checks whether it is valid by any of given package
      managers.

   <Arguments>
      filename:
         Filename of the package to check.

   <Exceptions>
      TypeError:
         If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      True if the package is valid and understood, False otherwise.
   """
   # check params
   arizonageneral.check_type_simple(filename, "filename", str, "storkpackage.is_package_understood")

   # initialize package managers
   initialize()

   # go through every possible package manager
   for packagemanager in inited_packmanager_list:      
      if packagemanager[1].is_package_understood(filename):
         return True

   return False





def get_package_metadata(filename, original_filename=None):
   """
   <Purpose>
      Given a package filename, returns a dict of the package metadata.

   <Arguments>
      filename:
              This is the package file we wish to extract metadata from
      original_filename:
              This is the original name, to be used when getting the hash
              on a file that has been temporarily renamed.

   <Exceptions>
      TypeError:
              If a type mismatch or parameter error is detected (not a package 
              file).
      IOError:
              If an error occurred opening the file, etc.

   <Side Effects>
      None.

   <Returns>
      String list which contains the metadata for the package file 
   """
   # check params
   arizonageneral.check_type_simple(filename, "filename", str, "storkpackage.get_package_metadata")

   arizonareport.send_out(4, "[DEBUG] get_package_metadata: filename = " + filename)

   if not os.path.exists(filename):
      raise TypeError, "File does not exist: " + str(filename)

   package_dict = {}
   if original_filename != None:
      package_dict['filename'] = original_filename
   else:
      package_dict['filename'] = os.path.basename(filename)

   # This fetches a list containing the name, version, release, and size
   info = get_package_info(filename)
   if info == None:
      raise TypeError, "Unrecognized package format: " + str(filename)

   package_dict['name'] = info[0]
   package_dict['version'] = info[1]
   package_dict['release'] = info[2]
   package_dict['size'] = info[3]
   
   # may throw IOError or TypeError 
   package_dict['hash'] = arizonacrypt.get_fn_hash(filename)
   package_dict['provides'] = get_packages_provide([filename])
   package_dict['requires'] = get_packages_require([filename])
   package_dict['files'] = get_packages_files([filename])

   return package_dict



def package_metadata_dict_to_fn(metadict, dest_dir, dest_fn=None):
   """
   <Purpose>
      This takes a metadata dict for a filename and writes it to a file. If
      dest_fn is specified, then the file will be written to that filename.
      Otherwise, if dest_fn==None, then a filename will be generated based
      on the metahash.

   <Arguments>
      metadict:
         The metadata dictionary with the data we want to write out
      dest_dir:
         The directory where the file should be written
      dest_fn:
         The filename where the file should be written (optional)

   <Exceptions>
      TypeError is raised when given an invalid argument.
      OError may be raised if writing the file fails

   <Side Effects>
      None

   <Returns>
      The file created
   """
   arizonageneral.check_type_simple(metadict, "metadict", dict, "package_metadata_dict_to_fn")
   if dest_dir:
      arizonageneral.check_type_simple(dest_dir, "dest_dir", str, "package_metadata_dict_to_fn")
   if dest_fn:
      arizonageneral.check_type_simple(dest_fn, "dest_fn", str, "package_metadata_dict_to_fn")

   (metadatahash, thisfilename) = package_metadata_dict_get_hash(metadict, True)

   # if dest_fn was specified, then use that filename
   if dest_fn:
      # if the caller specified both dest_dir and dest_fn, then splice them
      # together.
      if dest_dir:
          outfn = dest_dir + "/" + os.path.basename(dest_fn)
      else:
          outfn = dest_fn
   else:
      # no dest_fn was specified, so generate a filename based on the metahash
      outfn = dest_dir + "/" + metadatahash

   shutil.move(thisfilename, outfn)

   return outfn





def package_metadata_dict_get_hash(metadict, keep_temp_file=False):
   """
   <Purpose>
      Get the hash from a metadata file.

      This function strips out any temporary/generated entries of the metadict
      (entries that start with _) and then generates the hash.

   <Arguments>
      metadict - dictionary containing metadata
      keep_temp_file - True to keep the temporary disk file that contains the
                       metadata. False to automatically delete.

   <Returns>
      if keep_temp_file is true:
         a tuple (metadatahash, tempfilename)
      otherwise:
         metadatahash
   """
   mydict = metadict.copy()

   # Remove keys that start with _ as these are generated on the fly and not
   # included in the hash.
   for key in mydict.keys():
      if key[0] == '_':
         del mydict[key]

   kvpairs = []
   for pair in mydict.iteritems():
     kvpairs.append(pair)
   kvpairs.sort()

   # I now have a sorted kvpair list (sorting is important because dict order
   # is arbritrary and it needs to be written in the same order so the hashes
   # will match)

   # we will write the metadata to a temporary file, then compute the hash and
   # continue
   (thisfilefd, thisfilename) = tempfile.mkstemp(suffix=".xml_original_file.temp")

   for kvpair in kvpairs:
      os.write(thisfilefd, kvpair[0] + ":" + repr(kvpair[1]) + "\n")

   os.close(thisfilefd)

   # There might be a race condition here (security flaw) TODO NEEDS WORK FIXME
   metadatahash = arizonacrypt.get_fn_hash(thisfilename)

   if not keep_temp_file:
      os.remove(thisfilename)
      return metadatahash

   return (metadatahash, thisfilename)





def package_metadata_dict_validate(metadict):
   """
   <Purpose>
      Given a metadata dictionary, verify that it is valid

   <Arguments>
      metadict:
              Metadata dictionary

   <Side Effects>
      Sets metadict['_valid'] to True if it is valid

   <Returns>
      True if metadict is valid, false otherwise
   """
   if metadict.get('_valid', False):
      return True

   # compute the hash
   hash = package_metadata_dict_get_hash(metadict)

   if not '_metadatahash' in metadict:
      arizonareport.send_error(0, "metadata missing hash for " + metadict.get('name', 'unknown'))
      return False

   if metadict['_metadatahash'] != hash:
      arizonareport.send_error(0, "invalid metadata detected for " + metadict.get('name', 'unknown'))
      return False

   metadict['_valid'] = True

   return True





def get_package_metadata_hash(filename, createhashfile=False, original_filename=None):
   """
   <Purpose>
      Given a package filename, returns the hash of the package metadata.

   <Arguments>
      filename:
              This is the package file we wish to extract the hash of the
              metadata from

      createhashfile:
              If True, after the hash has been computed, a file will be
              written, filename.metahash, containing the metahash.  If
              file creation fails, it will not throw exceptions.

   <Exceptions>
      TypeError:
              If a type mismatch or parameter error is detected (not a package
              file).
      IOError:
              If an error occurred opening the file, etc.

   <Side Effects>
      Creates and then removes a temp file

   <Returns>
      The hash of the metadata (as a string)
   """
   # check params
   arizonageneral.check_type_simple(filename, "filename", str, "storkpackage.get_package_metadata_hash")

   arizonareport.send_out(4, "[DEBUG] get_package_metadata_hash: filename = " + filename)

   try:
      package_dict = get_package_metadata(filename, original_filename)
   except TypeError:
      arizonareport.send_error(0, "Error: Unrecognized Package Format - " + filename)
      # re-raise the TypeError, because we can't proceed without package_dict
      raise TypeError, "Error: Unrecognized Package Format - " + filename

   outfn = package_metadata_dict_to_fn(package_dict, "/tmp")
   
   # JRP 1/10/07 -- changed the call below
   # because outfn is a file, not a directory
   # and rmdir_recursive is for directories
   # (this was causing a leak of metahash files
   # in tmp
   #arizonageneral.rmdir_recursive(outfn)
   if os.path.isfile(outfn):
       os.unlink(outfn)

   metahash = os.path.basename(outfn)
   arizonareport.send_out(4, "[DEBUG] get_package_metadata_hash(" + filename + ") = " + metahash)
   
   # create the filename.metahash file, if requested
   if createhashfile:
      try:
         f = open(filename + ".metahash", "w")
         f.write(metahash + "\n")
         f.close()         
      except IOError: #changed from a general exception
         arizonareport.send_error(4, "[DEBUG] get_package_metadata_hash: couldn't create file: " + filename + ".metahash")
   
   return metahash





def get_packages_provide(filename_list):
   """
   <Purpose>
      Given a string list of package filenames, returns a string list of 
      dependencies that those packages can provide.

   <Arguments>
      filename_list:
              String list of package filenames.

   <Exceptions>
      TypeError:
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      String list of dependencies provided by the given package files.
      In the format "name = version" or "name".
   """
   # check params
   arizonageneral.check_type_stringlist(filename_list, "filename_list", "storkpackage.get_packages_provide")

   if len(filename_list) < 1:
      return []

   # a list that holds provided packages   
   providelist = []

   # initialize package managers
   initialize()

   # for each file, locate a package manager which can handle
   # that package, get the list, and continue to the next file.
   for filename in filename_list:
      for packagemanager in inited_packmanager_list:
         if packagemanager[1].is_package_understood(filename):
            # get a list of provided packages, and break
            providelist += packagemanager[1].get_packages_provide([filename])
            break

   return providelist





def get_packages_require(filename_list):
   """
   <Purpose>
      Given a string list of package filenames, returns a string list of 
      dependencies that those packages require.

   <Arguments>
      filename_list:
              String list of package filenames.

   <Exceptions>
      TypeError:
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      String list of dependencies required by the given package files.
   """
   # check params
   arizonageneral.check_type_stringlist(filename_list, "filename_list", "storkpackage.get_packages_require")

   if len(filename_list) < 1:
      return []

   # a list that holds required packages   
   requirelist = []

   # initialize package managers
   initialize()

   # for each file, locate a package manager which can handle
   # that package, get the list, and continue to the next file.
   for filename in filename_list:
      for packagemanager in inited_packmanager_list:
         if packagemanager[1].is_package_understood(filename):
            # get a list of required packages, and break
            requirelist += packagemanager[1].get_packages_require([filename])
            break

   return requirelist





def get_packages_files(filename_list):
   """
   <Purpose>
      Given a string list of package filenames, returns a string list of 
      files that are installed by those packages.

   <Arguments>
      filename_list:
              String list of package filenames.

   <Exceptions>
      TypeError:
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      String list of files in the given package files.
   """
   # check params
   arizonageneral.check_type_stringlist(filename_list, "filename_list", "storkpackage.get_packages_files")

   if len(filename_list) < 1:
      return []

   # a list that holds which files are provided in packages 
   fileslist = []

   # initialize package managers
   initialize()

   # for each file, locate a package manager which can handle
   # that package, get the list, and continue to the next file.
   for filename in filename_list:
      for packagemanager in inited_packmanager_list:
         if packagemanager[1].is_package_understood(filename):
            # get a list of files provided, and break
            fileslist += packagemanager[1].get_packages_files([filename])
            break

   return fileslist





def get_package_info(filename):
   """
   <Purpose>
      Given a package filename, returns a string list of package 
      information of the form: 
        [NAME, VERSION, RELEASE, SIZE]

   <Arguments>
      filename:
              Package filename.

   <Exceptions>
      TypeError:
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      String list containing package information, or None on error.
   """
   # check params
   arizonageneral.check_type_simple(filename, "filename", str, "storkpackage.get_package_info")

   arizonareport.send_out(4, "[DEBUG] get_package_info: filename = " + filename) 

   # initialize package managers
   initialize()

   # go through every possible package manager
   arizonareport.send_out(4, "[DEBUG] get_package_metadata: inited_packmanager_list = " + str(inited_packmanager_list)) 
   for packagemanager in inited_packmanager_list: 
      arizonareport.send_out(4, "[DEBUG] get_package_info: packagemanager = " + str(packagemanager)) 
      if packagemanager[1].is_package_understood(filename):
         arizonareport.send_out(4, "[DEBUG] get_package_info: is_package_understood = True") 
         info = packagemanager[1].get_package_info(filename)
         arizonareport.send_out(4, "[DEBUG] get_package_info: info = " + str(info)) 
         if info != None:
            return info
            
   return None





def get_installed_versions(package_list):
   """
   <Purpose>
      Given a package list, returns a list containing the name and version
      of each package if installed.

   <Arguments>
      package_list:
         List of strings containing the names of the packages to get 
         version information for.

   <Exceptions>
      TypeError:
         If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      String list containing each package name and version (in the format
      "name = version-release"). Packages that are not installed are not
      listed. If a package has more than one installed version, then multiple
      results may be returned for that package.
   """
   # check params
   arizonageneral.check_type_stringlist(package_list, "package_list", "storkpackage.get_installed_versions")

   # initialize package managers
   initialize()
   
   # initialize the list
   installed_list = []

   for packagemanager in inited_packmanager_list:      
      installed_list += packagemanager[1].get_installed_versions(package_list)

   # both rpm and nestrpm will report a match for the same version, so we need
   # to uniquify the list
   installed_list = arizonageneral.uniq(installed_list)

   return installed_list





def get_installedpackages_fulfilling(dep_list):
   """
   <Purpose>
      Given a string list of dependencies, returns a string list of 
      installed packages that fulfill those package dependencies.
      
   <Arguments>
      dep_list:
         String list of package dependencies.

   <Exceptions>
      TypeError:
         If given argument is not a list of strings.

   <Side Effects>
      None.

   <Returns>
      String list of installed packages that meet the given dependencies.
   """
   
   # type checking on the given list
   arizonageneral.check_type_stringlist(dep_list, "dep_list", "storkpackage.get_installedpackages_fulfilling")
   
   if len(dep_list) < 1:
      return []

   # a list that holds installed packages   
   fulfillinglist = []

   # initialize package managers
   initialize()

   # go through every possible package manager
   for packagemanager in inited_packmanager_list:      
      # for each manager, get a list of installed packages
      fulfillinglist += packagemanager[1].get_installedpackages_fulfilling(dep_list)         

   fulfillinglist = arizonageneral.uniq(fulfillinglist)

   return fulfillinglist


   
def get_installedpackages_requiring(dep_list):
   """
   <Purpose>
      Given a string list of dependencies, returns a string list of 
      installed packages that require those package dependencies.
      
   <Arguments>
      dep_list:
         String list of package dependencies.

   <Exceptions>
      TypeError:
         If given argument is not a list of strings.

   <Side Effects>
      None.

   <Returns>
      String list of installed packages that meet the given dependencies.
   """
   
   # type checking on the given list
   arizonageneral.check_type_stringlist(dep_list, "dep_list", "storkpackage.get_installedpackages_requiring")
   
   if len(dep_list) < 1:
      return []

   # a list that holds installed packages   
   requiringlist = []

   # initialize package managers
   initialize()

   # go through every possible package manager
   for packagemanager in inited_packmanager_list:      
      # for each manager, get a list of installed packages
      requiringlist += packagemanager[1].get_installedpackages_requiring(dep_list)  

   requiringlist = arizonageneral.uniq(requiringlist)

   return requiringlist


   
def get_installedpackages():
   """
   <Purpose>
      Return a list of all installed packages.
      
   <Arguments>

   <Exceptions>

   <Side Effects>
      None.

   <Returns>
      String list of installed packages.
   """
   
   # a list that holds installed packages   
   installedlist = []

   # initialize package managers
   initialize()

   # go through every possible package manager
   for packagemanager in inited_packmanager_list:      
      # for each manager, get a list of installed packages
      installedlist += packagemanager[1].get_installedpackages()         

   installedlist = arizonageneral.uniq(installedlist)
      
   return installedlist



def get_installedpackages_provide(package_list):
   """
   <Purpose>
      Given a string list of installed package names, returns a string 
      list of all dependencies fulfilled by those packages.

   <Arguments>
      package_list:
         String list of installed package names.

   <Exceptions>
      TypeError:
         If given argument is not a list of strings.

      IOError: 
         If asked to report on a package that is not installed.

   <Side Effects>
      None.

   <Returns>
      String list of all dependencies fulfilled by the given packages.
   """

   # type checking on the given list
   arizonageneral.check_type_stringlist(package_list, "package_list", "storkpackage.get_installedpackages_provide")

   if len(package_list) < 1:
      return []

   # a list that holds all dependencies
   providelist = []

   # initialize package managers
   initialize()

   # go thought every possible package manager
   for packagemanager in inited_packmanager_list: 
      # for each manager, get a list of all dependencies
      try:
         providelist += packagemanager[1].get_installedpackages_provide(package_list)

      # If asked to report on a package that is not installed.
      except IOError, (errno,strerr):
         arizonareport.send_error(2, "get_installedpackages_provide: I/O error(" + str(errno) + "): " + str(strerror))
         # return the list we got so far
         return providelist

   providelist = arizonageneral.uniq(providelist)

   return providelist




def get_installedpackages_requires(package_list):
   """
   <Purpose>
      Given a string list of installed package names, returns a string 
      list of all dependencies required by those packages.

   <Arguments>
      package_list:
         String list of installed package names.

   <Exceptions>
      TypeError:
         If given argument is not a list of strings.

      IOError: 
         If asked to report on a package that is not installed.

   <Side Effects>
      None.

   <Returns>
      String list of all dependencies fulfilled by the given packages.
   """

   # type checking on the given list
   arizonageneral.check_type_stringlist(package_list, "package_list", "storkpackage.get_installedpackages_provide")

   if len(package_list) < 1:
      return []

   # a list that holds all dependencies
   providelist = []

   # initialize package managers
   initialize()

   # go thought every possible package manager
   for packagemanager in inited_packmanager_list: 
      # for each manager, get a list of all dependencies
      try:
         providelist += packagemanager[1].get_installedpackages_requires(package_list)

      # If asked to report on a package that is not installed.
      except IOError, (errno,strerr):
         arizonareport.send_error(2, "get_installedpackages_provide: I/O error(" + str(errno) + "): " + str(strerror))
         # return the list we got so far
         return providelist

   providelist = arizonageneral.uniq(providelist)

   return providelist




   
def execute(trans_list):
   """
   <Purpose>
      Installs packages with the given filenames.

   <Arguments>
      filename_list:
         String list of filenames representing packages to install.

   <Exceptions>
      TypeError:
         If given argument is not a list of strings.

      arizonageneral.Exception_Data
         Either if none of package managers can install a package, or if 
         install fails in the middle of procedure.

   <Side Effects>
      None.

   <Returns>
      None.
   """
   # check params
   arizonageneral.check_type_simple(trans_list, "trans_list", list, "storkpackage.install")

   if (len(trans_list) < 1):
      # Error?
      return

   trans_list = trans_list[:]

   # initialize package managers
   initialize()

   # a list that holds valid packages
   # for each package it holds a package manager which will be used to install it
   # example ("nano.i386.rpm", <storkrpm.py module>)
   valid_install_pack_list = []

   for trans in trans_list:
      # if a package can't be handled by any package manager, then raise error
      # this flag is to check this
      check_flag = False

      # apply each transaction to every initialized package manager
      for packagemanager in inited_packmanager_list:
         check_val = packagemanager[1].is_package_understood(trans['filename'])
         
         if check_val:
            # add this valid file to a list
            valid_install_pack_list.append((trans, packagemanager[1]))
            # a manager that understand this file is found
            check_flag = True
            # let's move to the next file
            break

      # if there is no manager that understands given file
      if not check_flag:
         raise arizonageneral.Exception_Data("install(): " + trans['filename'] + " cannot be installed by any given package manager", ([], transactions))
      # set check_flag default
      check_flag = False

   
   # the list consisting of grouped filenames with a supporting package manager
   # [([list of files], package module),...]
   final_valid_pack_list = []

   # go through every package manager initialized in the order given by config
   for packmanager in inited_packmanager_list:
      # a temp list which holds filenames that can be installed by given package manager
      temp_trans_list = []

      # go through the list that will be installed
      for item in valid_install_pack_list:
         (trans, packman) = item
         
         # if package managers are equal
         if packman == packmanager[1]:
            # add the filename to the list
            temp_trans_list.append(trans)
      # append the tuple that holds installable filename and its package manager to the final list
      final_valid_pack_list.append((temp_trans_list, packmanager[1]))

 
   # a list that holds filenames installed
   installed_trans_list = []
   not_installed_trans_list = trans_list
   for each_trans_list in final_valid_pack_list:
      if each_trans_list[0] == []:
         continue
      # install packages 
      # each_filelist[1] is package manager module and each_filelist[0] is list of transactions
      try:
         each_trans_list[1].execute(each_trans_list[0]) 
         installed_trans_list += each_trans_list[0]

         for each_trans in each_trans_list[0]:
            not_installed_trans_list.remove(each_trans)

      # if a package failed to install properly
      # return a list of files which installed so far.
      except arizonageneral.Exception_Data, err:
         (succeeded_list, junk) = err.data
         installed_trans_list += succeeded_list

         for each_trans in succeeded_list:
            not_installed_trans_list.remove(each_trans)

         raise arizonageneral.Exception_Data("storkpackage: install(): '" + str(err.message) + "' failed to install ", (installed_trans_list, not_installed_trans_list))


         
         


def remove(package_list, nodeps=False):
   """
   <Purpose>
      Removes packages with the given package names.

   <Arguments>
      package_list:
         String list of packages to remove.
      nodeps:
         If True, then force removal of packages even if existing packages 
         depend upon them. 

   <Exceptions>
      TypeError:
         If given argument is not a list of strings.

      arizonageneral.Exception_Data:
         If it fails to remove a package.

   <Side Effects>
      None.

   <Returns>
      None.
   """

   # check params
   arizonageneral.check_type_stringlist(package_list, "package_list", "storkpackage.remove")

   if len(package_list) < 1:
      return

   # initialize package managers
   initialize()

   check_list = package_list[:]
   manager_list = []
   not_removed_list = []
   for manager in inited_packmanager_list:
      # see which packages this package manager can remove
      handled_list = []
      for i, pack in enumerate(check_list):
         installed = manager[1].get_installed_versions([pack])
         if installed:
            check_list[i] = None
            not_removed_list.append(pack)
            handled_list.append(pack)
      if handled_list:
         manager_list.append((manager[1], handled_list))
             
      # remove the things from check_list that we set to None
      check_list = [pack for pack in check_list if pack != None]

   # check_list contains all packages not installed
   # not_removed_list contains all packages that are installed
   # manager_list is a list of (manager, package_list) tuples

   # there shouldn't be any packages left in the check list
   # (all should have been claimed by a package manager)
   if len(check_list) > 0:
      raise arizonageneral.Exception_Data("ERROR: some packages do not appear to be installed: " + ", ".join(check_list), ([], package_list))

   # a list that holds packages removed
   removed_list = []
   for manager in manager_list:
      # remove packages
      # manager[0] is the package manager module
      # manager[1] is the list of package names
      try:
         manager[0].remove(manager[1], nodeps) 
         removed_list += manager[1]

         for pack in manager[1]:
            not_removed_list.remove(pack)

      # if a package failed to remove properly
      # return a list of files which were removed so far.
      except arizonageneral.Exception_Data, err:
         (succeeded_list, junk) = err.data
         removed_list += succeeded_list

         for pack in succeeded_list:
            not_removed_list.remove(pack)

         raise arizonageneral.Exception_Data("ERROR: failed to remove some packages: '" + str(err.message) + "'", (removed_list, not_removed_list))





def reset():
   global possible_packmanagers
   global glo_packagemanagers_provide
   global inited_packmanager_list

   possible_packmanagers = None
   glo_packagemanagers_provide = []
   inited_packmanager_list = []
