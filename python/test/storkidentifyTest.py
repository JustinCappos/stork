#! /usr/bin/env python
"""
<Module>
   storkidentifyTest
<Author>
   Mario Gonzalez under the direction of Justing Cappos
<Started>
   June 01, 2006
<Purpose>
   Test module for storkidentify. See storkidentify.py for more details.
"""

import os
import arizonaconfig
import arizonaunittest
import storkidentify
import sys


class test(arizonaunittest.TestCase):

    #---------------------------------------------------------
    # identify():
    #---------------------------------------------------------
    def test_identify(self):
        # TODO: connect to nest 
        storkidentify.identify()
        pass


    #--------------------------------------------------------
    # __handle_createddirectory(data):
    #--------------------------------------------------------
    def test__handle_createddirectory(self):
        pass


    #--------------------------------------------------------
    # __handle_removedirectory(data):
    #--------------------------------------------------------
    def test__handle_removedirectory(self):
        pass


    #--------------------------------------------------------
    # __handle_createfile(data):
    #--------------------------------------------------------
    def test__handle_createfile(self):
        pass


    #-------------------------------------------------------
    # __handle_removefile(data):
    #-------------------------------------------------------
    def test__handle_removefile(self):
        pass


    #------------------------------------------------------
    # __handle_appendactive(data):
    #------------------------------------------------------
    def test__handle_appendactive(self):
        pass


    #-----------------------------------------------------
    # __handle_overwriteactive(data):
    #-----------------------------------------------------
    def test__handle_overwriteactive(self):
        pass


    #-----------------------------------------------------
    # __handle_readactive(data):
    #-----------------------------------------------------
    def test__handle_readactive(self):
        pass


    #-----------------------------------------------------
    # __handle_setactive(data):
    #-----------------------------------------------------
    def test__handle_setactive(self):
        pass


    #-----------------------------------------------------
    # __handle_identifyfailed(junk_data):
    #-----------------------------------------------------
    def test__handle_identifyfailed(self):
        pass


    #-----------------------------------------------------
    # __handle_identified(data):
    #-----------------------------------------------------
    def test__handle_identified(self):
        pass


    #-----------------------------------------------------
    # __handle_send_out(data):
    #-----------------------------------------------------
    def test__handle_send_out(self):
        pass


    #-----------------------------------------------------
    # __handle_send_out_comma(data):
    #-----------------------------------------------------
    def test__handle_send_out_comma(self):
        pass


    #-----------------------------------------------------
    # __handle_send_error(data):
    #-----------------------------------------------------
    def test__handle_send_error(self):
        pass


    #-----------------------------------------------------
    # __handle_flush_out(junk_data):
    #-----------------------------------------------------
    def test__handle_flush_out(self):
        pass


    #-----------------------------------------------------
    # __handle_flush_error(junk_data):
    #-----------------------------------------------------
    def test__handle_flush_error(self):
        pass


    #-----------------------------------------------------
    # __identify_done(identified):
    #-----------------------------------------------------
    def test__identify_done(self):
        pass

    


# Run tests
if __name__ == '__main__':
    arizonaunittest.main()
