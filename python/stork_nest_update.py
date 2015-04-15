#!/usr/bin/env python
#Written by Jason Hardies for Stork, based on original stork_slice_update code
# and designed according to stork requirements/suggestions.
#stork_nest_update.py

import os,sys,time,threading,socket,errno
import signal
import arizonareport
import arizonatransfer
import arizonageneral
import pseprlib2 as pseprlib
#import arizonageneral as generallib
import arizonaxml as xmllib
import arizonaconfig as configlib
import arizonacrypt as cryptlib
import arizonacomm as commlib
import package.storktar as storktar
import shutil
import storkpackagelist
import storkpseprdaemon
import Queue

selffilename="stork_nest_update.py"

debugmode=True

"""arizonaconfig
   options=[
   ["","--storknestupdateconfigpath",   "storknestupdateconfigpath",    "store",        "string",       "/usr/local/stork/etc/storknestupdate.conf",    "storknestupdateconfigpath","The path of the config file (this should never be modified outside the script itself)"],
   ["","--retrievedir",                 "retrievedir",                  "store",        "string",       "/usr/local/stork/var/packages",                "DIRECTORY", "location to put retrieved files (default /usr/local/stork/var/packages)"],
   ["","--storknestupdatedebug","storknestupdatedebug","store","string","False","storknestupdatedebug","Whether to enter debug mode with the update daemon."],
   ["","--storknestupdatemetadir",      "storknestupdatemetadir",       "store",        "string",       "/usr/local/stork/var/content",                 "storknestupdatemetadir","The directory to put/check for a metadata in."],
   ["","--storknestupdatelistenerport", "storknestupdatelistenerport",  "store",        "int",          641,                                            "storknestupdatelistenerport","The port to have the update daemon listen to for local connections."],
   ["","--storknestupdatetransfermethods","storknestupdatetransfermethods","append",    "string",       ["coblitz","http","ftp"],                       "TransferMethods","The transfer methods the update daemon should use for updtates."]
   ]
   includes=[]
"""
def get_option(name,default=None):
	ret= configlib.get_option(name)
	if ret is None:
		return default
	else:return ret

class NestPsEPRDaemon(storkpseprdaemon.PsEPRDaemon):
        def __init__(self, update=None, msghandler=None, udaemon=None, debugmode=False):
           storkpseprdaemon.PsEPRDaemon.__init__(self, update, msghandler, debugmode)
           if udaemon:
               udaemon.set_psepr_expiration_handler(self.check_expired)
           self.udaemon = udaemon

        def update(self, filename, repoName=None):
           # get the repository name from the metafilename. We assume the
           # filename has a path that ends in:
           #    .../repository_name/packageinfo/metafile
           # XXX this is a bit of a hack; see if there is a way to put the
           # repository name in the PsEPR message.
           if not repoName:
              try:
                 repoName = filename.split("/")[-3] + "/" + filename.split("/")[-2]
              except IndexError:
                 print "unable to determine repository name from " + filename
                 return

           print "NestPsEPRDaemon: Received psepr update for: " + repoName

           if self.udaemon:
              self.udaemon.update_event(repoName)






class ListenerDaemon(commlib.listener):
	def __init__(self,port,max_impending=10,autostart=True,debugmode=False):
                self.debugmode=debugmode
                commlib.listener.__init__(self,port,None,None,max_impending,autostart)
        def send(self):
                self.default_list_check()
                if len(self.connlist)==0:
                        if self.debugmode:print "ListenerDaemon: send: no connections."
                        return
                #just to use the send method with our socket
                sender=commlib.single_conn("127.0.0.1",12345,{"Update":self.send},None,'\\',False,True)
                for i in self.connlist:
                        sender.sock=i[0]
                        if self.debugmode:print "ListenerDaemon: send: sending update to",i[1]
                        sender.send("Update","Update","\\")

class ScheduledUpdate(threading.Thread):
	def __init__(self,timeout,udaemon):
		"""wait timeout seconds and call update"""
		self.udaemon=udaemon
		self.timeout=timeout
		threading.Thread.__init__(self)
		self.start()
		self.done=False
	def run(self):
		starttime=time.time()
		while time.time()-starttime<self.timeout and not self.done:
			time.sleep(1)
		if self.done:return
		time.sleep(1)#ensure the time has expired
		#should be handled when the update method is called.
		#self.udaemon.scheduledupdate.stop()
		#self.udaemon.scheduledupdate=None
		self.udaemon.update()
	def stop(self):
		self.done=True

class UpdateDaemon(threading.Thread):
	def __init__(self, listenersendhandler, debugmode=False):
		threading.Thread.__init__(self)
		self.listenersendhandler=listenersendhandler
		self.debugmode=debugmode
		self.done=False
		self.pseprupdateexpirationhandler=None
		self.lasttime=time.time()
		self.maxupdateinterval=30 #cannot go any faster than 30 sec
		#                          between updates.
		self.lasttime-=self.maxupdateinterval+1
		self.scheduledupdate=None
                self.update_event_called = False
                self.repo_names = Queue.Queue()
                #self.start()

	def set_psepr_expiration_handler(self,handler):
		self.pseprupdateexpirationhandler=handler

        def add_repo(self, repo_name):
                # add a repository name to the list of repositories that need
                # to be updated
                self.repo_names.put(repo_name)

        def pop_repo(self):
                # pop a repository off the update list. Return None if no
                # repository needs updating
                try:
                   return self.repo_names.get(False) # nonblocking
                except Queue.Empty:
                   return None

        def update_event(self, repo_name):
                # called by psepr daemon. Pushes a repository name to the list
                # and calls update
                self.add_repo(repo_name)
                self.update_event_called = True

	def update(self):
                if self.debugmode:
                   print "UpdateDaemon: update"
		if time.time() - self.lasttime<self.maxupdateinterval:
			if self.debugmode:
                           print "UpdateDaemon:updates too frequent"
			if not self.scheduledupdate:
			   if self.debugmode:
                              print "UpdateDaemon:scheduling update."
			      self.scheduledupdate=ScheduledUpdate(self.maxupdateinterval-(time.time()-self.lasttime),self)
			return
		elif self.scheduledupdate:
			self.scheduledupdate.stop()
			self.scheduledupdate=None

		self.lasttime=time.time()#must be set here since the psepr daemon portion of this daemon calls this directly.
		if self.debugmode:
                   print "UpdateDaemon:syncing metadata directory."

                # for each repository on the update list, fetch its files
                repo_name = self.pop_repo()
                while repo_name:
                   print "updatedaemon: updating " + repo_name

                   # storkpackagelist will download the files from the repository
                   # it re-downloads the metahash file, which is unnecessary. It
                   # also unpacks the files, which may or may not be necessary.

                   # XXX hardcoded path -- fix me
                   storkpackagelist.download_repository(repo_name,
                                                        "/usr/local/stork/var/packageinfo",
                                                        True)

                   repo_name = self.pop_repo()

                # inform all the listener clients
		if self.listenersendhandler:
                   self.listenersendhandler()

	def run(self):
		#the magic number
		expirationtime=300
		if self.debugmode:
                   print "UpdateDaemon: starting loop"
		while not self.done:
			update=False

                        # if an update event was received, then we need to
                        # update
                        if self.update_event_called:
                           update = True

                        # check with the psepr daemon and see if it is not receiving
                        # messages.
			if not self.pseprupdateexpirationhandler:
                           # there is no pseprexpirationhandler, so we assume
                           # that psepr is stale
                           psepr_stale = True
                        elif self.pseprupdateexpirationhandler(expirationtime):
                           # the psepr daemon has told us it is not receiving
                           # messages
                           psepr_stale = True
                           if self.debugmode:
                              print "UpdateDaemon: psepr is stale"
                        else:
                           # the psepr daemon is receiving updates, so there is
                           # no reason for us to schedule an update of our
                           # own.
                           psepr_stale = False

                        # if psepr is not receiving updates, then the best we
                        # can do is to timeout ourselves
			if psepr_stale:
                           if time.time()-self.lasttime>expirationtime:
			      if self.debugmode:
                                 print "UpdateDaemon: updating due to stale psepr and/or timeout"
   			      update=True

			if update:
			   self.update()

			try:
                           # cleanup any children that have been killed off
			   os.waitpid(-1, os.WNOHANG)
			except OSError:# just means there is no child waiting...
			   pass

			time.sleep(1.0)
		if self.debugmode:
                   print "UpdateDaemon: done."

	def stop(self):
		self.done=True

def main():
	#should work with the current arizonaconfig code
	configlib.init_options(configfile_optvar='configfile')
        if get_option("storknestupdatedebug").strip().lower()=="true":
           debugmode=True
	else:
           debugmode=False #despite being declared above, this is still necessary...

	#use config settings to override settings from the config file
	configlib.set_option('transfermethod',get_option("storknestupdatetransfermethods"))
	if debugmode:
           print "Transfermethod changed:",get_option("transfermethod")
	if not debugmode:
           arizonageneral.make_daemon("stork_nest_update.py")
	if debugmode:
           print "Configuration loaded.\nDaemonizing blocked by debugmode."

	ldaemon=ListenerDaemon(get_option("storknestupdatelistenerport"), 10, True, debugmode)
        udaemon=UpdateDaemon(ldaemon.send, debugmode)
	pdaemon=NestPsEPRDaemon(None, None, udaemon, debugmode)
        udaemon.start()
	if debugmode:
           print "All Deamons started."

if __name__=="__main__":main()
