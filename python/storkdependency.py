#! /usr/bin/env python
"""
<Program Name>
   storkdependency.py

<Started>
   June 20, 2006

<Author>
   Programmed by Jeffry Johnston.

<Purpose>
   Resolve package dependencies.
"""


#           [option, long option,                    variable,      action,        data,  default, metavar, description]
"""arizonaconfig
   options=[   
            ["-a",   "--abort",                      "abort",       "store_true",  None,  False,   None,    "if we reject a package then abort"],
            ["-A",   "--abortdepth",                 "abortdepth",  "store",       "int", 0,       "depth", "ignore rejections past a certain depth (for abort)"],
            ["",     "--disabletrustedpackagesdata", "disable_tpf", "store_true",  None,  False,   None,    "do not check the trustedpackages file before installing a package (WARNING: allows untrusted package installation)"],
            ["",     "--noupgradedeps",              "upgrade_deps","store_false", None,  True,   None,     "do not automatically upgrade dependencies when upgrading or installing packages"]]
   includes=[]        
"""

import os
import sys
import string
import arizonaconfig
import arizonageneral
import storkpackage
import storkpackagelist
import storktrustedpackagesparse
import arizonareport

EQUAL = 1
LESS = 2
LESS_EQUAL = LESS | EQUAL
GREATER = 4
GREATER_EQUAL = GREATER | EQUAL

def greater_than_zero(x):
   """
   <Purpose>
      Returns True if x>0. If x cannot be converted to an integer, return False
   """
   try:
      v = int(x)
      return (v > 0)
   except ValueError:
      return False

def this_satisfies(name, ver, candidate):
   """
   <Purpose>
      Indicates if a candidate string matches the "name", "ver" 
      requirements.

   <Arguments>
      name:
              The base name of the package (without version, etc).
      ver:
              Package version (usu. starts with relational operator),
              where relational_operator is one of:
                 =, >=, <=, >, <
      candidate:
              "name of package = version".

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      False unless the string meets the name and version requirements.
   """
   # check params
   arizonageneral.check_type_simple(name, "name", str, "stork.this_satisfies")
   arizonageneral.check_type_simple(ver, "ver", str, "stork.this_satisfies")
   arizonageneral.check_type_simple(candidate, "candidate", str, "stork.this_satisfies")

   #arizonareport.send_out(4, "[DEBUG] storkdependency.this_satisfies(" +name+ ", " +ver+ ", " +candidate+ ")")

   # Comparison takes place in up to five steps:
   # 1) compare package names
   # 2) check for a relational operator
   # 3) compare epochs, if an epoch exists then steps 4 and 5 are ignored
   # 4) compare versions
   # 5) compare release numbers

   required_name = name
   original_ver = ver
   original_candidate = candidate

   # Break candidate into name, =, epoch, version, and release parts
   candidate = candidate.strip()

   # candidate name
   i = candidate.find("=")
   if i == -1:
      candidate_name = candidate
      candidate_epoch = ""
      candidate_version = ""
      candidate_release = ""
      candidate = ""
   else:
      candidate_name = candidate[:i].rstrip()
      candidate = candidate[i + 1:].lstrip()

   # Step 1: Compare package names
   # -----------------------------
   if candidate_name != required_name:
      return False

   # if the candidate has no version number, then always return True
   # XXX this appears to be how rpm behaves
   if not candidate:
       return True

   # Break ver into relational operator, epoch, version, and release parts
   ver = ver.strip()

   # relational operator
   # TODO need to support >> and << for Debian
   if ver.startswith(">="):
      rel_oper = GREATER_EQUAL
      ver = ver[2:]
   elif ver.startswith(">"):
      rel_oper = GREATER
      ver = ver[1:]
   elif ver.startswith("<="):
      rel_oper = LESS_EQUAL
      ver = ver[2:]
   elif ver.startswith("<"):
      rel_oper = LESS
      ver = ver[1:]
   elif ver.startswith("="):
      rel_oper = EQUAL
      ver = ver[1:]
   else:
      rel_oper = None
   ver = ver.lstrip()

   #arizonareport.send_out(4, "[DEBUG] storkdependency.this_satisfies rel_oper " + str(rel_oper))

   # Step 2: Check for a relational operator
   # ---------------------------------------  
   if rel_oper == None:
      # if there isn't a relational operator, then anything with the 
      # correct name satisfies the dependency
      return True

   # required epoch
   i = ver.find(":")
   if i == -1:
      required_epoch = ""
   else:
      required_epoch = ver[:i].rstrip()
      ver = ver[i + 1:].lstrip()

   # candidate epoch
   i = candidate.find(":")
   if i == -1:
      candidate_epoch = ""
   else:
      candidate_epoch = candidate[:i].rstrip()
      candidate = candidate[i + 1:].lstrip()

   # Step 3: Compare epochs
   # ----------------------
   # Note: If one has an nonzero epoch and the other does not, then the one with
   #       the epoch is automatically greater than the one without an
   #       epoch.
   if greater_than_zero(required_epoch) or greater_than_zero(candidate_epoch):
      if not greater_than_zero(required_epoch):
         # required didn't have an epoch, so candidate is automatically
         # greater than required
         result = GREATER
      elif not greater_than_zero(candidate_epoch):
         # candidate didn't have an epoch, so candidate is automatically
         # less than required
         result = LESS
      else:
         # both candidate and required have epochs, compare them directly
         if candidate_epoch > required_epoch:
            result = GREATER
         elif candidate_epoch < required_epoch:
            result = LESS
         else:
            result = EQUAL   
           
      # if rel_oper contains the result, then the candidate satisfies the
      # dependency, otherwise it doesn't         
      return (rel_oper & result) != 0
      
   # required version and release
   i = ver.rfind("-")
   if i == -1:
      required_version = ver
      required_release = ""
   else:
      required_version = ver[:i].rstrip()
      required_release = ver[i + 1:].lstrip()

   # candidate version and release
   i = candidate.rfind("-")
   if i == -1:
      candidate_version = candidate
      candidate_release = ""
   else:
      candidate_version = candidate[:i].rstrip()
      candidate_release = candidate[i + 1:].lstrip()

   # Step 4: Compare versions   
   # ------------------------
   if required_version == "":
      # if there isn't a specific required version, then any version 
      # should satisfy the dependency
      return True
      
   if candidate_version == "":
      # we don't know what version the candidate is, so reject to be safe
      return False 
   
   result = __compare_version(candidate_version, required_version)
   
   #arizonareport.send_out(4, "[DEBUG]   ver cand=" + candidate_version + " req=" +required_version+ " res=" + str(result))
   
   # if the result contains LESS or GREATER, and we're looking for something 
   # that is less or greater, then we have satisfied the dependency and do not
   # need to check release numbers.
   if (rel_oper & result & LESS) != 0:
      return True
   if (rel_oper & result & GREATER) != 0:
      return True
      
   # we're done unless the versions were equal
   if result != EQUAL:
      return False
   
   # Step 5: Compare release numbers
   # -------------------------------   
   if required_release == "":
      # if there isn't a specific required release, then any release 
      # satisfies the dependency if the version was satisifed
      return (rel_oper & result) != 0
      
   if candidate_version == "":
      # we don't know what release the candidate is, so reject to be safe
      return False 
      
   result = __compare_version(candidate_release, required_release)
   #arizonareport.send_out(4, "[DEBUG]   rel cand=" + candidate_release + " req=" +required_release+ " res=" + str(result))

   # if rel_oper contains the result, then the candidate satisfies the
   # dependency, otherwise it doesn't         
   return (rel_oper & result) != 0





def this_satisfies_list(name, ver, candidate_list):
   """
   <Purpose>
      Indicates if a candidate string matches the "name", "ver" 
      requirements.
   """

   for candidate in candidate_list:
       if this_satisfies(name, ver, candidate):
           return True

   return False





def __compare_version(str1, str2):
   """
   <Purpose>
      Compares the version numbers by number and if they match then by 
      string.
   
   <Arguments>
      str1:
              Version string to be used in the comparison
      str2:
              Version string to be used in the comparison

   <Exceptions>
      None.

   <Side Effects>
      None.
      
   <Returns>   
      4 (GREATER) if the version str1 is greater than str2
      2 (LESS) if the version str1 is less than str2
      1 (EQUAL) if the version str1 is the same as str2
   """
   # check params
   arizonageneral.check_type_simple(str1, "str1", str, "stork.__compare_version")
   arizonageneral.check_type_simple(str2, "str2", str, "stork.__compare_version")

   str1list = str1.split('.')
   str2list = str2.split('.')

   count = max(len(str1list), len(str2list))

   for num in range(count):
      if len(str1list) <= num:
         return LESS
      if len(str2list) <= num:
         return GREATER
      if str1list[num].isdigit() and str2list[num].isdigit():
         if int(str1list[num]) > int(str2list[num]):
            return GREATER
         elif int(str1list[num]) < int(str2list[num]):
            return LESS
      else:
         t1 = str1list[num].strip(string.letters)
         t2 = str2list[num].strip(string.letters)
         if t1.isdigit() and t2.isdigit():
            if int(t1) > int(t2):
               return GREATER
            elif int(t1) < int(t2):
               return LESS
            # fall through and do a string compare if equal
         else:
            # it's okay, this just means they have an embedded char portion
            # We'll string compare...
            pass

   if str1list < str2list:
      return LESS
   elif str1list > str2list:
      return GREATER

   return EQUAL





def find_satisfying_packages(name, ver):
   """
   <Purpose>
      Searches for packages meeting the name and version requirements.
      
   <Arguments>
      name:
              The single dependency needing to be satisfied.
      ver:
              The required version of the dependency, in the format:
              "OPERATOR VERSION", or "".  Where, OPERATOR is a relational
              operator (=, >, etc), and version is a plain version,
              without release number (example: 1.2.3, not 1.2.3-1)

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      Returns a list of package information dictionaries.
   """
   # check params
   arizonageneral.check_type_simple(name, "name", str, "stork.find_satisfying_packages")
   arizonageneral.check_type_simple(ver, "ver", str, "stork.find_satisfying_packages")

   arizonareport.send_out(4, "[DEBUG] storkdependency.find_statisfying_packages " + 
                             "name = " + name + "ver = " + ver);

   # find packages that have the desired package name in their provides
   # field (this means they satisfy the dependency)
   criteria_dict = {}
   criteria_dict['provides'] = name
   mylist = storkpackagelist.find_packages(criteria_dict)
   criteria_dict['provides'] = name + " =*"
   mylist += storkpackagelist.find_packages(criteria_dict)
   retlist = []

   arizonareport.send_out(4, "[DEBUG] storkdependency.find_satisfying_packages mylist = " + 
       str([(pack['name'], pack['version'], pack['release']) for pack in mylist]));

   # now check that the version is adequate
   for package in mylist:
      for provided in package['provides']:
         if this_satisfies(name, ver, provided):
            retlist.append(package)
   return retlist





def find_file_satisfying_packages(filename):
   """
   <Purpose>
      Searches for packages meeting the filename requirement.
      
   <Arguments>
      filename:
              The single file dependency needing to be satisfied.
   
   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      Returns a list of package information dictionaries.
   """
   # check params
   arizonageneral.check_type_simple(filename, "filename", str, "stork.find_file_satisfying_packages")

   # find packages that have the desired filename in their files 
   # field (this means they satisfy the dependency)
   criteria_dict = {}
   criteria_dict['files'] = filename
   return storkpackagelist.find_packages(criteria_dict)





def find_trusted_satisfying_packages(name, ver, tags, ignore_mantags=False):
   """
   <Purpose>
      Searches for packages meeting the name and version requirements that
      are also trusted by the user.

   <Arguments>
      name:
              The single dependency needing to be satisfied.
      ver:
              The required version of the dependency, in the format:
              "OPERATOR VERSION", or "".  Where, OPERATOR is a relational
              operator (=, >, etc), and version is a plain version,
              without release number (example: 1.2.3, not 1.2.3-1)
      tags:
              A comma-delimited string of tags.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      Returns a list of package information dictionaries.
   """
   # check params
   arizonageneral.check_type_simple(name, "name", str, "stork.find_trusted_satisfying_packages")
   arizonageneral.check_type_simple(ver, "ver", str, "stork.find_trusted_satisfying_packages")

   # Find a list of possible packages to fulfill this requirement
   if name[0] == "/":
      # file dependency
      pkg_list = find_file_satisfying_packages(name)
   else:
      # package dependency
      pkg_list = find_satisfying_packages(name, ver)

   # remove duplicate entries
   pkg_list = arizonageneral.uniq(pkg_list)

   # remove any invalid packages from list 
   pkg_list = [pkg for pkg in pkg_list if storkpackage.package_metadata_dict_validate(pkg)]

   arizonareport.send_out(4, "[DEBUG] storkdependency.find_trusted_satisfying_packages pkg_list = " + 
       str([(pack['name'], pack['version'], pack['release']) for pack in pkg_list]));

   # create a list of allowed (trusted) packages
   trusted_pkg_list = []

   # if we've disabled trusted packages data, then use the above (unsafe!)
   # otherwise, filter out packages that are untrusted or unwanted
   if arizonaconfig.get_option("disable_tpf"):
      # Use what we were given... unsafe, but assume the user knows best
      for package in pkg_list:
         # append package dictionary, as is
         trusted_pkg_list.append(package)
   else:
      # Form a list of (filename, metahash, dictionary) tuples that rank_packages will use
      rank_packages_list = []
      for package in pkg_list:
         rank_packages_list.append((package["filename"], package["_metadatahash"], package))

      # Clobber/rank packages based upon trust and version information
      (allow_list, deny_list, unspecified_list) = \
         storktrustedpackagesparse.rank_packages(rank_packages_list, tags,
                                                 ignore_mantags)

      # a list of items that we don't want to issue warnings about.
      do_not_warn_list = []
      
      # we only care about the list of allowed items (element 0)
      for item in allow_list:
         # allowed is a tuple: (filename, metahash, dictionary, tpentry) same as we
         # passed in above.  So, package[0]=filename, package[1]=metahash,
         # package[2]=package dictionary
         # we don't need the separate filename or metahash anymore
         trusted_pkg_list.append(item[2])
         do_not_warn_list.append(item[2])

      for item in deny_list:
         if not item[0] in do_not_warn_list:
            arizonareport.send_out(2, "   package " + item[0] + " was denied by a trusted packages file")
            do_not_warn_list.append(item[0])
         
      for item in unspecified_list:
         if not item[0] in do_not_warn_list:
            arizonareport.send_out(2, "   package " + item[0] + " ignored because it does not match any tp files")         
            do_not_warn_list.append(item[0])
   
   # return the list of package dictionaries      
   return arizonageneral.uniq(trusted_pkg_list)




def split_pack_name(pack):
   """
   <Purpose>
      Splits a package name of the form packOPver, pack OPver, or pack OP ver
      into the package name (pack) and the op+version (ver)
   <Returns>
      A tuple (name, ver, tags)
   """   

   # check params
   arizonageneral.check_type_simple(pack, "pack", str, "storkdependency.split_pack_name")

   # find relational operators, if any
   pos = pack.find(">") # also handles >=
   if pos == -1:
      pos = pack.find("<") # also handles <=
      if pos == -1:
         pos = pack.find("=")

   # add the package to the list of packages that need to be installed
   if pos == -1:
      # package
      name = pack
      ver = ""
   else:
      # package and version
      name = pack[:pos].rstrip()
      ver = pack[pos:]

   # Depending on whether the user did 'pack = ver # tag' or 'pack # tag = ver',
   # the tags could be in either 'name', or 'ver' at this point, so check them
   # both.
      
   tags = ""
   pos = name.find("#")
   if pos != -1:
      tags = name[pos+1:].lstrip()
      name = name[:pos].rstrip()
   else:
      pos = ver.find("#")
      if pos != -1:
          tags = ver[pos+1:].lstrip()
          ver = ver[:pos].rstrip()

   return (name, ver, tags)

   


def get_installed_by_name(pack):
    """
    <Purpose>
       Given a package and optional relop and version (nameOPver), see what
       packages satisfy the version requirements. Packages are checked based
       on name and version number, not provided dependencies.
    <Returns>
       A tuple (sat_vers, unsat_vers), where sat_vers is a list of packages
       that satisfy the version requirement, and unsat_vers is a list of 
       packags (of the same name) that do not satisfy the version requirement.
    """   

    # check params
    arizonageneral.check_type_simple(pack, "pack", str, "storkdependency.get_installed_by_name")
   
    (name, ver, tags) = split_pack_name(pack)
    
    cur_versions = storkpackage.get_installed_versions([name])

    unsatisfying_versions = []
    satisfying_versions = []

    for cur in cur_versions:
        if cur != None:
            # cur will be of the format "name = ver". we want "name-ver"
            packname = cur;
            if packname.find(" = "):
                packname = packname.replace(" = ", "-")
                
            if this_satisfies(name, ver, cur):
                satisfying_versions.append(packname)
            else:
                unsatisfying_versions.append(packname)

    if satisfying_versions or unsatisfying_versions:
        arizonareport.send_out(3, "[INFO] pack " + str(pack) +
                                  " has installed satisfying versions " + str(satisfying_versions) +
                                  " and unsatisfying versions " + str(unsatisfying_versions)) 

    return (satisfying_versions, unsatisfying_versions)



def remove_version_numbers(dep_list):
    """
    <Purpose>
       Remove version numbers from dependencies in a list
    <Returns>
       A list of dependencies with the version numbers removed
    """  
    
    # check params
    arizonageneral.check_type_stringlist(dep_list, "dep_list", "storkdependency.remove_version_numbers")
    
    dep_list_new = []
    for dep in dep_list:
       pos = dep.find('=')
       if pos != -1:
           dep = dep[:pos].rstrip()
       dep_list_new.append(dep)

    return dep_list_new

        

def get_installed_by_provides(dep_list):
    """
    <Purpose>
       Given a list of dependencies, return the packages that provide those
       dependencies.
    <Returns>
       A list of packages that provide the dependencies
    """   

    # check params
    arizonageneral.check_type_stringlist(dep_list, "dep_list", "storkdependency.get_installed_by_provides")

    #dep_list_orig = dep_list

    # remove any version numbers from the dep_list.
    dep_list = remove_version_numbers(dep_list)
   
    (unmet_list, dep_list) = installed_satisfy_list(dep_list, [], True)

    #print "get_installed_by_provides("+str(dep_list_orig)+") = "+str(dep_list)

    return dep_list



def get_reverse_dep(check_list, remove_list, install_list):
    """
    <Purpose>
       Given a list of packages that are currently installed, see what existing
       packages depend on those. Optionally, a list of packages that are to
       be installed may be provided, and this function will compute the packages
       that depend on 'remove_list', but are not satisfied by 'install_list'
    <Arguments>
       check_list:
              A list of packages whose dependencies we wish to check.
       remove_list:
              A list of existing packages that are installed that we are
              intending to remove. This list contains package names.
       install_list:
              [optional] A list of new packages that we intend to install 
              (possibly replacing some of those packages in remove_list). This
              list contains package dictionaries.
    <Returns>
       A list of packages that will be broken if the packages are removed.
    """

    # check params
    arizonageneral.check_type_stringlist(check_list, "check_list", "storkdependency.get_referse_dep")
    arizonageneral.check_type_stringlist(remove_list, "remove_list", "storkdependency.get_reverse_dep")

    arizonareport.send_out(4, "[DEBUG] get_reverse_dep check_list=" + str(check_list))
    arizonareport.send_out(4, "[DEBUG] remove_list=" + str(remove_list))

    # install_list can either be None or a list of package dicts.
    if install_list:
       arizonageneral.check_type_simple(install_list, "install_list", list, "storkdependency.get_reverse_dep")
       arizonareport.send_out(4, "[DEBUG] install_list = " + str([pack['name']+'-'+pack['version'] for pack in install_list]))

    # build up a list of what is provided by the packages that we want to
    # check
    provides_list = storkpackage.get_installedpackages_provide(check_list)

    provides_list = arizonageneral.uniq(provides_list)

    # generate a list of dependencies that will be provided by the packages in
    # the install_list.
    replace_list = []
    if install_list != None:
        for pack in install_list:
           if pack.get('provides', None):
               replace_list += pack['provides']
        replace_list = arizonageneral.uniq(replace_list)

    arizonareport.send_out(4, "[DEBUG] replace_list="+str(replace_list))
    arizonareport.send_out(4, "[DEBUG] provides_list="+str(provides_list))

    # get a list of the packages that depend on the packages we intend to
    # remove. We have to do this without version numbers because
    # 'rpm -q --whatrequires' does not support version numbers. We'll have to
    # recheck our results against version numbers later.
    requires_list = storkpackage.get_installedpackages_requiring(
                                      remove_version_numbers(provides_list))

    # remove the packages that we're deleting from the requires list
    # this also takes care of packages that depend on themselves
    for pack in remove_list:
        while pack in requires_list:
            requires_list.remove(pack)

    arizonareport.send_out(4, "[DEBUG] requires_list="+str(requires_list))

    #return requires_list

    # TODO: smbaker: more tests of the following...

    # now we match the version numbers...
    broken_list = []
    for pack in requires_list:
        # get the dependencies that are required by the package.
        requires = storkpackage.get_installedpackages_requires([pack])
        arizonareport.send_out(4, "[DEBUG] pack "+str(pack)+ " requires " +str(requires))

        for dep in requires:
            (depname, depver, deptags) = split_pack_name(dep)
            arizonareport.send_out(4, "[DEBUG]   checking "+str((depname, depver)))

            # see if the dependency matches one of the ones we are removing
            if this_satisfies_list(depname, depver, provides_list):
                arizonareport.send_out(4, "[DEBUG]     "+str((depname, depver))+" matched by provides_list")

                # see if the dependency matches on of the ones that we will be
                # adding.
                if not this_satisfies_list(depname, depver, replace_list):
                    arizonareport.send_out(4, "[DEBUG]        and not matched by replace_list")
                    broken_list.append(pack)
                else:
                    arizonareport.send_out(4, "[DEBUG]        *** and matched by replace_list")
            else:
                arizonareport.send_out(4, "[DEBUG]     "+str((depname, depver))+" not matched by provides_list")

    arizonareport.send_out(4, "[DEBUG] broken_list="+str(broken_list))

    # what we have left is the packages that will be broken if we remove the
    # packages in remove_list (and install the packages in install_list)

    return broken_list




        
def installed_satisfy_list(dep_list, upgrade_pack=[], reportInstalled=False):
   """
   <Purpose>
      Given a list of dependencies, decides which dependencies are met by
      installed packages, and returns a filtered list containing only the 
      unmet dependencies.

   <Arguments>
      dep_list:
              A list of dependencies in one of the following forms:
                name
                name OP ver
                nameOPver  
              Where OP is one of: = < > <= >=

      upgrade_pack:
              (Default: [])
              List of packages scheduled for an upgrade.
      
      reportInstalled:        
              (Default: False)
              If True, returns a tuple ([unmet], [satisfying_packages])
              Where unmet is the list of unmet dependencies, and 
              satisfying_packages is a list of installed packages that 
              satisfied at least one dependency.
   
   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      Returns a either a list of unmet dependencies or a tuple containing 
      a list of unmet dependencies, and a list of installed packages that
      met at least one dependency.
   """
   # check params
   arizonageneral.check_type_stringlist(dep_list, "dep_list", "stork.installed_satisfy_list")
   arizonageneral.check_type_stringlist(upgrade_pack, "upgrade_pack", "installed_satisfy")

   # remove duplicate entries
   temp_list = arizonageneral.uniq(dep_list)
   #arizonareport.send_out(4, "[DEBUG] installed_satisfy_list, unique dependencies: " + str(temp_list))

   # separate out file dependencies, and build some lists we'll need later
   name_list = []
   dep_list = []
   filedep_list = []
   for item in temp_list:
      # if this is a file dependency, see if it is already on the disk
      # if not, there are two situations: 
      #   1) the file was deleted
      #   2) the file dependency has not been met
      # TODO? for now, we assume that 1) is very rare, so we assume that
      # any remaining file dependencies are not met by installed packages
      item = item.strip()
      if item[0] == "/":
         if not os.path.exists(item):
            filedep_list.append(item)
      else:
         (name, ver, tags) = split_pack_name(item)
         name_list.append(name)   
         dep_list.append((name, ver, item))
         
   arizonareport.send_out(4, "[DEBUG] installed_satisfy_list, filedep_list: " + str(filedep_list))
   arizonareport.send_out(4, "[DEBUG] installed_satisfy_list, dep_list: " + str(dep_list))
   arizonareport.send_out(4, "[DEBUG] installed_satisfy_list, name_list: " + str(name_list)) 

   # get a list of packages that provide the dependencies
   try:
      candidate_list = storkpackage.get_installedpackages_fulfilling(name_list)
   except TypeError: #changed from a general exception
      exc_info = sys.exc_info()
      e = exc_info[1]
      try:
         message = e.message
      except:
         raise exc_info[0], exc_info[1], exc_info[2]
      arizonareport.send_error(0, "An error occurred while finding packages to fulfill the `" + \
                                  ", ".join(name_list) + "' dependencies:\n" + message)
      arizonareport.send_error(0, "Aborting installation.")
      sys.exit(1)

   arizonareport.send_out(4, "[DEBUG] installed_satisfy_list, candidate_list: " + str(candidate_list))

   # Remove from consideration any installed packages that are scheduled
   # for an upgrade
   for item in candidate_list:
      if item in upgrade_pack:
         candidate_list.remove(item)

   # now, get a list of what dependencies these packages provide.  We have
   # to do this because it is possible that dependencies weren't provided
   # by the above packages, and we need to figure out which dependencies
   # those are.  Also, some packages might not be of the required version.
   try:
      if reportInstalled:
         # this is slower, but we need to keep track of which candidate
         # package satisfied which dependency
         provide_list = []
         for candidate in candidate_list:
            temp_list = storkpackage.get_installedpackages_provide([candidate])
            for item in temp_list:
               provide_list.append((item, candidate))
         satisfying_packages = []
      else:
         # faster: don't care which package satisfied the dependency as
         # long as one of them did
         provide_list = storkpackage.get_installedpackages_provide(candidate_list)
         arizonareport.send_out(4, "[DEBUG] installed_satisfy_list, provide_list: " + str(provide_list))
   except (TypeError, IOError): #changed from a general exception
      exc_info = sys.exc_info()
      e = exc_info[1]
      try:
         message = e.message
      except:
         raise exc_info[0], exc_info[1], exc_info[2]
      arizonareport.send_error(0, "An error occurred while finding what the packages `" + \
                                  ", ".join(candidate_list) + "' provide:\n" + message)
      arizonareport.send_error(0, "Aborting installation.")
      sys.exit(1)

   # go through the above provides list and remove provided dependencies
   #arizonareport.send_out(4, "[DEBUG] installed_satisfy_list, provide_list: " + str(provide_list))
   unsat_dep_list = []
   for i, dep in enumerate(dep_list):
      satisfied = None
      for item in provide_list:
         if reportInstalled:
            if this_satisfies(dep[0], dep[1], item[0]):
               satisfying_packages.append(item[1])
               satisfied = item
               break
         else:
#            if dep[0].startswith("perl(File::Path") and item.startswith("perl(File::Path"):
#               print "dep=" + str(dep) + " item=" + str(item) + " ts=" + str(this_satisfies(dep[0], dep[1], item))
            if this_satisfies(dep[0], dep[1], item):
               #arizonareport.send_out(4, "[DEBUG] installed_satisfy_list, satisfied: " + dep[0] + ", " + dep[1] + ", " + item)
               satisfied = item
               break
      if satisfied:
          arizonareport.send_out(4, "[DEBUG] installed_satisfy_list, satisfied: " + dep[0] + ", " + dep[1] + " with " + satisfied)
      else:
          arizonareport.send_out(4, "[DEBUG] installed_satisfy_list, did not satisfy: " + dep[0] + ", " + dep[1])
          unsat_dep_list.append(dep)

   arizonareport.send_out(4, "[DEBUG] installed_satisfy_list, unsat_dep_list=" + str(unsat_dep_list))

   missing_list = []
   for dep in unsat_dep_list:                    
      missing_list.append(dep[2])

   arizonareport.send_out(4, "[DEBUG] installed_satisfy_list, filedep_list: " + str(filedep_list))
   arizonareport.send_out(4, "[DEBUG] installed_satisfy_list, missing_list: " + str(missing_list))

   # add on file dependencies and return the combined list of unmet deps
   missing_list = filedep_list + missing_list

   # return the requested information
   if reportInstalled:
      return (missing_list, arizonageneral.uniq(satisfying_packages))
   else:
      return missing_list
      




glo_internal_deps = []
def find_unsat_dependencies(package):
   """
   <Purpose>
      Given a package dictionary entry, returns a list of unsatisfied
      dependencies.
   
   <Arguments>
      package:
                Package dictionary entry.
   
   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>             
      Returns a list of what dependencies of a package aren't satisfied, 
      in other words, returns a list of unmet dependencies.
   """
   global glo_internal_deps

   # check params
   arizonageneral.check_type_simple(package, "package", dict, "stork.find_unsat_dependencies")
   
   # build a list of raw dependencies of this package
   dep_list = package['requires']
   #arizonareport.send_out(4, "[DEBUG] find_unsat_dependencies, requires: " + str(dep_list))

   # filter out the met dependencies (some packages are installed)
   dep_list = installed_satisfy_list(dep_list)
   #arizonareport.send_out(4, "[DEBUG] find_unsat_dependencies, filtered installed: " + str(dep_list)) 
   
   # remove any dependencies fulfilled by the package managers themselves
   ret_list = []
   for dep in dep_list:
      # split up dependency into name and ver parts
      fields = dep.split()
      name = fields[0]
      if len(fields) > 1:
         ver = " ".join(fields[1:])
      else:
         ver = ""
      
      # see if any of the internal dependencies match
      for intdep in storkpackage.get_packagemanagers_provide():
         if this_satisfies(name, ver, intdep):
            break
      else:
         # nope, this must be a real dependency
         ret_list.append(dep)
   #arizonareport.send_out(4, "[DEBUG] find_unsat_dependencies, filtered internal: " + str(ret_list))

   return arizonageneral.uniq(ret_list)



glo_pkgver_satisfied = []
glo_filemeta_satisfied = []
glo_cannot_satisfy = []
def satisfy(pkg, ver="", tags="", upgrade=False, trace=[], ignore_mantags=False):
   """
   <Purpose>
      This returns a list of every package needed to satisfy all
      installation dependencies of a given version of a package, and all
      installation dependencies of the needed packages.

   <Arguments>
       pkg:
           the name of the package, minus version number.
       ver:
           the version number of the desired package. May contain relational
           operators.
       upgrade:
           True if upgrades are allowed.
           Note: At this time, recursive upgrading is not supported. Satisfy
              will always pass 'False' to recursive calls to satisfy.
       trace:
           Used to filter out circular dependencies.

   TODO fix comment
   """
   global glo_pkgver_satisfied
   global glo_filemeta_satisfied
   global glo_cannot_satisfy

   # check params
   arizonageneral.check_type_simple(pkg, "pkg", str, "stork.satisfy")
   arizonageneral.check_type_simple(ver, "ver", str, "stork.satisfy")
   arizonageneral.check_type_stringlist(trace, "trace", "stork.satisfy")

   pkgver = (pkg, ver)
   if pkgver in glo_pkgver_satisfied:
      return []

   # tell the user which package we're trying to satisfy
   arizonareport.send_out(2, (arizonageneral.recur_depth("satisfy") - 1) * "   " + \
                             "Attempting to satisfy " + pkg + " " + ver)

   # Find a list of trusted packages that fulfill the immediately obvious
   # dependency requirements (not recursive, so these answers are verified
   # below)
   trusted_pkg_list = find_trusted_satisfying_packages(pkg, ver, tags, ignore_mantags)

   arizonareport.send_out(4, "[DEBUG] storkdependency.satisfy trusted_pkg_list = " +
      str([(pack['name'], pack['version'], pack['release']) for pack in trusted_pkg_list]));

   # Now there is a list of packages that can satisfy the requirement,
   # however some of these packages might not be satisfiable themselves.
   # Go through the candidates in order and try to satisfy them:
   for package in trusted_pkg_list:
      # build package id from package filename and metahash (assumed to be unique)
      pack_id = package['name'] + "_" + package['_metadatahash']

      # check for circular package dependencies
      if pack_id in trace:
         if not pkgver in glo_pkgver_satisfied:
            glo_pkgver_satisfied.append(pkgver)
         arizonareport.send_out(2, (arizonageneral.recur_depth("satisfy") - 1) * "   " + \
                                   "Satisfied " + pkg + " by " + package['filename'])
         return []
      trace.append(pack_id)

      # if we've previously found that the candidate package cannot be
      # satisfied, then reject the package now before we waste time
      # rediscovering the fact
      if pack_id in glo_cannot_satisfy:
         continue

      # if we've previously found that the candidate package is satisfied,
      # then accept the package right away.
      if pack_id in glo_filemeta_satisfied:
         if not pkgver in glo_pkgver_satisfied:
            glo_pkgver_satisfied.append(pkgver)
         return []

      # keep the user informed
      arizonareport.send_out(2, (arizonageneral.recur_depth("satisfy") - 1) * "   " + \
                                "Trying " + package['filename'] + \
                                " to satisfy " + pkg + " " + ver)

      # find out what unmet dependencies (if any) this candidate has
      dep_list = find_unsat_dependencies(package)

      # find what existing packages will conflict with this package. There are
      # two different ways we could do this:
      #   a) a package conflicts if the name is identical
      #   b) a package conflicts if it provides the same dependencies
      #   or... c) a packages conflicts if contains the same files
      # 'c' is probably the right one (it's what RPM does?)
      # 'b' doesn't appear to be correct
      # ... so let's do 'a' for now.
      # TODO: implement 'c'? research what yum/apt do?
      
      # conflict_list = get_installed_by_provides(package['provides'])  # 'b'
      
      (conflict_list, nothing) = get_installed_by_name(package['name'])  # 'a'

      # see what conflicts we have with existing installed packages
      if conflict_list:
          if upgrade:
              # upgrade: we'll end up removing the conflicts
              package['_upgrade_conflicts'] = conflict_list
              arizonareport.send_out(3, (arizonageneral.recur_depth("satisfy") - 1) * 
                                        "   " + "Upgrade of package "+package['filename'] + 
                                        " will replace package " + str(conflict_list))
          else:
              # install: we cannot remove a conflict, so we cannot use this
              # package
              arizonareport.send_out(1, (arizonageneral.recur_depth("satisfy") - 1) * 
                                        "   " + "Cannot use package "+package['filename'] + 
                                        " because version "+str(conflict_list)+" is already installed")
              glo_cannot_satisfy.append(pack_id)
              continue

      # tell extra verbose user which dependencies need to be met
      if dep_list:
         arizonareport.send_out(3, (arizonageneral.recur_depth("satisfy") - 1) * \
                                   "   " + pkg + " has unmet dependencies on: " + \
                                   ", ".join(dep_list))

      # go through each dependency and try to satisfy it
      need_to_install = []
      for dep in dep_list:
         # recursively call satisfy on this dependency.  base case occurs
         # when a package either has no unmet dependencies (see the "else"
         # part of this for loop), or when a package cannot be satisfied.

         # TODO handle OR dependencies (only one is needed): a | b | ...

         # split dependency string into package name and version
         dep_pieces = dep.split(None, 1)
         dep_pkg = dep_pieces[0]
         if len(dep_pieces) == 2:
            dep_ver = dep_pieces[1]
         else:
            dep_ver = ""

         # skip file dependency if it is satisfied by the package itself
         if dep[0] == "/" and (dep in package['files']):
            continue

         # skip dependency if it is satisfied by the package itself
         # go through provides candidates to try to find a match
         skip = False
         for candidate in package['provides']:
            if this_satisfies(dep_pkg, dep_ver, candidate):
               skip = True
               break
         if skip:
            continue

         # find a list of packages that need to be installed
         dep_needs_to_install = satisfy(dep_pkg, dep_ver, [], 
                                        arizonaconfig.get_option("upgrade_deps"),
                                        trace,
                                        True)  # ignore mandataory tags on deps

         # could the package be satisfied?  (if not, cur_ans == None)
         if dep_needs_to_install == None:
            # no.. remember this package so we never want to try it again
            glo_cannot_satisfy.append(pack_id)

            # let user know we took a wrong turn
            # TODO: should we combine these two print statements?
            arizonareport.send_out(1, (arizonageneral.recur_depth("satisfy") - 1) * \
                                      "   " + "Cannot satisfy dependency: " + \
                                      dep + " of " + package['filename'])
            arizonareport.send_out(1, (arizonageneral.recur_depth("satisfy") - 1) * \
                                      "   " + "Rejecting " + \
                                      package['filename'])
            if arizonaconfig.get_option("abort") and \
                 (arizonaconfig.get_option("abortdepth") == 0 or \
                 arizonaconfig.get_option("abortdepth") < \
                 arizonageneral.recur_depth("satisfy")):
               arizonareport.send_out(1, "Aborting because " + \
                                         package['filename'] + \
                                         " was rejected...")
               sys.exit(1)
            break

         # dependency was satisfied
         for item in dep_needs_to_install:
            # remember this package, so we never need to check it again
            pack_id = item["filename"] + "_" + item["_metadatahash"]

            # only add it to the list once
            if not pack_id in glo_filemeta_satisfied:
               glo_filemeta_satisfied.append(pack_id)

            if not pkgver in glo_pkgver_satisfied:
               glo_pkgver_satisfied.append(pkgver)

         # dependency was satisfied.. add whatever packages it needed to
         # a master list of needed packages
         need_to_install += dep_needs_to_install
      else:
         # Either the package had no unmet dependencies, or all of them
         # have tentatively been met (recursively).  So the package has
         # or can be satisfied.  (This is the base case)
         arizonareport.send_out(2, (arizonageneral.recur_depth("satisfy") - 1) * \
                                   "   " + "Satisfied " + pkg + \
                                   " by " + package['filename'])
         need_to_install.append(package)
         need_to_install = arizonageneral.uniq(need_to_install)
         return need_to_install

      # reaches this comment if the package was rejected.. now tries the
      # next candidate package in trusted_pkg_list
   else:
      # went through every candidate package, but none could be satisfied.
      # cannot satisfy this pkg/ver dependency
      arizonareport.send_out(2, (arizonageneral.recur_depth("satisfy") - 1) * "   " + \
                                "Cannot satisfy " + pkg + " " + ver)
      return None
