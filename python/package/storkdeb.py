#! /usr/bin/env python

"""
<Program Name>
   storkdeb.py

<Started>
   June 19, 2006

<Author>
   Programmed by Jeffry Johnston.

<Purpose>
   Implements Debian package manager functionality.
"""

import os
import arizonageneral
import arizonareport




def initialize():
   """
   <Purpose>
      Initializes the package manager.  
      This must be called before can_satisfy.

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      Returns a list of dependencies that the package manager itself 
      satisfies.
   """
   return []





def is_package_understood(filename):
   """
   <Purpose>
      Given a filename, checks whether it is a valid Debian package.

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
   arizonageneral.check_type_simple(filename, "filename", str, "storkdeb.is_package_understood")
   
   (out, err, status) = arizonageneral.popen5("dpkg-deb -I" + arizonageneral.list_to_args([filename]))
   return status == 0





def __understood_packages(filename_list):
   """
   <Purpose>
      Given a string list of package filenames, returns a string list of 
      package filenames that are understood by Debian package manager.

   <Arguments>
      filename_list:
              String list of package filenames.

   <Exceptions>
      TypeError:
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      String list of Debian package filenames.
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
   arizonageneral.check_type_stringlist(filename_list, "filename_list", "storkdeb.get_packages_provide")

   # only work on packages we understand
   filename_list = __understood_packages(filename_list)   

   if len(filename_list) < 1:
      return []

   retlist = []
   for filename in filename_list:
      (out, err, status) = arizonageneral.popen5("dpkg-deb -I" + arizonageneral.list_to_args([filename]))
      templist = []
      package = None
      version = None
      for line in out:
         if line.startswith(" Package: ") and package == None:
            package = line[10:].strip()
         elif line.startswith(" Version: ") and version == None:
            version = line[10:].strip()
         elif line.startswith(" Provides: "):
            templist = line[11:].split(", ")
   
      # we need to manually provide ourselves      
      if package != None and version != None:
         templist.append(package + " = " + version)      
   
      # strip entries
      for item in templist:
         retlist.append(item.strip())
      
   return retlist





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
   arizonageneral.check_type_stringlist(filename_list, "filename_list", "storkdeb.get_packages_require")

   # only work on packages we understand
   filename_list = __understood_packages(filename_list)   

   if len(filename_list) < 1:
      return []

   retlist = []
   for filename in filename_list:
      (out, err, status) = arizonageneral.popen5("dpkg-deb -I" + arizonageneral.list_to_args([filename]))
      templist = []
      for line in out:
         if line.startswith(" Depends: "):
            templist += line[10:].split(", ")
         if line.startswith(" Pre-Depends: "):
            templist += line[14:].split(", ")
   
      # reformat entries
      for entry in templist:
         # TODO FIXME | isn't handled properly (alternatives are ignored)
         entry = entry.strip().split(" | ")[0]
         if entry[-1] == ")":
            i = entry.rfind("(")
            if i != -1:
               entry = entry[:i] + entry[i + 1:-1].strip()
               entry = entry.replace(">>", ">")
               entry = entry.replace("<<", "<")
         retlist.append(entry)      
      
   return retlist





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
   arizonageneral.check_type_stringlist(filename_list, "filename_list", "storkdeb.get_packages_files")

   # only work on packages we understand
   filename_list = __understood_packages(filename_list)   

   if len(filename_list) < 1:
      return []

   retlist = []
   for item in filename_list:
      (out, err, status) = arizonageneral.popen5("dpkg-deb -c" + arizonageneral.list_to_args([item]))
      for line in out:
         filename = line.split()[5].strip()
         if filename.startswith("./"):
            filename = filename[1:]
         retlist.append(filename)   
      
   return retlist





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
   arizonageneral.check_type_simple(filename, "filename", str, "storkdeb.get_package_info")

   if not is_package_understood(filename):
      return None

   (out, err, status) = arizonageneral.popen5("dpkg-deb -I" + arizonageneral.list_to_args([filename]))
   name = ""
   version = ""
   release = ""
   size = ""
   for line in out:
      if line.startswith(" Package: ") and name == "":
         name = line[10:].strip()
      elif line.startswith(" Version: ") and version == "":
         version = line[10:].strip()
         i = version.rfind("-")
         if i != -1:
            release = version[i + 1:].strip()
            version = version[:i].strip()
      elif line.startswith(" Installed-Size: "):
         try:
            # need to multiply by 1024 because size is given in kilobytes
            size = str(int(line[17:].strip()) * 1024)
         except ValueError:
            size = ""     
   
   return [name, version, release, size]





def get_installed_versions(package_list):
   """
   <Purpose>
      Given a package list, returns a list containing the name and version
      of each package if installed, or None for a package that is not 
      installed.

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
      "name = version-release"), otherwise None for each package not 
      installed.
   """
   # check params
   arizonageneral.check_type_stringlist(package_list, "package_list", "storkdeb.get_installed_versions")

   if len(package_list) < 1:
      return []

   # find out which packages have info about them
   (out, status) = arizonageneral.popen6("dpkg-query -W" + arizonageneral.list_to_args(package_list))
   
   # for each package there will be one line of output, either with the 
   # info we want, or starting with "No packages found matching ".
   version_list = []
   temp_list = [] 
   for line in out:
      line = line.strip()
      if line.startswith("No packages "):
         version_list.append(None)
      else:
         line = line.split()
         temp_list.append(line[0])   
         if len(line) > 1:
            line = " = ".join(line)
         version_list.append(line)   

   # the above list will show packages that have been uninstalled but have
   # residual config files, etc.  So we need to filter the list again.
   if len(temp_list) > 0:
      (out, err, status) = arizonageneral.popen5("dpkg-query -l" + arizonageneral.list_to_args(temp_list))
      i = None
      for line in out:
         if i != None:
            # is the package installed?  if not, remember its name
            if len(line) >= 2 and line[1] == "i":
               temp_list[i] = None
            else:
               line = line.split()
               if len(line) >= 2:
                  temp_list[i] = line[1]
               else:  
                  # in case something weird goes on, fall back
                  temp_list[i] = None
            i += 1
            if i >= len(temp_list):
               break
         elif line.startswith("+++"):
            # found the last line of explanation text
            i = 0  

      # now remove items that are left in the temp list
      for item in temp_list:
         if item != None:
            for i in range(len(version_list)):
               if version_list[i] != None and \
                  (version_list[i].startswith(item + " = ") or \
                  version_list[i].endswith(item)):
                  version_list[i] = None
      
   return version_list





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
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      String list of installed packages that meet the given dependencies.
   """
   # check params
   arizonageneral.check_type_stringlist(dep_list, "dep_list", "storkdeb.get_installedpackages_fulfilling")

   if len(dep_list) < 1:
      return []

   for dep in dep_list:
      dep = dep.strip()
      (out, err, status) = arizonageneral.popen5("grep -b \"Package: " + \
                           arizonageneral.grep_escape(dep) + \
                           "\" /var/lib/dpkg/status")
      if status != 0 and len(err) > 0:
         # error searching the file, abort      
         break
   
      
      for line in out:
         line = line.split(":")
         line[2] = line[2].strip()
         if line[2] == dep:
            f = open("/var/lib/dpkg/status", "rb")
            f.seek(int(line[0]))
            data = f.read(4096).split("\n")[1:]
            for line2 in data:
               if line2.startswith("Package:"):
                  # didn't find status
           
   
   # TODO    NOT WRITTEN!   

   # 1) grep for installed packages, then check the version
   # grep -b /var/lib/dpkg/status Package: DEP
   # make sure we didn't pick up the front of a longer name (libc6 vs libc6-dev)
   # now open the status file and read until we figure out the Version 
   # also need to check whether the package is installed
   # dpkg --compare-versions VER1 OP VER2

   # 2) search provides fields
   # grep -b Provides:.*DEP
   # take the line and parse it... see if it actually contained what we wanted
   # now open the status file and figure out what the package was called,
   # this will involve reading backwards for a line starting with Package:
   # also need to check whether the package is installed
   
   return retlist





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
              If a type mismatch or parameter error is detected.

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
   arizonageneral.check_type_stringlist(package_list, "package_list", "storkdeb.get_installedpackages_provide")

   if len(package_list) < 1:
      return []

   retlist = []
   for item in package_list:
      (out, err, status) = arizonageneral.popen5("dpkg-query -s" + arizonageneral.list_to_args([item]))
      templist = []
      package = None
      version = None
      for line in out:
         if line.startswith("Package: ") and package == None:
            package = line[9:].strip()
         elif line.startswith("Version: ") and version == None:
            version = line[9:].strip()
         elif line.startswith("Provides: "):
            templist = line[10:].split(", ")
   
      # we need to manually provide ourselves      
      if package != None and version != None:
         templist.append(package + "=" + version)      
   
      # strip entries
      for item in templist:
         retlist.append(item.strip())
      
   return retlist





def install(filename_list):
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
   # check params
   arizonageneral.check_type_stringlist(filename_list, "filename_list", "storkdeb.install")

   #print
   #print "***************************************************************"
   #print "filename_list:", filename_list 
   #print "***************************************************************"
   #print

   if len(filename_list) < 1:
      return

   # install packages
   filenames = arizonageneral.list_to_args(filename_list)
   (out, err, status) = arizonageneral.popen5("dpkg -i" + filenames)
   
   #print
   #print "***************************************************************"
   #print "status:", status 
   #print "err:", err 
   #print "out:", out 
   #print "***************************************************************"
   #print
   
   """ TODO     NOT WRITTEN!
   # if there were errors: determine which packages were not installed
   if status != 0:

      # get package names
      package_list = []
      cmd_in = os.popen("rpm -qp" + filenames)
      output = cmd_in.readline().strip()
      while output:
         if output.startswith("error:"):
            output = "."
         package_list.append(output)
         output = cmd_in.readline().strip()
      cmd_in.close()
      
      # generate lists of installed and failed packages 
      # TODO comment this better
      installed_list = []
      not_installed_list = []
      for i, pack in enumerate(get_installed_versions(filename_list)):
         if pack == None:
            not_installed_list.append(filename_list[i])
         else:
            installed_list.append(filename_list[i])

      # raise an exception unless everything installed
      if len(not_installed_list) > 0: 
         raise arizonageneral.Exception_Data(err, (installed_list, not_installed_list))
   """




def remove(package_list):
   """
   <Purpose>
      Removes packages with the given package names.

   <Arguments>
      package_list:
              String list of packages to remove.

   <Exceptions>
      arizonageneral.Exception_Data:
              Error removing a package.
      TypeError:
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      None.
   """
   # check params
   arizonageneral.check_type_stringlist(package_list, "package_list", "storkdeb.remove")
   
   if len(package_list) < 1:
      return

   # remove packages
   (junk_in, cmd_out, junk_err) = os.popen3("dpkg -r" + arizonageneral.list_to_args(package_list))
   junk_in.close()
   
   """ TODO     NOT WRITTEN!
   # check for errors
   error = []
   message = ""
   output = cmd_out.readline()
   while output:
      message += output + "\n"
      if output.strip().startswith("error:"):
         error.append(output)
      output = cmd_out.readline()
   cmd_out.close()
   junk_err.close()

   # if there were errors: determine which packages were not removed
   if len(error) > 0:
      # generate lists of removed and failed packages
      removed_list = []
      not_removed_list = []
      for i, pack in enumerate(get_installed_versions(package_list)):
         if pack == None:
            removed_list.append(package_list[i])
         else:
            not_removed_list.append(package_list[i])

      # raise an exception unless everything was removed
      if len(not_removed_list) > 0: 
         raise arizonageneral.Exception_Data(", ".join(error), (removed_list, not_removed_list))
   """
