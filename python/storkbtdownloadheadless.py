#!/usr/bin/python
#
#storkbtdownloadheadless.py

""" This is a modified form of btdownloadheadless.py from BitTorrent 4.0.1-1.
    Modified by Jason Hardies for use with stork via storktorrent.py
    
    Changes are as follows:
	-The original if __name__=="__main__": statement is wrapped by the btdownloadheadless method.
	-By default, the method will start a quiet bittorrent download that will stop once the download is complete (which can be changed by passing non-default options to the method)
	-An urllib.urlretrieve like download indicator can be used.
	-The host and port of the tracker can be specified to override the values found in the torrent files.
	-The download object (DL) can be directly accessed by passing an empty object to the btdownloadheadless method.  This object can be used to stop the torrent if it was set to seed forever, for example.
	-A seed locator timeout class is added to raise an error when no seed is located within a certain timeout.
    (Changes are outlined using the ##CHANGE:  ... ##END blocks.)
"""
# The contents of this file are subject to the BitTorrent Open Source License
# Version 1.0 (the License).  You may not copy or use this file, in either
# source code or executable form, except in compliance with the License.  You
# may obtain a copy of the License at http://www.bittorrent.com/license/.
#
# Software distributed under the License is distributed on an AS IS basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied.  See the License
# for the specific language governing rights and limitations under the
# License.

# Written by Bram Cohen, Uoti Urpala and John Hoffman

from __future__ import division

import sys
import os
import threading
from time import time, strftime
from signal import signal, SIGWINCH
from cStringIO import StringIO

from BitTorrent.download import Feedback, Multitorrent
from BitTorrent.defaultargs import get_defaults
from BitTorrent.parseargs import parseargs, printHelp
from BitTorrent.zurllib import urlopen
from BitTorrent.bencode import bdecode
from BitTorrent.ConvertedMetainfo import ConvertedMetainfo
from BitTorrent import configfile
from BitTorrent import BTFailure
from BitTorrent import version

##CHANGE:ADDED:
#since time was imported from time, above...
from time import sleep as timesleep
##END

def fmttime(n):
    if n == 0:
        return 'download complete!'
    try:
        n = int(n)
        assert n >= 0 and n < 5184000  # 60 days
    except:
        return '<unknown>'
    m, s = divmod(n, 60)
    h, m = divmod(m, 60)
    return 'finishing in %d:%02d:%02d' % (h, m, s)

def fmtsize(n):
    s = str(n)
    size = s[-3:]
    while len(s) > 3:
        s = s[:-3]
        size = '%s,%s' % (s[-3:], size)
    if n > 999:
        unit = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
        i = 1
        while i + 1 < len(unit) and (n >> 10) >= 999:
            i += 1
            n >>= 10
        n /= (1 << 10)
        size = '%s (%.0f %s)' % (size, n, unit[i])
    return size

##CHANGE:ADDED:
class SeedLocatorTimeout(threading.Thread):
    """
        A timer class, added to timeout if no seed is located
    """
    def __init__(self, dlobj, timeout=30.0):
        # default timeout = 30 sec.
        threading.Thread.__init__(self)
        self.dlobj=dlobj
        self.seedlocated=False
        self.running=False
        self.timeout=timeout
    def run(self):
        self.running=True
        elapsed=0
        tstart=time()
        while self.running and not self.seedlocated:
            timesleep(1.0)
            elapsed=time()-tstart
            if elapsed>=self.timeout:self.running=False
        if not self.seedlocated:
            #raise an error via the dl object
            self.dlobj.error(self.dlobj.torrent,0,"Seed Location Timeout: no seed found after "+str(self.timeout)+" seconds.")
    def stop(self):
        self.running=False
        self.seedlocated=True #don't want to have the run function attempting to raise an error
##END

class HeadlessDisplayer(object):

    ##CHANGE:
    def __init__(self, doneflag,quiet=0,downloadindicator=None):
        ##ORIGINAL:
        #def __init__(self, doneflag):
        ##END
        self.doneflag = doneflag
        ##CHANGE:ADDED:
        self.quiet=quiet
        self.downloadindicator=downloadindicator
        ##END

        self.done = False
        self.percentDone = ''
        self.timeEst = ''
        self.downRate = '---'
        self.upRate = '---'
        self.shareRating = ''
        self.seedStatus = ''
        self.peerStatus = ''
        self.errors = []
        self.file = ''
        self.downloadTo = ''
        self.fileSize = ''
        self.numpieces = 0

    def set_torrent_values(self, name, path, size, numpieces):
        self.file = name
        self.downloadTo = path
        self.fileSize = fmtsize(size)
        self.numpieces = numpieces

    def finished(self):
        self.done = True
        self.downRate = '---'
        ##CHANGE:MODIFIED:(added if not self.quiet:)
        if not self.quiet:self.display({'activity':'download succeeded', 'fractionDone':1})
        ##END

    def error(self, errormsg):
        newerrmsg = strftime('[%H:%M:%S] ') + errormsg
        self.errors.append(newerrmsg)
        if not self.quiet:self.display({})

    def display(self, statistics):
        fractionDone = statistics.get('fractionDone')
        activity = statistics.get('activity')
        timeEst = statistics.get('timeEst')
        downRate = statistics.get('downRate')
        upRate = statistics.get('upRate')
        spew = statistics.get('spew')

        print '\n\n\n\n'
        if spew is not None:
            self.print_spew(spew)

        if timeEst is not None:
            self.timeEst = fmttime(timeEst)
        elif activity is not None:
            self.timeEst = activity

        if fractionDone is not None:
            self.percentDone = str(int(fractionDone * 1000) / 10)
        if downRate is not None:
            self.downRate = '%.1f KB/s' % (downRate / (1 << 10))
        if upRate is not None:
            self.upRate = '%.1f KB/s' % (upRate / (1 << 10))
        downTotal = statistics.get('downTotal')
        if downTotal is not None:
            upTotal = statistics['upTotal']
            if downTotal <= upTotal / 100:
                self.shareRating = 'oo  (%.1f MB up / %.1f MB down)' % (
                    upTotal / (1<<20), downTotal / (1<<20))
            else:
                self.shareRating = '%.3f  (%.1f MB up / %.1f MB down)' % (
                   upTotal / downTotal, upTotal / (1<<20), downTotal / (1<<20))
            numCopies = statistics['numCopies']
            nextCopies = ', '.join(["%d:%.1f%%" % (a,int(b*1000)/10) for a,b in
                    zip(xrange(numCopies+1, 1000), statistics['numCopyList'])])
            if not self.done:
                self.seedStatus = '%d seen now, plus %d distributed copies ' \
                                  '(%s)' % (statistics['numSeeds'],
                                         statistics['numCopies'], nextCopies)
            else:
                self.seedStatus = '%d distributed copies (next: %s)' % (
                    statistics['numCopies'], nextCopies)
            self.peerStatus = '%d seen now' % statistics['numPeers']

        for err in self.errors:
            print 'ERROR:\n' + err + '\n'
        ##CHANGE:ADDED: (plus indentation on the following lines)
        if not self.quiet:
        ##END
            print 'saving:        ', self.file
            print 'percent done:  ', self.percentDone
            print 'time left:     ', self.timeEst
            print 'download to:   ', self.downloadTo
            print 'download rate: ', self.downRate
            print 'upload rate:   ', self.upRate
            print 'share rating:  ', self.shareRating
            print 'seed status:   ', self.seedStatus
            print 'peer status:   ', self.peerStatus
        ##CHANGE:ADDED:
        #attempt to use the download_indicator(block_count,block_size,file_size)
        if not self.downloadindicator is None:
            self.downloadindicator(int(fractionDone * 1000),1,1000)
        ##END

    def print_spew(self, spew):
        s = StringIO()
        s.write('\n\n\n')
        for c in spew:
            s.write('%20s ' % c['ip'])
            if c['initiation'] == 'L':
                s.write('l')
            else:
                s.write('r')
            total, rate, interested, choked = c['upload']
            s.write(' %10s %10s ' % (str(int(total/10485.76)/100),
                                     str(int(rate))))
            if c['is_optimistic_unchoke']:
                s.write('*')
            else:
                s.write(' ')
            if interested:
                s.write('i')
            else:
                s.write(' ')
            if choked:
                s.write('c')
            else:
                s.write(' ')

            total, rate, interested, choked, snubbed = c['download']
            s.write(' %10s %10s ' % (str(int(total/10485.76)/100),
                                     str(int(rate))))
            if interested:
                s.write('i')
            else:
                s.write(' ')
            if choked:
                s.write('c')
            else:
                s.write(' ')
            if snubbed:
                s.write('s')
            else:
                s.write(' ')
            s.write('\n')
        print s.getvalue()


class DL(Feedback):

    ##CHANGE:
    def __init__(self, metainfo, config,host=None,port=None,quiet=0,downloadindicator=None,seed=0,sltimeout=30):
        ##ORIGINAL:
        #def __init__(self, metainfo, config):
        ##END
        self.doneflag = threading.Event()
        self.metainfo = metainfo
        self.config = config
        ##CHANGE:ADDED:
        self.success=0
        self.quiet = quiet
        self.downloadindicator = downloadindicator
        self.m_host=host
        self.m_port=port
        self.seed=seed
        self.sltimeout=SeedLocatorTimeout(self,sltimeout)
        ##END

    def run(self):
        ##CHANGE:
        self.d = HeadlessDisplayer(self.doneflag,self.quiet,self.downloadindicator)
        ##ORIGINAL:
        #self.d = HeadlessDisplayer(self.doneflag)
        ##END
        try:
            self.multitorrent = Multitorrent(self.config, self.doneflag,
                                             self.global_error)
            # raises BTFailure if bad
            metainfo = ConvertedMetainfo(bdecode(self.metainfo))
            ##CHANGE:ADDED:
            # set the host and port if specified
            if not self.m_host is None:
                cport=6969
                if not self.m_port is None:cport=self.m_port
                metainfo.announce="http://"+self.m_host+":"+str(cport)+"/announce"
            ##END
            torrent_name = metainfo.name_fs
            if config['save_as']:
                if config['save_in']:
                    raise BTFailure('You cannot specify both --save_as and '
                                    '--save_in')
                saveas = config['save_as']
            elif config['save_in']:
                saveas = os.path.join(config['save_in'], torrent_name)
            else:
                saveas = torrent_name

            self.d.set_torrent_values(metainfo.name, os.path.abspath(saveas),
                                metainfo.total_bytes, len(metainfo.hashes))
            self.torrent = self.multitorrent.start_torrent(metainfo,
                                self.config, self, saveas)
            ##CHANGE:ADDED:
            #don't run timeout if it's expecting to run forever
            if not self.seed:self.sltimeout.start()
            ##END
        except BTFailure, e:
            print str(e)
            return
        self.get_status()
        self.multitorrent.rawserver.listen_forever()
        ##CHANGE:MODIFIED: (added if not self.quiet)
        if not self.quiet:self.d.display({'activity':'shutting down', 'fractionDone':0})
        ##END
        self.torrent.shutdown()

    def reread_config(self):
        try:
            newvalues = configfile.get_config(self.config, 'btdownloadcurses')
        except Exception, e:
            self.d.error('Error reading config: ' + str(e))
            return
        self.config.update(newvalues)
        # The set_option call can potentially trigger something that kills
        # the torrent (when writing this the only possibility is a change in
        # max_files_open causing an IOError while closing files), and so
        # the self.failed() callback can run during this loop.
        for option, value in newvalues.iteritems():
            self.multitorrent.set_option(option, value)
        for option, value in newvalues.iteritems():
            self.torrent.set_option(option, value)

    def get_status(self):
        self.multitorrent.rawserver.add_task(self.get_status,
                                             self.config['display_interval'])
        status = self.torrent.get_status(self.config['spew'])
        #if a seed has been located, stop the timer...
        if not self.sltimeout is None and not status.get('downTotal') is None and status['numCopies']>0:self.sltimeout.stop()
        if not self.quiet:self.d.display(status)

    def global_error(self, level, text):
        self.d.error(text)
        
    def error(self, torrent, level, text):
        self.d.error(text)
        ##CHANGE:ADDED:
        if "Seed Location Timeout" in text:
            self.success=-1
            #self.sltimeout.stop()
            self.doneflag.set()
            #raise BTFailure(text)
        elif "urlopen error" in text and "tracker" in text:
            self.success=-1
            self.sltimeout.stop()
            self.doneflag.set()
            raise BTFailure("Tracker connection error.")
        ##END

    def failed(self, torrent, is_external):
        self.doneflag.set()
        ##CHANGE:ADDED:
        self.success=-1
        self.sltimeout.stop()
        ##END

    def finished(self, torrent):
        self.d.finished()
        ##CHANGE:ADDED:
        self.success=1
        #forces it to stop once it's done:
        if not self.seed:
            self.doneflag.set()
            self.sltimeout.stop()
        ##END

    ##CHANGE:ADDED:
    def stop(self):
        """attempts to stop the current process"""
        self.doneflag.set()
        self.sltimeout.stop()
    ##END

##CHANGE:MODIFIED/ADDED:
# (see original below -- basically, made into a method, with extra args and try blocks in __main__)
def btdownloadheadless(argv,host=None,port=None,quiet=0,downloadindicator=None,seed=0,dlobj=None,sltimeout=30):
    """
        Wraps the original if __name__=="__main__": block and allows for additional functionality
	
	Arguments:
	  argv: The argv as the btdownloadheadless.py would receive from sys.argv
	  host: The tracker host for the torrent. (if None, will use the torrent's settings) (default:None)
	  port: The tracker port for the torrent. (if None, will use the torrent's settings) (default: None)
	  quiet: Whether the downloader should print out download status like btdownloadheadless (default: 0)
	  downloadindicator: The download indicator (like would be passed to urllib.urlretrieve) (default: None)
	  seed: Whether the downloader should continue seeding after downloading (note: may not return set to continue seeding) (default:0)
	  dlobj: An object that can be used to get the DL object for the download.  If not None, the DL object can be accessed via dlobj.dl. (default: None)
	  sltimeout: The timeout value in seconds for the seed locator.  (Default: 30)
	  
	Any method using this method should handle the IOError and BTFailure exceptions that this can raise.
    """
    global uiname
    global defaults
    global config
    global args
    uiname = 'btdownloadheadless'
    defaults = get_defaults(uiname)

    if len(argv) <= 1:
        printHelp(uiname, defaults)
        sys.exit(1)
    config, args = configfile.parse_configuration_and_args(defaults,
                                  uiname, argv[1:], 0, 1)
    if args:
        if config['responsefile']:
            raise BTFailure, 'must have responsefile as arg or parameter, not both'
        config['responsefile'] = args[0]
    #try:
    #    try:
    if config['responsefile']:
        h = file(config['responsefile'], 'rb')
        metainfo = h.read()
        h.close()
    elif config['url']:
        h = urlopen(config['url'])
        metainfo = h.read()
        h.close()
    else:
        raise BTFailure('you need to specify a .torrent file')
        #don't exit here (not like it would be possible right after raising an error)
        #sys.exit(1)
    #except IOError, e:
    #    raise BTFailure('Error reading .torrent file: ', str(e))
    #don't handle the error here, pass it up
    #except BTFailure, e:
    #    print str(e)
    #    sys.exit(1)

    dl = DL(metainfo, config,host,port,quiet,downloadindicator,seed,sltimeout)
    if not dlobj is None:dlobj.dl=dl
    dl.run()
    return dl.success

if __name__ == '__main__':
    try:
        try:
            btdownloadheadless(sys.argv)
        except IOError,e:
            raise BTFailure('Error reading .torrent file: '+str(e))
    except BTFailure, e:
        #print str(e)
        #sys.exit(1)
        raise Exception(str(e))
##ORIGINAL:
#if __name__ == '__main__':
#    uiname = 'btdownloadheadless'
#    defaults = get_defaults(uiname)
#
#    if len(sys.argv) <= 1:
#        printHelp(uiname, defaults)
#        sys.exit(1)
#    try:
#        config, args = configfile.parse_configuration_and_args(defaults,
#                                      uiname, sys.argv[1:], 0, 1)
#        if args:
#            if config['responsefile']:
#                raise BTFailure, 'must have responsefile as arg or ' \
#                      'parameter, not both'
#            config['responsefile'] = args[0]
#        try:
#            if config['responsefile']:
#                h = file(config['responsefile'], 'rb')
#                metainfo = h.read()
#                h.close()
#            elif config['url']:
#                h = urlopen(config['url'])
#                metainfo = h.read()
#                h.close()
#            else:
#                raise BTFailure('you need to specify a .torrent file')
#        except IOError, e:
#            raise BTFailure('Error reading .torrent file: ', str(e))
#    except BTFailure, e:
#        print str(e)
#        sys.exit(1)
#
#    dl = DL(metainfo, config)
#    dl.run()
##END
