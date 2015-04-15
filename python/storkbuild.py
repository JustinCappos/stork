#! /usr/bin/env python

# Justin Cappos
# stork_build program
# Started: May 5, 2004

#ADD PBROOT/PBSIBLING

#           [option, long option,                variable,     action,       data,     default,                            metavar,      description]
"""arizonaconfig
   options=[
            ["-C",   "--configfile",             "configfile", "store",      "string", "/usr/local/stork/etc/stork.conf",  "FILE",       "use a different config file (/usr/local/stork/etc/stork.conf is the default)"],
            ["-P",   "--packagetype",            "pmtype",     "store",      "string", "rpm",                              "packtype",   "override the default package type"],
            ["-r",   "--rebuild",                "rebuild",    "store_true", None,     False,                              None,         "do not update the repository info files, rebuild them from scratch"],
            ["",     "--packagebuildroot",       "pbroot",     "store",      "string", "/var/packages",                    "ROOTDIR",    "prepend this directory to package build commands (default /var/packages)"],
            ["",     "--packagebuildrepository", "pbdir",      "append",     "string", None,                               "dir",        "package directory to use (the switch may appear multiple times)"],
            ["",     "--packagebuildsibling",    "pbsibling",  "store",      "string", "stork.info",                       "SIBLINGDIR", "put package information files in this subdirectory from the root (default stork.info)"],
            ["-D",   "--digest",                 "digest",     "store",      "string", "sha1",                             "dtype",      "use a different digest type (SHA1 default)"]]
   includes=[]        
"""
#            ["",     "--dbinfo",                 "dbinfo",    "store",      "string", "/usr/local/stork/var/db.info", "dir",        "directory where the database information is stored (default /usr/local/stork/var/db.info)"],

import sys
import os
import glob

import arizonaconfig
import arizonacrypt
import arizonareport
import storkpackagelist

# Make the profiler happy...
storkpm = None


def fetch_package_data(file):
   """ fetches the database information for a file
      
   needs to be changed if provides/requires change or similar items are added"""

   total_list=[]
   for field in field_list:
      if field == 'hash':
         total_list = total_list+[arizonacrypt.get_file_hash(file,arizonaconfig.get_option("digest"))]
      elif field == 'file':
         total_list = total_list+[os.path.basename(file)]
      elif field == 'provides':
         pro_list = storkpm.get_package_provides(file)
      elif field == 'requires':
         req_list = storkpm.get_package_requires(file)
      else:
         # This is a big bottleneck here... Can speed up later
         total_list = total_list +storkpm.get_package_data(file,[field])

   count = max(len(req_list),len(pro_list))
   final_list = []
   for num in range(count):
      this_item=''

      for item in total_list:
         this_item += item + storkpackagelist.field_sep

      if num < len(req_list):
         this_item += req_list[num].strip()+storkpackagelist.field_sep
      else:
         this_item += storkpackagelist.field_sep

      if num < len(pro_list):
         this_item += pro_list[num].strip()
      final_list.append(this_item)

   return final_list



def fetch_old_info(infofilename):
   """returns a list containing information about the current package data files
      """
   try:
      infofile=file(infofilename,"r")
   except IOError:
      arizonareport.send_error(1,"Cannot open previous information '"+infofilename+"'.   Rebuilding package databases from scratch")
      return []

   try:
      ret_list = []
      for line in infofile:
         if line.startswith('dir '):
            linelist = line.split()
            if len(linelist)!=3:
               raise IOError
            ret_list=ret_list+[[linelist[1],linelist[2],[]]]
         elif line.startswith('retry '):
            linelist = line.split()
            if len(linelist)!=2:
               raise IOError
            ret_list[len(ret_list)-1][2]=ret_list[len(ret_list)-1][2]+[linelist[1]]
         else:
            raise IOError
   except IOError:
      arizonareport.send_out(1,"Error parsing line:"+line+"\nRebuilding database from scratch")
      return []
   return ret_list
      

def write_new_data(infofilename,datalist):
   """Puts the new information about the current packages in the file
      """
   try:
      infofile=file(infofilename,"w")
   except IOError:
      arizonareport.send_out(1,"Cannot clobber information '"+infofilename+"'.   Attempting to clobber")
      os.remove(infofilename)

   for item in datalist:
      print >> infofile, "dir "+item[0],item[1]
      for subitem in item[2]:
         print >> infofile, "retry "+subitem
      

def get_old_info(dirname, infolist):
   """returns a pair (time, retries) that is the last time, failed packages
   """
   for info in infolist:
      if dirname==info[0]:
         return (info[1],info[2])

   return (0,[])
   




########################### MAIN ###############################


def main():
   global storkpm

   args = arizonaconfig.init_options('storkbuild.py', configfile_optvar='configfile', version="2.0")

   # Right now only use rpm...   Could change this to work with deb
   if arizonaconfig.get_option("pmtype")=='rpm':
      import storkrpm as storkpm
   else:
      arizonareport.send_error(0,"Unknown package manager '"+arizonaconfig.get_option("pmtype")+"'")
      sys.exit(1)
   
   basedir = arizonaconfig.get_option("pbroot")+"/"+arizonaconfig.get_option("pbsibling")
   if not os.path.isdir(basedir):
      os.mkdir(basedir)

   # If there are no options, build what it says in the config file...
   if not args:
      try:
         args=arizonaconfig.get_option("pbdir")
      except:
         arizonareport.send_error(0,"Error: You must list what directories to work on in the config file or on the command line")
         sys.exit(1)
   
   if arizonaconfig.get_option("rebuild"):
      # Redo everything from scratch (discard all information)
      old_info=[]
   else:
      # Read the package file (in the case of updating)
      old_info = fetch_old_info(basedir+"/storkbuild.data")

   import time
   begintime=time.time()

   new_info=[]

   for this in args:

      # find out what happened the last time (and when)
      (oldtime,oldretries) = get_old_info(this,old_info)
      
      if this.startswith("./") or this.startswith("/"):
         # Treat as an absolute path
         thispath=os.path.normpath(this)
      else:
         thispath=os.path.normpath(arizonaconfig.get_option("pbroot")+"/"+this)

      arizonareport.send_out(2,"Package directory: "+thispath)

      packs = glob.glob(thispath+'/'+storkpm.package_glob())
      if not packs:
         arizonareport.send_out(1,"Nothing to build...")

      if oldtime==0:
         pack_file=file(os.path.normpath(basedir+"/"+this+'.pkgdat'),'w')
      else:
         pack_file=file(os.path.normpath(basedir+"/"+this+'.pkgdat'),'a')

      retries=[]

      print "Building",
      for a_pack in packs:
         # if this needs to be updated (cmtime > last packaging time)
         if a_pack in oldretries or float(os.stat(a_pack)[9])>=float(oldtime):
            a_pack_data_list=[]
            try:
               a_pack_data_list += fetch_package_data(a_pack)
            except IOError:
               arizonareport.send_out(2,"\nAn I/O error occurred on "+a_pack)
               arizonareport.send_out(2,"Skipping this file")
               retries = retries + [a_pack]
               continue
            arizonareport.send_out_comma(2,".")
            arizonareport.flush_out(2)
            for dat in a_pack_data_list:
               print >> pack_file, dat
      print
      new_info = new_info + [[this,begintime,retries]]

      pack_file.close()

   # Merge the old unused information with the new stuff
   for item in old_info:
      if get_old_info(item[0],new_info)==(0,[]):
         new_info.append(item)

   # Write our the file that has been updated with this run information
   write_new_data(basedir+"/storkbuild.data", new_info)
         
   sys.exit(0)



# Start main
if __name__ == "__main__":
    main()
