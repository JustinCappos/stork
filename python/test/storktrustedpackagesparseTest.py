#! /usr/bin/env python
"""
<Module>
   storktrustedpackagesTest
<Author>
   Justin Cappos
<Started>
   November 10, 2005   
<Purpose>
   Test module for storktrustedpackagesparse.  See that file for more details
"""

import arizonaconfig
import arizonacrypt
import arizonaunittest
import storktrustedpackagesparse
import storkusername
import os

# some helper functions used in writing the test cases
# TODO: comments

def init_keys(username):
   """
   <Purpose>
      Create public/private key pairs to be used by test cases.
   """
   privk = "/tmp/" + username + ".privatekey"
   arizonacrypt.generate_privatekey_fn(privk)
   pubk_sl = arizonacrypt.extract_publickey_sl_from_privatekey_fn(privk)
   pubk = arizonacrypt.sl_to_fn(pubk_sl)
   pubk_string = arizonacrypt.publickey_sl_to_fnstring(pubk_sl)
   tp_fn = "/tmp/"+username+"."+pubk_string+".tpfile"

   return (username, privk, pubk, pubk_string, tp_fn)

def tpheader():
   return ['<?xml version="1.0" encoding="ISO-8859-1" standalone="yes" ?>', '', '<TRUSTEDPACKAGES>']

def tpfooter():
   return ['</TRUSTEDPACKAGES>']

def tpuser(pattern, name, key, action, orderby="default"):
   return ['    <USER PATTERN="'+pattern+'" USERNAME="'+name+'" PUBLICKEY="'+key+'" ACTION="'+action+'" ORDER-BY="'+orderby+'" />']

def tpfile(pattern, hash, action, timestamp="0"):
   return ['    <FILE PATTERN="'+pattern+'" HASH="'+hash+'" ACTION="'+action+'" TIMESTAMP="'+timestamp+'" />']

def tpsign(sl, fn, privk):
   temp_fn = arizonacrypt.sl_to_fn(sl)
   os.rename(temp_fn, fn)

   arizonacrypt.XML_sign_file_using_privatekey_fn(fn, privk)

def tprank(name, hash):
   """
   <Purpose>
      Given a name and hash, send it to rank_packages. Return either "allow",
      "deny", or "unspecified", depending on what trusted packages entries
      exist.
   """
   (allow, deny, unspecified) = storktrustedpackagesparse.rank_packages([(name, hash, "blah")])

   if allow:
       assert(not deny)
       assert(not unspecified)
       return "allow"

   if deny:
      assert(not unspecified)
      return "deny"

   if unspecified:
      return "unspecified"

   assert(False)

def tpranktwo(name1, hash1, name2, hash2):
   """
   <Purpose>
      Given two names and hashes, send them to rank_packages and collect the
      results of the allow_list that is returned. 
   """
   (allow, deny, unspecified) = \
      storktrustedpackagesparse.rank_packages([(name1, hash1, "blah"),
                                               (name2, hash2, "blah2")])

   result_list = []

   for pack in allow:
       result_list.append(pack[0])

   return result_list

def rank_packages(package_list, tags="", ignore_mantags=False):
   """
   <Purpose>
      Strips the link to the tpentry out of the tuples returned from 
      rank_packages. This makes it easier to test the results in test
      cases with an assert.
   """
   (allow, deny, unknown) = storktrustedpackagesparse.rank_packages(package_list, tags, ignore_mantags)

   allow1 = []
   for pack in allow:
       allow1.append((pack[0], pack[1], pack[2]))

   deny1 = []
   for pack in deny:
       deny1.append((pack[0], pack[1], pack[2]))

   unknown1 = []
   for pack in unknown:
       unknown1.append((pack[0], pack[1], pack[2]))

   return (allow1, deny1, unknown1)

       
# Unit tests for each function, listed in code order
class test(arizonaunittest.TestCase):

   def reset_options(self):
       reload(storktrustedpackagesparse)
       reload(storkusername)
       reload(arizonaconfig)

   #------------------------------------------------------------------
   # rank_packages(package_list, trustedpackages_fn=None):
   #------------------------------------------------------------------
   def test_rank_packages(self):

      self.reset_options()

      try: 
         arizonaconfig.init_options("stork.py", configfile_optvar="configfile", version="2.0")
      
         # Create two public/private key pairs
         joe_privk = "/tmp/joe.privatekey"
         arizonacrypt.generate_privatekey_fn(joe_privk)
         joe_pubk_sl = arizonacrypt.extract_publickey_sl_from_privatekey_fn(joe_privk)
         joe_pubk = arizonacrypt.sl_to_fn(joe_pubk_sl)
         joe_pubk_string = arizonacrypt.publickey_sl_to_fnstring(joe_pubk_sl)

         jim_privk = "/tmp/jim.privatekey"
         arizonacrypt.generate_privatekey_fn(jim_privk)
         jim_pubk_sl = arizonacrypt.extract_publickey_sl_from_privatekey_fn(jim_privk)
         jim_pubk = arizonacrypt.sl_to_fn(jim_pubk_sl)
         jim_pubk_string = arizonacrypt.publickey_sl_to_fnstring(jim_pubk_sl)

         # Set up options so that we are "joe"
         arizonaconfig.set_option("username","joe")
         arizonaconfig.set_option("publickeyfile",joe_pubk)
         arizonaconfig.set_option("tpdir","/tmp")
         arizonaconfig.set_option("tpdtd","trustedpackages.dtd")

         # Create example trustedpackages files
         joe_tp_fn = "/tmp/joe."+joe_pubk_string+".tpfile"
         jim_tp_fn = "/tmp/jim."+jim_pubk_string+".tpfile"

         joe_tp_sl = ['<?xml version="1.0" encoding="ISO-8859-1" standalone="yes" ?>', '', '<TRUSTEDPACKAGES>', '    <FILE PATTERN="a.rpm" HASH="a8924367f832d012c56db" ACTION="allow" />', '    <USER PATTERN="foo*" USERNAME="jim" PUBLICKEY="'+jim_pubk_string+'" ACTION="allow">', '     lasdfasdf asldf as df asfa sdf lasfadsfasfasdfakjlkjlkjl ', '    </USER>', '    <USER PATTERN="stork*" USERNAME="jim" PUBLICKEY="'+jim_pubk_string+'" ACTION="allow" />', '    <FILE PATTERN="*.rpm" HASH="a89247f832d012c56db" ACTION="deny" />', '    <FILE PATTERN="*.deb" HASH="*" ACTION="deny" />', '</TRUSTEDPACKAGES>']
         temp_joe_fn = arizonacrypt.sl_to_fn(joe_tp_sl)
         os.rename(temp_joe_fn, joe_tp_fn)

         arizonacrypt.XML_sign_file_using_privatekey_fn(joe_tp_fn, joe_privk)

         jim_tp_sl = ['<?xml version="1.0" encoding="ISO-8859-1" standalone="yes" ?>', '', '<TRUSTEDPACKAGES>', '    <FILE PATTERN="*.rpm" HASH="joea8923732d012c56db" ACTION="allow"/>', '    <FILE PATTERN="*.rpm" HASH="joea237832d012c56db" ACTION="allow"/>', '</TRUSTEDPACKAGES>']
         temp_jim_fn = arizonacrypt.sl_to_fn(jim_tp_sl)
         os.rename(temp_jim_fn, jim_tp_fn)
      
         arizonacrypt.XML_sign_file_using_privatekey_fn(jim_tp_fn, jim_privk)

         self.assertEquals(rank_packages([("abc.rpm","joea8923732d012c56db","unknown")]),([], [], [('abc.rpm', 'joea8923732d012c56db', 'unknown')]))
         self.assertEquals(rank_packages([("foo.rpm","joea8923732d012c56db","allow")]), ([('foo.rpm', 'joea8923732d012c56db', 'allow')], [], []))
         self.assertEquals(rank_packages([("foo.deb","anyhash","deny")]), ([],[('foo.deb', 'anyhash', 'deny')], []))
         self.assertEquals(rank_packages([("abc.rpm","joea8923732d012c56db","unknown"), ("foo.rpm","joea8923732d012c56db","allow"), ("foo.deb","anyhash","deny")]), ([ ("foo.rpm","joea8923732d012c56db","allow")],[ ("foo.deb","anyhash","deny")], [("abc.rpm","joea8923732d012c56db","unknown")]))

      finally:
         try:
            # Clean up
            os.remove(joe_tp_fn)
            os.remove(joe_pubk)
            os.remove(joe_privk)
            os.remove(jim_tp_fn)
            os.remove(jim_pubk)
            os.remove(jim_privk)
         except:
            pass
      
   def test_rank_packages_hierarchy(self):

      self.reset_options() 
   
      try: 
         arizonaconfig.init_options("stork.py", configfile_optvar="configfile", version="2.0")

         (top, top_privk, top_pubk, top_pubk_string, top_tp_fn) = init_keys("top")
         (sub1, sub1_privk, sub1_pubk, sub1_pubk_string, sub1_tp_fn) = init_keys("sub1")
         (sub2, sub2_privk, sub2_pubk, sub2_pubk_string, sub2_tp_fn) = init_keys("sub2")
         (bytime1, bytime1_privk, bytime1_pubk, bytime1_pubk_string, bytime1_tp_fn) = init_keys("bytime1")
         (bytime2, bytime2_privk, bytime2_pubk, bytime2_pubk_string, bytime2_tp_fn) = init_keys("bytime2")

         arizonaconfig.set_option("username",top)
         arizonaconfig.set_option("publickeyfile",top_pubk)
         arizonaconfig.set_option("tpdir","/tmp")
         arizonaconfig.set_option("tpdtd","trustedpackages.dtd")

         top_tp_sl = tpheader() + \
                     tpuser("*", sub1, sub1_pubk_string, "any", "default") + \
                     tpuser("*", sub2, sub2_pubk_string, "any", "default") + \
                     tpfooter()
                     
         tpsign(top_tp_sl, top_tp_fn, top_privk)

         # allow the following:
         #    foo-1.0.rpm
         #    foo-1.1.rpm
         #    bar-1.0-2.rpm
         #    bar*.rpm other than bar-1.0*.rpm
         # deny the following:
         #    bar-1.0*.rpm other than bar-1.0-2.rpm
         sub1_tp_sl = tpheader() + \
                     tpfile("foo-1.0.rpm",    "hashfoo10",  "allow") + \
                     tpfile("foo-1.1.rpm",    "hashfoo11",  "allow") + \
                     tpfile("bar-1.0-2.rpm",  "hashbar102", "allow") + \
                     tpfile("bar-1.0*.rpm",   "*",           "deny") + \
                     tpfile("bar-1.0-3.rpm",  "hashbar103", "allow") + \
                     tpfile("bar*.rpm",       "*",          "allow") + \
                     tpuser("*", bytime1, bytime1_pubk_string, "any", "timestamp") + \
                     tpuser("*", bytime2, bytime2_pubk_string, "any", "timestamp") + \
                     tpfooter()

         tpsign(sub1_tp_sl, sub1_tp_fn, sub1_privk)

         sub2_tp_sl = tpheader() + \
                     tpfile("foo-2.0.rpm",    "hashfoo20",  "allow") + \
                     tpfile("bar-1.0-5.rpm",  "hashbar105", "allow") + \
                     tpfile("bar-2*.rpm",     "*",          "deny") +  \
                     tpfooter()
                     
         tpsign(sub2_tp_sl, sub2_tp_fn, sub2_privk)

         bytime1_tp_sl = tpheader() + \
                     tpfile("lynx-1.0.rpm",   "hashlynx10", "allow", "1") + \
                     tpfooter()

         tpsign(bytime1_tp_sl, bytime1_tp_fn, bytime1_privk)

         bytime2_tp_sl = tpheader() +  \
                     tpfile("lynx-2.0.rpm",   "hashlynx20", "allow", "2") + \
                     tpfooter()     

         tpsign(bytime2_tp_sl, bytime2_tp_fn, bytime2_privk)

         # storktrustedpackagesparse.TrustedPackagesDump(None)

         # sub1's rules
         self.assertEquals(tprank("foo-1.0.rpm", "hashfoo10"), "allow")
         self.assertEquals(tprank("foo-1.1.rpm", "hashfoo11"), "allow")
         self.assertEquals(tprank("bar-0.93.rpm", "hashbar093"), "allow")
         self.assertEquals(tprank("bar-1.0-2.rpm", "hashbar102"), "allow")
         self.assertEquals(tprank("bar-1.0.rpm", "hashbar10"), "deny")
         self.assertEquals(tprank("bar-1.0-1.rpm", "hashbar101"), "deny")
         self.assertEquals(tprank("bar-1.0-3.rpm", "hashbar103"), "deny")
         
         # sub2's rules
         self.assertEquals(tprank("foo-2.0.rpm", "hashfoo20"), "allow")
         self.assertEquals(tprank("bar-1.0-5.rpm", "hashbar105"), "deny") # denied by sub1 and thus rule ignored in sub2
         self.assertEquals(tprank("bar-2.0.0.rpm", "hashbar200"), "allow") # allowed by sub1 and thus rule ignored in sub2

         # bytime rules 
         self.assertEquals(tprank("lynx-1.0.rpm", "hashlynx10"), "allow")
         self.assertEquals(tprank("lynx-2.0.rpm", "hashlynx20"), "allow")

         # package that does not exist
         self.assertEquals(tprank("nothing.rpm", "hashnothing"), "unspecified")

         # default ordering
         # foo-1.0.rpm occurred before foo-2.0.rpm, so it should
         # get ranked first
         self.assertEquals(tpranktwo("foo-1.0.rpm", "hashfoo10", 
                                     "foo-2.0.rpm", "hashfoo20"), 
                           ["foo-1.0.rpm", "foo-2.0.rpm"])
         # order of packages passed in shouldn't matter...
         self.assertEquals(tpranktwo("foo-2.0.rpm", "hashfoo20", 
                                     "foo-1.0.rpm", "hashfoo10"), 
                           ["foo-1.0.rpm", "foo-2.0.rpm"])


         # timestamp ordering
         # lynx-2.0.rpm has a higher timestamp than lynx-1.0.rpm, so it should
         # get ranked first
         self.assertEquals(tpranktwo("lynx-1.0.rpm", "hashlynx10", 
                                     "lynx-2.0.rpm", "hashlynx20"), 
                           ["lynx-2.0.rpm", "lynx-1.0.rpm"])
         # order of packages passed in shouldn't matter...
         self.assertEquals(tpranktwo("lynx-2.0.rpm", "hashlynx20", 
                                     "lynx-1.0.rpm", "hashlynx10"), 
                           ["lynx-2.0.rpm", "lynx-1.0.rpm"])

      finally:
         try:
            # Clean up
            os.remove(top_tp_fn)
            os.remove(top_pubk)
            os.remove(top_privk)
            os.remove(sub1_tp_fn)
            os.remove(sub1_pubk)
            os.remove(sub1_privk)
            os.remove(sub2_tp_fn)
            os.remove(sub2_pubk)
            os.remove(sub2_privk)
            os.remove(bytime1_tp_fn)
            os.remove(bytime1_pubk)
            os.remove(bytime1_privk)
            os.remove(bytime2_tp_fn)
            os.remove(bytime2_pubk)
            os.remove(bytime2_privk)
         except:
            pass

   def test_rank_packages_filter(self):

      self.reset_options() 
   
      try: 
         arizonaconfig.init_options("stork.py", configfile_optvar="configfile", version="2.0")

         (top, top_privk, top_pubk, top_pubk_string, top_tp_fn) = init_keys("top")
         (sub1, sub1_privk, sub1_pubk, sub1_pubk_string, sub1_tp_fn) = init_keys("sub1")
         (sub2, sub2_privk, sub2_pubk, sub2_pubk_string, sub2_tp_fn) = init_keys("sub2")
         (sub1a, sub1a_privk, sub1a_pubk, sub1a_pubk_string, sub1a_tp_fn) = init_keys("sub1a")
         (sub1b, sub1b_privk, sub1b_pubk, sub1b_pubk_string, sub1b_tp_fn) = init_keys("sub1b")

         arizonaconfig.set_option("username",top)
         arizonaconfig.set_option("publickeyfile",top_pubk)
         arizonaconfig.set_option("tpdir","/tmp")
         arizonaconfig.set_option("tpdtd","trustedpackages.dtd")

         top_tp_sl = tpheader() + \
                     tpuser("foo*", sub1, sub1_pubk_string, "any", "default") + \
                     tpuser("bar*", sub2, sub2_pubk_string, "any", "default") + \
                     tpfooter()
                     
         tpsign(top_tp_sl, top_tp_fn, top_privk)

         sub1_tp_sl = tpheader() + \
                     tpfile("foo-1.0.rpm",    "*",          "allow") + \
                     tpfile("bar-1.0.rpm",    "*",          "allow") + \
                     tpuser("*1.0*", sub1a, sub1a_pubk_string, "any", "timestamp") + \
                     tpuser("*2.0*", sub1b, sub1b_pubk_string, "any", "timestamp") + \
                     tpfooter()

         tpsign(sub1_tp_sl, sub1_tp_fn, sub1_privk)

         sub2_tp_sl = tpheader() + \
                     tpfile("foo-2.0.rpm",  "*", "allow") + \
                     tpfile("bar-2.0.rpm",  "*", "allow") + \
                     tpfooter()
                     
         tpsign(sub2_tp_sl, sub2_tp_fn, sub2_privk)

         sub1a_tp_sl = tpheader() + \
                     tpfile("foo-1.0-1.rpm",    "*",          "allow") + \
                     tpfile("bar-1.0-1.rpm",    "*",          "allow") + \
                     tpfile("foo-2.0-1.rpm",    "*",          "allow") + \
                     tpfile("bar-2.0-1.rpm",    "*",          "allow") + \
                     tpfooter()

         tpsign(sub1a_tp_sl, sub1a_tp_fn, sub1a_privk)

         sub1b_tp_sl = tpheader() + \
                     tpfile("foo-1.0-2.rpm",    "*",          "allow") + \
                     tpfile("bar-1.0-2.rpm",    "*",          "allow") + \
                     tpfile("foo-2.0-2.rpm",    "*",          "allow") + \
                     tpfile("bar-2.0-2.rpm",    "*",          "allow") + \
                     tpfooter()

         tpsign(sub1b_tp_sl, sub1b_tp_fn, sub1b_privk)



         # storktrustedpackagesparse.TrustedPackagesDump(None)

         # sub1's rules
         self.assertEquals(tprank("foo-1.0.rpm", "hashfoo10"), "allow")
         self.assertEquals(tprank("bar-1.0.rpm", "hashbar10"), "unspecified")

         # sub2's rules
         self.assertEquals(tprank("foo-2.0.rpm", "hashfoo20"), "unspecified")
         self.assertEquals(tprank("bar-2.0.rpm", "hashbar20"), "allow")

         # sub1a's rules
         self.assertEquals(tprank("foo-1.0-1.rpm", "hashfoo101"), "allow")
         self.assertEquals(tprank("bar-1.0-1.rpm", "hashbar101"), "unspecified")
         self.assertEquals(tprank("foo-2.0-1.rpm", "hashfoo101"), "unspecified")
         self.assertEquals(tprank("bar-2.0-1.rpm", "hashbar101"), "unspecified")

         # sub1b's rules
         self.assertEquals(tprank("foo-1.0-2.rpm", "hashfoo101"), "unspecified")
         self.assertEquals(tprank("bar-1.0-2.rpm", "hashbar101"), "unspecified")
         self.assertEquals(tprank("foo-2.0-2.rpm", "hashfoo101"), "allow")
         self.assertEquals(tprank("bar-2.0-2.rpm", "hashbar101"), "unspecified")


      finally:
         try:
            # Clean up
            os.remove(top_tp_fn)
            os.remove(top_pubk)
            os.remove(top_privk)
            os.remove(sub1_tp_fn)
            os.remove(sub1_pubk)
            os.remove(sub1_privk)
            os.remove(sub2_tp_fn)
            os.remove(sub2_pubk)
            os.remove(sub2_privk)
            os.remove(sub1a_tp_fn)
            os.remove(sub1a_pubk)
            os.remove(sub1a_privk)
            os.remove(sub1b_tp_fn)
            os.remove(sub1b_pubk)
            os.remove(sub1b_privk)

         except:
            pass

   #------------------------------------------------------------------
   # init():
   #------------------------------------------------------------------
   def test_init(self):
      pass



# Run tests
if __name__ == '__main__':
   arizonaconfig.init_options() 
   arizonaunittest.main()
