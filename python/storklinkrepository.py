#!/usr/bin/python

"""
<Program Name>
   storklinkrepository.py

<Started>
   Jan 7, 2007

<Author>
   Programmed by Jeremy Plichta.

<Purpose>
    Make symlinks in a directory for all the files in the repository.
"""

"""arizonaconfig
   options=[["-C",   "--configfile",    "configfile",  "store",      "string", "/usr/local/stork/etc/stork.conf", "FILE",  "use a different config file (/usr/local/stork/etc/stork.conf is the default)"]]
   includes=[]
"""
import os
import sys
import shutil
import arizonaconfig
import arizonareport
import storkpackage

glo_known_metahash = {}

def get_metahash(file):
      """
        <Purpose>
           Given a filename, find the metahash and the filename of the metadata
           file, if a metadata file exists.

        <Returns>
           (metahash, metafilename)
      """

      global glo_known_metahash

      # if we already know the answer, return it
      if glo_known_metahash.has_key(file):
          return glo_known_metahash[file]

      metalink = file + ".metalink"

      metahash = None
      metafile = None

      # first check and see if a metalink exists. If it does, then extracting
      # the metahash can be done by looking at the link.
      if os.path.exists(metalink):
          try:
              metafile = os.readlink(metalink)
              metahash = os.path.basename(metafile)
              arizonareport.send_out(0, "loaded metahash from metalink to " + str(metafile))
          except:
              pass

      if not metahash:
          try:
              arizonareport.send_out(0, "Extracting metahash: "+os.path.basename(file))
              metadata = storkpackage.get_package_metadata(file)
          except:
              return (None, None)

          metafile_tmp = storkpackage.package_metadata_dict_to_fn(metadata, '/tmp')
          metahash = os.path.basename(metafile_tmp)
          os.unlink(metafile_tmp)

      # remember this in case this function is called again.
      glo_known_metahash[file] = (metahash, metafile)

      return (metahash, metafile)


def getLinkName(fullfile):
      """
        <Purpose>
           Give a filename, compute the name of the link that should be used
           for BitTorrent and S3.

        <Returns>
           linkname, or None if file should be skipped
      """

      file = os.path.basename(fullfile)

      metafile = None

      if ispackage(file):
         (metahash, metafile) = get_metahash(fullfile)
         if not metahash:
            return None

         linkname = file + "-" + metahash
      else:
         linkname = file

      return linkname


def copyFile_s3(fullfile):
        import storks3
        storks3.init()

        file = os.path.basename(fullfile)
        linkname=""
        if ismetadatafile(file) or ismetalinkfile(file):
            arizonareport.send_out(1, "Skipping metadata/metalink file " + file);
            return

        (metahash, metafile) = get_metahash(fullfile)

        linkname = getLinkName(fullfile)
        if not linkname:
            return

        # upload the metafile, assuming we know what it is
        if metafile:
           metalinkname = linkname + ".metadata"

           # prep some s3 metadata headers to go with the metafile. They will
           # provide enough information to link metafile to the package.
           s3MetafileMetadata = {}
           s3MetafileMetadata['kind'] = "metafile"
           s3MetafileMetadata['packagename'] = linkname
           s3MetafileMetadata['package_localname'] = fullfile
           try:
              arizonareport.send_out(1, "upload metafile to s3: " + metafile + " as " + metalinkname)
              storks3.put_file(metafile, metalinkname)
              arizonareport.send_out(1, "  success")
           except IOError, e:
               arizonareport.send_error(0, "error s3-copying: "+fullfile+": "+ str( e ) )
           except:
               arizonareport.send_error(0, "error s3-copying: "+fullfile+": "+ str( sys.exc_info()[0] ) )

        # prep some s3 metadata headers to go with the package.
        s3PackageMetadata = {}
        s3PackageMetadata['kind'] = "package"
        if metahash:
            s3PackageMetadata['metahash'] = metahash
        if metafile:
            s3PackageMetadata['metafile'] = metafile

        # upload the package
        try:
            arizonareport.send_out(1, "upload to s3: " + fullfile + " as " + linkname)
            storks3.put_file(fullfile, linkname, s3PackageMetadata)
            arizonareport.send_out(1, "  success")
        except IOError, e:
            arizonareport.send_error(0, "error s3-copying: "+fullfile+": "+ str( e ) )
        except:
            arizonareport.send_error(0, "error s3-copying: "+fullfile+": "+ str( sys.exc_info()[0] ) )


def copyFile(fullfile, targetdir):
      file = os.path.basename(fullfile)
      linkname=""
      if ismetadatafile(file) or ismetalinkfile(file):
          arizonareport.send_out(1, "Skipping metadata/metalink file " + file);
          return

      linkname = getLinkName(fullfile)
      if not linkname:
          return

      try:
         shutil.copy(fullfile, os.path.join(targetdir, linkname))
      except:
         arizonareport.send_error(0, "error copying: "+linkname+ str( sys.exc_info()[0]) )


def addLink(fullfile, targetdir):
      file = os.path.basename(fullfile)
      linkname=""
      if ismetadatafile(file) or ismetalinkfile(file):
          arizonareport.send_out(1, "Skipping metadata/metalink file " + file);
          return

      linkname = getLinkName(fullfile)
      if not linkname:
          return

      try:
         os.symlink(fullfile,os.path.join(targetdir, linkname))
      except OSError:
         arizonareport.send_error(0, "Duplicate: "+linkname)


def copyFiles(basedir, targetdir):
        for dirpath, dirnames, filenames in os.walk( basedir ):
            for file in filenames:
                fullfile = os.path.join(dirpath, file)
                copyFile(fullfile, targetdir)


def copyFiles_s3(basedir):
        for dirpath, dirnames, filenames in os.walk( basedir ):
            for file in filenames:
                fullfile = os.path.join(dirpath, file)
                copyFile_s3(fullfile)

def makeSym(basedir, targetdir):
        for dirpath, dirnames, filenames in os.walk( basedir ):
            for file in filenames:
                fullfile = os.path.join(dirpath, file)
                addLink(fullfile, targetdir)


def ismetadatafile(string):
    return string.endswith(".metadata")

def ismetalinkfile(string):
    return string.endswith(".metalink")

def ispackage(string):
    return  "rpm" in string or \
            "tar" in string or \
            "gz"  in string or \
            "bz2" in string


def main(args):
    usage = "storklinkrepository.py <sourcedir> [sourcedir2,sourcedir3,...] <destination directory>"
    addusage = "storklinkrepository.py addlink <sourcefile> <linkdir>"
    copyusage = "storklinkrepository.py copyfiles <sourcedir1> [sourcedir2....sourcedirn]  <linkdir>"
    copyoneusage = "storklinkrepository.py copy <sourcefile> <targetdir>" 
    if len(args)<2:
        arizonareport.send_error(0,usage)
        sys.exit(1)

    #just add a link for one file
    if args[0] == "addlink":
        if len(args)<3:
            arizonareport.send_error(0, addusage )
            sys.exit(1)

        if not os.path.isfile(args[1]):
            arizonareport.send_error(0, "error: "+args[1]+" is not a file")
            sys.exit(1)
        if not os.path.isdir(args[2]):
            arizonareport.send_error(0, "error: "+args[2]+" is not a directory")
            sys.exit(1)

        addLink(args[1],args[2])

    elif args[0] == "copyfiles":
        if len(args)<3:
            arizonareport.send_error(0, copyusage)
            sys.exit(1)

        numargs= len(args)
        if not os.path.isdir(args[numargs-1]):
            arizonareport.send_error(0, "error: destination dir ("+args[numargs-1]+") is not a directory")
            sys.exit(1)
        index  = 1
        while( index<numargs - 1 ):
            if os.path.isdir(args[index]):
                copyFiles(args[index], args[numargs-1])
            else:
                arizonareport.send_error(0, "Skipping: "+args[index]+", is not a directory")
            index+=1

    elif args[0] == "copyfiles_s3":
        if len(args)<3:
            arizonareport.send_error(0, copyusage)
            sys.exit(1)

        numargs= len(args)
        index  = 1
        while( index<numargs ):
            if os.path.isdir(args[index]):
                copyFiles_s3(args[index])
            else:
                arizonareport.send_error(0, "Skipping: "+args[index]+", is not a directory")
            index+=1

    elif args[0] == "copy":
        if len(args)<3:
            arizonareport.send_error(0, addusage )
            sys.exit(1)

        if not os.path.isfile(args[1]):
            arizonareport.send_error(0, "error: "+args[1]+" is not a file")
            sys.exit(1)
        if not os.path.isdir(args[2]):
            arizonareport.send_error(0, "error: "+args[2]+" is not a directory")
            sys.exit(1)

        copyFile(args[1],args[2])

    # add a link files in several directories
    else:
        numargs= len(args)
        if not os.path.isdir(args[numargs-1]):
            arizonareport.send_error(0, "error: destination dir ("+args[numargs-1]+") is not a directory")
            sys.exit(1)
        index  = 0
        while( index<numargs - 1 ):
            if os.path.isdir(args[index]):
                makeSym(args[index], args[numargs-1])
            else:
                arizonareport.send_error(0, "Skipping: "+args[index]+", is not a directory")
            index+=1




if __name__ == "__main__":
    args = arizonaconfig.init_options("storklinkrepository.py", configfile_optvar="configfile", version="2.0")
    main(args)
