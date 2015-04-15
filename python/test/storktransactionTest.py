"""
<Program Name>
   storktransactionTest.py

<Started>
   Oct 15, 2007

<Author>
   Collin Reynolds

<Purpose>
   To test the storktransaction.py module, see it for details
"""

import arizonaunittest
import arizonageneral
import storktransaction

class test(arizonaunittest.TestCase):

   #----------------------------------------------------------
   # tl_create()
   #----------------------------------------------------------
   def test_tl_create(self):
      tl = storktransaction.tl_create()
      self.assertEqual(tl,[])
      
      
      
      
      
      
   #----------------------------------------------------------
   # tl_add(tl, transaction)
   #----------------------------------------------------------
   def test_tl_add(self):
      tl = storktransaction.tl_create()
      storktransaction.tl_add(tl,"TEST")
      self.assertEqual(tl,["TEST"])
   
   
   
   
   
   
   #----------------------------------------------------------
   # tl_install(tl, filename)
   #----------------------------------------------------------
   def test_tl_install(self):
      #Test normal functionality
      tl = storktransaction.tl_create()
      storktransaction.tl_install(tl,"installthis.tar.gz")
      self.assertEqual(tl,[{'op':'INSTALL','filename':"installthis.tar.gz"}])
      storktransaction.tl_install(tl,"another.test.gz")
      self.assertEqual(tl,[{'op':'INSTALL','filename':"installthis.tar.gz"},{'op':'INSTALL','filename':"another.test.gz"}])
      
      tl = None      
      #Try with none for transaction list, should raise TypeError
      self.assertException(TypeError,storktransaction.tl_install,tl,"test")
      #Try with dict
      tl = {}
      self.assertException(TypeError,storktransaction.tl_install,tl,"test")
      
      
      
      
      
      
   #----------------------------------------------------------
   # tl_upgrade(tl, filename, conflict_list)
   #----------------------------------------------------------
   def test_tl_upgrade(self):
      #Test normal functionality
      tl = storktransaction.tl_create()
      #Test one conflict
      storktransaction.tl_upgrade(tl,"installthis.tar.gz",["conflict1"])
      self.assertEqual(tl,[{'op':'UPGRADE','filename':"installthis.tar.gz",'conflicts':["conflict1"]}])
      #Test two conflicts
      storktransaction.tl_upgrade(tl,"test2.tar.gz",["conflict2","conflict3"])
      self.assertEqual(tl,[{'op':'UPGRADE','filename':"installthis.tar.gz",'conflicts':["conflict1"]},{'op':'UPGRADE','filename':"test2.tar.gz",'conflicts':["conflict2","conflict3"]}])
      #Test no conflict
      tl = storktransaction.tl_create()
      storktransaction.tl_upgrade(tl,"installthis.tar.gz",[])
      self.assertEqual(tl,[{'op':'UPGRADE','filename':"installthis.tar.gz",'conflicts':[]}])
      #Test None as conflict, should raise TypeError
      tl = storktransaction.tl_create()
      self.assertException(TypeError,storktransaction.tl_upgrade,tl,"installthis.tar.gz",None)
      
      
      
      
      
      
   #----------------------------------------------------------
   # tl_remove(tl, packname)
   #----------------------------------------------------------
   def test_tl_remove(self):
      #Test normal functionality
      tl = storktransaction.tl_create()
      storktransaction.tl_remove(tl,"remove.tar.gz")
      self.assertEqual(tl,[{'op':'REMOVE','packname':"remove.tar.gz"}])
      storktransaction.tl_remove(tl,"another.test.gz")
      self.assertEqual(tl,[{'op':'REMOVE','packname':"remove.tar.gz"},{'op':'REMOVE','packname':"another.test.gz"}])
      
      tl = None      
      #Try with none for transaction list, should raise TypeError
      self.assertException(TypeError,storktransaction.tl_remove,tl,"test")
      #Try with dict
      tl = {}
      self.assertException(TypeError,storktransaction.tl_remove,tl,"test")
      
      
      
      
      
      
   #----------------------------------------------------------
   # tl_print(tl)
   #----------------------------------------------------------
   def test_tl_print(self):
      #Test normal functionality
      tl = storktransaction.tl_create()
      storktransaction.tl_install(tl,"installthis.tar.gz")
      storktransaction.tl_upgrade(tl,"installthis.tar.gz",["conflict1"])
      storktransaction.tl_remove(tl,"remove.tar.gz")
      storktransaction.tl_print(tl)
      #Above should not create any errors, possibly need to check output of print somehow
      
      #Make sure it only prints transaction lists
      tl = {}
      self.assertException(TypeError,storktransaction.tl_print,tl)
      tl = ["TEST"]
      self.assertException(TypeError,storktransaction.tl_print,tl)
      tl = [None]
      self.assertException(TypeError,storktransaction.tl_print,tl)
      
      
      
      
      
      
   #----------------------------------------------------------
   # tl_get_count(tl, kind)
   #----------------------------------------------------------   
   def test_tl_get_count(self):
      #Create a tl
      tl = storktransaction.tl_create()
      for x in xrange(0,20):
         storktransaction.tl_install(tl,"test%d.tar.gz"%x)
         
      #Test that it counts the install ops and all ops correctly
      self.assertEqual(storktransaction.tl_get_count(tl,None),20)
      self.assertEqual(storktransaction.tl_get_count(tl,storktransaction.INSTALL),20)
      self.assertEqual(storktransaction.tl_get_count(tl,storktransaction.REMOVE),0)      
      self.assertEqual(storktransaction.tl_get_count(tl,storktransaction.UPGRADE),0)
      
      
      
      
      
      
   #----------------------------------------------------------
   # tl_get_filename_list(tl, kind):
   #----------------------------------------------------------   
   def test_tl_get_filename_list(self):
      #Create a tl
      tl = storktransaction.tl_create()
      testList = []
      for x in xrange(0,20):
         storktransaction.tl_install(tl,"test%d.tar.gz"%x)
         testList.append("test%d.tar.gz"%x)
         
      #Test that it gets all of the the install ops and all ops filenames correctly
      self.assertEqual(storktransaction.tl_get_filename_list(tl,None),testList)
      self.assertEqual(storktransaction.tl_get_filename_list(tl,storktransaction.INSTALL),testList)
      self.assertEqual(storktransaction.tl_get_filename_list(tl,storktransaction.REMOVE),[])      
      self.assertEqual(storktransaction.tl_get_filename_list(tl,storktransaction.UPGRADE),[])
      
      
      
      
      
      
   #----------------------------------------------------------   
   # tl_get_packname_list(tl, kind)
   #----------------------------------------------------------   
   def test_tl_get_packname_list(self):
      #Create a tl
      tl = storktransaction.tl_create()
      testList = []
      for x in xrange(0,20):
         storktransaction.tl_remove(tl,"test%d.tar.gz"%x)
         testList.append("test%d.tar.gz"%x)
         
      #Test that it gets all of the packnames
      self.assertEqual(storktransaction.tl_get_packname_list(tl,None),testList)
      self.assertEqual(storktransaction.tl_get_packname_list(tl,storktransaction.REMOVE),testList)
      self.assertEqual(storktransaction.tl_get_packname_list(tl,storktransaction.INSTALL),[])      
      self.assertEqual(storktransaction.tl_get_packname_list(tl,storktransaction.UPGRADE),[])
      
      
      
      
      
     
   #----------------------------------------------------------   
   # tl_get_conflict_list(tl, kind)
   #----------------------------------------------------------   
   def test_tl_get_conflict_list(self):
      #Create a tl
      tl = storktransaction.tl_create()
      testList = []
      for x in xrange(0,20):
         storktransaction.tl_upgrade(tl,"test%d.tar.gz"%x,["conflict%d"%x,"conflict%d"%(x+1),"conflict%d"%(x+2),"conflict%d"%(x+3)])
         testList.append("conflict%d"%x)
         testList.append("conflict%d"%(x+1))
         testList.append("conflict%d"%(x+2))
         testList.append("conflict%d"%(x+3))
      
      testList = arizonageneral.uniq(testList)
         
      #Test that it gets all of the unique conflicts
      self.assertEqual(storktransaction.tl_get_conflict_list(tl,None),testList)
      self.assertEqual(storktransaction.tl_get_conflict_list(tl,storktransaction.UPGRADE),testList)
      self.assertEqual(storktransaction.tl_get_conflict_list(tl,storktransaction.INSTALL),[])      
      self.assertEqual(storktransaction.tl_get_conflict_list(tl,storktransaction.REMOVE),[])
      
      
      
      
      
      
#=====================================================================
# Run tests
#=====================================================================
if __name__=='__main__':
   arizonaunittest.main()
