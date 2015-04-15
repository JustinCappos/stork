#! /usr/bin/env python
"""
<Module>
   stork_nest_commTest

<Author>
   Mario Gonzalez.

<Started>
   July 25, 2006

<Purpose>
   Test module for stork_nest_comm.py. See stork_nest_comm.py for more details.
"""

import os
import arizonaconfig
import sys
import arizonageneral
import arizonaunittest
import arizonareport
import stork_nest_comm



class test(arizonaunittest.TestCase):

    #----------------------------------------------------------------------------
    # handle_connection():
    #----------------------------------------------------------------------------
    def test_handle_connection(self):

        # Pass invalid data:
        # 1st argument invalid:
        self.assertException(TypeError, stork_nest_comm.handle_connection, 1, 2) # 1st argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, [], 2) # 1st argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, 3.4, 2) # 1st argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, (), 2) # 1st argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, {}, 2) # 1st argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, None, 2) # 1st argument invalid
        #Can't pass in multiple decimal number, was raising syntax error
        #self.assertException(TypeError, stork_nest_comm.handle_connection, 123.345.123.2, 2) # 1st argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, "", 2) # 1st argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, "-", 2) # 1st argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, " ", 2) # 1st argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, " sjkfhskj haal", 2) # 1st argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, "&@&AHHAKJHDKHKsd", 2) # 1st argument invalid
        # 2nd argument invalid:
        self.assertException(TypeError, stork_nest_comm.handle_connection, "1.2.3.4", None) # 2nd argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, "1.2.3.4", 1.3) # 2nd argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, '1.2.3.4', {}) # 2nd argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, '1.2.3.4', []) # 2nd argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, '1.2.3.4', () ) # 2nd argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, '1.2.3.4', "string") # 2nd argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, "1.2.3.4", "-") # 2nd argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, "1.2.3.4", " ") # 2nd argument invalid
        self.assertException(TypeError, stork_nest_comm.handle_connection, "1.2.3.4", [[]]) # 2nd argument invalid
        





if __name__=='__main__':
    arizonaunittest.main()
        
