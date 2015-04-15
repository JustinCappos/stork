#! /usr/bin/env python
 
# Programmed by Jeffry Johnston under the direction of Justin Cappos
# storkquery program
# Started: November 13, 2004

#           [option, long option,     variable,     action,       data,     default,                           metavar, description]
"""arizonaconfig
   options=[
            ["-C",   "--configfile",  "configfile", "store",      "string", "/usr/local/stork/etc/stork.conf", "FILE",  "use a different config file (/usr/local/stork/etc/stork.conf is the default)"],
            ["",     "--hash",        "hash",       "store",      "string", None,                              None,    "restrict query results to this hash value"],
            ["",     "--packagefile", "pfile",      "store",      "string", None,                              None,    "restrict query results to this package list file"],
            ["-e",   "--exact",       "exact",      "store_true", None,     False,                             None,    "return exact matches only"]]
   includes=[]        
"""

#---------------------------------------------------------------------
# Imports
#---------------------------------------------------------------------
import os
import sys
import arizonageneral
import arizonaconfig
import storkpackage
import storkpackagelist
import arizonareport
import storkerror





def filter_database(name, exact):
   """
   <Purpose>
      Filters the package database by name, hash, and/or package file.

   <Arguments>
      name: 
              Partial name match.
 
      exact: 
              Return exact matches only?  True or False.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      A list of all matching package names.
   """
   greplist = []
   categorylist = []

   # partial name match
   if name != None:
      if exact:
         greplist.append(name)
      else :
         greplist.append('.*' + name + '.*')
      categorylist.append('name')

   # --hash=... filter    
   if arizonaconfig.get_option("hash") != None:
      greplist.append(arizonaconfig.get_option("hash"))
      categorylist.append('hash')

   retlist = []
   
   for pkg_db in arizonaconfig.get_option("pdir"):
      # --packagefile=... filter 
      if arizonaconfig.get_option("pfile") != None and not pkg_db.endswith(arizonaconfig.get_option("pfile")):
         continue
      
      # display "Searching..." output 
      if arizonareport.get_verbosity() > 1: 
         pos = pkg_db.find("://")
         if pos == -1:
            offset = 0
         else:
            offset = pos + 3
         pos2 = pkg_db[offset:].find("/")
         system_name = pkg_db[offset:offset + pos2]
         pos3 = pkg_db[offset + pos2:].find("|")
         repository_dir = pkg_db[offset + pos2: offset + pos2 + pos3]
         package_file = pkg_db[offset + pos2 + pos3 + 1:] 
         arizonareport.send_out(2, "Searching " + repository_dir + " on " + 
                              system_name + " (" + arizonaconfig.get_option("dbdir") + 
                              "): " + package_file)
      
      # do the search
      grep = storkpackagelist.cull_database(greplist, categorylist) + " " + \
             storkpackagelist.package_cache_name(pkg_db)

      (junk_in, out, junk_err) = os.popen3(grep)
      junk_in.close()
      junk_err.close()

      # collect results
      output = out.readline()
      while output:
         if storkpackagelist.get_db_field(output, 'name'):
            retlist = retlist + [storkpackagelist.get_db_field(output, 'name')]
         output = out.readline()
      out.close()
   
   arizonareport.send_out(2, "Collecting results...")
                     
   # return a sorted list of unique results         
   retlist = arizonageneral.uniq(retlist)
   retlist.sort()
   return retlist





def package_info(name, hash_value): 
   """
   <Purpose>
      Returns a list of information about the given package:
      [version, release, size, filename, [requires], [provides], 
       installed]

   <Arguments>
      name: 
              Name of the package.
 
      hash: 
              Hash value of the package.  If None is given then the only 
              returned info will be a list of the available hashes.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      A list of hash or package information. 
   """
   # check for a package name 
   if name == None:
      return None
   
   # information to collect      
   hashes = []
   release = None
   version = None
   size = None
   filename = None
   requires = []
   provides = []
   installed = None

   # scan package files   
   for pkg_db in arizonaconfig.get_option("pdir"):
      # --packagefile=... filter
      if arizonaconfig.get_option("pfile") != None and not pkg_db.endswith(arizonaconfig.get_option("pfile")):
         continue
         
      # build a search string for this package file     
      if hash_value == None:
         grep = storkpackagelist.cull_database([ name ], ['name']) + " " + \
                                         storkpackagelist.package_cache_name(pkg_db)
      else:
         grep = storkpackagelist.cull_database([ name, hash_value ], ['name', 'hash']) + \
                                         " " + storkpackagelist.package_cache_name(pkg_db)
      
      # search the package file
      (junk_in, out, junk_err) = os.popen3(grep)
      junk_in.close()
      junk_err.close()
      
      # scan the package file output
      while (True):
         output = out.readline()
         if output == "":
            break
            
         if hash_value == None:
            # build the hash list 
            field = storkpackagelist.get_db_field(output, 'hash').strip()
            if field != "":
               hashes.append(field)            
         else: 
            # collect package information for a specific hash
         
            # release
            if release == None:
               field = storkpackagelist.get_db_field(output, 'release').strip()
               if field != "":
                  release = field
            
            # version           
            if version == None:
               field = storkpackagelist.get_db_field(output, 'version').strip()
               if field != "":
                  version = field
            
            # size
            if size == None:
               field = storkpackagelist.get_db_field(output, 'size').strip()
               if field != "":
                  size = field
                  
            # filename
            if filename == None:
               field = storkpackagelist.get_db_field(output, 'file').strip()
               if field != "":
                  filename = field
            
            # requires
            field = storkpackagelist.get_db_field(output, 'requires').strip()
            if field != "":
               requires.append(field)
            
            # provides
            field = storkpackagelist.get_db_field(output, 'provides').strip()
            if field != "":
               provides.append(field)

   # installed
   installed = storkpackage.get_installed_versions([name])[0]
   if installed == None:
      installed = "Not installed"

   # return results
   if hash_value == None:
      return arizonageneral.uniq(hashes)
   else:
      requires = arizonageneral.uniq(requires)
      provides = arizonageneral.uniq(provides)
      return [ version, release, size, filename, requires, provides, installed ]   





def init():
   """
   <Purpose>
      Processes and handles some command line arguments.

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      A list of unhandled command line arguments.
   """
   
   # get command line and config file options
   args = arizonaconfig.init_options('storkquery.py', configfile_optvar='configfile', version='2.0')

   # init package lists
   storkpackagelist.init()
   
   """global storkpm
   #### Set up the packaging tool
                                                                                
   # Right now only use rpm...   Could change this to work with deb
   if glo_options.pmtype=='rpm':
      import storkrpm as storkpm
   else:
      arizonareport.send_error(0, "Unknown package manager '" + 
                             glo_options.pmtype + "'")
      sys.exit(1)
                                                                                
   # Figure out what the package tool can do...
   arizonareport.send_out(2, "Fetching information about our packaging " + 
                           "tool (" + glo_options.pmtype + ")")
   storkpm.init_package_manager()
   """

   return args





########################### MAIN ###############################
def main():

   # process command line arguments
   args = init()
   
   # if no packages were listed, display warning message
   if len(args) == 0:
      args = ['']
      if not arizonaconfig.get_option("exact"): 
         arizonareport.send_out(2, "Warning: Building a list of all " + 
                              "packages, this may take a while...")
         arizonareport.send_out(2, "")
   
   for pack in args:
      # find matching packages for pack
      packages = filter_database(pack, arizonaconfig.get_option("exact"))
      
      # get a count of exact matches
      exact = packages.count(pack)
      
      # were there any matches?
      if len(packages) == 0 or (arizonaconfig.get_option("exact") and exact == 0):
         arizonareport.send_out(2, "")
         arizonareport.send_out(0, pack + ": No matching packages found...")
         arizonareport.send_out(0, "")
         continue
   
      # display extended info for exact matches of the package name
      if exact > 0:
         hashes = package_info(pack, None)
         arizonareport.send_out(2, "")
         for myhash in hashes:
            info = package_info(pack, myhash)
            arizonareport.send_out(0, "Package:   " + pack) 
            arizonareport.send_out(1, "Version:   " + info[0])
            arizonareport.send_out(1, "Release:   " + info[1])
            arizonareport.send_out(1, "Hash:      " + myhash)
            arizonareport.send_out(0, "Size:      " + info[2] + " bytes")
            arizonareport.send_out(0, "Filename:  " + info[3])
            arizonareport.send_out(1, arizonageneral.format_list(info[4], ", ", \
                                    "Requires:  ", "           ", None))
            arizonareport.send_out(1, arizonageneral.format_list(info[5], ", ", \
                                    "Provides:  ", "           ", None))
            arizonareport.send_out(0, "Installed: " + info[6])
            arizonareport.send_out(0, "")
         packages.remove(pack)
      
      # display "Did you mean..." output
      if not arizonaconfig.get_option("exact"): 
         if exact <= 0:
            arizonareport.send_out(2, "")
         packlen = len(packages)
         if packlen > 0:
            if packlen == 1:
               head = "Did you mean package " 
            else:
               head = "Did you mean one of the packages " 
            
            # display output, inserting newlines to avoid a very long line
            arizonareport.send_out(0, arizonageneral.format_list(packages, ", ", 
                                 head, None, "..."))
            arizonareport.send_out(0, "")       
          
   # exit
   sys.exit(0)

# Start main
if __name__ == "__main__":
   try:
      storkerror.init_error_reporting("storkquery.py")
      main()
   except KeyboardInterrupt:
      arizonareport.send_out(0, "Exiting via keyboard interrupt...")
      sys.exit(0)
