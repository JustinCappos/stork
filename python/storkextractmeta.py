#! /usr/bin/env python

# Justin Cappos
# storkextractmeta.py
# Started: May 24, 2006

#           [option, long option,       variable,      action,       data,     default,                           metavar, description]
"""arizonaconfig
   options=[["-C",   "--configfile",    "configfile",  "store",      "string", "/usr/local/stork/etc/stork.conf", "FILE",  "use a different config file (/usr/local/stork/etc/stork.conf is the default)"],
            ["",     "--movetometadir", "movemetadir", "store_true", None,     False,                             None,    "after extracting metadata, move the package to a new directory containing the hash"]]
   includes=[]
"""

import os
import sys
import arizonaconfig
import arizonareport
import storkpackage
import storkpackagelist

def load_metadata(filename):
   ret_dict = storkpackagelist.load_package_metadata_fn(filename)

   # TODO: verify the file did contain metadata

   return ret_dict

def extract_metadata(files, dest_dir, copyto=None):

   # create the dest_dir if it doesn't exist
   try:
      os.makedirs(dest_dir)
   except OSError:
      pass

   # extract the metadata for each file
   for item in files:
      if item.endswith(".metalink"):
         # it's a symbolic link to a metadata file. Do not process it.
         continue

      arizonareport.send_out(1, "Extracting Metadata: " + item)
      try:
         if item.endswith(".metadata"):
             mymeta = load_metadata(item)
         else:
             mymeta = storkpackage.get_package_metadata(item)
      except TypeError, e:
         arizonareport.send_error(1, "Skipping " + item + " (" + str(e) + ")")
         continue

      metafile = storkpackage.package_metadata_dict_to_fn(mymeta, dest_dir)
      metahash = os.path.basename(metafile)

      # movemetadir is used by the repository to move files into a directory
      # named by their hash.
      if arizonaconfig.get_option("movemetadir"):
         # new path is base of the old path, plus metahash
         move_dir = os.path.join(os.path.dirname(item), metahash)

         # new filename is the move_dir plus the filename
         move_filename = os.path.join(move_dir, os.path.basename(item))

         # this string is read from stdin by the repository. Do not modify.
         arizonareport.send_out(0, move_filename);

         # create the move_dir if it doesn't exist
         try:
            os.makedirs(move_dir)
         except OSError:
            pass

         # move the package
         try:
            os.rename(item, move_filename)
         except OSError:
            pass

         # we've renamed the file, so change item to reflect the new filename
         item = move_filename

      # copyto is used by storkrepbuild to import files into a repository from
      # an outside directory.
      if copyto:
         # new path is the dest_dir
         copy_dir = os.path.join(copyto, metahash)

         # create the copy_dir if it doesn't exist
         try:
           os.makedirs(copy_dir)
         except OSError:
           pass

         # new filename is the copy_dir plus the filename
         copy_filename = os.path.join(copy_dir, os.path.basename(item))

         # copy the package
         try:
           shutil.copy( file, copy_filename)
         except:
           print "could not copy " + file + " to " + copy_filename
           pass

         # we've copied the file, so change item to reflect the new location,
         # so that the code below can create metalink in the right spot
         item = copy_filename

      # create metalink. The metalink is a symbolic link to the metadata
      # file. It is used to make life easier for storklinkrepository and
      # other tools that need to be able to get the metahash of a
      # package.
      try:
         metalink = item + ".metalink"

         # remove the old one if it exists
         try:
             os.remove(metalink)
         except OSError:
             pass

         # make a new one
         os.symlink(metafile, metalink)
      except OSError:
         arizonareport.send_error(2, "failed to create metalink symlink "+metalink)
         pass





def main(args):
   # check command line args
   if len(args) < 2:
      arizonareport.send_error(2, "Usage: storkextractmeta.py [OPTION(s)] file(s) metadestdir")
      sys.exit(1)

   # nestrpm is unnecessary and prints some useless warnings, so remove it
   # from the list of package managers
   packmans = arizonaconfig.get_option("packagemanagers")
   if 'nestrpm' in packmans:
       packmans = [packman for packman in packmans if packman != "nestrpm"]
       arizonaconfig.set_option("packagemanagers", packmans)

   # extract the metadata
   extract_metadata(args[:-1], args[-1])





# Start main
if __name__ == "__main__":
   args = arizonaconfig.init_options("storkextractmeta.py", configfile_optvar="configfile", version="2.0")
   main(args)
