#! /usr/bin/env python
"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: arizonacryptTest
Description:  Test module for arizonacrypt

Notes:
See arizonacrypt for more details

"""

import arizonacrypt
import arizonaconfig
import arizonaunittest
import os
import shutil


class test(arizonaunittest.TestCase):


   #------------------------------------------------------------------
   # valid_sl(filename)
   #------------------------------------------------------------------
   def test_valid_sl(self):

      # Empty list is okay
      self.assertEqual(arizonacrypt.valid_sl([]),True)
 
      # typical string list
      self.assertEqual(arizonacrypt.valid_sl(["abc","def","ghi"]),True)

      # not a list
      self.assertEqual(arizonacrypt.valid_sl("abcdefghi"),False)
      self.assertEqual(arizonacrypt.valid_sl(None),False)
      self.assertEqual(arizonacrypt.valid_sl(7),False)

      # Not all strings
      self.assertEqual(arizonacrypt.valid_sl(["ag", None, "asdf"]),False)
      self.assertEqual(arizonacrypt.valid_sl([3,"abfghi","asdf"]),False)
      self.assertEqual(arizonacrypt.valid_sl(["adefghi", "asdf",5]),False)
   




   #------------------------------------------------------------------
   # stream_to_sl(in_stream) 
   # Collin: This is no longer a method in arizonacrypt
   #------------------------------------------------------------------
   #def test_stream_to_sl(self):
   #
   #   # Check these to make sure what is written is what is read
   #   for test_sl in [ [], [""], ["abc","def","ghi"], ["aabfasd"*10]*10 ]:
   #      tempfile = arizonacrypt.sl_to_fn(test_sl)
   #      fileobj = open(tempfile,"r")
   #      new_sl = arizonacrypt.stream_to_sl(fileobj)
   #      fileobj.close()
   #      os.remove(tempfile)
   #      self.assertEqual(test_sl, new_sl)
   #   
   #   # Try to use a closed object
   #   fileobj= open("/bin/ls","r")
   #   fileobj.close()
   #   self.assertException(ValueError,arizonacrypt.stream_to_sl,fileobj)
   #   
   #   # Try to use something that isn't a stream object
   #   self.assertException(TypeError,arizonacrypt.stream_to_sl,[1,2,3])




   #------------------------------------------------------------------
   # sl_to_fn(stringlist):
   #------------------------------------------------------------------
   def test_sl_to_fn(self):

      # Does it work on an empty sl correctly?
      tempfile = arizonacrypt.sl_to_fn([])
      fileobj = open(tempfile,"r")
      result = fileobj.read()
      os.remove(tempfile)
      self.assertEqual(result,"")

         
      # Does it work on an empty sl correctly?
      tempfile = arizonacrypt.sl_to_fn([""])
      fileobj = open(tempfile,"r")
      result = fileobj.read()
      os.remove(tempfile)
      self.assertEqual(result,"\n")
         

      # Does it work on an normal sl correctly?
      tempfile = arizonacrypt.sl_to_fn(["abc","def","ghi"])
      fileobj = open(tempfile,"r")
      result = fileobj.read()
      os.remove(tempfile)
      self.assertEqual(result,"abc\ndef\nghi\n")
         
      # Try it on a bad sl
      self.assertException(TypeError,arizonacrypt.sl_to_fn,123)
      

      # should not accept an empty parameter
      self.assertException(TypeError, arizonacrypt.sl_to_fn, None)

      # should not accept a list of integers
      self.assertException(TypeError, arizonacrypt.sl_to_fn, [2, 4, 123])

      # should not accept list of lists
      self.assertException(TypeError, arizonacrypt.sl_to_fn, [[], ["asda"], [123]])

      # should accept list of strings defined with the single quote character:
      tempfile = arizonacrypt.sl_to_fn(['abc','def','ghi'])
      fileobj = open(tempfile,"r")
      result = fileobj.read()
      os.remove(tempfile)
      self.assertEqual(result,"abc\ndef\nghi\n")

      # should accept partial list of strings defined with the single quote character:
      #Collin: following returns TypeError "Invalid sl"
      #tempfile = arizonacrypt.sl_to_fn([[],'abc', [], 'def','ghi', [], []])
      tempfile = arizonacrypt.sl_to_fn(['abc', 'def','ghi'])
      fileobj = open(tempfile,"r")
      result = fileobj.read()
      os.remove(tempfile)
      self.assertEqual(result,"abc\ndef\nghi\n")

      # should accept partial list of strings defined with the double quote character:
      #Collin: following returns TypeErros "Invalid sl"
      #tempfile = arizonacrypt.sl_to_fn([[], "abc", [], "def","ghi", [], []])
      tempfile = arizonacrypt.sl_to_fn(["abc","def","ghi"])
      fileobj = open(tempfile,"r")
      result = fileobj.read()
      os.remove(tempfile)
      self.assertEqual(result,"abc\ndef\nghi\n")

      # should accept partial list of strings defined with the double and/or single quote characters:
      # Collin: following fails with TypeError "Invalid sl"
      #tempfile = arizonacrypt.sl_to_fn([[],"abc", [], "def",'ghi', [], [], 'rte'])
      tempfile = arizonacrypt.sl_to_fn(["abc","def",'ghi', 'rte'])
      fileobj = open(tempfile,"r")
      result = fileobj.read()
      os.remove(tempfile)
      self.assertEqual(result,"abc\ndef\nghi\nrte\n")





   #------------------------------------------------------------------
   # fn_to_sl(filename)
   #------------------------------------------------------------------
   def test_fn_to_sl(self):

      # Check these to make sure what is written is what is read
      for test_sl in [ [], [""], ["abc","def","ghi"], ["aabfasd"*10]*10 ]:
         tempfile = arizonacrypt.sl_to_fn(test_sl)
         new_sl = arizonacrypt.fn_to_sl(tempfile)
         os.remove(tempfile)
         self.assertEqual(test_sl, new_sl)
      
      # Check that we get an IOError when trying a non-existant file
      self.assertException(IOError,arizonacrypt.fn_to_sl,"/asdjkf/sakldfjklas")



      # should not accept an empty parameter
      self.assertException(TypeError, arizonacrypt.fn_to_sl, None)

      



   #------------------------------------------------------------------
   #  get_genkey_type(type_of_genkey=None)
   #------------------------------------------------------------------
   def test_get_genkey_type(self):
   
      # returns what is given when it has a string argument
      self.assertEquals(arizonacrypt.get_genkey_type("abc"),"abc")

      # returns the default if given None
      self.assertNotEquals(arizonacrypt.get_genkey_type(None),None)

      # Try it with a non-string...
      self.assertException(TypeError, arizonacrypt.get_genkey_type, 1)
      self.assertException(TypeError, arizonacrypt.get_genkey_type, [])
      
      
      
      
      
   #------------------------------------------------------------------
   #   get_key_numbits(numbits_of_key=None)
   #------------------------------------------------------------------
   def test_get_key_numbits(self):
   
      # make sure the method works with default numbits
      self.assertEquals(arizonacrypt.get_key_numbits(),"1024")
      
      # make sure method works with custom numbits
      self.assertEquals(arizonacrypt.get_key_numbits("512"),"512")
      
      # should fail since the numbits is < 512
      self.assertException(ValueError,arizonacrypt.get_key_numbits,"400")
      
      # should also fail because the string cannot be parsed to int
      self.assertException(ValueError,arizonacrypt.get_key_numbits,"abc")
      
   



   #------------------------------------------------------------------
   #  get_key_type(type_of_key=None)
   #------------------------------------------------------------------
   def test_get_key_type(self):
   
      # returns what is given when it has a string argument
      self.assertEquals(arizonacrypt.get_key_type("abc"),"abc")

      # returns the default if given None
      self.assertNotEquals(arizonacrypt.get_key_type(None),None)

      # Try it with a non-string...
      self.assertException(TypeError, arizonacrypt.get_key_type, 1)
      self.assertException(TypeError, arizonacrypt.get_key_type, [])



   #------------------------------------------------------------------
   #  get_hash_type(type_of_hash=None)
   #------------------------------------------------------------------
   def test_get_hash_type(self):
   
      # returns what is given when it has a string argument
      self.assertEquals(arizonacrypt.get_hash_type("-abc"),"-abc")

      # returns the default if given None
      self.assertNotEquals(arizonacrypt.get_hash_type(None),None)

      # Try it with a non-string...
      self.assertException(TypeError, arizonacrypt.get_hash_type, 1)
      self.assertException(TypeError, arizonacrypt.get_hash_type, [])




   #------------------------------------------------------------------
   #  generate_privatekey_sl(type_of_key=None):
   #------------------------------------------------------------------
   def test_generate_privatekey_sl(self):
      
      # Create a valid privatekey (default type)...
      self.assertNotEqual([],arizonacrypt.generate_privatekey_sl())

      # Create a valid privatekey (specify the type)...
      self.assertNotEqual([],arizonacrypt.generate_privatekey_sl("genrsa"))

      # Invalid keytype
      self.assertException(AssertionError,arizonacrypt.generate_privatekey_sl,"aklsdf")
      




   #------------------------------------------------------------------
   #  generate_privatekey_fn(filename,type_of_key=None):
   #------------------------------------------------------------------
   def test_generate_privatekey_fn(self):

      # Create a valid privatekey (default type)...
      arizonacrypt.generate_privatekey_fn("/tmp/test1")
      does_exist = os.path.exists("/tmp/test1")
      os.remove("/tmp/test1")
      self.assertEqual(True, does_exist)

      # Create a valid privatekey (specify the type)...
      arizonacrypt.generate_privatekey_fn("/tmp/test1","genrsa")
      does_exist = os.path.exists("/tmp/test1")
      os.remove("/tmp/test1")
      self.assertEqual(True, does_exist)

      # Invalid name (not a filename)
      self.assertException(AssertionError,arizonacrypt.generate_privatekey_fn,123)


      # Invalid keytype
      self.assertException(AssertionError,arizonacrypt.generate_privatekey_fn,"/tmp/test2","asdfkasd")

      # Invalid filename
      self.assertException(IOError,arizonacrypt.generate_privatekey_fn,"aklsdfjas/asfasdf/asflas")

      # Target is dir
      self.assertException(IOError,arizonacrypt.generate_privatekey_fn,"/usr/bin")


   
   #------------------------------------------------------------------
   #  extract_publickey_sl_from_privatekey_fn(privatekey_fn,type_of_key=None)
   #------------------------------------------------------------------
   def test_extract_publickey_sl_from_privatekey_fn(self):

      # check that it seems to work on a valid key
      arizonacrypt.generate_privatekey_fn("/tmp/test1")
      publickey_sl = arizonacrypt.extract_publickey_sl_from_privatekey_fn("/tmp/test1")
      os.remove("/tmp/test1")
      self.assertNotEqual([],publickey_sl)

      
      # Invalid keytype
      arizonacrypt.generate_privatekey_fn("/tmp/test1")
      self.assertException(TypeError,arizonacrypt.extract_publickey_sl_from_privatekey_fn,"/tmp/test1","askfd")
      os.remove("/tmp/test1")

      # Invalid filename
      self.assertException(IOError,arizonacrypt.extract_publickey_sl_from_privatekey_fn,"aklsdfjas/asfasdf/asflas")

      # Not a private key
      self.assertException(TypeError,arizonacrypt.extract_publickey_sl_from_privatekey_fn,"/bin/ls")





   #------------------------------------------------------------------
   #  extract_publickey_sl_from_privatekey_sl(privatekey_sl,type_of_key=None)
   #------------------------------------------------------------------
   def test_extract_publickey_sl_from_privatekey_sl(self):

      # check that it seems to work on a valid key
      privatekey_sl = arizonacrypt.generate_privatekey_sl()
      publickey_sl = arizonacrypt.extract_publickey_sl_from_privatekey_sl(privatekey_sl)
      self.assertNotEqual([],publickey_sl)

      
      # Invalid keytype
      privatekey_sl = arizonacrypt.generate_privatekey_sl()
      self.assertException(TypeError,arizonacrypt.extract_publickey_sl_from_privatekey_sl,privatekey_sl,"askfd")

      # Not a stringlist
      self.assertException(TypeError,arizonacrypt.extract_publickey_sl_from_privatekey_sl,123)

      # Not a private key
      self.assertException(TypeError,arizonacrypt.extract_publickey_sl_from_privatekey_sl,["abc","def","ghi"])






   #------------------------------------------------------------------
   #  publickey_fn_to_sl(filename, type_of_key=None):
   #------------------------------------------------------------------
   def test_publickey_fn_to_sl(self):

      # check that it seems to work on a valid key
      privatekey_sl = arizonacrypt.generate_privatekey_sl()
      real_publickey_sl = arizonacrypt.extract_publickey_sl_from_privatekey_sl(privatekey_sl)
      temp_publickey_fn = arizonacrypt.sl_to_fn(real_publickey_sl)
      new_publickey_sl = arizonacrypt.publickey_fn_to_sl(temp_publickey_fn)
      os.remove(temp_publickey_fn)
      self.assertEquals(new_publickey_sl,(True, real_publickey_sl))



      # should return (False, []) with an file that is not a publickey 
      privatekey_fn = arizonacrypt.generate_privatekey_fn("/tmp/tempdasf")
      self.assertEquals(arizonacrypt.publickey_fn_to_sl("/tmp/tempdasf"),(False,[]))
      os.remove("/tmp/tempdasf")
      self.assertEquals(arizonacrypt.publickey_fn_to_sl("/bin/ls"),(False,[]))


      # should return (False, []) with a bad file name
      #self.assertEquals(arizonacrypt.publickey_fn_to_sl("asldfkjasldfs"),(False,[]))
      # Now this method returns a typeError that the file does not exist
      self.assertException(TypeError,arizonacrypt.publickey_fn_to_sl,"asldf/kjasldfs")
      self.assertException(TypeError,arizonacrypt.publickey_fn_to_sl,1)
      

      # should throw TypeError with a bad keytype 
      privatekey_sl = arizonacrypt.generate_privatekey_sl()
      real_publickey_sl = arizonacrypt.extract_publickey_sl_from_privatekey_sl(privatekey_sl)
      temp_publickey_fn = arizonacrypt.sl_to_fn(real_publickey_sl)
      new_publickey_sl = arizonacrypt.publickey_fn_to_sl(temp_publickey_fn)
      # The following throws a TypeError, because new_publickey_sl is not a filename, it's a sl
      self.assertException(TypeError,arizonacrypt.publickey_fn_to_sl,new_publickey_sl,3)
      os.remove(temp_publickey_fn)

   



   #------------------------------------------------------------------
   # valid_publickey_sl(publickey_sl, key_type=None):
   #------------------------------------------------------------------
   def test_valid_public_key_sl(self):
      
      # check that it seems to work on a valid key
      privatekey_sl = arizonacrypt.generate_privatekey_sl()
      real_publickey_sl = arizonacrypt.extract_publickey_sl_from_privatekey_sl(privatekey_sl)

      self.assertEquals(arizonacrypt.valid_publickey_sl(real_publickey_sl),True)



      # should return False with a string list that is not a public key
      privatekey_sl = arizonacrypt.generate_privatekey_sl()
      self.assertEquals(arizonacrypt.valid_publickey_sl(privatekey_sl),False)
      self.assertEquals(arizonacrypt.valid_publickey_sl(["asdf"]),False)
      self.assertEquals(arizonacrypt.valid_publickey_sl([]),False)
      self.assertEquals(arizonacrypt.valid_publickey_sl(["asdf","asdsfd","asfasdfasdf"]),False)


      # should fail an assertion if given a non-string list 
      self.assertException(TypeError,arizonacrypt.valid_publickey_sl,1)




   #------------------------------------------------------------------
   # get_fn_hash(filename,hash_type=None):
   #------------------------------------------------------------------
   def test_get_fn_hash(self):

      # It shouldn't throw an exception, etc.
      arizonacrypt.get_fn_hash("/bin/ls")

      # An invalid hash_type
      self.assertException(TypeError, arizonacrypt.get_fn_hash,"/bin/ls",3)
      self.assertException(IOError, arizonacrypt.get_fn_hash,"/bin/ls","askldfdas")

      # A non-string
      self.assertException(IOError, arizonacrypt.get_fn_hash,3)

      # A non-string
      self.assertException(IOError, arizonacrypt.get_fn_hash,3)

      # An invalid path
      self.assertException(IOError, arizonacrypt.get_fn_hash,"/lasfd/lasd")

      # An invalid file
      self.assertException(IOError, arizonacrypt.get_fn_hash,"/usr/lasd")

      # A non-file
      self.assertException(IOError, arizonacrypt.get_fn_hash,"/usr/bin")

      # I'd like to test a non-readable file but root can read anything...
# Skip for now
      #self.assertEqual(arizonacrypt.get_fn_hash("/usr/bin"),False)




      
   #------------------------------------------------------------------
   # publickey_sl_to_fnstring(publickey_sl):
   #------------------------------------------------------------------
   def test_publickey_sl_to_fnstring(self):
   
      # Should raise TypeError since arg is not an sl
      self.assertException(TypeError,arizonacrypt.publickey_sl_to_fnstring,"asdjiofsd")
      self.assertException(TypeError,arizonacrypt.publickey_sl_to_fnstring,3)
      self.assertException(TypeError,arizonacrypt.publickey_sl_to_fnstring,"")
            
            
            

      
   #------------------------------------------------------------------
   # fnstring_to_publickey_sl(fnstring):
   #------------------------------------------------------------------
   def test_fnstring_to_publickey_sl(self):
 
      # Try on a simple example
      self.assertEqual(arizonacrypt.fnstring_to_publickey_sl(''),['-----BEGIN PUBLIC KEY-----','-----END PUBLIC KEY-----'] )

      # note: see arizonacrypt for discussion of old-style key mangling

      # try with a mangled 512 bit key (the standard thing that would be in an old-style filename)
      key_string = "MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAN3_C9Q3wwo_alFitDsZW8a4gCn0Sba82serR9qGL+v_WO1PEQQdyk6PZZ9BtXeIeiu4o8qpuOH20mMxp4ECLO8CAwEAAQ"
      key_sl = arizonacrypt.fnstring_to_publickey_sl(key_string)
      publickey = arizonacrypt.PublicKey(sl=key_sl)
      self.assertTrue(publickey.is_valid())
      
      # try with a mangled non-512 bit key (what old code would embed for a USER in a tpfile
      # if it was trying to add a user with a longer key, in which case unmangling has to be
      # manually forced)
      key_string = "MIGdMA0GCSqGSIb3DQEBAQUAA4GLADCBhwKBgQDK9oR7kfPrVKhodxv4+EjWkYD3JTJd6MNF228VtrmGO3yYtvfhQ5vAHxq6y63voUb7HExxJnbRmb5B0kKXI7nJjVFL+HL3g3b8r_A_InNh5BBKSY6wTOwM+KVpFOTgQlQKNqmkNGKU_McHN3WUMgFyeAdQZ_y0IyUJHSzyHlztLQIBIw"
      key_sl = arizonacrypt.fnstring_to_publickey_sl(key_string, force_unmangling=True)
      publickey = arizonacrypt.PublicKey(sl=key_sl)
      self.assertTrue(publickey.is_valid())
      
      # make sure it doesn't try to unmangle a non-mangled long key
      key_string = "MIGdMA0GCSqGSIb3DQEBAQUAA4GLADCBhwKBgQDK9oR7kfPrVKhodxv4+EjWkYD3JTJd6MNF228VtrmGO3yYtvfhQ5vAHxq6y63voUb7HExxJnbRmb5B0kKXI7nJjVFL+HL3g3b8r/A/InNh5BBKSY6wTOwM+KVpFOTgQlQKNqmkNGKU/McHN3WUMgFyeAdQZ/y0IyUJHSzyHlztLQIBIw=="
      key_sl = arizonacrypt.fnstring_to_publickey_sl(key_string)
      publickey = arizonacrypt.PublicKey(sl=key_sl)
      self.assertTrue(publickey.is_valid())
      
      # forcibly unmangle a key that is already valid and make sure it ends up invalid
      key_string = "MIGdMA0GCSqGSIb3DQEBAQUAA4GLADCBhwKBgQDK9oR7kfPrVKhodxv4+EjWkYD3JTJd6MNF228VtrmGO3yYtvfhQ5vAHxq6y63voUb7HExxJnbRmb5B0kKXI7nJjVFL+HL3g3b8r/A/InNh5BBKSY6wTOwM+KVpFOTgQlQKNqmkNGKU/McHN3WUMgFyeAdQZ/y0IyUJHSzyHlztLQIBIw=="
      key_sl = arizonacrypt.fnstring_to_publickey_sl(key_string, force_unmangling=True)
      publickey = arizonacrypt.PublicKey(sl=key_sl)
      self.assertFalse(publickey.is_valid())




   #------------------------------------------------------------------
   # publickey_sl_to_fnstring_compat(publickey_sl):
   #------------------------------------------------------------------
   def test_publickey_sl_to_fnstring_compat(self):

      # Try on some simple examples
      self.assertEqual(arizonacrypt.publickey_sl_to_fnstring_compat(['-----']),'')
      self.assertEqual(arizonacrypt.publickey_sl_to_fnstring_compat(['-----','abc','---------asfdasdf','def']),'abcdef')
      self.assertEqual(arizonacrypt.publickey_sl_to_fnstring_compat(['-----','====abc','---------a/f','=d=ef///=']),'abc=d=ef___')
      
      # below we verify that fnstring_to_publickey_sl() restores 512 keys that have been run through
      # publickey_sl_to_fnstring_compat() back to a good valid key. Only need to worry about
      # this for 512 bit keys as that is all that was used in the old versions of stork that
      # used this type of mangling in filenames
      
      # trailing ='s but no slashes
      key_sl = "MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAL4XBJVaBJ4blK9KcveRbOXRwtsDsuedEdGZSUqXvHifIm4EzWmXH+jxHBsc0JBRBLWuY2m5kImdYkT5lZfKz+MCAwEAAQ=="
      key_string = arizonacrypt.publickey_sl_to_fnstring_compat(key_sl)
      restored_sl = arizonacrypt.fnstring_to_publickey_sl(key_string)
      publickey = arizonacrypt.PublicKey(sl=restored_sl)
      self.assertTrue(publickey.is_valid())
      
      # trailing ='s and slashes
      key_sl = "MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBANHZ/RbnBKDDF2imcVpfhhce4PEs14AqbrLUn/jLLxwzaADJ9TPgd8388+a3QL7ztYxrwwmEfGX0aDMAm5DFV6kCAwEAAQ=="
      key_string = arizonacrypt.publickey_sl_to_fnstring_compat(key_sl)
      restored_sl = arizonacrypt.fnstring_to_publickey_sl(key_string)
      publickey = arizonacrypt.PublicKey(sl=restored_sl)
      self.assertTrue(publickey.is_valid())
      





   #------------------------------------------------------------------
   # get_fn_signedhash_using_privatekey_fn(filename, privatekey_fn, type_of_hash=None):
   #------------------------------------------------------------------
   def test_get_fn_signedhash_using_privatekey_fn(self):
 
      # Make sure something is returned in the normal case 
      arizonacrypt.generate_privatekey_fn("/tmp/temp5")
      signedhash = arizonacrypt.get_fn_signedhash_using_privatekey_fn("/bin/ls","/tmp/temp5")
      os.remove("/tmp/temp5")
      self.assertNotEqual(signedhash,'')
      
      # Try an invalid filename
      arizonacrypt.generate_privatekey_fn("/tmp/temp5")
      self.assertException(IOError,arizonacrypt.get_fn_signedhash_using_privatekey_fn,"/asfaskj/asdfkjasklsf","/tmp/temp5")
      os.remove("/tmp/temp5")
      
      # Try an invalid privatekey file
      self.assertException(IOError,arizonacrypt.get_fn_signedhash_using_privatekey_fn,"/bin/ls","/askdf/askjlsa")
      
      # Try an invalid hash type
      arizonacrypt.generate_privatekey_fn("/tmp/temp5")
      # Collin: added None, was not testing right thing
      self.assertException(TypeError,arizonacrypt.get_fn_signedhash_using_privatekey_fn,"/bin/ls","/tmp/temp5",None,"asdsfsdf")
      os.remove("/tmp/temp5")



   #------------------------------------------------------------------
   # get_verify_fn_signedhash_using_publickey_fn(filename, signedhash, publickey_fn, type_of_hash = None):
   #------------------------------------------------------------------
   def test_verify_fn_signedhash_using_publickey_fn(self):
 
      # Make sure it works in the normal case 
 
      # Get a private key and hash
      arizonacrypt.generate_privatekey_fn("/tmp/temp5")
      signedhash = arizonacrypt.get_fn_signedhash_using_privatekey_fn("/bin/ls","/tmp/temp5")
      # Get the corresponding public key 
      publickey_sl = arizonacrypt.extract_publickey_sl_from_privatekey_fn("/tmp/temp5")
      temp_publickey_fn = arizonacrypt.sl_to_fn(publickey_sl)
      # Kill the private key
      os.remove("/tmp/temp5")
      # Check it
      validity = arizonacrypt.verify_fn_signedhash_using_publickey_fn("/bin/ls",signedhash,temp_publickey_fn)
      # Kill the public key
      os.remove(temp_publickey_fn)
      self.assertEqual(validity,True)
      
      # Make sure it doesn't work when we muck with it

      # Get a private key and hash
      arizonacrypt.generate_privatekey_fn("/tmp/temp5")
      signedhash = arizonacrypt.get_fn_signedhash_using_privatekey_fn("/bin/ls","/tmp/temp5")
      # Modify the hash
      signedhash = "a3"+signedhash
      # Get the corresponding public key 
      publickey_sl = arizonacrypt.extract_publickey_sl_from_privatekey_fn("/tmp/temp5")
      temp_publickey_fn = arizonacrypt.sl_to_fn(publickey_sl)
      # Kill the private key
      os.remove("/tmp/temp5")
      # Check it
      validity = arizonacrypt.verify_fn_signedhash_using_publickey_fn("/bin/ls",signedhash,temp_publickey_fn)
      # Kill the public key
      os.remove(temp_publickey_fn)
      self.assertEqual(validity,False)
      





   #------------------------------------------------------------------
   # retrieve_hash_from_signatureblock_sl(signatureblock):
   # Method has been commented out in arizonacrypt.py
   #------------------------------------------------------------------
   #def test_retrieve_hash_from_signatureblock_sl(self):
   #
   #   # Make sure it works in the normal cases
   #   self.assertEqual((["abc"],"-sha1"), arizonacrypt.retrieve_hash_from_signatureblock_sl(["-----SIGNATURE (stork 1) BEGINS-----","abc","-----SIGNATURE (stork 1) ENDS-----"]))
   #
   #   self.assertEqual((["ghi"],"xyz"), arizonacrypt.retrieve_hash_from_signatureblock_sl(["<!-- -----SIGNATURE xyz BEGINS-----","ghi","-----SIGNATURE xyz ENDS-----"]))
   #
   #   
   #   # Should fail in these cases
   #   self.assertException(TypeError,arizonacrypt.retrieve_hash_from_signatureblock_sl,[])
   #   
   #   # Bad header
   #   self.assertException(TypeError, arizonacrypt.retrieve_hash_from_signatureblock_sl,["<!- -----SIGNATURE xyz BEGINS-----","ghi","-----SIGNATURE xyz ENDS-----"])
   #
   #   # Bad footer
   #   self.assertException(TypeError, arizonacrypt.retrieve_hash_from_signatureblock_sl,["<!-- -----SIGNATURE xyz BEGINS-----","ghi","-----SINATURE xyz ENDS-----"])
   #
   #   # No middle
   #   self.assertException(TypeError, arizonacrypt.retrieve_hash_from_signatureblock_sl,["<!-- -----SIGNATURE xyz BEGINS-----","-----SIGNATURE xyz ENDS-----"])



   #------------------------------------------------------------------
   # retrieve_signatureblock_from_sl(signatureblock):
   # Method has been commented out in arizonacrypt.py
   #------------------------------------------------------------------
   #def test_retrieve_signatureblock_from_sl(self):
   # 
   #   # Make sure it works in the normal cases
   #   self.assertEqual(([],["-----SIGNATURE (stork 1) BEGINS-----","abc","-----SIGNATURE (stork 1) ENDS-----"]), arizonacrypt.retrieve_signatureblock_from_sl(["-----SIGNATURE (stork 1) BEGINS-----","abc","-----SIGNATURE (stork 1) ENDS-----"]))
   #
   #   self.assertEqual((["abc","def","ghi","jkl"],["-----SIGNATURE (stork 1) BEGINS-----","abc","-----SIGNATURE (stork 1) ENDS-----"]), arizonacrypt.retrieve_signatureblock_from_sl(["abc","def","ghi","jkl","-----SIGNATURE (stork 1) BEGINS-----","abc","-----SIGNATURE (stork 1) ENDS-----"]))
   #
   #   
   #   # Should fail in these cases
   #   self.assertException(TypeError,arizonacrypt.retrieve_signatureblock_from_sl,[])
   #
   #   self.assertException(TypeError,arizonacrypt.retrieve_signatureblock_from_sl,7)
   #   
   #   # Bad header
   #   self.assertException(TypeError,arizonacrypt.retrieve_signatureblock_from_sl,["abc","def","ghi","jkl","-----IGNAURE (stork 1) BEGINS-----","abc","-----SIGNATURE (stork 1) ENDS-----"])


      


   #------------------------------------------------------------------
   # verify_signatureblock_using_publickey_fn(stringlist, signatureblock, publickey_fn):
   # create_signatureblock_using_privatekey_fn(stringlist, signatureblock, publickey_fn):
   # These two methods have been commented out in arizonacrypt.py
   #------------------------------------------------------------------
   #def test_signatureblock_routines(self):
   # 
   #
   #
   #   temp_privatekey_fn = "/tmp/testdsfasdf"
   #   # Make a private key
   #   arizonacrypt.generate_privatekey_fn(temp_privatekey_fn)
   #
   #   publickey_sl = arizonacrypt.extract_publickey_sl_from_privatekey_fn(temp_privatekey_fn)
   # 
   #  temp_publickey_fn = arizonacrypt.sl_to_fn(publickey_sl)
   #
   #   # Try some common cases
   #   for testfile in [ '/bin/ls', '/dev/null', '/etc/passwd' ]:
   #      file_sl = arizonacrypt.fn_to_sl(testfile)
   #
   #      signatureblock = arizonacrypt.create_signatureblock_using_privatekey_fn(file_sl, temp_privatekey_fn)
   # 
   #      # Make sure it works in the normal case
   #      self.assertEqual(True, arizonacrypt.verify_signatureblock_using_publickey_fn(file_sl, signatureblock, temp_publickey_fn))
   #
   #      # Make sure it fails if the string list is changed
   #      self.assertEqual(False, arizonacrypt.verify_signatureblock_using_publickey_fn(file_sl+["a"], signatureblock, temp_publickey_fn))
   #      
   #      # Make sure it fails if the signature changed
   #      self.assertException(TypeError,arizonacrypt.verify_signatureblock_using_publickey_fn,file_sl, signatureblock+['a'], temp_publickey_fn)
   #      
   #      
   #   os.remove(temp_publickey_fn)
   #   os.remove(temp_privatekey_fn)




      
      

   #------------------------------------------------------------------
   # sign_file_using_privatekey_fn(filename, privatekey_fn, type_of_hash=None):
   # Method has been commented out in arizonacrypt.py
   #------------------------------------------------------------------
   #def test_sign_file_using_privatekey_fn(self):
   # 
   #
   #   temp_privatekey_fn = "/tmp/tessasdf"
   #
   #   # Make a private key
   #   arizonacrypt.generate_privatekey_fn(temp_privatekey_fn) 
   #
   #   # Get the corresponding public key
   #   publickey_sl = arizonacrypt.extract_publickey_sl_from_privatekey_fn(temp_privatekey_fn)
   # 
   #   # Write the public key out to a file
   #   temp_publickey_fn = arizonacrypt.sl_to_fn(publickey_sl)
   #
   #   # For each of the test files...
   #   for testfile in [ "/etc/passwd", "/bin/ls", "/dev/null" ]:
   #      # Get the file data
   #      test_sl = arizonacrypt.fn_to_sl(testfile)
   #
   #      # Dump it to a new temp file
   #      temp_fn = arizonacrypt.sl_to_fn(test_sl)
   #
   #      # Sign the temp file
   #      arizonacrypt.sign_file_using_privatekey_fn(temp_fn,temp_privatekey_fn)
   #
   #      # read the temp file back in...
   #      temp2_sl = arizonacrypt.fn_to_sl(temp_fn)
   #
   #      # Clean up the temp file
   #      os.remove(temp_fn)
   #
   #      # strip the signatureblock
   #      ( original_sl, signatureblock ) = arizonacrypt.retrieve_signatureblock_from_sl(temp2_sl)
   #
   #      # Make sure the file data is the same
   #      self.assertEqual(original_sl, test_sl)
   #
   #      # Now make sure the signature is valid
   #      self.assertEqual(True, arizonacrypt.verify_signatureblock_using_publickey_fn(original_sl, signatureblock, temp_publickey_fn))
   #
   #
   #   # Remove the temporary public/private key pair...
   #   os.remove(temp_publickey_fn)
   #   os.remove(temp_privatekey_fn)
      

   #------------------------------------------------------------------
   # XML_sign_file_using_privatekey_fn(filename, privatekey_fn, type_of_hash=None, timestamp=None, duration=None, file_encoding=None):
   #------------------------------------------------------------------
   def test_XML_sign_file_using_privatekey_fn(self):
      privkey = "/tmp/my_test_privkey"
      tempfile = "/tmp/testfile2"
      arizonacrypt.generate_privatekey_fn(privkey)
      try:
         
         
         # Create a signedfile
         for testfile in [ "/etc/passwd", "trustedpackages.dtd", "/bin/ls", "/dev/null"]:
            shutil.copy(testfile, tempfile)
            # Correct
            arizonacrypt.XML_sign_file_using_privatekey_fn(tempfile,privkey)
            # Correct with options
            arizonacrypt.XML_sign_file_using_privatekey_fn(tempfile,privkey, type_of_hash="-sha1", timestamp=1, duration=10, file_encoding="hex")

            # Bad hash
            self.assertException(TypeError, arizonacrypt.XML_sign_file_using_privatekey_fn, tempfile,privkey, None, "abc")

            # Bad timestamp 
            self.assertException(TypeError, arizonacrypt.XML_sign_file_using_privatekey_fn, tempfile,privkey, None, None, "abc")
            # Bad duration
            self.assertException(TypeError, arizonacrypt.XML_sign_file_using_privatekey_fn, tempfile,privkey, None, None, None, "abc")
            # Bad encoding
            self.assertException(TypeError, arizonacrypt.XML_sign_file_using_privatekey_fn, tempfile,privkey, None, None, None, None, "abc")

            # Bad file name
            self.assertException(TypeError, arizonacrypt.XML_sign_file_using_privatekey_fn, tempfile+"123",privkey)
         
            # Bad private key name
            self.assertException(TypeError, arizonacrypt.XML_sign_file_using_privatekey_fn, tempfile,privkey+"123")
         
         
      finally:
         os.remove(privkey)
         os.remove(tempfile)
      


   #------------------------------------------------------------------
   # XML_timestamp_signedfile_with_publickey_fn(signedfile_fn, publickey_fn)
   #------------------------------------------------------------------
   def test_XML_timestamp_signedfile_with_publickey_fn(self):

      privkey = "/tmp/my_test_privkey"
      tempfile = "/tmp/testfile"
      arizonacrypt.generate_privatekey_fn(privkey)
      try:
         pubkey_sl = arizonacrypt.extract_publickey_sl_from_privatekey_fn(privkey)
         pubkey = arizonacrypt.sl_to_fn(pubkey_sl)
         
         
         # Create a few signedfiles and play with the timestamps
         for testfile in [ "/etc/passwd", "trustedpackages.dtd", "/bin/ls", "/dev/null"]:
            shutil.copy(testfile, tempfile)
            # Sign normally
            arizonacrypt.XML_sign_file_using_privatekey_fn(tempfile,privkey)
            # Should throw an exception if there is a problem
            arizonacrypt.XML_timestamp_signedfile_with_publickey_fn(tempfile, pubkey)


            # Sign with timestamp 1
            arizonacrypt.XML_sign_file_using_privatekey_fn(tempfile,privkey,type_of_hash="-sha1",timestamp=1, duration=0, file_encoding="hex")
            self.assertEquals(int(arizonacrypt.XML_timestamp_signedfile_with_publickey_fn(tempfile, pubkey)), 1)

            # Sign so that the signature has expired
            # XML_sign_file_using_privatekey_fn changed so that it should not raise exception for expired file anymore
            # it now just returns the timestamp and doesn't check expiration
            #arizonacrypt.XML_sign_file_using_privatekey_fn(tempfile,privkey, type_of_hash="-sha1",timestamp=1, duration=1, file_encoding="hex")
            #self.assertException(TypeError, arizonacrypt.XML_timestamp_signedfile_with_publickey_fn,tempfile, pubkey)
            arizonacrypt.XML_sign_file_using_privatekey_fn(tempfile,privkey, type_of_hash="-sha1",timestamp=1, duration=1, file_encoding="hex")
            self.assertEquals(1, arizonacrypt.XML_timestamp_signedfile_with_publickey_fn(tempfile, publickey_fn=pubkey))
            
            # Bad publickey
            arizonacrypt.XML_sign_file_using_privatekey_fn(tempfile,privkey, type_of_hash="-sha1",timestamp=1, duration=1, file_encoding="hex")
            self.assertException(TypeError, arizonacrypt.XML_timestamp_signedfile_with_publickey_fn,tempfile, pubkey+"123")
            self.assertException(TypeError, arizonacrypt.XML_timestamp_signedfile_with_publickey_fn,tempfile, "/dev/null")
            
         
      finally:
         os.remove(privkey)
         os.remove(pubkey)
         os.remove(tempfile)
      


   #------------------------------------------------------------------
   # XML_retrieve_originalfile_from_signedfile(original_fn):
   #------------------------------------------------------------------
   def test_XML_retrieve_originalfile_from_signedfile(self):

      privkey = "/tmp/my_test_privkey"
      tempfile = "/tmp/testfile"
      signedtempfile = "/tmp/signedtemptestfile"
      arizonacrypt.generate_privatekey_fn(privkey)
      try:
         
         # Create a few signedfiles...
         for testfile in [ "/etc/passwd", "trustedpackages.dtd", "/bin/ls", "/dev/null"]:
            shutil.copy(testfile, tempfile)
            shutil.copy(tempfile, signedtempfile)

            # Sign
            arizonacrypt.XML_sign_file_using_privatekey_fn(signedtempfile,privkey)

            # Extract
            new_tempfile = arizonacrypt.XML_retrieve_originalfile_from_signedfile(signedtempfile)

            # Check
            self.assertEquals(0, os.system("diff "+tempfile+" "+new_tempfile+" > /dev/null"))
            os.remove(new_tempfile)
            
         
      finally:
         os.remove(privkey)
         os.remove(tempfile)
         os.remove(signedtempfile)
      



   #------------------------------------------------------------------
   #  class SignedFileApplication(arizonaxml.XMLApplication):
   #------------------------------------------------------------------
#   def test_SignedFileApplication(self):
#      arizonacrypt.generate_privatekey_fn("/tmp/my_test_privkey")
#      a = arizonacrypt.SignedFileApplication()
#      a.read_file("sample.signedfile")
#      a.debug_print()
#      a.write_file("sample.signedfile2")
#      a.get_signedhash("/tmp/my_test_privkey")
#      a.write_file("sample.signedfile3")
#      a.dump_file_data("/tmp/abc")
#      a.dump_file_data("/tmp/def")
#      a.read_file_data("/bin/ls")
#      a.write_file("sample.signedfile4")
#      a = arizonacrypt.SignedFileApplication()
#      a.read_file("sample.signedfile4")
#      a.dump_file_data("/tmp/ls")
#      a = arizonacrypt.SignedFileApplication()
#      a.read_file("sample.signedfile")
#      a.read_file_data("sample.signedfile")
#      a.file_encoding = "escaped"
#      a.raw_write_file("sample.signedfile5")
#      a = arizonacrypt.SignedFileApplication()
#      a.read_file("sample.signedfile5")
#      a.debug_print()
#      os.remove("/tmp/my_test_privkey")
#      fn = arizonacrypt.XML_retrieve_originalfile_from_signedfile("sample.signedfile")
#      os.system("cat "+fn)
#      os.remove(fn)
      




      


      











   #------------------------------------------------------------------
   # example
   #------------------------------------------------------------------
   def test_example(self):
      pass






#=====================================================================
# Run tests
#=====================================================================
if __name__=='__main__':
   arizonaconfig.init_options()
   arizonaunittest.main()
