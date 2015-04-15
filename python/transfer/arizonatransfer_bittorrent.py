#! /usr/bin/env python
"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: arizonatransfer_bittorrent
Description:   Provides a general file transferring via BitTorrent

"""

"""arizonaconfig
options=[['',"--bittorrenttrackerhost","arizonabittorrenttrackerhost","store","string","quadrus.cs.arizona.edu","TrackerHost","The host name of the tracker server."],
         ['',"--bittorrenttrackerport","arizonabittorrenttrackerport","store","int",6880,"TrackerPort","The number to specify as the tracker port number for torrents."],
         ['',"--bittorrentuploadrate","arizonabittorrentuploadrate","store","int",0,"UploadRate","The max upload rate for the bittorrent processes (0 means no limit)."],
         ['',"--bittorrentseedlookuptimeout","arizonabittorrentseedlookuptimeout","store","int",30,"SeedLookupTimeout","The number of seconds bittorrent should timeout after not finding a seed."]]
includes=[]
"""

import arizonareport
import time
import os
import urllib,urllib2, math, random, sys, os, socket, string
import arizonaconfig

from storkbtdownloadheadless import *

def log_transfer(function, pid, timestamp, timestampend):
   try:
      import storklog
      storklog.log_transfer(function, pid, timestamp, timestampend)
   except:
      pass

#default settings list
defaultset=[60,"/tmp/aztorrents/files","/tmp/aztorrents/updates",0,True,"quadrus.cs.arizona.edu",6880,30]

# Makes the profiler stop complaining...
glo_filename = ''
glo_confname = "/tmp/aztorrents/btshare.conf"
glo_daemonname = "/etc/init.d/storkbtsharedaemon"
glo_updatedir = defaultset[2]

def get_option(optname,default=None):
   """
   <Purpose>
      A small wrapper for the arizona_config.get_option method.

   <Arguments>
      None.
   
   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      True.
   """
   ret=arizonaconfig.get_option(optname)
   if ret is None:ret=default
   return ret

def close_transfer_program():
   """
   <Purpose>
      This closes a connection (dummy function for BitTorrent).

   <Arguments>
      None.
   
   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      True.
   """
 
   return True



def init_transfer_program(ignore=None, ignore2=None, ignore3=None, ignore4=None):
   """
   <Purpose>
      This initializes a connection (dummy function for BitTorrent).

   <Arguments>
      None.
   
   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      True.
   """
   return True

def ensure_settings(checkinterval=60,filedir="/usr/local/stork/torrents/files",updatedir="/usr/local/stork/torrents/updates",uploadrate=0,sharing=True):
   """<Purpose>
   ensures that the current instance of the torrent sharing program has the correct settings
and also stops or starts the instance of the sharing program depending on sharing status

<Arguments>
   checkinterval:
      how frequently the sharing program should check the update directory
      (default=60)
   filedir:
      the directory where the sharing program should look for downloaded files
      (default="/usr/local/stork/torrents/torrents")
   updatedir:
      the directory where the sharing program should check for torrent files
      (default="/usr/local/stork/torrents/updates")
   uploadrate:
      the maximum rate set for uploading (and therefore downloading) files (0 means no max)
      (default=0)
   sharing:
      whether or not the sharing program should be running
      (default=True)

<Exceptions>
   None.

<Side Effects>
   writes to the file in glo_confname and may start/stop/restart the storkbtshare daemon

<Returns>
   None.

<Comments>
   None.
"""
   global glo_confname
   global glo_daemonname
   global defaultset
   altered=False

   #exists can throw an exception if the directory doesn't exist
   try:os.path.exists(glo_confname)
   except:
      os.makedirs(glo_confname[:glo_confname.rfind('/')])
   
   if os.path.exists(glo_confname):
      fo=open(glo_confname)
      rd=fo.readlines()
      fo.close()
      ccheckint=None
      cfiledir=None
      #cdestdir=None
      cuploadrate=None
      cupdatedir=None
      #cforcedshareduration=None
      for i in rd:
         s=i.split("=")
         s[0]=s[0].strip()
         s[1]=s[1].strip()
         if s[0]=="checkinterval":
            ccheckint=s[1]
            if s[1]!=str(checkinterval):altered=True
         elif s[0]=="filedir":
            cfiledir=s[1]
            if s[1]!=filedir:altered=True
         #elif s[0]=="downloaddir":
         #   cdestdir=s[1]
         #   if s[1]!=destdir:altered=True
         elif s[0]=="updatedir":
            cupdatedir=s[1]
            if s[1]!=updatedir:altered=True
         elif s[0]=="uploadrate":
            cuploadrate=s[1]
            if s[1]!=str(uploadrate):altered=True
         #elif s[0]=="forcedshareduration":
         #   cforcedshareduration=s[1]
         #   if s[1]!=forcedshareduration:altererd=True
      if not altered:
         #check if the settings are missing and the settings passed to this function are different than the defaults
         if ccheckint is None and checkinterval!=defaultset[0]:altered=True
         if cfiledir is None and filedir!=defaultset[1]:altered=True
         #if cdestdir is None and destdir!="/tmp":altered=True
         if cupdatedir is None and updatedir!=defaultset[2]:altered=True
         if cuploadrate is None and uploadrate!=defaultset[3]:altered=True
         #if cforcedshareduration is None and forcedshareduration!=-2.0:altered=True
   elif checkinterval!=defaultset[0] or filedir!=defaultset[1] or updatedir!=defaultset[2] or uploadrate!=defaultset[3]: #or destdir!="/tmp" 
      altered=True
   if altered:#save the settings
      fo=open(glo_confname,"w")
      fo.write("checkinterval="+str(checkinterval)+"\n")
      fo.write("torrentdir="+filedir+"\n")
      #fo.write("downloaddir="+destdir+"\n")
      fo.write("updatedir="+updatedir+"\n")
      fo.write("uploadrate="+str(uploadrate)+"\n")
      #fo.write("forcedshareduration="+forcedshareduration+"\n")
      fo.close()
   #restart the daemon
   #is it running?
   po=os.popen(glo_daemonname+" status")
   rd=po.read()
   po.close()
   running="running" in rd.lower()
   if altered and sharing and not running:os.popen(glo_daemonname+" start").close()
   elif altered and sharing and running:os.popen(glo_daemonname+" restart").close()
   elif sharing and not running:os.popen(glo_daemonname+" start").close()
   elif not sharing and running:os.popen(glo_daemonname+" stop") .close()

def make_torrent(filename,destfile,host,port):
   """
   <purpose>
      Creates torrent files from the given arguments.  The torrent file should be saved as filename.
   <arguments>
      filename
         the file to save the torrent as
      destfile
         the file to make the torrent from
      host
         the host name of the tracker (should not include the port or protocol)
      port
         the port the tracker is running on
   """   
   os.popen("/usr/bin/btmaketorrent.py --target "+filename+" http://"+host+":"+str(port)+"/announce "+destfile).close()

def retrieve_files(host, filelist, destdir='.', indicator=None):
   """
   <Purpose>
      This retrieves files from a host to a destdir.

   <Arguments>
      host:
         'host' holds two things, a server name and target directory.
         For example, if you want to retrieve files from '/tmp/' directory
         in 'quadrus.cs.arizona.edu' server, the 'host' will be
         'quadrus.cs.arizona.edu/tmp'.         

      filelist:
         'filelist' is a list of files which need to be retrieved.

      junk_hashlist:
         'junk_hashlist' is a list of the hashes for this list of files.
         It should be a list of strings.

      destdir:
         'destdir' is a destination directory where retrieved files will 
         be placed. A user should have 'destdir' exist before retrieving 
         files. 'destdir' should be a string. Default is a current dir.

      indicator:
         'indicator' is a module which has set_filename and
         download_indicator functions. 'indicator' will be passed in 
         'urlretrieve' function so that progress bar will be shown 
         while downloading files. Default is 'None'.

   <Exceptions>
      All exceptions should be caught.

   <Side Effects>
      If the storkbtshare daemon is set to be running, this method will create
      hard links, torrent files, and ensure that the daemon is running.

   <Returns>
      (True, grabbed_list)
      'grabbed_list' is a list of files which are retrieved
   """
   global defaultset
   # set grabbed_list as a empty list. Later it will be appended with retrieved files
   grabbed_list = []

   #arizonareport.send_out(3, "[Bittorrent Debug]: retrieve_files: "+str(filelist)+" "+str(junk_hashlist) )
   # hack to make bt work
   try:
      def errorfunc():
          pass
      from BitTorrent.ConvertedMetainfo import set_filesystem_encoding
      set_filesystem_encoding("ascii", errorfunc)
   except:
      pass

   # check if host is a string   
   if not isinstance(host, str):
      arizonareport.send_syslog(arizonareport.ERR, "retrieve_files(): host should be a string")
      # return false and empty list
      return (False, grabbed_list)
   
   # check if filelist contains only strings
   # Later should just use something like justin.valid_sl   TODO!!!
   # TODO - check for valid tuple list
   #if not valid_sl(filelist):
   #   arizonareport.send_syslog(arizonareport.ERR, "retrieve_files(): filelist should be a list of strings")
   #   # return false and empty list
   #   return (False, grabbed_list)
   
   # check if destdir is a string
   if not isinstance(destdir,str):
      arizonareport.send_syslog(arizonareport.ERR, "retrieve_files(): destdir should be a string")
      # return false and empty list
      return (False, grabbed_list)

   # check that the destination directory exists  
   if not os.path.isdir(destdir):
      arizonareport.send_syslog(arizonareport.ERR, "\nretrieve_files(): The destination directory '" + destdir + "' for a requested does not exist")
      # return false and empty list
      return (False, grabbed_list)

   # if destdir is a empty string, then make it as a current directory
   if destdir == '':
      destdir = '.'

   #verify the connection and that the directory exists
   # this has issues with this transfer stub due to the way bittorrent may
   #  interoperate with certain standard modules (and possibly their naming
   #  conventions).
   #if not __verify_connection(host):
   #   # return false and empty list
   #   return (False, grabbed_list)





   #make sure the sharing program is working:
   set=defaultset[:]#[60,"/usr/local/stork/torrents/files","/usr/local/stork/torrents/updates",0,True,"quadrus.cs.arizona.edu",6880,30]

   set[0]=get_option("arizonabittorrentcheckinterval",set[0])
   set[1]=get_option("arizonabittorrentfiledir",set[1])
   set[2]=get_option("arizonabittorrentupdatedir",set[2])
   glo_updatedir=set[2]
   set[3]=get_option("arizonabittorrentuploadrate",set[3])
   set[4]=get_option("arizonabittorrentsharing",str(set[4])).lower().strip()=="true"
   set[5]=get_option("arizonabittorrenttrackerhost",set[5])
   set[6]=get_option("arizonabittorrenttrackerport",set[6])
   set[7]=get_option("arizonabittorrentseedlookuptimeout",set[7])

   #the share daemon should take care of itself now.
   #ensure_settings(set[0],set[1],set[2],set[3],set[4])

   #make sure the torrent and update directories exist
   if not os.path.isdir(set[1]):
      os.makedirs(set[1])
   if not os.path.isdir(set[2]):
      os.makedirs(set[2])

   # go through every file in the file list
   for file in filelist:
      filename = file['filename']
      hash = file.get('hash', None)

      if hash:
         filename = "/" + hash + "/" + filename

      starttime = time()

      # build url which specifies host and filename to be retrieved
      thisurl = __build_url(host,filename)

      # find the name of the torrent file and its directory
      ufilename=thisurl[thisurl.rfind('/')+1:]
      #make sure it's the right length:
      if len(ufilename)>255:ufilename=ufilename[-255:]
      udir=thisurl[:thisurl.rfind('/')]                   
      #find the real file name to download to
      rfilename=filename[filename.rfind('/')+1:]

      #to allow for multiple users to have differing files of the same name and still
      # find and use the corrent .torrent file, the torrent file names are long enough to
      # hopefully include enough of the file's subdirectory(ies) to be distinguishable.
      tfilename=ufilename+".torrent"
      #since python cannot handle files with names longer than 255 characters, cut off the front characters
      # (this will keep the hash)
      if len(tfilename)>255:tfilename=tfilename[-255:]

      #arizonareport.send_out(3, "[Bittorrent Debug]: about to try to download: "+udir+"/"+tfilename )

      # download the file
      btargs=["storkbtdownloadheadless.py","--display_interval","4.0", "--max_upload_rate", str(set[3]),"--save_as",destdir+"/"+rfilename,"--url",udir+'/'+tfilename]

      # if the file already exists, it must be unlinked to avoid possible errors with overwriting hard-linked files
      #if os.path.exists(destdir+"/"+rfilename):
      #   os.unlink(destdir+"/"+rfilename)

      prog_indic=None

      #try downloading
      status=-1

      # if an idicator is passed in
      if (indicator):
         # make indicator_file store a file name which will be used in download_indicator function
         indicator_file = rfilename
         try:
            # set the filename so that indicator module can use the name to show for progress bar
            indicator.set_filename(indicator_file)
         # indicator doesn't have method set_filename or download_indicator
         except AttributeError:
            arizonareport.send_syslog(arizonareport.ERR, 'retrieve_files(): indicator module passed in is incorrect')
            return (False, grabbed_list)
         # if indicator_file which used for set_filename is not a string
         except TypeError:
            arizonareport.send_syslog(arizonareport.ERR, 'retrieve_files(): indicator_file is incorrect')
            return (False, grabbed_list)
         prog_indic=indicator.download_indicator
         arizonareport.send_out(3, "")
      try:
         #operating in quiet mode - only output should be via the progess indicator.
         #try this when assured the that host argument is correct:
         #status=btdownloadheadless(btargs,host,6969,1,prog_indic)
         status=btdownloadheadless(btargs,set[5],set[6],1,prog_indic,0,None,set[7])
      except IOError,e:
         arizonareport.send_syslog(arizonareport.ERR, "retrieve_files(): azbt - error reading torrent file: " + str(e))
         return (False, grabbed_list)
      except BTFailure,e:
         arizonareport.send_syslog(arizonareport.ERR, "retrieve_files(): azbt - "+str(e))
         return (False, grabbed_list)

      if status==1:#sucess should mean that it exists
         grabbed_list.append(file)
         endtime = time()
         storklog.log_transfer("bittorrent",str( os.getpid() ), str(starttime), str(endtime) )
         #taken care of by the share daemon:
         #if it's sharing make a torrent and hard link in the appropriate directories
         #if set[4]:
         #    #make a hard link
         #    os.popen("/bin/ln "+destdir+"/"+rfilename+" "+set[1]+"/"+ufilename).close()
         #    #make a torrent for it
         #    make_torrent(set[2]+"/"+tfilename,set[1]+"/"+ufilename,set[5],set[6])
      else:#an error must have occurred?
         arizonareport.send_syslog(arizonareport.ERR, "retrieve_files(): azbt - unknown transfer error: success= "+str(status))
         return (False, grabbed_list)

      # TODO FIXME? commented this out because blank lines were appearing in the stork output - JLJ
      #arizonareport.send_out(0, "")

   if (grabbed_list) :
      return (True, grabbed_list)
   # if nothing in grabbed_list
   else:
      return (False, grabbed_list)

def transfer_name():
   """
   <Purpose>
      This gives the name of this transfer method.

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      'arizona_bittorrent' as an string
   """

   return 'arizona_bittorrent'



def __build_url(host,fname):
   """
   <Purpose>
      This builds a url string with Http address.

   <Arguments>
       host:
         'host' holds two things, a server name and target directory.
         For example, if you want to retrieve files from '/tmp/' directory
         in 'quadrus.cs.arizona.edu' server, the 'host' will be
         'quadrus.cs.arizona.edu/tmp'.
      fname:
         A file name to be retrieved
   
   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      A whole url string created

   <Comments>
      This function changes the URL to be virtually that of the torrent file.
   """
   
   # remove the 'http://' or 'ftp://'
   host = host.replace("ftp://", "")      
   host = host.replace("http://","")

   #remove the directory information on the host
   # and replace it with the torrent directory
   dir = "/torrents/"
   dpos=host.find("/")
   if dpos!=-1:
       host=host[:dpos]

   # make the fname into a single filename using the final hash/directory of the filename
   #arizonareport.send_out(3, "[Bittorrent Debug]: __build_url fname="+fname)
   fpos=fname.rfind('/')
   fpos2=fname.rfind('/',0,fpos)
   #arizonareport.send_out(3, "[Bittorrent Debug]: __build_url fpos="+str(fpos)+", fpos2="+str(fpos2) )
   if not fpos==-1:
       fname=fname[fpos+1:]+'-'+fname[fpos2+1:fpos]
   
   # return url which contains host and filename
   # should now look like: http://quadrus.cs.arizona.edu/torrents/file.rpm-hash
   return "http://" + host + dir + fname

          
      
def __verify_connection(host):
   """
   <Purpose>
      This verifies a connection, testing a host and target directory.

   <Arguments>
      host:
         'host' holds two things, a server name and target directory.
         For example, if you want to retrieve files from '/tmp/' directory
         in 'quadrus.cs.arizona.edu' server, the 'host' will be
         'quadrus.cs.arizona.edu/tmp'.
            
   <Exceptions>
      urllib2.URLError:
         If host name is incorrect or host is dead, then return False

      urllib2.HTTPError:
         If given target directory is incorrect, then return False

   <Side Effects>
      None.

   <Returns>
      True or False (see above)
   """
   
   # split host into server name and directory
   host.replace("http://","")
   host.replace("ftp://","")
   index = host.find('/')
   # set hostname to hold only a server name
   if index != -1:
      hostname = host[:index]
   else :
      hostname = host   

   # checking only host
   #the port number is for the odd bittorrent imports which interfere with
   # the regular usage of urllib2.urlopen
   checkurl = __build_url("http://"+hostname+"80", "")

   # urllib2 is used since urllib doestn't offer a nice way to check the connection is valid
   try :
      urllib2.urlopen(checkurl)
   # incorrect host name or host is dead
   except urllib2.URLError, (msg):      
      arizonareport.send_syslog(arizonareport.ERR, '__verify_connection(): "' + hostname + '" '+ str(msg).split("'")[1])
      return False


   # checking if the directory exists in the server
   checkurl = __build_url(host, "")
   try:
      urllib2.urlopen(checkurl)
   # if the directory doesn't exist in the server
   except urllib2.HTTPError, (strerror):
      arizonareport.send_syslog(arizonareport.ERR, '__verify_connection(): "' + str(strerror) + '" on the url "' + checkurl + '"')
      return False

   # everything is fine       
   return True
   



# TODO: should go away!!!
def valid_sl(stringlist):
   """
   <Purpose>
      This returns True if stringlist is a list of strings or False if it is 
      not.

   <Arguments>
      stringlist:
          The variable to be checked.

   <Exceptions>
      None

   <Side Effects>
      None

   <Returns>
      True or False (see above)
   """

   # If it's a list
   if isinstance(stringlist,list):

      for item in stringlist:
         # If an item in the list isn't a string then False
         if not isinstance(item,str):
            return False
      else:
         # It's a list of strings so True
         return True
   else:
      # Not a list so false
      return False

   
