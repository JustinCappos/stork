#! /usr/bin/env python
"""
<Program Name>
   s3test.py

<Started>
   6/5/07

<Author>
   Programmed by Scott Baker

<Purpose>
   Test for storks3
"""

#           [option, long option,    variable,     action,        data,     default,                            metavar, description]
"""arizonaconfig
   options=[
            ["-C",   "--configfile", "configfile", "store",       "string", "/usr/local/stork/etc/stork.conf", "FILE",   "use a different config file (/usr/local/stork/etc/stork.conf is the default)"]]
   includes=[]
"""


import arizonaconfig
import arizonareport
import storks3
import os
import sys
import shutil

def try_remove(fn):
      # remove the file if it exists
      try:
         os.remove(fn)
      except OSError:
         pass

def areyousure(prompt):
   print prompt
   print "Are you sure (y/N) ? ",
   
   result = sys.stdin.readline()
   if (result[0] != 'y') and (result[0] != 'Y'):
       print "aborted by user request"
       sys.exit(1)

def download_repo_Tar():
   # parse command line and options
   args = arizonaconfig.init_options("s3downloadrepo.py", configfile_optvar="configfile", version="2.0")

   arizonaconfig.set_option("awsbucket", "stork-repository-import")

   storks3.init()

   print "reading directory"
   storks3.dumpdir()

   print "getting repository tar files..."

   for entry in storks3.readdir():
      if not entry.key.startswith("reposplit"):
          print "   ignoring: " + entry.key
          continue

      fn = os.path.join("/mnt", entry.key)
      print "   getting " + entry.key + " to " + fn
      try:
          storks3.get_file(entry.key, fn)
      except TypeError, e:
          print "download of " + entry.key + " failed with error " + str(e) + " trying again"
          try:
              storks3.get_file(entry.key, fn)
          except TypeError, e:
              print "upload of " + entry.key + " failed with error " + str(e) + " gave up"

def upload_repo_tar():
   arizonaconfig.set_option("awsbucket", "stork-repository-import")

   areyousure("the repository tarball on S3 will be replaced")

   storks3.init()

   print "reading directory"
   storks3.dumpdir()

   print "putting repository tar files..."

   for entry in os.listdir("/mnt"):
       if entry.startswith("reposplit"):
           fn = os.path.join("/mnt", entry)
           print "  putting " + str(fn)
           try:
               storks3.put_file(fn, entry)
           except TypeError, e:
               print "upload of " + fn + " failed with error " + str(e) + " trying again"
               try:
                   storks3.put_file(fn, entry)
               except TypeError, e:
                   print "upload of " + fn + " failed with error " + str(e) + " gave up"

   print "reading directory"
   storks3.dumpdir()

def destroy_repo():
   areyousure("the repository contents on S3 will be destroyed")

   storks3.init()
   storks3.destroy()

def dump_repo():
   storks3.init()
   storks3.dumpdir()

def list_buckets():
   storks3.init()
   storks3.dumpbuckets()

def put_file(name):
   storks3.init()
   storks3.put_file(name, os.path.basename(name))

def download_repo():
   storks3.init()

   entries = storks3.readdir()
   for entry in entries:
      tempname = os.path.join("/tmp", entry.key)
      print "downloading: " + entry.key
      try:
         metadata = storks3.get_file(entry.key, tempname)
      except:
         arizonareport.send_error(0, "failed to get " + entry.key)
         continue

      kind = metadata.get("kind", None)

      local_filename = metadata.get("local-filename", None)
      if not local_filename:
          arizonareport.send_error(0, "failed to determine local filename for " + entry.key)
          continue

      # create the directory if it does not exist
      try:
         os.makedirs(os.path.dirname(local_filename))
      except OSError:
         pass

      try_remove(local_filename)

      try:
         shutil.move(tempname, local_filename)
      except OSError:
         arizonareport.send_error(0, "failed to move file to local_filename: " + local_filename)
         continue

      if kind == "package":
         metafile_name = metadata.get("metafile", None)
         if metafile_name:
            metalink_name = local_filename + ".metalink"

            # remove the old metalink symlink
            try_remove(metalink_name)

            try:
               os.symlink(metafile_name, metalink_name)
            except OSError:
               arizonareport.send_error(0, "failed to create metalink " + metalink_name + " to " + metafile_name)



def help():
   arizonareport.send_out(0,"syntax: s3tool <command>")
   arizonareport.send_out(0,"")
   arizonareport.send_out(0,"repo tarball commands:")
   arizonareport.send_out(0,"   downloadrepotar: download the repository tarball to /mnt")
   arizonareport.send_out(0,"   uploadrepotar: upload the repository tarball to /mnt")
   arizonareport.send_out(0,"")
   arizonareport.send_out(0,"repository commands:")
   arizonareport.send_out(0,"   destroy: destroy the repository")
   arizonareport.send_out(0,"   dump: list the contents of the repository")
   arizonareport.send_out(0,"   downloadrepo: download repository")
   sys.exit(1)

def main():
   # parse command line and options
   args = arizonaconfig.init_options("s3uploadrepo.py", configfile_optvar="configfile", version="2.0")

   if len(args) == 0:
      help()

   if args[0] == "downloadrepotar":
      download_repo_tar()
   elif args[0] == "uploadrepotar":
      upload_repo_tar()
   elif args[0] == "destroy":
      destroy_repo()
   elif args[0] == "dump":
      dump_repo()
   elif args[0] == "listbuckets":
      list_buckets()
   elif args[0] == "downloadrepo":
      download_repo()
   elif args[0] == "putfile":
      put_file(args[1])
   else:
      help()

if __name__ == "__main__":
   main()
