#! /usr/bin/env python

"""
<Program Name>
   storkrpm.py

<Started>
   April 27, 2004

<Author>
   Programmed by Justin Cappos.  Refactored by Jeffry Johnston.

<Purpose>
   Implements RPM functionality.
"""

import os
import arizonageneral
import arizonareport
import sys
import storktransaction




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
   # build list of dependencies internally satisfied by rpm
   (junk_in, the_out, the_err) = os.popen3("rpm --showrc")
   junk_in.close()
   output = the_out.readline()
   rpm_sats = []
   while output:
      output = output.strip()
      if output.startswith('rpmlib('):
         rpm_sats.append(output)
      output = the_out.readline()

   return rpm_sats





def is_package_understood(filename):
   """
   <Purpose>
      Given a filename, checks whether it is a valid RPM package.

   <Arguments>
      filename:
              Filename of the rpm to check.

   <Exceptions>
      TypeError:
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      True if the package is valid and understood, False otherwise.
   """
   # check params
   arizonageneral.check_type_simple(filename, "filename", str, "storkrpm.is_package_understood")
   
   # does the file exist?
   if not os.path.isfile(filename):
      return False
   
   # if we can get package information, then the rpm was understood
   return get_package_info(filename) != None





def __understood_packages(filename_list):
   """
   <Purpose>
      Given a string list of package filenames, returns a string list of 
      package filenames that are understood by RPM.

   <Arguments>
      filename_list:
              String list of package filenames.

   <Exceptions>
      TypeError:
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      String list of RPM package filenames.
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
   arizonageneral.check_type_stringlist(filename_list, "filename_list", "storkrpm.get_packages_provide")

   filename_list = __understood_packages(filename_list)   

   if len(filename_list) < 1:
      return []

   (junk_in, the_out, the_err) = os.popen3("rpm -qp --provides" + arizonageneral.list_to_args(filename_list))
   junk_in.close()
   output = the_out.readline()
   retlist = []
   while output:
      if not (output.startswith('error:') or output.endswith('Is a directory')):
         retlist.append(output.strip())
      output = the_out.readline()
      
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
   arizonageneral.check_type_stringlist(filename_list, "filename_list", "storkrpm.get_packages_require")

   filename_list = __understood_packages(filename_list)   

   if len(filename_list) < 1:
      return []

   (junk_in, the_out, the_err) = os.popen3("rpm -qp --requires" + arizonageneral.list_to_args(filename_list))
   junk_in.close()
   output = the_out.readline()
   retlist = []
   while output:
      if not (output.startswith('error:') or output.endswith('Is a directory')):
         retlist.append(output.strip())
      output = the_out.readline()
      
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
   arizonageneral.check_type_stringlist(filename_list, "filename_list", "storkrpm.get_packages_files")

   if len(filename_list) < 1:
      return []

   filename_list = __understood_packages(filename_list)   

   (junk_in, the_out, the_err) = os.popen3("rpm -qpl" + arizonageneral.list_to_args(filename_list))
   junk_in.close()
   output = the_out.readline()
   retlist = []
   while output:
      if not (output.startswith('error:') or output.endswith('Is a directory')):
         retlist.append(output.strip())
      output = the_out.readline()
   
   # rpm prints a special message when an rpm has no files, correct this  
   if retlist == ['(contains no files)']:
      retlist = []
   
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
   arizonageneral.check_type_simple(filename, "filename", str, "storkrpm.get_package_info")

   (out, err, status) = arizonageneral.popen5("rpm -qp --qf \"%{NAME}|%{EPOCH}:%{VERSION}|%{RELEASE}|%{SIZE}\"" + arizonageneral.list_to_args([filename]))
   if len(out) < 1:
      return None
      
   if status != 0:
      return None
      
   output = out[0].split("|")
   if len(output) != 4:
      return None

   # if there was no epoch, then get rid of the (none): prefix      
   if output[1].startswith("(none)"):
      output[1] = output[1][7:]

   return output





def get_installed_versions(package_list):
   """
   <Purpose>
      Given a package list, returns a list containing the name and version
      of each package if installed, 
   
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
   arizonageneral.check_type_stringlist(package_list, "package_list", "storkrpm.get_installed_versions")

   if len(package_list) < 1:
      return []

   version_list = []   
   cmd_in = os.popen("rpm -q --qf \"%{name} = %{epoch}:%{version}-%{release}\n\"" + arizonageneral.list_to_args(package_list))
   output = cmd_in.readline().strip()

   # for each package there will be one line of output, either with the 
   # formatted info we want, or ending with "not installed".
   while output:
      if not output.endswith("not installed"):
         # if there isn't an epoch, remove the "(none):" text
         output = output.replace(" = (none):", " = ")
         version_list.append(output)
      output = cmd_in.readline().strip()
   cmd_in.close()
   
   return version_list

   

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
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      String list of installed packages that require the given dependencies.
   """
   # check params
   arizonageneral.check_type_stringlist(dep_list, "dep_list", "storkrpm.get_installedpackages_fulfilling")

   if not dep_list:
      return []

   out = os.popen("rpm -q --whatrequires" + arizonageneral.list_to_args(dep_list) + " 2>/dev/null")
   retlist = []
   for line in out:
      # no package provides...
      if not line.startswith('no package '):
         retlist.append(line.rstrip())
   out.close()
      
   return retlist



   
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
   arizonageneral.check_type_stringlist(dep_list, "dep_list", "storkrpm.get_installedpackages_fulfilling")

   if not dep_list:
      return []

   out = os.popen("rpm -q --whatprovides" + arizonageneral.list_to_args(dep_list) + " 2>/dev/null")
   retlist = []
   for line in out:
      # no package provides...
      if not line.startswith('no package '):
         retlist.append(line.rstrip())
   out.close()
      
   return retlist

   

   
def get_installedpackages():
   """
   <Purpose>
      Return a list of all packages installed.

   <Arguments>

   <Exceptions>

   <Side Effects>
      None.

   <Returns>
      String list of installed packages that are installed.
   """

   out = os.popen("rpm -q -a 2>/dev/null")
   retlist = []
   for line in out:
      # no package provides...
      if not line.startswith('no package '):
         retlist.append(line.rstrip())
   out.close()
      
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
      IOError: 
              If asked to report on a package that is not installed.
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
   arizonageneral.check_type_stringlist(package_list, "package_list", "storkrpm.get_installedpackages_provide")

   if len(package_list) < 1:
      return []

   (junk_in, the_out, the_err) = os.popen3("rpm -q --provides" + arizonageneral.list_to_args(package_list))
   junk_in.close()
   output = the_out.readline()
   if output.endswith('is not installed'):
      raise IOError, "Inconsistent RPM database!"
   
   retlist = []
   while output:
      retlist.append(output.strip())
      output = the_out.readline()
      
   return retlist





def get_installedpackages_requires(package_list):
   """
   <Purpose>
      Given a string list of installed package names, returns a string 
      list of all dependencies required by those packages. 

   <Arguments>
      package_list:
              String list of installed package names.

   <Exceptions>
      IOError: 
              If asked to report on a package that is not installed.
      TypeError:
              If a type mismatch or parameter error is detected.

   <Side Effects>
      None.

   <Returns>
      String list of all dependencies required by the given packages.
      Dependencies will either be in the form:
        name=version-release (possible spaces around `=')
      Or:
        name  
   """
   # check params
   arizonageneral.check_type_stringlist(package_list, "package_list", "storkrpm.get_installedpackages_requires")

   if len(package_list) < 1:
      return []

   (junk_in, the_out, the_err) = os.popen3("rpm -q --requires" + arizonageneral.list_to_args(package_list))
   junk_in.close()
   output = the_out.readline()
   if output.endswith('is not installed'):
      raise IOError, "Inconsistent RPM database!"
   
   retlist = []
   while output:
      retlist.append(output.strip())
      output = the_out.readline()
      
   return retlist





def check_install_status(filename_list):
   """
   <Purpose>
      Given a list of filenames, see if they were installed.

   <Arguments>
      filename_list:
              String list of filenames representing packages to check.

   <Returns>
      (installed_list, not_installed_list), where installed_list is a list of
      the filenames that were installed.
   """
   arizonageneral.check_type_stringlist(filename_list, "filename_list", "storkrpm.check_install_status")

   installed_list = []
   not_installed_list = []
  
   for filename in filename_list:

     # get the package name from the rpm file
     package_names = []
     cmd_in = os.popen("rpm -qp " + filename)
     output = cmd_in.readline().strip()
     while output:
        if output.startswith("error:") or output.startswith("warning:"):
           pass
        else:
           package_names.append(output)
        output = cmd_in.readline().strip()
     cmd_in.close()

     # can package_names have more than one item? example?
      
     # use get_installed_versions to see if the packages was installed. If so,
     # then add it to installed_list. else, add it to not_installed_list
     if get_installed_versions(package_names):
        installed_list.append(filename)
     else:
        not_installed_list.append(filename)

   return (installed_list, not_installed_list)




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
   # check params
   arizonageneral.check_type_simple(trans_list, "trans_list", list, "storkrpm.install")

   if len(trans_list) < 1:
      return

   # get a list of the RPMs that we're going to install or upgrade
   filename_list = \
      storktransaction.tl_get_filename_list(trans_list, storktransaction.INSTALL) + \
      storktransaction.tl_get_filename_list(trans_list, storktransaction.UPGRADE)

   if len(filename_list) < 1:
      return

   # install (or upgrade) packages
   filenames = arizonageneral.list_to_args(filename_list)
   (out, err, status) = arizonageneral.popen5("rpm --upgrade --force -i" + filenames)
   
   # if there were errors: determine which packages were not installed
   if status != 0:
      (installed_list, not_installed_list) = check_install_status(filename_list)

      # hmmm... it seems we can fail an install due to something like the
      # postinstall script failing, but the rpm database still thinks the
      # package is installed and thus we do not report any error. 

      # rather than failing silently, let's at least display the stderr
      if len(not_installed_list) == 0:
          sys.stderr.write("".join(err).strip() + "\n")

      # raise an exception unless everything installed
      if len(not_installed_list) > 0: 
         raise arizonageneral.Exception_Data("".join(err).strip(), (installed_list, not_installed_list))





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
   arizonageneral.check_type_stringlist(package_list, "package_list", "storkrpm.remove")
   
   if len(package_list) < 1:
      return

   # remove packages
   if nodeps:
       (out, err, status) = arizonageneral.popen5("rpm -e --nodeps" + arizonageneral.list_to_args(package_list))
   else:
       (out, err, status) = arizonageneral.popen5("rpm -e" + arizonageneral.list_to_args(package_list))
   
   # if there were errors: determine which packages were not removed
   if status != 0:
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
         raise arizonageneral.Exception_Data("".join(err).strip(), (removed_list, not_removed_list))
