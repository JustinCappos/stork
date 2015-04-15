#!/usr/bin/env python
#Written by Jason Hardies for Stork, based on original stork_slice_update code
# and designed according to stork requirements/suggestions.

import os,sys,time,threading,socket,errno
import signal
import arizonareport
import arizonatransfer
import arizonageneral
import pseprlib2 as pseprlib
import arizonaxml as xmllib
import arizonaconfig as configlib
import arizonacrypt as cryptlib
import arizonacomm as commlib
import package.storktar as storktar
import shutil
import storkpackagelist

debugmode=True

"""arizonaconfig
   options=[
   ["","--pseprserverxmlurl",           "pseprserverurl",               "store",        "string",       "http://www.dsmt.org/PsEPRServer/jClient.xml",  "pseprserverxmlurl","The url of the xml containing PsEPR server data."],
   ["","--pseprusername",               "pseprusername",                "store",        "string",       "arizona_stork2",                               "pseprusername","The username to use with psepr services."],
   ["","--pseprpassword",               "pseprpassword",                "store",        "string",       "etlk3vXZ23d",                                  "pseprpassword","The password to use with psepr services (note: psepr only accepts passwords in plain-text)."],
   ["","--pseprdaemonchannel",          "pseprdaemonchannel",           "store",        "string",       "/edu/arizona/stork2/psepr/",                   "pseprdaemonchannel","The channel name the psepr daemon should use."],
   ["","--pseprkeepduplicates",         "pseprkeepduplicates",          "store_true",   None,           False,                                          None, "Process duplicate psepr message"],
   ["","--repositorypublickeyfilepath", "repositorypublickeyfilepath",  "store",        "string",       "/usr/local/stork/var/keys/StorkRepository_nr06.publickey","repositorypublickeyfilepath","Path for the publickey for the repository."],
   ["","--pseprpublickey",              "pseprpublickey",               "store",        "string",       None,                                           None, "Public key to use when verifying psepr messages"],   
   ]
   includes=[]
"""
def get_option(name,section=None,default=None):
	ret= configlib.get_option(name,section)
	if ret is None:
		return default
	else:return ret

class PsEPRDaemon(threading.Thread):
	def __init__(self, section = None, update=None, msghandler=None, debugmode=False):
		threading.Thread.__init__(self)

                # initialize stuff from arizonaconfig
                self.section = section
                self.ignore_duplicates = not get_option("pseprkeepduplicates", self.section, False)
                self.server_url = get_option("pseprserverurl", self.section)
		self.metadir = None
                self.username = get_option("pseprusername", self.section)
                self.password = get_option("pseprpassword", self.section)
                self.channel = get_option("pseprdaemonchannel", self.section)

                # there are two ways we can get a public key: by filename and
                # by key string. It is expected that strings will be used in
                # the future instead of files, because it makes a config file
                # self-contained (no need to reference an external public
                # key)

		pkfile = get_option("repositorypublickeyfilepath", self.section)
                pkstring = get_option("pseprpublickey", self.section)
                if pkstring:
                   self.PublicKey = cryptlib.PublicKey(string = pkstring)
                elif pkfile:
                   self.PublicKey = cryptlib.PublicKey(file = pkfile)
                else:
                   self.PublicKey = None
                   
                if not self.PublicKey:
                   raise TypeError, "psepr daemon needs public key file or string"

		self.debugmode=debugmode
		self.msghandler=msghandler
		self.updatehandler=update
		self.lasttime=0#time of last update from update itself
		self.lasttimetime=0#actual time of last update
		if msghandler is None:
                   self.msghandler = self.msg_handler
                if update is None:
                   self.updatehandler = self.update
		self.done=False
		self.plist=None
		self.start()
	def run(self):
		self.done=False
		self.psm=pseprlib.PsEPRServerManager()
		self.psm.load_server_list_from_url(self.server_url)
		self.plist=None
		if self.debugmode:print "Starting PsEPRDaemon loop."
		while not self.done:
			if self.debugmode:print "Beginning PsEPRDaemon loop iteration.\nGetting PsEPRListener."

			#this method already performs the desired function with timeout even
			self.plist=pseprlib.GetPsEPRListener(self.username, self.password, self.msghandler,self.channel,900,60,self.psm,self.debugmode)
			if self.debugmode:
                           print "Received authentificated PsEPRListener."

			while self.plist.authentificated:
                           #if disconnected, this will change...
       		           time.sleep(1.0)

			if self.debugmode:
                           print "PsEPRListener authentification lost."

	def stop(self):
		self.done=True
		if not self.plist is None:self.plist.close()

	def check_expired(self,expirationtime=300):#default 5 minutes
		if time.time() - self.lasttimetime > expirationtime:
                   return True
		return False

        def update(self,filename):
           print "PSEPR update: " + str(filename)

	def msg_handler(self,data):
		if self.debugmode:print "Handling PsEPR message:",data
		#authentificate:
		#  make sure message meets basic criteria:
		if not data[0]==self.channel:
			if self.debugmode:print "InvalidChannelName:",data[0]
			return
		if not "arizona" in data[1]:#probably not from us...
			if self.debugmode:print "InvalidServiceName:",data[1]
			return
		#assume that if it's signed properly, we meant to send it regardless of source
		#if not ".cs.arizona.edu" in data[2]:#not from one of our servers
		#	if self.debugmode:print "InvalidInstanceName:",data[2]
		#	return
		#assume that the person pushing it out (if valid), knows what they're doing.
		#if not "/metafile" in data[3]:#metafiles only
		#	if self.debugmode:print "InvalidFieldName:",data[3]
		#	return
		if self.debugmode:
			print "PsEPRDaemon:msg passed initial tests"
		#only one file should be replaced.
		tmpfname=""
		tfn=""
		try:
			tmpfname="/tmp/pseprmsg"+str(time.time())

                        if self.metadir:
   			   fullpath=os.path.join(self.metadir,data[3])
                        else:
                           fullpath = data[3]

			fo=open(tmpfname,"w")
			fo.write(xmllib.unescape(data[4]))
			fo.close()
			if self.debugmode:print "PsEPRDaemon:msg passed part 1"

			#the try/except block will catch this

                        valResult = cryptlib.XML_validate_file(tmpfname, self.PublicKey.get_file(), certify_filename=False)
                        ctime = valResult['timestamp']

			if self.debugmode:print "PsEPRDaemon:msg passed part 2"
			if ctime<=self.lasttime:
				if self.debugmode:print "Message",data[3],"at",ctime,"older than previous message at",self.lasttime,"."
				raise Exception("Message older than previous message.")
			self.lasttime=ctime
			self.lasttimetime=time.time()#timetime = time.time
			if self.debugmode:print "PsEPRDaemon:msg passed part 3"
			#why doesn't this take a keyfile???
			tfn=cryptlib.XML_retrieve_originalfile_from_signedfile(tmpfname,tmpfname+".1")
			if tfn!=tmpfname+".1":
				if self.debugmode:print "Message",data[3],"extracted with wrong filename."
				raise Exception("Message extracted with wrong filename.")
			if self.debugmode:print "PsEPRDaemon:msg passed part 4"
			#since this is in a try/except(finally) block, this won't bomb if the directory structure doesn't exist
			#check first to see if the file is different than the old file
			po=os.popen("/usr/bin/diff "+fullpath+" "+tfn)
			if not po.close():#no change
			   if self.debugmode:print "Message is same as old message:",tfn
			   #not really an error, but need to raise an exception to do cleanup
                           if self.ignore_duplicates:
   			       raise Exception("New message is same as old message.")

			if self.debugmode:
                           print "PsEPRDaemon:msg passed part 5"

                        # if fullpath has a directory component to it, then
                        # make sure the directory is created
			fullpathpath=os.path.split(fullpath)[0]
                        if fullpathpath:
   			   if not os.path.isdir(fullpathpath):
			      os.makedirs(fullpathpath)

			if os.path.isfile(fullpath):
                           os.unlink(fullpath)

			os.rename(tfn,fullpath)
			if self.debugmode:
				print "Replaced", fullpath, "with data from valid message:"
				fo=open(fullpath)
				rd=fo.read()
				fo.close()
				print [rd]

			if self.debugmode:
                           print "PsEPRDaemon:msg passed part 6:updatehandler method started"

			#update everything
			self.updatehandler(fullpath)
		except Exception,e:
			if self.debugmode:print "PsEPRDaemon:Exception:", e
		if tmpfname and os.path.isfile(tmpfname):
			os.unlink(tmpfname)
		if tfn and os.path.isfile(tfn):
			os.unlink(tfn)


