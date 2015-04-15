#! /usr/bin/env python
"""
<Program Name>
   stork.py

<Started>
   April 27, 2004

<Author>
   Programmed by Justin Cappos.  Refactored by Jeffry Johnston.

<Purpose>
   Install/remove package(s) and package dependencies.
"""


#           [option, long option,    variable,     action,        data,     default,                            metavar, description]
"""arizonaconfig
   options=[
            ["-C",   "--configfile", "configfile", "store",       "string", "/usr/local/stork/etc/stork.conf", "FILE",   "use a different config file (/usr/local/stork/etc/stork.conf is the default)"],
            ["-s",   "--simulate",   "simulate",   "store_true",  None,     False,                              None,    "simulate the action"],
            ["-R",   "--remove",     "remove",     "store_true",  None,     False,                              None,    "remove packages rather than install them"],
            ["",     "--force",      "force",      "store_true",  None,     False,                              None,    "force removal and upgrade of packages"],
            ["",     "--list",       "list",       "store_true",  None,     False,                              None,    "list all installed packages"],
            ["",     "--dumpkeys",   "dumpkeys",   "store_true",  None,     False,                              None,    "dump the public key database to stdout"],
            ["",     "--nowait",     "nowait",     "store_true",  None,     False,                              None,    "exits if another instance of stork is in progress"],
            ["",     "--whatrequires","whatrequires","store_true",  None,     False,                              None,    "list all installed packages that require a dependency"],
            ["",     "--lockdir",    "lockdir",    "store",       "string", "/var/lock",                        "dir",   "use the specified mutex lock directory (default /var/lock)"],
            ["-U",   "--upgrade",    "upgrade",    "store_true",  None,     False,                              None,    "upgrade packages listed to the first version listed in the trustedpackages file"],
            ["",     "--upgradeall", "upgradeall", "store_true",  None,     False,                              None,    "attempt to upgrade all packages"],
            ["",     "--find",       "find",       "store_true",  None,     False,                              None,    "find a package"],
            ["",  "--noupdateonstart","noupdateonstart","store_true", None, False,None, "do not try to download latest custom configuration files and keys from repository upon start of stork.py"],
            ["",     "--tpdump",     "tpdump",     "store_true",  None,     False,                              None,    "dump trusted packages data"],
            ["",     "--log",        "log",        "store_true",  None,     False,                              None,    "record package actions in the system log"],
            ["",     "--packagelogfile", "packagelogfile",     "store",        "string",       "/usr/local/stork/var/package.log",  None,       "package log file"],
            ["",     "--noinstall",  "noinstall",  "store_true",  None,     False,                              None,    "download, but do not install/update/remove anything"],
            ["",     "--timeoutput", "timeoutput", "store_true",  None,     False,                              None,    "timestamp each line of output with time since start"]]
   includes=[]
"""

import os
import errno
import sys
import arizonaconfig
import arizonageneral
import storktrustedpackagesparse
import arizonareport
import arizonatransfer
import storkpackage
import storkerror
import storkpackagelist
import storkdependency
import storkversion
import storktransaction
import storkusername
import arizonacurl
import time
import storkstatuscodes



glo_tstart = time.time()
glo_linestart = True

glo_counters = {}

def output_func_timestamp(type, verbosity, output):
    global glo_tstart
    global glo_linestart

    tnow = time.time()

    if glo_linestart and (type != "send_syslog"):
        time_str = "[%.2f] " % (tnow - glo_tstart)
        output = time_str + output

    if (type == "send_out") or (type == "send_error"):
        glo_linestart = True
    elif (type == "send_out_comma") or (type == "send_error_comma"):
        glo_linestart = False

    return output

def increment_counter(name, amount=1):
    global glo_counters

    if amount==0:
       return

    glo_counters[name] = glo_counters.get(name, 0) + amount





def format_counters():
    global glo_counters

    result = ""

    for counter in glo_counters:
        if result:
            result = result + ", "
        result = result + str(counter) + ": " + str(glo_counters[counter])

    if result:
        return "(" + result + ")"
    else:
        return ""





def exit(reason, exitstatus):

   # set an exit code if something has already been done.
   if (glo_counters.get("already installed", 0) > 0) or \
      (glo_counters.get("already upgraded", 0) > 0):
      exitstatus = exitstatus | storkstatuscodes.STATUS_ALREADY_DONE

   if glo_counters.get("not found", 0) > 0:
      exitstatus = exitstatus | storkstatuscodes.STATUS_NOT_FOUND

   # we still want to return status '0' on success, so we only add other bits
   # that indicate success (packages removed, packages installed) if we have
   # some other condition than success.
   if exitstatus != 0:
      if glo_counters.get("installed", 0) > 0:
         exitstatus = exitstatus | storkstatuscodes.STATUS_PACKAGES_INSTALLED
      if glo_counters.get("removed", 0) > 0:
         exitstatus = exitstatus | storkstatuscodes.STATUS_PACKAGES_REMOVED

   arizonareport.send_out(0, reason + " [" + str(exitstatus) + "] " + str(format_counters()))
   sys.exit(exitstatus)



   
def do_dumpkeys(args):
   storkusername.dump()





def do_list(packlist):
   """
   <Purpose>
      Lists all installed packages.

   <Arguments>
      None

   <Returns>
      None
   """

   if packlist:
      packageList = storkpackage.get_installed_versions(packlist)
   else:
      packageList = storkpackage.get_installedpackages()

   for pack in packageList:
       print pack




       
def do_upgradeall(packList):
   """
   <Purpose>
      Upgrades all installed packages.

   <Arguments>
      None

   <Returns>
      None
   """

   packageList = storkpackage.get_installedpackages()

   arizonaconfig.set_option("upgrade", True)

   packNames = []
   for pack in packageList:
       if pack.find('-'):
           pack = pack.split('-')[0]
       packNames.append(pack)

   packNames = arizonageneral.uniq(packNames)

   do_install(packNames)





def do_whatrequires(deplist):
   """
   <Purpose>
      Lists installed packages that require a dependency.
      
   <Arguments>
      deplist:
          A list of dependencies
      
   <Returns>
      None
   """
   # check params
   arizonageneral.check_type_stringlist(deplist, "deplist", "stork.do_whatrequires")

   packageList = storkpackage.get_installedpackages_requiring(deplist)

   for pack in packageList:
       print pack



def do_remove(package_list):
   """
   <Purpose>
      Removes (uninstalls) packages.

   TODO fix comment
   """
   # check params
   arizonageneral.check_type_stringlist(package_list, "package_list", "stork.do_remove")

   # remove packages
   arizonareport.send_out_comma(0, "Processing:")

   pkg_string = ", ".join(package_list)

   if arizonaconfig.get_option("simulate"):
      arizonareport.send_out(0, "\n   Would remove " + pkg_string)
   else:
      arizonareport.send_out(0, "\n   Removing packages " + pkg_string)
      try:
         storkpackage.remove(package_list, arizonaconfig.get_option("force"))
         packagelog("remove", "success", package_list)
         increment_counter("removed", len(package_list))
      except (TypeError, arizonageneral.Exception_Data):
         exc_info = sys.exc_info()
         e = exc_info[1]
         try:
            message = e.message
            removed_list = e.data[0]
            not_removed_list = e.data[1]
         except IndexError:  #changed from general exception
            e = None
         if e == None:
            raise exc_info[0], exc_info[1], exc_info[2]

         arizonareport.send_error(0, "\nAn error occurred while removing packages:\n" + str(message))
         arizonareport.send_error(0, "Packages removed: " + ", ".join(removed_list))
         arizonareport.send_error(0, "Packages NOT removed: " + ", ".join(not_removed_list))
         increment_counter("removed", len(removed_list))
         increment_counter("not removed", len(not_removed_list))
         packagelog("remove", "success", removed_list)
         packagelog("remove", "failure", not_removed_list)
         exit("Failure", 1)





def download_packages(download_list):
   if arizonareport.get_verbosity() > 1:
      width = arizonareport.console_size()[1]
      if width == None:
         width = 70
   else:
      width = 0

   arizonatransfer.reset_transfer_method()

   for pack in download_list:
      # the pack better have been previously validated before we attempt to
      # download it
      assert(pack.get('_valid', False) == True)

      pack_filename = pack['filename']

      # get the file hash
      pack_filehash = pack.get('hash', None)
      if not pack_filehash:
         arizonareport.send_error(0, "package " + str(pack) + " is missing file hash") 
         exit("Failure", 1);

      # get the canonical hash. For packages without a user-specified URL, this
      # is the same as pack['_metadatahash']. For packages with a user-specified
      # URL, it is the hash with the 'URL' entry removed.
      pack_metahash = storkpackagelist.package_metadata_dict_get_canonical_hash(pack)

      # see if the package has already been downloaded (exists in
      # /tmp) from a previous attempt.  Checks the hash to be sure.
      filename = os.path.join("/tmp", pack_filename)
      # does the file exist?
      if os.path.isfile(filename):
         # check its hash
         metahash = storkpackage.get_package_metadata_hash(filename)
         if metahash == pack_metahash:
            # hash matched!  don't download this package
            arizonareport.send_out(0, "\n   Already retrieved " + pack_filename + \
                              " with hash " + pack_metahash)
            pack['_localfilename'] = filename
            continue

      # pack['_URL'] is a list of possible URLs to retrieve the package, so
      # we'll try each one until we find a successful result.
      successful = False
      for pack_url in pack['_URL']:
         if not successful:
            got_list = []
            if arizonaconfig.get_option("simulate"):
               arizonareport.send_out(0, "\n   Would retrieve " + pack_filename +
                                    " with metahash=" + pack_metahash +
                                    ", filehash=" + pack_filehash +
                                    " from " +
                                    pack_url)
               pack['_localfilename'] = "/tmp/" + pack_metahash + "/" + pack_filename;
               successful = True
            else:
               arizonareport.send_out(0, "\n   Retrieving " + pack_filename +
                                    " with metahash=" + pack_metahash +
                                    ", filehash=" + pack_filehash + 
                                    " from " +
                                    pack_url)

               # split the URL into url_dir: everything leading up to the
               # filename and url_fn: the filename.
               (url_dir, url_fn) = os.path.split(pack_url)

               file = {'filename' : url_fn,
                       'hash' : pack_filehash,
                       'hasfuncs' : [arizonatransfer.default_hashfunc]}

               (successful, got_list) = arizonatransfer.getfiles1(url_dir,
                                        [file], "/tmp", width)

               if successful:
                  pack['_localfilename'] = got_list[0]

      # we were unable to download the package from any of the available URLs
      if not successful:
         # report errors and abort immediately
         arizonareport.send_error(0, "\n   Unable to retrieve " + pack_filename +
                                   " with hash " + pack_metahash + " from " +
                                   str(pack['_URL']))
         arizonareport.send_error(0, "Aborting installation.")
         exit("Failure", 1);





def packagelog(op, status, names):
   """
   <Purpose>
      Logs status information about packages. If the configuration option
      'packagelogfile' is set, then information will be written to a file.
      If 'log' is set then information will be written to syslog. If both
      are set, then the log will be written to both places.

   <Arguments>
      None

   <Returns>                       
      None
   """
   if not names:
      return

   # write it to the syslog if that's what the user wants
   if arizonaconfig.get_option("log"):
      try:
         for name in names:
            arizonareport.send_syslog(arizonareport.INFO, \
                                "[stork] " + op + " <" + status + "> " + name)
      except TypeError:
         arizonareport.send_error(0, "failed to write syslog")

   # write it to the log file if that's what the user wants
   fn = arizonaconfig.get_option("packagelogfile")
   if fn:
       try:
           file = open(fn, "a")
           if file:
               for name in names:
                   file.write(op + " <" + status + "> " + name + "\n")
               file.close()
       except IOError:
           arizonareport.send_error(0, "failed to write package log: " + str(fn))


def do_find(package_list):
   for pack in package_list:
      (name, ver, tags) = storkdependency.split_pack_name(pack)

      trusted_pkg_list = storkdependency.find_trusted_satisfying_packages(name, ver, tags)

      for pkg in trusted_pkg_list:
         print pkg['filename']
         print "  url: ", pkg.get("_URL", None)

def do_install(package_list):
   """
   <Purpose>
      Installs packages.  Installation is done in the following order (if
      a step fails, the next steps will not be attempted):
        1) resolve all package dependencies
        2) download any packages that need to be downloaded
        3) perform package removals
        4) perform package installations
        5) (TODO) remove temporary copies of installed packages

   TODO fix comment
   """
   # check params
   arizonageneral.check_type_stringlist(package_list, "package_list", "stork.do_install")

   # 1) resolve all dependencies
   inst_list = []
   for pack in package_list:
      # check to see if the requested package and version level is already satisfied.
      (sat_vers, unsat_vers) = storkdependency.get_installed_by_name(pack)

      if arizonaconfig.get_option("upgrade"):
          # upgrade mode, always attempt to install what the user wants 
          # regardless of whether or not it is already installed.
          if (sat_vers or unsat_vers):
              arizonareport.send_out(0, "Installed package(s) " + str(sat_vers+unsat_vers) + 
                                  " to be upgraded by " + pack)
      else:
          # install mode, don't install a package we already have
          if sat_vers:
              increment_counter("already installed");
              arizonareport.send_out(0, "Installed package(s) " + str(sat_vers) + 
                                  " already satisfies the requirement " + pack)
              continue
          # install mode, don't install if we have something that conflicts
          if unsat_vers:
              increment_counter("already installed");
              arizonareport.send_out(0, "Installed package(s) " + str(unsat_vers) +
                                  " block the requirement " + pack)
              arizonareport.send_out(0, "Use '--upgrade' to upgrade an existing package");
              continue    

      (name, ver, tags) = storkdependency.split_pack_name(pack)

      # get the dependencies necessary to satisfy this package

      #Duy Nguyen: Error report was generated because the disk was full.  This catches
      #  The exception that is thrown when there isn't enough space on disk.
      # TODO: Should we come up with a more-generic solution for catching
      #    ENOSPC? Perhaps detect it and exit in storkerror?
      try:
         cur_list = storkdependency.satisfy(name, ver, tags, arizonaconfig.get_option("upgrade"))
      except OSError,e:
         # smbaker: only print the error message on ENOSPC errors.
         if e[0] == errno.ENOSPC:
            arizonareport.send_error(0, "Error: Not enough space on disk")
            sys.exit(1)
         else:
            # if it wasn't a disk-space error, then re-raise it
            raise OSError,e

      if cur_list == None:
         increment_counter("not found")
      else:
         inst_list += cur_list

      arizonareport.send_out(2, "")

   # at this point, inst_list contains a list of packages that we want to
   # install. Any package that is an upgrade will contain a dictionary entry
   # for '_upgrade_conflicts'

   # look in the inst_list for packages that conflict with themselves; this 
   # indicates a package that is already installed and does not need upgrading.
   new_inst_list = []
   for pack in inst_list:
       if '_upgrade_conflicts' in pack:
          packname = ".".join(pack['filename'].split('.')[:-2])
          if packname in pack['_upgrade_conflicts']:
              increment_counter("already upgraded");
              arizonareport.send_out(2, "No need to upgrade '" + packname + "'")
              continue
       new_inst_list.append(pack)
   inst_list = new_inst_list

   # construct the list of packages to remove by looking at the packages to 
   # install and seeing what is marked as conflicting
   conflict_list = []
   for pack in inst_list:
       if '_upgrade_conflicts' in pack:
           conflict_list += pack['_upgrade_conflicts']

   # are there any packages left to deal with? If not, then we are done.
   if len(inst_list) == 0:
      return
   
   inst_list = arizonageneral.uniq(inst_list)

   # make sure what we're planning to remove will not break other installed
   # packages.
   abort_broken_by_removal = False
   if not arizonaconfig.get_option("force"):
       for conflict in conflict_list:
           broken_by_removal = storkdependency.get_reverse_dep(
                                                  [conflict],
                                                  conflict_list,
                                                  inst_list)
           if broken_by_removal:
               arizonareport.send_error(0, "\n   Removal of " + conflict +
                                        " would break package(s) " + str(broken_by_removal))
               abort_broken_by_removal=True
               if abort_broken_by_removal:
                  arizonareport.send_error(0, "Aborting installation.")
                  sys.exit(1)

   arizonareport.send_out_comma(0, "Downloading:")

   # 2) download any packages that need to be downloaded
   download_packages(inst_list)

   transactions = storktransaction.tl_create()
   for pack in inst_list:
      if '_upgrade_conflicts' in pack:
         storktransaction.tl_upgrade(transactions,
                                     pack['_localfilename'],
                                     pack['_upgrade_conflicts'])
      else:
         storktransaction.tl_install(transactions,
                                     pack['_localfilename'])

   if arizonaconfig.get_option("simulate") or arizonaconfig.get_option("noinstall"):
      arizonareport.send_out(0, "\nWould perform: ")
      storktransaction.tl_print(transactions)
   else:
      arizonareport.send_out(0, "\nTransaction List:")
      storktransaction.tl_print(transactions)

      try:
         arizonareport.send_out(0, "\nExecuting:")
         storkpackage.execute(transactions)

         # update statistics 
         installed_filenames = storktransaction.tl_get_filename_list(transactions, storktransaction.INSTALL)
         upgraded_filenames = storktransaction.tl_get_filename_list(transactions, storktransaction.UPGRADE)
         increment_counter("installed", len(installed_filenames))
         increment_counter("upgraded", len(upgraded_filenames))
         packagelog("install", "success", installed_filenames)
         packagelog("upgrade", "success",  upgraded_filenames)
      except (TypeError,arizonageneral.Exception_Data): #changed from general exception
         exc_info = sys.exc_info()
         e = exc_info[1]
         try:
            message = e.message
            installed_list = e.data[0]
            not_installed_list = e.data[1]
            installed_filenames = storktransaction.tl_get_filename_list(installed_list, None)
            not_installed_filenames = storktransaction.tl_get_filename_list(not_installed_list, None)
         except IndexError: #changed from general exception
            e = None
         if e == None:
            raise exc_info[0], exc_info[1], exc_info[2]

         arizonareport.send_error(0, "\nAn error occurred while installing packages:\n" + str(message))
         arizonareport.send_error(0, "Packages installed: " + ", ".join(installed_filenames))
         arizonareport.send_error(0, "Packages NOT installed: " + ", ".join(not_installed_filenames))
         increment_counter("installed", len(installed_filenames))
         increment_counter("not installed", len(not_installed_filenames))
         packagelog("install", "success", installed_filenames)
         packagelog("install", "failure", not_installed_filenames)
         exit("Failure", 1)

      # 5) remove temporary copies of installed packages
      # TODO arizonaconfig.get_option("transfertempdir"), from arizonatransfer



def wait_for_mutex():
   """
   <Purpose>
      If another copy of stork is running in the background, the wait until
      it has completed.
   """

   complained = False

   # make sure we're the only stork running
   while not arizonageneral.mutex_lock("stork", arizonaconfig.get_option("lockdir")):
      # Note: it's important that while we're looping, we only print one
      # line of output per loop, because the error report will only eliminate
      # single duplicate lines. Therefore, only complain once with the
      # "stork is already runnning" message.
      if not complained:
         complained = True
         arizonareport.send_error(0, "Another copy of stork is already running...")

      if arizonaconfig.get_option("nowait"):
         exit("Failure", storkstatuscodes.STATUS_ALREADY_RUNNING)
      else:
         # print this message on every iteration, so the user knows
         # we're still waiting
         print "Waiting for stork to finish..."
         time.sleep(15)

def init(args):
   """ TODO comment """
   # check params
   arizonageneral.check_type_stringlist(args, "args", "stork.init")

   # check for root user
   if os.geteuid() > 0:
      arizonareport.send_error(0, "You must be root to run this program...")
      exit("Failure", storkstatuscodes.STATUS_ERROR)

   # set up package list
   # note that this may have been already initialized by arizonacurl
   if not storkpackagelist.glo_initialized:
      storkpackagelist.init()

   # set up trustedpackages file
   if not arizonaconfig.get_option("disable_tpf"): 
      storktrustedpackagesparse.init()

   # look up each "package name" in the package list.  the user may have 
   # given a filename by mistake, so we want to convert filenames to
   # real package names, if possible.
   new_args = []  
   for name in args:
      # the user may have used a relational operator (=,>,etc) in the package
      # name. We'll check both the full name, and the name without the relop.
      (name_only, ver, tags) = storkdependency.split_pack_name(name)
      
      if (not storkpackagelist.package_exists(name)) and  \
            (not storkpackagelist.package_exists(name_only)):
         arizonareport.send_error(2, "Warning: A package named `" + name + \
                                     "' does not exist.\n         Attempting filename match.")
         try:
            packname = storkpackagelist.find_package_name(name)
         except TypeError, e:
            arizonareport.send_error(0, str(e))
            sys.exit(1)
            
         if packname != None:
            # found a match
            arizonareport.send_error(2, "Warning: Using package name `" + \
                                        packname + "' instead of `" + \
                                        name + "'.\n")
            new_args.append(packname)
         else:
            # couldn't find anything, but try the original name anyway
            new_args.append(name)
      else:
         new_args.append(name)

   return new_args





########################### MAIN ###############################
def main(args):
   """ TODO comment """

   global glo_exitstatus;

   # check params
   arizonageneral.check_type_stringlist(args, "args", "stork.main")

   # process command line and initialize variables
   args = init(args)

   # build up a list of operations the user has specified. The user is only
   # supposed to ask for one of these, so if he wants more than one, we
   # can complain.
   mode = []
   if arizonaconfig.get_option("remove"):
      mode.append("remove")
      op = do_remove
   if arizonaconfig.get_option("whatrequires"):
      mode.append("whatrequires")
      op = do_whatrequires
   if arizonaconfig.get_option("list"):
      mode.append("list")
      op = do_list
   if arizonaconfig.get_option("tpdump"):
      mode.append("tpdump")
      op = storktrustedpackagesparse.TrustedPackagesDump
   if arizonaconfig.get_option("upgrade"):
      mode.append("upgrade")
      op = do_install
   if arizonaconfig.get_option("upgradeall"):
      mode.append("upgradeall")
      op = do_upgradeall
   if arizonaconfig.get_option("dumpkeys"):
      mode.append("dumpkeys")
      op = do_dumpkeys
   if arizonaconfig.get_option("find"):
      mode.append("find")
      op = do_find

   # if the user didn't say what he wanted, then lets assume he wants
   # to install
   if not mode:
      mode.append("install")
      op = do_install

   # complain if the user asked for more than one thing
   if len(mode)>1:
      arizonareport.send_error(0, "ERROR: you may use only one of " +
                                  ",".join(mode))
      exit("Failure", 1)

   # now perform the operation
   op(args)

   exit("Success", 0)






# Start main
if __name__ == "__main__":
   try:
      # use error reporting tool
      storkerror.init_error_reporting("stork.py")

      # get command line and config file options
      args = arizonaconfig.init_options("stork.py", configfile_optvar="configfile", version=storkversion.VERREL)

      if arizonaconfig.get_option("timeoutput"):
          arizonareport.set_output_function(output_func_timestamp)

      if os.geteuid() > 0:
          arizonareport.send_error(0, "You must be root to run this program...")
          sys.exit(1)

      # smbaker: wait for mutex before doing arizonacurl update, to prevent
      # multiple storks from downloading keys/config files
      wait_for_mutex()


      # attempt to fetch the users pub key and configuration
      # files
      if not arizonaconfig.get_option("noupdateonstart"):
          #Duy Nguyen:  If there is no more space on disk, arizonacurl can't use the temp directories.
          #           This catches the exception that is thrown and notifies the user that there
          #           is a problem with the disk space or temp directories
          try:
             restart = arizonacurl.fetch_conf()
          except IOError:
             arizonareport.send_error(0, "Unable to find usable temp directories: Check permissions/Disk Space")
             sys.exit(1)

          if restart:
              args = arizonaconfig.init_options("stork.py",configfile_optvar="configfile",version="2.0")
              #username = arizonaconfig.get_option("username")
              #arizonareport.send_out(0,"just updated configuration file. username="+username)

          restart = arizonacurl.fetch_pubkey()
          if restart:
             # tell stork username it needs to reload its key database
             storkusername.reset_key_database()
             # TODO: public keys have changed, so we need to need to go back and
             # try arizonacurl.fetch_conf() using the new public key. Note:
             # watch out for endless loop / cycle. 


      #import hotshot
      #p = hotshot.Profile("stork.profile", 1, 1)
      #p.runcall(main, args)
      #p.close()
      main(args)
   except KeyboardInterrupt:
      arizonareport.send_out(0, "Exiting via keyboard interrupt...")
      sys.exit(0)
