#! /usr/bin/python

# The contents of this file are subject to the BitTorrent Open Source License
# Version 1.0 (the License).  You may not copy or use this file, in either
# source code or executable form, except in compliance with the License.  You
# may obtain a copy of the License at http://www.bittorrent.com/license/.
#
# Software distributed under the License is distributed on an AS IS basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied.  See the License
# for the specific language governing rights and limitations under the
# License.

# Written by John Hoffman, altered for use with the Stork project by Jason Hardies

import sys
import os

from BitTorrent.launchmanycore import LaunchMany
from BitTorrent.defaultargs import get_defaults
from BitTorrent.parseargs import parseargs, printHelp
from BitTorrent import configfile
from BitTorrent import version
from BitTorrent import BTFailure

import socket
from time import time as currenttime
from time import sleep

import arizonaconfig

from threading import Thread
import string

#        [option, long option,                        variable,                                action,  data,     default,                           metavar,              description]
"""arizonaconfig
options=[['',     "--bittorrentcheckinterval",        "arizonabittorrentcheckinterval",        "store", "float",  60.0,                              "CheckInterval",      "change the interval that the storkbtshare.py program is set to check for new files at."],
         ['',     "--bittorrentfiledir",              "arizonabittorrentfiledir",              "store", "string", "/tmp/aztorrents/files",           "FileDirectory",      "the local directory to look for files to be shared."],
         ['',     "--bittorrentupdatedir",            "arizonabittorrentupdatedir",            "store", "string", "/tmp/aztorrents/updates",         "UpdateDirectory",    "The directory the sharing daemon will place/look for torrent files."],
         ['',     "--bittorrentignoredirs",           "arizonabittorrentignoredirs",           "store", "string", "True",                            "IgnoreDirs",         "A True/False value indicating whether the sharing daemon should ignore folders found in the file directory."],
         ['',     "--bittorrentsharing",              "arizonabittorrentsharing",              "store", "string", "True",                            "Sharing",            "The boolean value indicating whether or not the storkbtshare daemon should be running."],
         ['',     "--bittorrenttrackerhost",          "arizonabittorrenttrackerhost",          "store", "string", "quadrus.cs.arizona.edu",          "TrackerHost",        "The host name of the tracker server."],
         ['',     "--bittorrenttrackerport",          "arizonabittorrenttrackerport",          "store", "int",    6880,                              "TrackerPort",        "The number to specify as the tracker port number for torrents."],
         ['',     "--bittorrentuploadrate",           "arizonabittorrentuploadrate",           "store", "int",    0,                                 "UploadRate",         "The max upload rate for the bittorrent processes (0 means no limit)."],
         ['',     "--bittorrentsharelogging",         "arizonabittorrentsharelogging",         "store", "string", "False",                           "BTShareLogging",     "A string true/false value indicating whether the BT sharing daemon should be logging."],
         ['',     "--bittorrentsharelogginginterval", "arizonabittorrentsharelogginginterval", "store", "int",    10,                                "BTShareLoggingRate", "The seconds between regular logging intervals for the BT sharing daemon."],
         ['',     "--bittorrentshareconfig",          "arizonabittorrentshareconfig",          "store", "string", "/usr/local/stork/etc/stork.conf", "BTShareConfig",      "The filename/path of the config file for the sharing daemon."]]
includes=[]
"""

#default settings list
defaultset=[60,"/tmp/aztorrents/files","/tmp/aztorrents/updates",0,True,"quadrus.cs.arizona.edu",6880,30,"False",10]

glo_logging = False
glo_log="/var/log/storkbtshare.log"
#glo_confname = "/tmp/aztorrents/btshare.conf"
glo_daemonname = "/etc/init.d/storkbtsharedaemon"
glo_possibleserverdomain=".cs.arizona.edu"
glo_stillalive=True

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

exceptions = []

class HeadlessDisplayer:
    def display(self, data):
        global glo_logging
        global glo_log
        if glo_logging:
            lo=open(glo_log,"a")
            lo.write(str(currenttime())+"\n")
            if not data:
                self.message('no torrents')
            for x in data:
                ( name, status, progress, peers, seeds, seedsmsg, dist,
                  uprate, dnrate, upamt, dnamt, size, t, msg ) = x
                lo.write( '"%s": "%s" (%s) - %sP%s%s%.3fD u%0.1fK/s-d%0.1fK/s u%dK-d%dK "%s" \n' % (
                            name, status, progress, peers, seeds, seedsmsg, dist,
                            uprate/1000, dnrate/1000, upamt/1024, dnamt/1024, msg) )
            lo.close()
        return False

    def message(self, s):
        global glo_logging
        global glo_log
        if glo_logging:
            lo=open(glo_log,"a")
            lo.write(str(currenttime())+"\n")
            lo.write("### "+s+"\n")
            lo.close()

    def exception(self, s):
        exceptions.append(s)
        self.message('SYSTEM ERROR - EXCEPTION GENERATED')


#modified for use with storkbtshare
def daemonize(program,log):
    """ 
      Turns the currently running program into a daemon, detaching it from
      the console so that it runs in the background.  

      program:
              Filename (not including path) of the program being turned 
              into a daemon.  Used for logging, error reporting, and to 
              write the pid of the daemon to `/var/run/PROGRAM.pid'. 
      log:
              Filename of the log to be used.
     TypeError if a bad parameter is detected.
     Terminates the program if the command fails.
     Returns pid of the daemon
    """

    if not log is None and log=="": log is None
    flog = None
    if log and os.path.isdir(os.path.split(log)[0]):    
        flog = open(log,"a")
        # log what we're about to do and fork
        flog.write(str(currenttime())+"\nDaemonizing:now\n")
        flog.flush()
    pid = os.fork()

    # if fork was successful, exit the parent process so it returns 
    try:
        if pid > 0:
            os._exit(0) 
    except OSError:
        if not log is None:
            flog.write(str(currenttime())+"\nERROR: fork failed, daemon not started")
            flog.flush()
            flog.close()
            sys.exit(1) 
            
    # Print my pid into /var/run/PROGRAM.pid
    #unnecessary for testing:
    pid = str(os.getpid())
    filename = "/var/run/" + program + ".pid"
    try:
        out_file = open(filename, "w")
        out_file.write(pid)
        out_file.close()
    except IOError:
        if not log is None:
            flog.write(str(currenttime())+"\nERROR: IOError writing pid "+filename)
            flog.flush()

    # close any open files 
    sys.stdin.close()
    sys.stdout.close()
    sys.stderr.close()
    for i in range(1023):
        try:
            os.close(i)
        except OSError:
            pass
         
    # redirect stdin to /dev/null
    # redirect stdout/err to log files.
    sys.stdin = open('/dev/null')       # fd 0
    #sys.stdout = open(program+'.pyout', 'w') # fd 1
    #sys.stderr = open(program+'.pyerr', 'w') # fd 2
    sys.stdout = open('/dev/null') # fd 1
    sys.stderr = open('/dev/null') # fd 2
    
   
    # disassociate from parent 
    os.chdir(os.environ["HOME"]) #must maintain the home directory to keep the logs together
    os.setsid()
    os.umask(0) 
    try:
        if not log is None:flog.close() # might have been closed by the os.close(#) for loop
    except:pass
    return pid

def make_torrent_filename(filename):
    dir=filename[:filename.rfind("/")]*('/' in filename)
    filename=filename[filename.rfind("/")+1:]+".torrent"
    if len(filename)>255:filename=filename[-255:]
    return dir+"/"*(dir!='')+filename

def make_torrent(host,port,filename,dir):
    """
   <purpose>
      Creates torrent files from the given arguments.  The torrent file should be saved as filename.
   <arguments>
      host
         the host name of the tracker (should not include the port or protocol)
      port
         the port the tracker is running on
      filename
         the file to make the torrent from
      dir
         the dir to make the new torrent file in
    """
    tfilename=make_torrent_filename(filename)
    if not os.path.exists(dir) or not os.path.isfile(filename):
        raise Exception("Torrent directory or file does not exist:"+str(dir)+" : "+filename)
    po=os.popen("/usr/bin/btmaketorrent.py --target "+dir+"/"+tfilename[tfilename.rfind("/")+1:]+" http://"+host+":"+str(port)+"/announce "+filename)
    #return True #should really do error checking on the return value of btmaketorrent to give more validity to this
    lines=po.readlines()
    po.close()
    if "IOError:" in lines[-1]:
        raise Exception(lines[-1])
    if os.path.exists(dir+'/'+tfilename[tfilename.rfind("/")+1:]):return True
    return False

class TorrentMakerTimer(Thread):
    def __init__(self,checkint,filedir,torrentdir,host,port,logging=False,log=None,ignoredirs=True):
        Thread.__init__(self)
        self.interval=checkint                
        self.filedir=filedir
        self.torrentdir=torrentdir
        self.ignoredirs=ignoredirs
        self.host=host
        self.port=port
        self.logging=logging
        self.log=log
    def run(self):
        global glo_stillalive
        while (glo_stillalive):
            ctime=currenttime()
            while (glo_stillalive):
                #timer
                sleep(1.0)
                if currenttime()-ctime>=self.interval:
                    break
            if glo_stillalive:#don't do this if told to quit
                #do this the simple and dirty way - convert all the filenames to torrents
                # and see if those files are listed in the torrent dir.
                filelist=os.listdir(self.filedir)
                if self.ignoredirs:
                    f=0
                    while f<len(filelist):
                        if os.path.isdir(os.path.join(self.filedir,filelist[f])):filelist=filelist[:f]+filelist[f+1:]
                        else:f+=1
                tfilelist=[make_torrent_filename(fname) for fname in filelist]
                torrlist=os.listdir(self.torrentdir)
                mlist=[]
                for f in range(len(filelist)):
                    if not tfilelist[f] in torrlist:
                        mlist.append(filelist[f])
                for i in mlist:
                    try:
                        if not make_torrent(self.host,self.port,os.path.join(self.filedir,i),self.torrentdir):
                            if self.logging:
                                lo=open(self.log,"a")
                                lo.write(str(currenttime())+":")
                                lo.write("TorrentMakerTimer - unknown error making torrent in '"+self.torrentdir+"' from file '"+i+"'.\n")
                                lo.close()
                    except Exception, e:
                        lo=open(self.log,"a")
                        lo.write(str(currenttime())+":")
                        lo.write("TorrentMakerTimer - "+str(e)+'\n')
                        lo.close()

if __name__ == '__main__':
    uiname = 'btlaunchmany'

    defaults = get_defaults(uiname)

    set=defaultset[:]
    #conffile=None
    #if os.path.isfile(glo_confname):conffile=glo_confname
    arizonaconfig.init_options(sys.argv[0],'.',[],None,"arizonabittorrentshareconfig")#conffile)

    set[0]=get_option("arizonabittorrentcheckinterval",set[0])
    set[1]=get_option("arizonabittorrentfiledir",set[1])
    set[2]=get_option("arizonabittorrentupdatedir",set[2])
    set[3]=get_option("arizonabittorrentuploadrate",set[3])
    set[4]=get_option("arizonabittorrentsharing",str(set[4])).lower().strip()=="true"
    set[5]=get_option("arizonabittorrenttrackerhost",set[5])
    glo_possibleserverdomain=set[5]
    set[6]=get_option("arizonabittorrenttrackerport",set[6])
    set[8]=get_option("arizonabittorrentsharelogging",set[8])
    set[9]=get_option("arizonabittorrentsharelogginginterval",set[9])
    if get_option("arizonabittorrentsharing","true").lower()=="false":
       #this program should not be running...
       sys.exit()
   

    
    # this will be done the simple and dirty way -
    #  configuration settings will be translated
    # for extra simplicity, settings will be read from a personal config file
    #confname = glo_confname#"/usr/local/stork/etc/storkbtshare.conf"
    
    #defaults
    ccheckint=set[0]#"60"
    cfiledir=set[1]#"/usr/local/stork/torrents/files"
    cupdatedir=set[2]#"/usr/local/stork/torrents/updates"
    cuploadrate=set[3]#"0"
    clogging=set[8]#"false"
    clogginginterval=str(set[9])

    #if os.path.exists(confname):
    #    fo=open(confname)
    #    rd=fo.readlines()
    #    fo.close()
    #    
    #    for i in rd:
    #        s=i.split("=")
    #        s[0]=s[0].strip()
    #        s[1]=s[1].strip()
    #        if s[0]=="checkinterval":
    #            ccheckint=s[1]
    #        elif s[0]=="filedir":
    #            cfiledir=s[1]
    #        elif s[0]=="updatedir":
    #            cupdatedir=s[1]
    #        elif s[0]=="uploadrate":
    #            cuploadrate=s[1]
    #        elif s[0]=="logging":
    #            clogging=s[1]
    #        elif s[0]=="logginginterval":
    #            clogginginterval=s[1]
    extra=[]

    glo_logging=clogging.lower()=="true"

    #make sure it's daemonized
    daemonize('storkbtshare.py',""+glo_log*glo_logging)

    #if this is the seed program for the repository, it must specify the ip address
    if glo_possibleserverdomain in socket.gethostname().lower():
        extra=extra+["--ip",socket.gethostbyname(gethostname())]

    #also, set a default 10 second display interval - this could be sharing A LOT of files and shouldn't refesh that quickly
    sys.argv=["btlaunchmany.py"]+extra+["--display_interval",clogginginterval,"--parse_dir_interval",ccheckint,"--save_in",cfiledir,"--max_upload_rate",cuploadrate,cupdatedir]
 
    try:
        if len(sys.argv) < 2:
            printHelp(uiname, defaults)
            sys.exit(1)
        config, args = configfile.parse_configuration_and_args(defaults,
                                      uiname, sys.argv[1:], 0, 1)
        if args:
            config['torrent_dir'] = args[0]
        if not os.path.isdir(config['torrent_dir']):
            raise BTFailure("Warning: "+args[0]+" is not a directory")
    except BTFailure, e:
        #print 'error: ' + str(e) + '\nrun with no args for parameter explanations'
        if glo_logging:
            lo=open(glo_log,"a")
            lo.write(str(currenttime())+"\n")
            lo.write('error: ' + str(e) + '\n')
            lo.close()
        glo_stillalive=False
        sys.exit(1)
    tmt=TorrentMakerTimer(set[0],set[1],set[2],set[5],set[6],glo_logging,glo_log,get_option("arizonabittorrentignoredirs","True").lower()=="true")
    tmt.start()

    LaunchMany(config, HeadlessDisplayer(), 'btlaunchmany')
    glo_stillalive=False
    if exceptions:
        #print '\nEXCEPTION:'
        #print exceptions[0]
        if glo_logging:
            lo=open(glo_log,"a")
            lo.write(str(currenttime())+"\n")
            lo.write('EXCEPTION: ' + str(exceptions) + '\n')
            lo.close()
        
