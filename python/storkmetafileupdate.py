#! /usr/bin/env python

"""
<Program Name>
   storkmetafileupdate.py

<Started>
   June 7, 2006

<Author>
   Programmed by Jeffry Johnston

<Purpose>
   Updates the metafile with hashes for metafile tarballs.
"""

#           [option, long option,      variable,       action,  data,     default,                           metavar, description]
"""arizonaconfig
   options=[["-C",   "--configfile",   "configfile",   "store", "string", "/usr/local/stork/etc/stork.conf", "FILE",  "use a different config file (/usr/local/stork/etc/stork.conf is the default)"],
            ["",     "--metafiledir",  "metafiledir",  "store", "string", "/repository/packageinfo",         "DIR",   "use the specified metafile package directory (default is /repository/packageinfo)"],
            ["",     "--metafilename", "metafilename", "store", "string", "metafile",                        "FILE",  "use the specified metafile filename (default is metafile)"],
            ["",     "--repprivatekey","repprivatekey","store", "string", None,                              "FILE",  "the private key this repository should use to sign the metafile"],
            ["",     "--metafilenamesigned", "metafilenamesigned", "store", "string", "metafile.signed",     "FILE",  "use the specified signed metafile filename (default is metafile.signed)"]]
   includes=[]        
"""

import sys
import os
import arizonaconfig
import arizonacrypt
import arizonareport
import storkpackage



def main():
   # process command line arguments
   args = arizonaconfig.init_options("storkmetafileupdate.py", configfile_optvar="configfile", version="2.0")
   if len(args) < 1:
      arizonareport.send_error(1, "Usage: storkextractmeta.py [OPTION(s)] tarball(s)")
      sys.exit(1)
   
   # prepare metafile directory and filename
   metafiledir = arizonaconfig.get_option("metafiledir")
   if metafiledir[-1] != "/": # add trailing slash if there isn't one
      metafiledir += "/" 
   if not os.path.isdir(metafiledir):   
      try:   
         os.makedirs(metafiledir)
      except OSError, e:
         arizonareport.send_error(1, "Could not create metafile directory: " + metafiledir + " (" + str(e) + ")")
         sys.exit(1)
      
   metafilename = arizonaconfig.get_option("metafilename")

   # read the existing metafile   
   try:
      f = open(metafiledir + metafilename)
      oldmetafile = f.readlines()
      f.close()
   except IOError:
      oldmetafile = [] 
   
   # add existing entries that won't be updated
   newmetafile = []
   items = [] # list of tuples in format (filepath, hash)
   for item in oldmetafile:
      itemparts = item.split()
      try:
         filename = itemparts[0]
      except IndexError:
         continue
      if not filename in args:
         # make sure the tarball exists before adding it back to the metafile
         if os.path.isfile(metafiledir + filename):
            items.append((filename, itemparts[1]))
            newmetafile.append(item)
      
   # build the new metafile entries
   for filename in args:
      arizonareport.send_out(2, "Processing: " + metafiledir + filename)
      
      # get tarball metadata 
      try:
         hash = storkpackage.get_package_metadata_hash(metafiledir + filename)
      except TypeError, e:
         arizonareport.send_error(1, "Skipping " + metafiledir + filename + " (" + str(e) + ")")
         continue
      
      # add the new entry
      items.append((filename, hash))
      newmetafile.append(filename + " " + hash + "\n")

   # write the new metafile   
   f = open(metafiledir + metafilename, "w")
   f.write("".join(newmetafile))   
   f.close()   

   # write and sign the signed metafile
   # ideally both the metafile and signed metafile would be created and then moved
   # into place at the same time
   privatekey_fn = arizonaconfig.get_option("repprivatekey")
   if not privatekey_fn:
       arizonareport.send_out(1, "No repository private key specified. Cannot create signed metafile.")
       sys.exit(1)
       
   signedmetafile_fn =  arizonaconfig.get_option("metafilenamesigned")
   f = open(metafiledir + signedmetafile_fn, "w")
   for (fn, hash) in items:
       size = str(os.path.getsize(metafiledir + fn))
       f.write(fn + " " + hash + " " + size + "\n")
   f.close()   
   
   arizonacrypt.XML_sign_file_using_privatekey_fn(metafiledir + signedmetafile_fn, privatekey_fn)
   os.chmod(metafiledir + signedmetafile_fn, 0644)


# Start main
if __name__ == "__main__":
    main()
