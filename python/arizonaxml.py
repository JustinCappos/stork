#!/usr/bin/env python

"""
<Program Name>
   arizonaxml.py

<Author>
   Justin Cappos  

<Purpose>
   arizona_xml parser
"""

import sys
import os
import string
import re
import arizonareport

try:
   from xml.parsers.xmlproc import xmlproc, xmlapp, xmldtd, xmlval
   import xml.sax.saxutils
except ImportError:
   print >> sys.stderr, "Python XML support is missing.  Install PyXML-0.8.3-6.i386.rpm or equivalent."
   sys.exit(1)  
   
   
   
   

class XMLError(ValueError):
   "XML syntax error"





class ShadowedAttribute(AttributeError):
   "Class's attribute shadows superclass's attribute of same name"





def CreateAttr(obj, attr, value):
   """
   <Purpose>
      TODO fix comment
   """
   if hasattr(obj, attr):
      # The programmer used a variable name that is already used
      raise ShadowedAttribute, attr
   setattr(obj, attr, value)





class XMLApplication(xmlproc.Application):

   def __init__(self):
      """
      <Purpose>
         TODO fix comment
      """
      xmlproc.Application.__init__(self)

      # Parser locator
      CreateAttr(self, 'loc', None)      





   def set_locator(self, locator):
      """
      <Purpose>
         TODO fix comment
      """
      self.loc = locator





def XMLParse(app, dtd, filename):
   """
   <Purpose>
      Creates the parser for the trustedpackages file and parses it. 
      Returns a dictionary of group members.
         
   TODO finish comment
   """
   parser = Validator(dtd, app)
   
   # May raise XMLError
   parser.parse_resource(filename)
   
   return app





class Parser(xmlproc.XMLProcessor):
   """
   <Purpose>
      Handles parsing an XML document based on an external DTD. 
      Any DOCTYPE in the XML file itself is ignored. 

   TODO finish comment
   """

   def parse_doctype(self):
      """
      <Purpose>
         Skips DOCTYPE declaration
         
      TODO finish comment
      """
      if self.seen_doctype == 1:
         xmlproc.XMLProcessor.parse_doctype(self)
      else:
         arizonareport.send_out(4, str("Ignoring DOCTYPE (%s,%d)" % (self.get_current_sysid(), self.get_line())) )
         self.scan_to("]>")
         self.seen_doctype = 1





class Validator(xmlval.XMLValidator):
   """
   <Purpose>
      Handles parsing an XML document based on an external DTD. 
      Any DOCTYPE in the XML file itself is ignored. 

   TODO finish comment
   """
   def __init__(self, dtd_id, app):
      self.parser = Parser()
      dtd = xmlval.load_dtd(dtd_id)
      self.app = app
      self.dtd = dtd
      self.val = xmlval.ValidatingApp(self.dtd, self.parser)
      self.val.reset()
      self.parser.reset()
      self.parser.set_application(self.app)
      self.parser.dtd = self.dtd
      self.parser.ent = self.dtd
      self.parser.set_read_external_subset(1)





def escape(string):
   """
   <Purpose>
      TODO fix comment
   """
   return xml.sax.saxutils.escape(string)





def unescape(string):
   """
   <Purpose>
      TODO fix comment
   """
   return xml.sax.saxutils.unescape(string)
