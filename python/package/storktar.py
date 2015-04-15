#! /usr/bin/env python
"""
<Program Name>
   storktar.py

<Author>
   Programmed by Byung Suk, refactored by Jeffry Johnston.
   Additional tar formats and special files support by Jeffry Johnston.

<Purpose>
   Install/remove:
     tar file (.tar)
     gzipped tar file (.tar.gz, .tar.gzip, .tgz) 
     bzipped tar file (.tar.bz2, .tar.bzip2, .tbz2, .tbz) 
     compressed tar file (.tar.Z, .taz)
   
<Details>   
   Installing a package creates a PACKAGENAME.packinfo file in the 
   tarpackinfo directory, containing:
      name              Name of the package
      version           Package version (default is 0.0.0)
      release           Package release (default is 0)
      files             Tab separated list of files in the tarball, for 
                        file removal on uninstall
      
   Packages may contain the following special files (files with these 
   names are omitted from the files list above):
      .preinstall       Pre-install script which is run before install, 
                        then removed
      .postinstall      Post-install script which is run after install,
                        then removed
      .preremove        Pre-uninstall script which is run before removal.  
                        Moved to the tarpackinfo directory and renamed to 
                        PACKAGENAME.preremove
      .postremove       Post-uninstall script which is run after removal.  
                        Moved to the tarpackinfo directory and renamed to 
                        PACKAGENAME.postremove
"""

import os
import pwd
import re
import arizonageneral
import arizonaconfig
import arizonareport
import securerandom
import storktransaction

# import flags for os.stat()
from stat import *

"""arizonaconfig
   options=[["",     "--tarpackinfo", "tarpackinfopath", "store", "string", "/usr/local/stork/tar_packinfo", "PATH", "use this path to store tar package info (default is /usr/local/stork/tar_packinfo)"]]
   includes=[]
"""

DEFAULT_VERSION = "0.0.0"
DEFAULT_RELEASE = "0"
RECOGNIZED_EXTENSIONS = [".tar", \
                         ".tar.gz", ".tar.gzip", ".tgz", \
                         ".tar.bz2", ".tar.bzip2", ".tbz2", ".tbz", \
                         ".tar.Z", ".taz"]
SPECIAL_FILES = [".preinstall", ".postinstall", ".preremove", ".postremove"]
INSTALL_FLAGS = ["", "z", "j", "Z"]



tarpackinfo_path = None
def __init_packinfo():
   """ Returns True on error, False on success """
   global tarpackinfo_path
   
   if tarpackinfo_path == None:
      # get tar package info path
      tarpackinfo_path = arizonaconfig.get_option("tarpackinfopath")

      if tarpackinfo_path == None:
         arizonareport.send_error(0, "tar package manager: missing --tarpackinfo setting")
         return True
         
      # create tar package info path if it doesn't exist   
      if not os.path.exists(tarpackinfo_path): 
         try:
            os.makedirs(tarpackinfo_path)
         except OSError:
            raise arizonageneral.Exception_Data("tar package manager: Can't create tar package info path `" + tarpackinfo_path + "'", ([], []))         

   return False





def initialize():
   """
   <Purpose>
      Initializes the package manager.  

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      Returns a list of dependencies that the package manager itself 
      satisfies (empty list for tar), or None on error. 
   """
   if __init_packinfo():
     return None
      
   return []





def is_package_understood(filename):
   """
   <Purpose>
      Given a filename, checks whether it is a valid Tar package.

   <Arguments>
      filename:
              Tar filename to check.

   <Exceptions>
      TypeError:
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      True if the package is valid and understood, False otherwise.
   """
   # check the arguments
   arizonageneral.check_type_simple(filename, "filename", str, "storktar.is_package_understood")

   # run command to check if the file is valid (returns None, if not)
   # It apparently now returns false instead of none
   flag = __determine_package_type(filename)
   
   return flag != False





def __understood_packages(filename_list):
   """
   <Purpose>
      Given a string list of package filenames, returns a string list of 
      package filenames that are understood by tar.

   <Arguments>
      filename_list:
              String list of package filenames.

   <Exceptions>
      TypeError:
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      String list of tar package filenames.
   """
   understood = []
   for filename in filename_list:
      if is_package_understood(filename):
         understood.append(filename)
   return understood      





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
   """
   # check params
   arizonageneral.check_type_stringlist(filename_list, "filename_list", "storktar.get_packages_provide")

   if len(filename_list) < 1:
      return []
   
   # filter out packages we don't understand   
   filename_list = __understood_packages(filename_list)
   
   # build a list of provided dependencies 
   deplist = []
   for filename in filename_list:
      info = get_package_info(filename)
      if info == None:
         continue
      deplist.append(info[0] + " = " + info[1] + "-" + info[2])
   
   return deplist





def get_packages_require(filename_list):
   """
   <Purpose>
      Given a string list of package filenames, returns a string list of 
      dependencies that those packages require.  For now, tar doesn't
      implement nested dependencies, so always returns [].

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
   arizonageneral.check_type_stringlist(filename_list, "filename_list", "storktar.get_packages_require")

   return []
   
   



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
   arizonageneral.check_type_stringlist(filename_list, "filename_list", "storktar.get_packages_files")

   if len(filename_list) < 1:
      return []

   # filter out packages we don't understand
   filename_list = __understood_packages(filename_list)

   package_files = []
   for filename in filename_list:
      tarinfo = __get_tar_info(filename)
      if not tarinfo:
         # TODO: is this the right thing to do on an error? I decided to mimic
         # what the existing code did when len(err) > 0
         return []

      (out, err, status) = (tarinfo[4], tarinfo[5], tarinfo[6])

      # old code below to use tar rather than using cached result
      # flag = __determine_package_type(filename)
      # (out, err, status) = arizonageneral.popen5("tar -P" + flag + "tvf " + re.escape(filename))

      if status != 0:
         return []
         
      if len(out) < 1:
         continue

      for line in out:
         # the format of a line of tar output is:
         # <permissions> <username> <size> <date> <time> <filename>
         line = line.strip("\n").split()
         if len(line) < 6:
            continue

         thisname = line[5]

         # filter out special files
         skip = False
         for name in SPECIAL_FILES:
            if thisname == name:
               skip = True
         if skip:
            continue

         package_files.append(thisname)

   return package_files


      

      
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
   arizonageneral.check_type_simple(filename, "filename", str, "storktar.get_package_info")

   if not is_package_understood(filename):
      return None

   tarinfo = __get_tar_info(filename)
   if not tarinfo:
      return None

   (out, err, status) = (tarinfo[4], tarinfo[5], tarinfo[6])

   # old code below to use tar rather than using cached result
   # flag = __determine_package_type(filename)
   # (out, err, status) = arizonageneral.popen5("tar -t" + flag + "vf " + re.escape(filename))

   if status != 0:
      return None

   # name
   name = os.path.basename(filename)

   # remove .tar extensions
   for ext in RECOGNIZED_EXTENSIONS:
      if name.endswith(ext):
         name = name[0:-len(ext)]
         break

   # version, release
   fields = name.split("-")
   if len(fields) == 2:
      name = fields[0]
      version = fields[1]
      release = DEFAULT_RELEASE
   elif len(fields) == 3:
      name = fields[0]
      version = fields[1]
      release = fields[2]
   else:
      version = DEFAULT_VERSION
      release = DEFAULT_RELEASE

   # size
   size = 0
   for line in out:
      # the format of a line of tar output is:
      # <permissions> <username> <size> <date> <time> <filename>
      tmp = line.strip("\n").split()
      if len(tmp) < 6:
         continue
      size += int(tmp[2])
   size = str(size)

   return [name, version, release, size]




def get_installed_versions(package_list):
   """
   <Purpose>
      Given a package list, returns a list containing the name 
      if installed,

   <Arguments>
      package_list:
         List of strings containing the names of the packages to get 
         version information for.

   <Exceptions>
      TypeError:
         If a type mismatch or parameter error is detected.
         Or if package info directory isn't specified.

   <Side Effects>
      None.

   <Returns>
      String list containing each package name and version (in the format
      "name = version-release"). Packages that are not installed are not
      listed. If a package has more than one installed version, then multiple
      results may be returned for that package. 
   """
   # check the arguments 
   arizonageneral.check_type_stringlist(package_list, "package_list", "storktar.get_installed_versions")

   # nothing given   
   if len(package_list) == 0:
      return []

   # get a tar package info path
   tarpackinfo_path = arizonaconfig.get_option("tarpackinfopath")
   
   # a list which holds the info about each package   
   installed_packages = []

   for package in package_list:
      info = __get_installed_package_info(package)
      if info != None:
         # installed, format info
         installed_packages.append(info[0] + " = " + info[1] + "-" + info[2])

   return installed_packages





def get_installedpackages_fulfilling(dep_list):
   """
   <Purpose>
      Given a string list of dependencies, returns a string list of 
      installed packages that fulfill those package dependencies.

   <Arguments>
      dep_list:
         String list of package dependencies.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      String list of installed packages that meet the given dependencies.
   """
   # check params
   arizonageneral.check_type_stringlist(dep_list, "dep_list", "storktar.get_installedpackages_fulfilling")

   if len(dep_list) < 1:
      return []

   # TODO need to find file dependencies
   retlist = []
   for package in dep_list:
      info = __get_installed_package_info(package)
      if info == None:
         continue
      retlist.append(info[0] + "-" + info[1] + "-" + info[2])
      
   return retlist


def get_installedpackages_requiring(deplist):
   """
   <Purpose>
      Return a list of all installed packages.

   <Arguments>

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      String list of installed packages
   """

   # TODO finish me

   return []


   
def get_installedpackages():
   """
   <Purpose>
      Return a list of all installed packages.

   <Arguments>

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      String list of installed packages
   """

   # TODO finish me

   return []



def get_installedpackages_provide(package_list):
   """
   <Purpose>
      Given a string list of installed package names, returns a string 
      list of all dependencies fulfilled by those packages. 

   <Arguments>
      package_list:
         String list of installed package names.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      String list of all dependencies fulfilled by the given packages.
      Dependencies will either be in the form:
        name=version-release (possible spaces around `=')
      Or:
        name  
   """
   # check params
   arizonageneral.check_type_stringlist(package_list, "package_list", "storktar.get_installedpackages_provide")

   if len(package_list) < 1:
      return []

   retlist = []
   for package in package_list:
      info = __get_installed_package_info(package)
      if info == None:
         continue
      retlist.append(info[0] + " = " + info[1] + "-" + info[2])
      
   return retlist





def get_installedpackages_requires(package_list):
   """
   <Purpose>
      Return a list of all dependencies required

   <Arguments>

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      String list of installed packages
   """

   # TODO finish me

   return []





def execute(trans_list):
   """
   <Purpose>
      Installs packages with the given filenames.

   <Arguments>
      filename_list:
              String list of filenames representing packages to install.

   <Exceptions>
      arizonageneral.Exception_Data:
         If a package failed to install properly
      TypeError:
         If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      None.
   """
   # check the arguments
   arizonageneral.check_type_simple(trans_list, "trans_list", list, "storktar.install")

   if len(trans_list) < 1:
      return

   # get a list of packages that we need to remove due to upgrades
   conflict_list = \
      storktransaction.tl_get_conflict_list(trans_list, storktransaction.UPGRADE)

   # remove them
   if conflict_list:
      remove(conflict_list)

   # get a list of the RPMs that we're going to install or upgrade
   filename_list = \
      storktransaction.tl_get_filename_list(trans_list, storktransaction.INSTALL) + \
      storktransaction.tl_get_filename_list(trans_list, storktransaction.UPGRADE)

   if len(filename_list) < 1:
      return

   __init_packinfo()

   # list of which files have been installed so far
   installed_files = []

   # for each file to install
   for filename in filename_list:
      # get package information from the file
      packinfo = get_package_info(filename)
      if packinfo == None:
         # raise error
         not_installed_files = filename_list[len(installed_files):]
         raise arizonageneral.Exception_Data("tar package manager: Package " + filename + " contains errors and could not be installed", (installed_files, not_installed_files))

      # determine whether this package has already been installed
      info = __get_installed_package_info(packinfo[0])
      if info != None:
         # raise error
         not_installed_files = filename_list[len(installed_files):]
         raise arizonageneral.Exception_Data("tar package manager: Package " + filename + " is already installed", (installed_files, not_installed_files))

      homedir = __get_tar_install_dir(packinfo)

      # if files included in this package existed before installing this
      # package, remove them from the files list so they aren't removed on
      # uninstallation
      new_files = []
      for name in get_packages_files([filename]):
         if not os.path.exists(name):
            new_files.append(name)

      # replace size field with files list (convert list to tab separated)
      packinfo[3] = "\t".join(new_files)

      # install this package:
      #   1) .preinstall script (if any) is extracted and run
      #   2) The package is placed at the user's home directory and
      #      installed.  If absolute paths are set for the files, then
      #      those files will be installed anywhere in the file system
      #      (not just inside the home directory).
      #   3) packinfo file is created
      #   4) .postinstall script (if any) is extracted and run
      #   5) extract and move .preremove/.postremove scripts
      flag = __determine_package_type(filename)



      # 1) extract .preinstall file and execute it
      temp_dir = "/tmp/" + str(securerandom.SecureRandom().random())
      os.makedirs(temp_dir)
      (out, err, status) = arizonageneral.popen5("tar -C " + temp_dir + " -" + flag + "xf " + re.escape(filename) + " .preinstall")
      if status == 0:
         # script extracted okay, execute it
         os.system("chmod 777 " + temp_dir +"/.preinstall")
         status = os.system("cd " + homedir + "; " + temp_dir + "/.preinstall 1>/dev/null")
         if status != 0:
            arizonageneral.rmdir_recursive(temp_dir)
            # preinstall script failed, raise error         
            not_installed_files = filename_list[len(installed_files):]
            raise arizonageneral.Exception_Data("tar package manager: Preinstall script reported error", (installed_files, not_installed_files))



             
      # 2) install the package      
      (out, err, status) = arizonageneral.popen5("tar -C " + homedir + "/ --exclude='" + " ".join(SPECIAL_FILES) + "' -P" + flag + "xvf " + re.escape(filename) + " ")
      if status != 0:
         arizonageneral.rmdir_recursive(temp_dir)
         # failed to install the package, raise error         
         not_installed_files = filename_list[len(installed_files):]
         raise arizonageneral.Exception_Data(err, (installed_files, not_installed_files))

      # 3) create packinfo file
      try:
         infofile = open(tarpackinfo_path + "/" + packinfo[0] + ".packinfo", 'w')
         infofile.write("\n".join(packinfo) + "\n")
         infofile.close()
      except IOError:
         arizonageneral.rmdir_recursive(temp_dir)
         # raise error
         not_installed_files = filename_list[len(installed_files):]
         raise arizonageneral.Exception_Data("tar package manager: Could not create `" + tarpackinfo_path + "/" + packinfo[0] + ".packinfo' file for " + filename + ", package not completely installed", (installed_files, not_installed_files))




      # 4) extract .postinstall file and execute it
      #Duy Nguyen - temp directory has already been made
      #os.makedirs(temp_dir)
      (out, err, status) = arizonageneral.popen5("tar -C " + temp_dir + " -" + flag + "xf " + re.escape(filename) + " .postinstall")
      if status == 0:
         # script extracted okay, execute it

       # Duy Nguyen -tempdir does not exist, changed to temp_dir
         os.system("chmod 777 " + temp_dir + "/.postinstall")
         status = os.system("cd " + homedir + "; " + temp_dir + "/.postinstall 1>/dev/null")
         if status != 0:
            if os.path.exists( os.path.join(tarpackinfo_path, packinfo[0] + ".packinfo")):
               os.remove(os.path.join(tarpackinfo_path, packinfo[0] + ".packinfo"))

            arizonageneral.rmdir_recursive(temp_dir)
            # postinstall script failed, raise error
            not_installed_files = filename_list[len(installed_files):]
            raise arizonageneral.Exception_Data("tar package manager: Postinstall script reported error", (installed_files, not_installed_files))




      # 5) extract and move uninstall files
      #Duy Nguyen - Directory already created
      #os.makedirs(temp_dir)
      (out, err, status) = arizonageneral.popen5("tar -C " + temp_dir + " -" + flag + "xf " + re.escape(filename) + " .preremove")
      if status == 0:
         try:
            os.system("chmod 777 " + temp_dir + "/.preremove")
            os.system("cp " + temp_dir + "/.preremove " + tarpackinfo_path + "/" + packinfo[0] + ".preremove") 
         except OSError:
            pass   
      
      (out, err, status) = arizonageneral.popen5("tar -C " + temp_dir + " -" + flag + "xf " + re.escape(filename) + " .postremove")
      if status == 0: 
         try:
            os.system("chmod 777 " + temp_dir + "/.postremove")
            os.system("cp " +temp_dir + "/.postremove " + tarpackinfo_path + "/" + packinfo[0] + ".postremove")
         except OSError:
            pass   
      arizonageneral.rmdir_recursive(temp_dir)

      # install succeeded, add the package to the installed_files list
      installed_files.append(filename)






def remove(package_list, nodeps=False):
   """
   <Purpose>
      Removes packages with the given package names.

   <Arguments>
      package_list:
         String list of packages to remove.
      nodeps:
         If True, then force removal of packages even if existing packages
         depend upon them. This likely makes no difference for tar packages.

   <Exceptions>
      TypeError:
         If a type mismatch or parameter error is detected.
      arizonageneral.Exception_Data:
         If a package failed to remove properly

   <Side Effects>
      None.

   <Returns>
      None.
   """
   # check the arguments
   arizonageneral.check_type_stringlist(package_list, "package_list", "storktar.remove")

   if len(package_list) < 1:
      return
   
   __init_packinfo()

   # list of which files have been removed so far
   removed_packages = []
   
   for package in package_list:
      packinfo = __get_installed_package_info(package)

      # is package installed?
      if packinfo == None:
         not_removed_packages = package_list[len(removed_packages):]         
         raise arizonageneral.Exception_Data("tar package manager: Package '" + package + "' is not installed", (removed_packages, not_removed_packages))

      homedir = __get_tar_install_dir(packinfo)

      # execute preremove script
      #Duy Nguyen - Check if script exists first

      script = tarpackinfo_path + "/" + package + ".preremove"
      status = 0
      if os.path.exists(script):
         os.system("chmod 777 " + script)
         status = os.system("cd " + homedir + "; " + script + " 1>/dev/null")
 
      if status != 0:
         # preremove script failed, raise error     
         not_removed_packages = package_list[len(removed_packages):]
         raise arizonageneral.Exception_Data(
         "tar package manager: Preremove script reported error", (removed_packages, not_removed_packages))

      if os.path.exists(script):
         os.remove(script)
   
      # remove files, make a list of directories
      directory_list = []
      for entry in packinfo[3]:
         if entry[-1] == '/':
            # directory, add to list
            directory_list.append(entry)
         else:
            # file
            try:
               os.system("rm " + homedir + "/" + entry)
            except OSError:
               not_removed_packages = package_list[len(removed_packages):]         
               raise arizonageneral.Exception_Data("tar package manager: Package `" + package + "' could not be removed, error removing " + entry, (removed_packages, not_removed_packages))
                     
      # files have been removed, now remove directories
      for entry in directory_list:
         try:
            os.rmdir(homedir + "/" +entry)
         except OSError:
            # although we would like to remove all traces, it is not fatal
            # if some directories are left behind
            arizonareport.send_error(1, "tar package manager: Package `" + package + "' not completely removed, directory not empty: " + entry)
      
      # remove .packinfo file
      try:
         os.remove(tarpackinfo_path + "/" + package + ".packinfo")
      except OSError:
         not_removed_packages = package_list[len(removed_packages):]
         raise arizonageneral.Exception_Data("tar package manager: Package info file `" + packinfo_file + "' could not be removed", (removed_packages, not_removed_packages))
     

      # execute postremove script
      #script = tarpackinfo_path + "/" + package + ".postremove"
      status = 0
      #if os.path.exists(script):
         #os.system("chmod 777 " + script)
         #status = os.system("cd " + homedir + "; " + script + " 1>/dev/null")
      if status != 0:
         # postremove script failed, raise error
         not_removed_packages = package_list[len(removed_packages):]
         raise arizonageneral.Exception_Data("tar package manager: Postremove script reported error", (removed_packages, not_removed_packages))
      #if os.path.exists(script): 
         #os.remove(script)

      # package removed, add to removed_packages list   
      removed_packages.append(package)
      


glo_package_cache = {}

def __get_tar_info(filename):
   """
   <Purpose>
      Determines the type of a tar package (z=gz, j=bzip2, ...) and reads the
      file table from the tarball. Results are cached so that multiple calls
      to this func do not need to process the tarball multiple times.

   <Arguments>
      filename:
         name of file to get info
         depend upon them. This likely makes no difference for tar packages.
         
   <Side Effects>
      None.

   <Returns>
      None if the file is not valid
      otherwise, a tuple, (dev, ino, mtime, typeflag, stdout, stderr, status)
         dev, ino, and mtime are used internally
         typeflag = "j" or "z"
         status = status from tar operation (probably 0)
         stdout, stderr = output streams containing tar file table
   """
   global glo_package_cache

   try:
      stat = os.stat(filename)
   except IOError:
      return None
   except OSError:
      return None

   # a simple caching scheme: if we've already determined the package type
   # of this file before, then return previous results.
   cached_result = glo_package_cache.get(filename, None)
   if cached_result:
      if (cached_result[0] == stat[ST_DEV]) and \
         (cached_result[1] == stat[ST_INO]) and \
         (cached_result[2] == stat[ST_MTIME]):
         return cached_result

   """ Returns the appropriate compression flag for invoking tar """
   arizonareport.send_out(4, "__get_tar_info " + str(filename))
   for flag in INSTALL_FLAGS:
      command="tar -" + flag + " -tvf " + re.escape(filename)

      (out, err, status) = arizonageneral.popen5(command)
      if status == 0 and len(out) > 0:
         result = (stat[ST_DEV], stat[ST_INO], stat[ST_MTIME], \
                   flag, out, err, status)
         glo_package_cache[filename] = result
         arizonareport.send_out(4, "  returning type " + str(flag))
         return result

   arizonareport.send_out(4, "  returning error")
   return None

def __determine_package_type(filename):
   info = __get_tar_info(filename)
   if not info:
      return False

   # return the typeflag
   return info[3]

"""
	The purpose of this method is to do exactly as the above method
	but without using re.esacpe on the filename. I have no clue why
	you would need to escape the string. As far as I can tell escaping
	the string makes this functino not work at all because you are basically
	callint tar -j \/path\/to\/file
	which doesnt make any sense, nor does it work.

	TODO: see if we can get rid of the re.escape or determine
	      why it is needed

"""
def determine_package_type_no_re(filename):
   """ Returns the appropriate compression flag for invoking tar """
   for flag in INSTALL_FLAGS:
      command="tar -" + flag + " -tf " + filename
      #print command
      (out, err, status) = arizonageneral.popen5(command)
      if status == 0 and len(out) > 0:
         return flag
   return None




def __get_installed_package_info(package):
   """ Returns data in the format [name, release, version, [file, ...]] """
   __init_packinfo()
   filename = tarpackinfo_path + "/" + package + ".packinfo"

   # see if package info exists (i.e. is package installed?)
   if not os.path.isfile(filename):
      filename = tarpackinfo_path + "/" + package + ".tgz.packinfo"
      if not os.path.isfile(filename):
         filename = tarpackinfo_path + "/" + package + ".tar.gz.packinfo"
         if not os.path.isfile(filename):
            return None

   # read data from packinfo file
   packinfo = []
   try:
      f = file(filename,"r")
      for line in f:
         packinfo.append(line.strip("\n"))
      f.close()
   except IOError:
      return None

   # check basic data integrity
   if len(packinfo) != 4:
      return None

   # convert tab separated files to a list
   packinfo[3] = packinfo[3].split("\t")

   return packinfo




def __get_tar_install_dir(packinfo):
   """
   <Purpose>
      Determines the directory where a package will be installed

   <Arguments>
      packinfo:
         The tar_packageinfo for the package. Eventually we will use this arg
         to allow the user to override the destination.

   <Returns>
      Directory name.
   """

   try:
      # use the home directory specified in the root user's password entry
      pwent = pwd.getpwuid(0)
      homedir = pwent.pw_dir
   except:
      # if the above fails for any reason, then we'll fall back to using HOME
      homedir = None

   # try getting the homedir from the 'HOME' environment variable
   if (not homedir) or (not os.path.exists(homedir)):
      homedir = os.environ.get("HOME", None)

   if not homedir:
      raise TypeError, "Unable to find a suitable tar directory"

   return homedir






#def get_package_names(filename_list):
#   """
#   <Purpose>
#      Given a list of package filenames (including paths if necessary), 
#      returns a list containing the name and version of each package, or
#      "." for invalid / missing packages.
#
#   <Arguments>
#      filename_list:
#         List of strings containing the filenames of the packages to get 
#         names and versions of.
#
#   <Exceptions>
#      None.
#
#   <Side Effects>
#      None.
#
#   <Returns>
#      Empty list.
#   """
#   
#   # TODO FIXME implement this... need to keep a list of installed packages
#   return []
