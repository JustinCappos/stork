#! /usr/bin/env python
"""
<Module>
   arizonaconfigTest
<Author>
   Jeffry Johnston, under the direction of Justin Cappos
<Started>
   July 23, 2005
<Purpose>
   Test module for arizonaconfig.  See arizonaconfig.py for more details.
"""

# testing TODO:

# What happens when __build_options_block has to read a file that cannot
# be read? (disk failure, insufficient permissions, etc).  Not sure how to
# test for this situation.


import atexit
import os
import arizonaconfig
import arizonaunittest

# these variables define the python source that will be read by arizonaconfig
# and the .conf file that will be used.
TEST_FILE = "test/arizonaconfigTest_testfile.py"
TEST_CONFIG_FILE = "arizonaconfigTest.conf"
TEST_CONFIG_DIR = "arizonaconfigTest.d"

def create_config_files():
      # build new config file
      out = file(TEST_CONFIG_FILE, "w")
      out.write("""packagetype rpm
digest= sha1
username =  PlanetLab
packagerepository =  ftp://quadrus.cs.arizona.edu/PlanetLab/V3|dist, stable
packageinforepository =  ftp://quadrus.cs.arizona.edu/PlanetLab/V3/stork.info
keyrepository =  ftp://quadrus.cs.arizona.edu/keyfile
noupdatekeyfiles
disablekeyfiles
transfermethod slice
rv0=0
rv1=1
rv2=2
repository=rep1
rv1=1001
rv3=1003
repositoryend
repository=rep2
rv2=2002
rv3=2003
rv4=2004
repositoryend
include=arizonaconfigTest.d/*.conf
""")
      out.close()

      try:
         os.mkdir(TEST_CONFIG_DIR)
      except OSError:
         pass

      out = file(os.path.join(TEST_CONFIG_DIR, "1.conf"), "w")
      out.write("""
repository=rep3
rv1=3001
repositoryend
""")
      out.close()

def cleanup():
   os.system("rm " + TEST_CONFIG_FILE)
   os.system("rm " + os.path.join(TEST_CONFIG_DIR, "1.conf"))
   os.system("rmdir " + TEST_CONFIG_DIR)

# Unit tests for each function, listed in code order
class test(arizonaunittest.TestCase):
   def setUp(self):
      arizonaunittest.TestCase.setUp(self)
      #atexit.register(cleanup)
      create_config_files()

   def tearDown(self):
      arizonaunittest.TestCase.tearDown(self)
      cleanup()

   #------------------------------------------------------------------
   # init_options(module="*", usage=None, version=None, configfile=True)
   #------------------------------------------------------------------
   def test_init_options(self):
      # test bad input params
      self.assertException(TypeError, arizonaconfig.init_options, 100)
      self.assertException(TypeError, arizonaconfig.init_options, "*", True)
      self.assertException(TypeError, arizonaconfig.init_options, "arizonaconfigTest.py", 100)
      self.assertException(TypeError, arizonaconfig.init_options, "*", None, 100)
      # FIXME self.assertException(TypeError, arizonaconfig.init_options, "*", None, None, 100)
    
      # test default usage statement
      self.set_cmdline(["--help"])
      self.assertException(SystemExit, arizonaconfig.init_options, "*", "arizonaconfigTest.py")
      self.assertTrue(self.stdout().startswith("usage: * [options]\n\noptions:\n  -h"))

      # test custom usage statement
      self.reset_stdout()
      self.assertException(SystemExit, arizonaconfig.init_options,"*", "arizonaconfigTest.py", [], """line1
  line2""")
      self.assertTrue(self.stdout().startswith("""usage: line1
  line2"""))

      # test default version (there isn't one, so --version should give usage)
      self.set_cmdline(["--version"])
      self.reset_stderr()
      self.assertException(SystemExit, arizonaconfig.init_options)
      self.assertTrue(self.stderr().startswith("""no such option: --version
Try '--help' for an informative help message"""))

      # test custom version
      self.reset_stdout()
      self.assertException(SystemExit, arizonaconfig.init_options, "arizonaconfigTest.py", ".", [], None, "1.00")
      self.assertTrue(self.stdout().startswith("storktests.py 1.00"))

      # test --debug-help
      self.set_cmdline([""])
      self.reset_stdout()
# SMB: I'm not sure what this is supposed to do -- investigate what debug=True means
#  to arizonaconfig.init_options and write an appropriate test
#      self.assertException(SystemExit, arizonaconfig.init_options, "arizonatransfer.py", ".", [], None, "1.00", None, True)
#      self.assertStdout( ??? )

      return # XXX finishme

      # test --help plain
      self.set_cmdline(["--help"])
      self.reset_stdout()
      self.assertException(SystemExit, arizonaconfig.init_options, TEST_FILE)
      self.assertStdout(
"""usage: test/arizonaconfigTest_testfile.py [options]

options:
  -h, --help            show this help message and exit
  -CFILE, --configfile=FILE
                        use a different config file (arizonaconfigTest.conf is
                        the default)
  --listenport=PORT     bind to this port (default 648)
  --bindfiles=DIRECTORY
                        location of the files to copy to the client upon
                        binding
  --retrievedir=DIRECTORY
                        location to put retrieved files (default
                        /usr/local/stork/var/packages)
  --not-daemon          specify that program should not attempt to detach from
                        the terminal
  --localoutput         display output locally, do not send to client
  --sliceport=PORT      unknown (default 640)
  --nesttype=NAME       the type of nest to be used (default planetlab)
  --transfermethod=program
                        use this method to transfer files (default ftp, http)
  --transfertempdir=PATH
                        use this path to save transferd files temporary
                        (default is /tmp/stork_trans_tmp)
  --metafilecachetime=METAFILECACHETIME
                        seconds to cache metafile without re-requesting
  -Q, --veryquiet       be very quiet
  -q, --quiet           be quiet
  -v, --verbose         be verbose (default)
  -V, --veryverbose     be very verbose (useful for debugging)
  --ultraverbose        be extremely verbose (might be useful for debugging)
""")

      # test --help usage
      self.set_cmdline(["--help"])
      self.reset_stdout()
      self.assertException(SystemExit, arizonaconfig.init_options, "*", None, "ABCDEF")
      self.debug_print(self.stdout())
      self.assertTrue(self.stdout().startswith("usage: ABCDEF"))

      # test --help version
      self.set_cmdline(["--version"])
      self.reset_stdout()
      self.assertException(SystemExit, arizonaconfig.init_options, "*", None, None, "1.00")
      self.assertStdout("""arizonaconfigTest.py 1.00
""")

      # test returned args
      self.set_cmdline(["not options"])
      self.assertEqual(arizonaconfig.init_options(), ["not options"])





   #------------------------------------------------------------------
   # get_option(variable)
   #------------------------------------------------------------------
   def test_get_option(self):
      # try to get option when arizonaconfig hasn't been initialized
      reload(arizonaconfig)
      self.assertEqual(arizonaconfig.get_option("digest"), None)
      self.assertEqual(arizonaconfig.get_option("xyz"), None)

      # pass bad/missing params (string expected)
      self.assertException(TypeError, arizonaconfig.get_option)
      self.assertException(TypeError, arizonaconfig.get_option, None)
      self.assertException(TypeError, arizonaconfig.get_option, True)
      self.assertException(TypeError, arizonaconfig.get_option, ["digest"])

      # empty string should be okay
      self.assertEqual(arizonaconfig.get_option(""), None)

      # with config file, no command line
      self.set_cmdline([])
      arizonaconfig.init_options(TEST_FILE, configfile_optvar='configfile')

      # test when config file == default, result = config file/default
      self.assertEqual(arizonaconfig.get_option("nesttype"), "planetlab")

      # test when config file != default, result = config file
      self.assertEqual(arizonaconfig.get_option("transfermethod"), ["slice"])

      # test when no option in config file but there is default, result = default
      self.assertEqual(arizonaconfig.get_option("configfile"), TEST_CONFIG_FILE)
      self.assertEqual(arizonaconfig.get_option("verbose"), 2)
      self.assertEqual(arizonaconfig.get_option("sliceport"), "640")

      # test when there is no option in config file or default, result = None
      self.assertEqual(arizonaconfig.get_option("xyz"), None)

      # sectioned variables - check those not in sections
      self.assertEqual(arizonaconfig.get_option("rv0"), "0")
      self.assertEqual(arizonaconfig.get_option("rv1"), "1")
      self.assertEqual(arizonaconfig.get_option("rv2"), "2")
      self.assertEqual(arizonaconfig.get_option("rv3"), "643")
      self.assertEqual(arizonaconfig.get_option("rv4"), "644")

      # the list of sections
      self.assertEqual(arizonaconfig.get_option("repository"), ["rep1", "rep2", "rep3"])

      # sectioned variables
      self.assertEqual(arizonaconfig.get_option("rep1.rv1"), "1001")
      self.assertEqual(arizonaconfig.get_option("rep1.rv3"), "1003")
      self.assertEqual(arizonaconfig.get_option("rep2.rv2"), "2002")
      self.assertEqual(arizonaconfig.get_option("rep2.rv3"), "2003")
      self.assertEqual(arizonaconfig.get_option("rep2.rv4"), "2004")



      # with config file and command line
      self.set_cmdline(["--quiet", "--sliceport=30000"])
      arizonaconfig.init_options(TEST_FILE, configfile_optvar='configfile')

      # test when config file == default, result = config file (or) default
      self.assertEqual(arizonaconfig.get_option("nesttype"), "planetlab")

      # test when config file != default, result = config file
      self.assertEqual(arizonaconfig.get_option("transfermethod"), ["slice"])

      # test when no option in config file but there is on cmdline, result = cmdline
      self.assertEqual(arizonaconfig.get_option("verbose"), 1)
      self.assertEqual(arizonaconfig.get_option("sliceport"), "30000")

      # test when no option in config file, or cmdline, result = default
      self.assertEqual(arizonaconfig.get_option("configfile"), TEST_CONFIG_FILE)

      # test when there is no option in config file or default, result = None
      self.assertEqual(arizonaconfig.get_option("xyz"), None)



      # without config file, no command line
      self.set_cmdline([])
      arizonaconfig.init_options(TEST_FILE)

      # there is default, result = default
      self.assertEqual(arizonaconfig.get_option("nesttype"), "planetlab")
      self.assertEqual(arizonaconfig.get_option("configfile"), TEST_CONFIG_FILE)
      self.assertEqual(arizonaconfig.get_option("transfermethod"), ["ftp", "http"])

      # test when there is no option, result = None
      self.assertEqual(arizonaconfig.get_option("xyz"), None)



      # without config file, with command line
      self.set_cmdline(["--quiet", "--nesttype=vserver"])
      arizonaconfig.init_options(TEST_FILE)

      # test there is on cmdline, result = cmdline
      self.assertEqual(arizonaconfig.get_option("verbose"), 1)
      self.assertEqual(arizonaconfig.get_option("nesttype"), "vserver")

      # test when no option on cmdline, result = default
      self.assertEqual(arizonaconfig.get_option("configfile"), TEST_CONFIG_FILE)
      self.assertEqual(arizonaconfig.get_option("transfermethod"), ["ftp", "http"])

      # test when there is no option, result = None
      self.assertEqual(arizonaconfig.get_option("xyz"), None)


   #------------------------------------------------------------------
   # get_option_section(variable, section)
   #------------------------------------------------------------------
   def test_get_option_section(self):
      # try to get option when arizonaconfig hasn't been initialized
      reload(arizonaconfig)
      self.assertEqual(arizonaconfig.get_option_section("digest"), None)

      # pass bad/missing params (string expected)
      self.assertException(TypeError, arizonaconfig.get_option_section)
      self.assertException(TypeError, arizonaconfig.get_option_section, None)
      self.assertException(TypeError, arizonaconfig.get_option_section, True)
      self.assertException(TypeError, arizonaconfig.get_option_section, ["digest"])

      # empty string should be okay
      self.assertEqual(arizonaconfig.get_option_section(""), None)

      # with config file, no command line
      self.set_cmdline([])
      arizonaconfig.init_options(TEST_FILE, configfile_optvar='configfile')

      self.assertEqual(arizonaconfig.get_option_section("rv0"), "0")
      self.assertEqual(arizonaconfig.get_option_section("rv1", "rep1"), "1001")
      self.assertEqual(arizonaconfig.get_option_section("rv2", "rep1"), "2")
      self.assertEqual(arizonaconfig.get_option_section("rv4", "rep1"), "644")
      self.assertEqual(arizonaconfig.get_option_section("rv1", "rep2"), "1")
      self.assertEqual(arizonaconfig.get_option_section("rv2", "rep2"), "2002")




   #------------------------------------------------------------------
   # get_sections(variable)
   #------------------------------------------------------------------
   def test_get_sections(self):
      # try to get option when arizonaconfig hasn't been initialized
      reload(arizonaconfig)
      self.assertEqual(arizonaconfig.get_sections("digest"), [])

      # pass bad/missing params (string expected)
      self.assertException(TypeError, arizonaconfig.get_sections)
      self.assertException(TypeError, arizonaconfig.get_sections, None)
      self.assertException(TypeError, arizonaconfig.get_sections, True)
      self.assertException(TypeError, arizonaconfig.get_sections, ["digest"])

      # empty string should be okay
      self.assertEqual(arizonaconfig.get_sections(""), [])

      # with config file, no command line
      self.set_cmdline([])
      arizonaconfig.init_options(TEST_FILE, configfile_optvar='configfile')

      self.assertEqual(arizonaconfig.get_sections("rv0"), [])
      self.assertEqual(arizonaconfig.get_sections("rv1"), ["rep1", "rep3"])
      self.assertEqual(arizonaconfig.get_sections("rv2"), ["rep2"])
      self.assertEqual(arizonaconfig.get_sections("rv3"), ["rep1", "rep2"])




   #------------------------------------------------------------------
   # set_option(variable, value)
   #------------------------------------------------------------------
   def test_set_option(self):
      # try to set option when arizonaconfig hasn't been initialized
      reload(arizonaconfig)
      self.assertException(UnboundLocalError, arizonaconfig.set_option, "xyz", "abc")

      self.set_cmdline([])
      arizonaconfig.init_options()

      # test invalid/missing params
      self.assertException(TypeError, arizonaconfig.set_option, True, "123")
      self.assertException(TypeError, arizonaconfig.set_option, "missing")

      # try setting option which does not yet exist (create new option)
      arizonaconfig.set_option("xyz", "abc")
      self.assertEqual(arizonaconfig.get_option("xyz"), "abc")

      # change existing option
      self.assertEqual(arizonaconfig.get_option("digest"), "sha1")
      arizonaconfig.set_option("digest", "pgp")
      self.assertEqual(arizonaconfig.get_option("digest"), "pgp")




   
   #------------------------------------------------------------------
   # get_version()
   #------------------------------------------------------------------
   def test_get_version(self):
      # test version not set, result = None
      arizonaconfig.init_options()
      self.assertEqual(arizonaconfig.get_version(), None)
      
      # test setting the version
      arizonaconfig.init_options(version="1.2.3")
      self.assertEqual(arizonaconfig.get_version(), "1.2.3")



# Run tests
if __name__=='__main__':
   arizonaunittest.main()
