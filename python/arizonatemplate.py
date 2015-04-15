# /usr/bin/env python

"""
<Program Name>
   arizonatemplate.py

<Started>   
   September 8, 2007

<Author>
   Justin Cappos

<Purpose>
   This loads simple templates and does replacements with caller specified 
   arguments.   Data is then returned as a string with the relevant tags 
   replaced.   There are a few HTML specific items in some of the functions,
   but there is nothing that is inherently HTML much of the functionality.

   An example document might look like this:

      <HTML>
      <head>
      <title>Foobar</title>
      <LINK href="static/stork.css" rel="stylesheet" type="text/css">
      </head>
      <body>
      <h1>
      ###FOO###
      </h1>
      <A HREF="###BAR###">###BAZ###</A> leads to ###BAR###
      </body>
      </html>
 
   There are three different replacement tags in this example (the BAR tag is
   listed twice).   This module replaces those tags with the appropriate text.   
"""


import os
import arizonaconfig

#           [option, long option,      variable,  action,        data,  default, metavar, description]
"""arizonaconfig
   options=[["","--tagindicator","tagindicator", "store",    "string",    "###",    None, "This is the symbol that denotes the start and stop of a tag (default '###')"]]

   includes=[]
"""


# a directory to search for templates. If it is none, then the current
# directory is searched

glo_template_dir = None


# This class is basically just a string but the type is different so that
# one can discern the difference between a string and a tag.
#
# If this gets any more complex it needs to be tested and documented better.
class Tag:
   tagname = ''
   def __init__(self, tn=''):
      self.tagname = tn




# We'll only load each template from disk the first time it's used.   From then
# on we'll just used the cached copy stored here
templatestore = {}

def retrieve_template(template_fn, tokendict={}):
   """
   <Purpose>
      Retrieve a template and fill it in.   This is the only function you
      need to use externally.

   <Arguments>
      template_fn: A string containing the file name of the template file.
      tokendict: A dictionary with the keys as the replacement tags and the
                 values the strings that should be listed there.

   <Exceptions>
      IOError:    as thrown by open(), read() and close()
      IndexError: if there is a mismatch with tokendict and the replacement
                  tags in the template document.
      ValueError: if the replacement tags are malformatted

   <Side Effects>
      May read the template from disk (if it isn't already cached) and if so
      will add the data to the global templatestore.

   <Returns>
      The HTML of the template with the items replaced.
   """

   # Argument checking needed


   global templatestore

   # Check to see if this is in my cache
   if template_fn not in templatestore:
      # if the glo_template_dir option was specified, then search for templates
      # in that directory
      if template_fn.startswith("/") or (not glo_template_dir):
         template_pathname = template_fn
      else:
         template_pathname = os.path.join(glo_template_dir, template_fn)

      # load it in
      templatefileobj = open(template_pathname,"r")
      templatestore[template_fn] = templatefileobj.read()
      templatefileobj.close()


   # It's now in my cache, so do the replacements...
   usedtags = []
   outstring = ''
   for item in divide_string_into_taglist(templatestore[template_fn]):
      if isinstance(item, str):
         # append strings
         outstring += item
      elif isinstance(item, Tag):
         # replace tags and append
         thistagname = item.tagname

         # put it in the used tag list
         if thistagname not in usedtags:
            usedtags.append(thistagname)
         
         # May throw an IndexError
         outstring += tokendict[thistagname]
      else:
         raise Exception, "Internal Error, item not a string or tag!"

   # Check that all the tokens were used
   usedtags.sort()
   totaltokens = tokendict.keys()
   totaltokens.sort()

   if usedtags != totaltokens:
      raise IndexError, "Mismatch between the used tags ("+str(usedtags)+") and the token keys ("+str(tokendict)+") in retrieve template"
 
   return outstring
   
         
         
       
   
   
   



        
def divide_string_into_taglist(instring):
   """
   <Purpose>
      Take a string and return a list comprised of strings and tags.
      This is intended to be private, but I can't figure out how to make 
      the unit test module test a function starting with __.

   <Arguments>   
      instring:  The string to manipulate

   <Exceptions>
      ValueError: if the tags are malformatted

   <Side Effects>
      None

   <Returns>
      A list containing strings and tags.   This can be used by the caller to
      do replacements on tags.   There will never be two consecutive
      strings or tags in the returned list.   However the strings may be '' if
      there are consecutive tags.
   """

   # I need to add argument checking...


   
   tagindicator = arizonaconfig.get_option("tagindicator")

   # Break the file into a list of strings.   The even should be tags and the 
   # odd should be strings.   
   stringlist = instring.split(tagindicator)

   # If the list has even length then there was an odd number of tag indicators
   if len(stringlist) % 2 == 0:
      raise ValueError, "Odd number of tag indicators in arizonatemplate"

   retlist = []
   for index in range(0, len(stringlist)):
      # if an odd element it's okay as is 
      # The code checks for even because list indices start at 0
      if index % 2 == 0:
         retlist.append(stringlist[index])
      # otherwise make it into a tag
      else:
         retlist.append(Tag(stringlist[index]))
      
   return retlist
      
   


     


