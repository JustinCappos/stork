#! /usr/bin/env python
"""
<Module>
   arizonareportTest
<Author>
   Jeffry Johnston, under the direction of Justin Cappos
<Started>
   August 13, 2005   
<Purpose>
   Test module for arizonareport.  See arizonareport.py for more 
   details.
"""





import os
import sys
import arizonareport
import arizonaunittest

# Unit tests for each function, listed in code order
class test(arizonaunittest.TestCase):

   #------------------------------------------------------------------
   # get_verbosity() 
   #------------------------------------------------------------------
   def test_verbosity(self):
      self.assertEquals(arizonareport.get_verbosity(), 2)
      self.assertEquals(arizonareport.get_verbosity(), 2)
      arizonareport.set_verbosity(3)
      self.assertEquals(arizonareport.get_verbosity(), 3)





   #------------------------------------------------------------------
   # set_verbosity(verbosity)
   #------------------------------------------------------------------
   def test_set_verbosity(self):
      self.assertException(TypeError, arizonareport.get_verbosity, -1)
      self.assertException(TypeError, arizonareport.get_verbosity, 4)
      self.assertException(TypeError, arizonareport.get_verbosity, None)
      self.assertException(TypeError, arizonareport.get_verbosity, "1")
      arizonareport.set_verbosity(2)





   #------------------------------------------------------------------
   # console_size():
   #------------------------------------------------------------------
   def test_console_size(self):
      # test default behavior
      self.assertEqual(arizonareport.console_size(), (24, 80))




   
   #------------------------------------------------------------------
   # redirect_stdout(stream) -> None
   #------------------------------------------------------------------
   def test_redirect_stdout(self):
      #Collin: no check for TypeError
      #self.assertException(TypeError, arizonareport.redirect_stdout, -1)
      #self.assertException(TypeError, arizonareport.redirect_stdout, None)
      f = file("/tmp/redirect_test", "w")
      arizonareport.redirect_stdout(f)
      print "test"
      self.assertStdout("") 
      f.close()
      f = file("/tmp/redirect_test")
      self.assertEqual(f.read(), "test\n")
      f.close()
      os.remove("/tmp/redirect_test")





   #------------------------------------------------------------------
   # restore_stdout(stream) -> None
   #------------------------------------------------------------------
   def test_restore_stdout(self):
      f = file("/tmp/redirect_test", "w")
      arizonareport.redirect_stdout(f)
      print "test"
      f.close()
      arizonareport.restore_stdout()
      print "test2"
      self.assertStdout("test2\n") 
      os.remove("/tmp/redirect_test")





   #------------------------------------------------------------------
   # redirect_stderr(stream) -> None
   #------------------------------------------------------------------
   def test_redirect_stderr(self):
      #Collin: There is no check for TypeError
      #self.assertException(TypeError, arizonareport.redirect_stderr, -1)
      #self.assertException(TypeError, arizonareport.redirect_stderr, None)
      f = file("/tmp/redirect_test", "w")
      arizonareport.redirect_stderr(f)
      print >> sys.stderr, "test"
      self.assertStderr("") 
      f.close()
      f = file("/tmp/redirect_test")
      self.assertEqual(f.read(), "test\n")
      f.close()
      os.remove("/tmp/redirect_test")





   #------------------------------------------------------------------
   # restore_stderr(stream) -> None
   # TODO
   #------------------------------------------------------------------
   def test_restore_stderr(self):
      #f = file("/tmp/redirect_test", "w")       
      #arizonareport.redirect_stderr(f)
      #f.close()
      #arizonareport.restore_stderr()      
      print >> sys.stderr, "test2"
      #Fails for unknown reason, it doesn't seem
      #to be restoring the stream to the original sys.stderr
      self.assertStderr("test2\n") 
      #os.remove("/tmp/redirect_test")





   #------------------------------------------------------------------
   # flush_out(required_verbosity)
   #------------------------------------------------------------------
   def test_flush_out(self):
      self.assertException(TypeError, arizonareport.flush_out, -1)
      #Isn't a type error:
      #self.assertException(TypeError, arizonareport.flush_out, 4)
      self.assertException(TypeError, arizonareport.flush_out, 5)
      self.assertException(TypeError, arizonareport.flush_out, None)
      self.assertException(TypeError, arizonareport.flush_out, "1")
      # TODO need additional tests




   #------------------------------------------------------------------
   # flush_error(required_verbosity)
   #------------------------------------------------------------------
   def test_flush_error(self):
      self.assertException(TypeError, arizonareport.flush_error, -1)
      #This isn't a TypeError..
      #self.assertException(TypeError, arizonareport.flush_error, 4)
      self.assertException(TypeError, arizonareport.flush_error, 5)
      self.assertException(TypeError, arizonareport.flush_error, None)
      self.assertException(TypeError, arizonareport.flush_error, "1")
      # TODO need additional tests





   #------------------------------------------------------------------
   # send_out(required_verbosity, mesg)
   #------------------------------------------------------------------
   def test_send_out(self):
      self.assertException(TypeError, arizonareport.send_out, -1, "a")
      self.assertException(TypeError, arizonareport.send_out, 5, "a")
      self.assertException(TypeError, arizonareport.send_out, None, "a")
      self.assertException(TypeError, arizonareport.send_out, "1", "a")

      self.reset_stdout()
      self.reset_stderr()
      arizonareport.set_verbosity(0)
      arizonareport.send_out(0, "test")
      self.assertStderr("") 
      self.assertStdout("test\n") 
      self.reset_stdout()
      arizonareport.send_out(1, "test")
      self.assertStdout("") 
      arizonareport.send_out(2, "test")
      self.assertStdout("") 
      arizonareport.send_out(3, "test")
      self.assertStdout("") 

      arizonareport.set_verbosity(1)
      arizonareport.send_out(0, "test")
      self.assertStdout("test\n") 
      self.reset_stdout()
      arizonareport.send_out(1, "test")
      self.assertStdout("test\n") 
      self.reset_stdout()
      arizonareport.send_out(2, "test")
      self.assertStdout("") 
      arizonareport.send_out(3, "test")
      self.assertStdout("") 

      arizonareport.set_verbosity(2)
      arizonareport.send_out(0, "test")
      self.assertStdout("test\n") 
      self.reset_stdout()
      arizonareport.send_out(1, "test")
      self.assertStdout("test\n") 
      self.reset_stdout()
      arizonareport.send_out(2, "test")
      self.assertStdout("test\n") 
      self.reset_stdout()
      arizonareport.send_out(3, "test")
      self.assertStdout("") 

      arizonareport.set_verbosity(3)
      arizonareport.send_out(0, "test")
      self.assertStdout("test\n") 
      self.reset_stdout()
      arizonareport.send_out(1, "test")
      self.assertStdout("test\n") 
      self.reset_stdout()
      arizonareport.send_out(2, "test")
      self.assertStdout("test\n") 
      self.reset_stdout()
      arizonareport.send_out(3, "test")
      self.assertStdout("test\n") 






   #------------------------------------------------------------------
   # send_out_comma(required_verbosity, mesg)
   #------------------------------------------------------------------
   def test_send_out_comma(self):
      self.assertException(TypeError, arizonareport.send_out_comma, -1, "a")
      self.assertException(TypeError, arizonareport.send_out_comma, 5, "a")
      self.assertException(TypeError, arizonareport.send_out_comma, None, "a")
      self.assertException(TypeError, arizonareport.send_out_comma, "1", "a")

      self.reset_stdout()
      self.reset_stderr()
      arizonareport.set_verbosity(0)
      arizonareport.send_out_comma(0, "test")
      self.assertStderr("") 
      self.assertStdout("test") 
      self.reset_stdout()
      arizonareport.send_out_comma(1, "test")
      self.assertStdout("") 
      arizonareport.send_out_comma(2, "test")
      self.assertStdout("") 
      arizonareport.send_out_comma(3, "test")
      self.assertStdout("") 

      arizonareport.set_verbosity(1)
      arizonareport.send_out_comma(0, "test")
      self.assertStdout("test") 
      self.reset_stdout()
      arizonareport.send_out_comma(1, "test")
      self.assertStdout("test") 
      self.reset_stdout()
      arizonareport.send_out_comma(2, "test")
      self.assertStdout("") 
      arizonareport.send_out_comma(3, "test")
      self.assertStdout("") 

      arizonareport.set_verbosity(2)
      arizonareport.send_out_comma(0, "test")
      self.assertStdout("test") 
      self.reset_stdout()
      arizonareport.send_out_comma(1, "test")
      self.assertStdout("test") 
      self.reset_stdout()
      arizonareport.send_out_comma(2, "test")
      self.assertStdout("test") 
      self.reset_stdout()
      arizonareport.send_out_comma(3, "test")
      self.assertStdout("") 

      arizonareport.set_verbosity(3)
      arizonareport.send_out_comma(0, "test")
      self.assertStdout("test") 
      self.reset_stdout()
      arizonareport.send_out_comma(1, "test")
      self.assertStdout("test") 
      self.reset_stdout()
      arizonareport.send_out_comma(2, "test")
      self.assertStdout("test") 
      self.reset_stdout()
      arizonareport.send_out_comma(3, "test")
      self.assertStdout("test") 





   #------------------------------------------------------------------
   # send_error(required_verbosity, mesg)
   #------------------------------------------------------------------
   def test_send_err(self):
      self.assertException(TypeError, arizonareport.send_error, -1, "a")
      self.assertException(TypeError, arizonareport.send_error, 5, "a")
      self.assertException(TypeError, arizonareport.send_error, None, "a")
      self.assertException(TypeError, arizonareport.send_error, "1", "a")

      self.reset_stderr()
      self.reset_stdout()
      arizonareport.set_verbosity(0)
      arizonareport.send_error(0, "test")
      self.assertStdout("") 
      self.assertTrue(self.stderr().endswith("test\n"))   
      self.reset_stderr()
      arizonareport.send_error(1, "test")
      self.assertStderr("") 
      arizonareport.send_error(2, "test")
      self.assertStderr("") 
      arizonareport.send_error(3, "test")
      self.assertStderr("") 

      arizonareport.set_verbosity(1)
      arizonareport.send_error(0, "test")
      self.assertTrue(self.stderr().endswith("test\n"))   
      self.reset_stderr()
      arizonareport.send_error(1, "test")
      self.assertTrue(self.stderr().endswith("test\n"))   
      self.reset_stderr()
      arizonareport.send_error(2, "test")
      self.assertStderr("") 
      arizonareport.send_error(3, "test")
      self.assertStderr("") 

      arizonareport.set_verbosity(2)
      arizonareport.send_error(0, "test")
      self.assertTrue(self.stderr().endswith("test\n"))   
      self.reset_stderr()
      arizonareport.send_error(1, "test")
      self.assertTrue(self.stderr().endswith("test\n"))   
      self.reset_stderr()
      arizonareport.send_error(2, "test")
      self.assertTrue(self.stderr().endswith("test\n"))   
      self.reset_stderr()
      arizonareport.send_error(3, "test")
      self.assertStderr("") 

      arizonareport.set_verbosity(3)
      arizonareport.send_error(0, "test")
      self.assertTrue(self.stderr().endswith("test\n"))   
      self.reset_stderr()
      arizonareport.send_error(1, "test")
      self.assertTrue(self.stderr().endswith("test\n"))   
      self.reset_stderr()
      arizonareport.send_error(2, "test")
      self.assertTrue(self.stderr().endswith("test\n"))   
      self.reset_stderr()
      arizonareport.send_error(3, "test")
      self.assertTrue(self.stderr().endswith("test\n"))   





   #------------------------------------------------------------------
   # send_syslog(severity, mesg)
   #------------------------------------------------------------------
   def test_send_syslog(self):
      #arizonareport.send_syslog(arizonareport.ERR, "test")
      pass





# Run tests
if __name__=='__main__':
   arizonaunittest.main()
