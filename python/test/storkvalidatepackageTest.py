#! /usr/bin/env python
"""
<Module>
   storkvalidatepackageTest

<Author>
   Mario Gonzalez.

<Started>
   July 24, 2006

<Purpose>
   Test module for storkvalidatepackage.py. See storkvalidatepackage.py for more details.
"""

import os
import arizonaconfig
import sys
import arizonageneral
import arizonaunittest
import arizonareport
import storkvalidatepackage



class test(arizonaunittest.TestCase):

    #---------------------------------------------------------
    # main():
    #---------------------------------------------------------
    def test_main(self):
        # Test without command line arguments
        self.assertException(SystemExit, storkvalidatepackage.main)
        # Get the error message sent
        self.assertEquals("Usage: storkvalidatepackage.py [OPTION(s)] <packagename>", arizonareport.message)

        filepath = None
        packagename = None
        uploaddirExists = False

        prefix = os.environ.get("TESTPREFIX")
        # Make the following tests independent of the testing path:
        # Extract the path where "stork/..." starts and leave the part before this substring to a variable
        # that will change so that the tests can be run in different machines:
        subIdx = prefix.find("/stork")
        path = prefix[:subIdx]
        self.debug_print(path)
                              

        # SUBTEST STARTS ------------------------------------------------------------------------------------
        # Check if the directory in the "uploaddir" variable already exists
        filepath = arizonaconfig.get_option("uploaddir")
        if os.path.isdir(filepath):
            self.debug_print(" 'uploaddir' directory already exists: " + filepath)
            uploaddirExists = True
        else:
            self.debug_print(" 'uploaddir' directory does NOT exist ")
            uploaddirExists = False
                                    
        # SUBTEST ENDS ------------------------------------------------------------------------------------
        


        # SUBTEST STARTS ------------------------------------------------------------------------------------

        # Test with a command line parameter: pass it an invalid package:
        packagename = "invalid_package"
        self.set_cmdline([packagename])
        
        if uploaddirExists == False:
            # If the directory in the "uploaddir" variable does not exist yet in the system, the function it should
            # send an error message and quit
            self.assertException(SystemExit, storkvalidatepackage.main)
            # Get the error message:
            filepath = arizonaconfig.get_option( "uploaddir" )
            filepath = filepath + '/' + packagename
            self.assertEquals( "[storkvalidatepackage.py] " + filepath + " is not a valid file.", arizonareport.message )
        else:
            # If the directory in the "uploaddir" variable DOES exist, the function should find that the package name
            # passed is invalid, and send the same message and quit:
            self.assertException(SystemExit, storkvalidatepackage.main)
            # Get the error message:
            filepath = arizonaconfig.get_option( "uploaddir" )
            filepath = filepath + '/' + packagename
            self.assertEquals( "[storkvalidatepackage.py] " + filepath + " is not a valid file.", arizonareport.message )
                                                                
        # SUBTEST ENDS ------------------------------------------------------------------------------------


        # SUBTEST STARTS ------------------------------------------------------------------------------------
        
        # Test with rpm packages

        # Pass invalid rpm package
        _filepath = arizonaconfig.get_option( "uploaddir" )
        self.debug_print(_filepath)
        packagename = 'invalid.rpm'
        f = file( _filepath + '/' + packagename, 'w' )
        f.close()
        self.set_cmdline([packagename])
        # Should not be understood by the package managers
        self.assertException(SystemExit, storkvalidatepackage.main)
        self.assertEquals( _filepath + '/' +  packagename + " is NOT a valid package.", arizonareport.message)
        # clean up and remove the files and dirs used for testing
        os.remove(_filepath + '/' + packagename)


        # Pass a valid rpm package
        # Move an rpm package into the dir in "uploaddir" or else it will not work
        os.popen( "cp " + path + '/' + "stork/testpack/stork-0.1.0-1.i386.rpm /tmp/" )
        self.set_cmdline(["stork-0.1.0-1.i386.rpm"])
        # SHould understand the package passed:
        self.assertException(SystemExit, storkvalidatepackage.main)
        self.assertEquals(_filepath + "/stork-0.1.0-1.i386.rpm" + " is a valid package.", arizonareport.message)
        # Clean the dir:
        os.remove( "/tmp/stork-0.1.0-1.i386.rpm" )
        # SUBTEST ENDS ------------------------------------------------------------------------------------


        # SUBTEST STARTS ------------------------------------------------------------------------------------
        # TODO: Test with tar packages

        # Pass invalid tar packages

        # Pass valid tar packages
        # SUBTEST ENDS ------------------------------------------------------------------------------------
        
        




if __name__=='__main__':
    arizonaconfig.init_options()
    arizonaunittest.main()
