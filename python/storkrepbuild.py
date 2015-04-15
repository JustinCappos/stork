#! /usr/bin/env python

# Jeremy Plichta
# storkrepbuild.py
# based on storkextractmeta.py
# Started: Dec 13, 2006

#           [option, long option,       variable,      action,       data,     default,                           metavar, description]
"""arizonaconfig
   options=[["-C",   "--configfile",    "configfile",  "store",      "string", "/usr/local/stork/etc/stork.conf", "FILE",  "use a different config file (/usr/local/stork/etc/stork.conf is the default)"],
            ["-H",   "--hostname",      "hostname",    "store",      "string", "", "STRING",                  "the hostname of the repository"],
            ["-B",   "--repositorybase",      "repbase",    "store",      "string", "/repository", "STRING",  "the base directory of the repository"],
            ["",     "--urlprefix",     "urlprefix",   "store",      "string", "", None,                      "string to insert directly after hostname when building URL"]]
   includes=[]
"""

import os
import sys
import shutil
import socket
import arizonaconfig
import arizonareport
import storkpackage
import storkpackagelist
import storkextractmeta



def translate_path(path):
    # get the hostname
    if arizonaconfig.get_option("hostname") != "":
         hostname = arizonaconfig.get_option("hostname")
    else:
         hostname = socket.gethostname()

    repbase  = arizonaconfig.get_option("repbase")

    # make a translated dest dir
    # ei: take the full path sourcepath
    # and swap out all the '/' for '_'
    # and add hostname in front of it

    urlprefix = arizonaconfig.get_option("urlprefix")
    if urlprefix:
        # make sure it has a leading slash but no trailing slash
        urlprefix = "/" + urlprefix.strip("/")
        urlprefix = urlprefix.replace("/","_")
    else:
        # set it to the empty string instead of None
        urlprefix = ""

    translate = hostname + urlprefix + os.path.abspath(path).replace(repbase,"").replace("/","_")

    return translate





def rebuild(sourcepath, metadestpath):
    if not os.path.isdir(sourcepath):
        arizonareport.send_error(1, "error: "+sourcepath+" is not a directory")
        sys.exit(1)

    if not os.path.isdir(metadestpath) and\
       not os.path.isfile(metadestpath):
        os.mkdir(metadestpath)

    elif os.path.isfile(metadestpath):
        arizonareport.send_error(1, "error: could create the directory: "+metadestpath+\
                                     "because that is the name of a file")
        sys.exit(1)

    # walk the sourcepath directory looking for files to accept
    for dirpath, dirnames, filenames in os.walk( sourcepath ):
        for file in filenames:
            if ispackage(file):
                fullfile = os.path.join(dirpath, file)
                filepath = os.path.dirname(fullfile)
                
                # the last path on here (if this is a correct)
                # existing repository should be a metahash,
                # remove this part.
                filepath = filepath[:filepath.rfind("/")]
                
                # now translate this, see the explanation
                # of translate in the next method
                translate = translate_path(filepath)
                transpath = os.path.join(metadestpath, translate)
                storkextractmeta.extract_metadata( [fullfile], transpath)
                

def addtorep(sourcepath, packagedestpath, metadestpath):
    if not os.path.isdir( metadestpath ):
        os.mkdir( metadestpath )
    if not os.path.isdir( packagedestpath ):
        os.mkdir( packagedestpath )

    translated = translate_path(packagedestpath)
    transpath  = os.path.join( metadestpath, translated )

    # if they handed us a directory
    if os.path.isdir( sourcepath ):

        
        if not os.path.isdir( transpath ):
            os.mkdir( transpath )
        
        #walk the dir looking for tar, gzs, or rpms to add
        
        for dirpath, dirnames, filenames in os.walk( sourcepath ):
            for file in filenames:
                if ispackage(file):
                    fullfile = os.path.join(dirpath, file)
                    filepath = os.path.dirname(fullfile)
                    storkextractmeta.extract_metadata([fullfile], transpath, packagedestpath)
                    
    elif os.path.isfile( sourcepath ) and ispackage(sourcepath):
        if not os.path.isdir( transpath ):
            os.mkdir( transpath )
            
        storkextractmeta.extract_metadata( [sourcepath], transpath, packagedestpath )
    
    else:
        arizonareport.send_error(1, "error: "+sourcepath+" is neither a file nor a directory")
        sys.exit(1)



def ispackage(string):
    return  "rpm" in string or \
            "tar" in string or \
            "gz"  in string or \
            "bz2" in string
    


def main(args):
   # check command oline args
   usage = """Usage: storkrepbuild.py <command> [options]
             command: 
                add         <directory or package> <packagedestdir> <metadestdir>
                rebuild     <directory> <metadestdir>"""
   


   if len(args) < 1:
      arizonareport.send_error(2, usage)
      sys.exit(1)

   command = args[0]
   
   if command == "add":
       if len(args) < 4:
           arizonareport.send_error(2, "Usage: storkrepbuild.py add <directory or package>"+\
                                       " <packagedestdir> <metadestdir>" )
           sys.exit(1)
   
       addtorep(args[1], args[2], args[3])
   
   elif command == "rebuild":
       if len(args) < 3:
           arizonareport.send_error(2, "Usage: storkrepbuild.py rebuild <repository path> <metadestdir>")
           sys.exit(1)
           
       rebuild(args[1], args[2])  
   else:
       arizonareport.send_error(2,"usage: "+usage)






# Start main
if __name__ == "__main__":
   args = arizonaconfig.init_options("storkrepbuild.py", configfile_optvar="configfile", version="2.0")
   main(args)
