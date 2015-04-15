#! /usr/bin/env python

"""
<Program Name>
   storknestrpm.py

<Started>
   November 22, 2005

<Author>
   Programmed by Jeffry Johnston.

<Purpose>
   Implements client side of RPM-nest functionality.
"""

#           [option, long option,    variable,     action,        data,     default,                            metavar, description]
"""arizonaconfig
   options=[
            ["",     "--simulatenestfail",   "simulate_nest_fail",   "store_true",  None,     False,                              None,    "simulate a nest failure during storknestrpm install"]]
   includes=[]
"""

import os
import arizonacomm
import arizonaconfig
import arizonageneral
import arizonareport
import storkidentify
import storkrpm
import storktransaction

glo_nestname = None

# Set to True once a successful _handle_prepared has been called by the nest
glo_prepared = False



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
   global glo_nestname

   rpm_sats = storkrpm.initialize()

   # connect to nest 
   try:
      arizonacomm.connect(arizonaconfig.get_option("transhost"), 
                          arizonaconfig.get_option("transport"))
   except IOError: 
      arizonareport.send_error(0, "nestrpm package manager: Could not connect to nest")
      return None
   
   # identify 
   glo_nestname = storkidentify.identify()

   # if not identified, report an error
   if glo_nestname == None:
      arizonareport.send_error(0, "nestrpm package manager: Could not retrieve nest name (identification failed)")
      return None

   storkidentify.verify_exportdir(glo_nestname)
      
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
   arizonageneral.check_type_simple(filename, "filename", str, "storknestrpm.is_package_understood")

   return storkrpm.is_package_understood(filename)

   



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

   return storkrpm.get_packages_provide(filename_list)





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

   return storkrpm.get_packages_require(filename_list)





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

   return storkrpm.get_packages_files(filename_list)





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

   return storkrpm.get_package_info(filename)





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
   arizonageneral.check_type_stringlist(package_list, "package_list", "storkrpm.get_installed_versions")

   return storkrpm.get_installed_versions(package_list)



   
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

   return storkrpm.get_installedpackages_requiring(dep_list)


   


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

   return storkrpm.get_installedpackages_fulfilling(dep_list)


   


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

   return storkrpm.get_installedpackages()





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

   return storkrpm.get_installedpackages_provide(package_list)





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
   arizonageneral.check_type_stringlist(package_list, "package_list", "storknestrpm.get_installedpackages_requires")

   return storkrpm.get_installedpackages_requires(package_list)



   
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
   global glo_prepared
   
   # check params
   arizonageneral.check_type_simple(trans_list, "trans_list", list, "storknestrpm.install")

   if len(trans_list) < 1:
      return

   # perform normal rpm install / upgrade
   storkrpm.execute(trans_list)

   # get a list of the RPMs that we're going to install or upgrade
   filename_list = \
      storktransaction.tl_get_filename_list(trans_list, storktransaction.INSTALL) + \
      storktransaction.tl_get_filename_list(trans_list, storktransaction.UPGRADE)

   if len(filename_list) < 1:
      return
      
   for i, filename in enumerate(filename_list):
      # not okay until the operation completes successfully 
      glo_prepared = False   

      # copy files from nest to client
      try:
         arizonareport.send_out(3, "   nest-sharing: " + filename);
         arizonacomm.send("share", filename) # was "prepare"
         arizonacomm.handle_session({"prepared": __handle_prepared, \
                                     "send_out": __handle_send_out, \
                                     "send_out_comma": __handle_send_out_comma, \
                                     "send_error": __handle_send_error, \
                                     "flush_out": __handle_flush_out, \
                                     "flush_error": __handle_flush_error})
      except:
         # if an exception ocurred while talking with the nest, then we will treat
         # it as a nest failure. 
         glo_prepared = False
                                  
      if not glo_prepared:
         arizonareport.send_error(0, "   nest share of " + filename + " failed")





def __handle_prepared(junk_data):
   """
   <Purpose>
      Called when the nest has finished copying files.

   <Arguments>
      data:
              Unused.

   <Exceptions>
      IOError if there was problem ending the current session.

   <Side Effects>
      Sets glo_prepared to True.

   <Returns>
      None.
   """
   global glo_prepared
   arizonacomm.end_session()
   glo_prepared = True

   if arizonaconfig.get_option("simulate_nest_fail"):
       arizonareport.send_out(0, "simulating nest failure")
       glo_prepared = False





def __handle_send_out(data):
   arizonareport.send_out(0, data)
   




def __handle_send_out_comma(data):
   arizonareport.send_out_comma(0, data)





def __handle_send_error(data):
   arizonareport.send_error(0, data)





def __handle_flush_out(junk_data):
   arizonareport.flush_out(0)





def __handle_flush_error(junk_data):
   arizonareport.flush_error(0)





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
   arizonageneral.check_type_stringlist(package_list, "package_list", "storknestrpm.remove")

   storkrpm.remove(package_list, nodeps)

