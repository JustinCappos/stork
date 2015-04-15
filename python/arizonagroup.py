#! /usr/bin/env python



"""
<Program Name>
   arizonagroup.py

<Started>   
   October 14 , 2006

<Author>
   Michael White

<Purpose>
   Creating and manipulating pacman groups.
"""

#           [option, long option,                    variable,            action,        data,     default,                            metavar,    description]
"""arizonaconfig
    options=[
	     ["", "--useunsignedfiles", "usesignedfiles", "store_false", None, True, None, "debug"]
            ]
    includes=[]
"""
#["",	"--setconfigfile",   "configfile", 	"store",  	"string", 	"/usr/local/stork/etc/stork.conf", 	"FILENAME",	"configuration file"]


#October 18, 2007Exception/error handling needs to be fully implemented

import types
import arizonacrypt
from xml.parsers.xmlproc import xmlproc
from arizonaxml import *
import arizonaconfig


#Should be true
#If it is False, it was left False for debugging purposes
#and should be changed to True before release
#This variable exists because I couldn't get init_options to work.
#Once it works, this should be removed
#usesignedfiles = False

usagemsg="""
DO IT RIGHT NEXT TIME
"""

def groupunion(groupName, A, B):
   """
   <Purpose>
      This function returns the union of the groups A and B. For the purposes of this function,
      a group is a list where the first element of the list is its name and all other elements
      are elements of the group

   <arguments>
      groupName:
         The name to be given the group this function will return.
	 
      A:
         The first group

      B:
         The second group

   <Exceptions>


   <Side Effects>
      None.

   <Returns>
      A new group containing all elements that are in A or B.
   """

#   if type(A) != types.ListType or type(B) != types.ListType type(groupName) != types.StringType:
#       raise Exception(TypeError)

   newGroup = [groupName]
      

   for elt in A[1:]:
      if newGroup[1:].count(elt) == 0:
	  newGroup.append(elt)

   for elt in B[1:]:
      if newGroup[1:].count(elt) == 0:
	  newGroup.append(elt)

   return newGroup





def groupintersect(groupName, A, B):
   """
   <Purpose>
      This function returns the intersection of the groups A and B. For the purposes of this function,
      a group is a list where the first element of the list is its name and all other elements
      are elements of the group

   <arguments>
      groupName:
         The name to be given the group this function will return.

      A:
         The first group.

      B:
         The second group.
   <Exceptions>


   <Side Effects>
      None.

   <Returns>
      A new group containing all that are in both A and B.
   """
   
   newGroup = [groupName]
   
   for elt in A[1:]:
      if B[1:].count(elt) > 0:
	  newGroup.append(elt)


   return newGroup






def groupinclude(A, newElements):
   """
   <Purpose>
      This function populates a group with elements. It is similar to groupunion with the
      difference that it does not create a new group.
      
   <arguments>

      A:
        The group to which elements will be added.

      newElements:
        The list of elements to be added.
        
   <Exceptions>


   <Side Effects>
      Adds the elements of newElements to A.

   <Returns>
      None.
   """
   
   for elt in newElements:
      if A.count(elt) == 0:
	  A.append(elt)

   return A




def groupexclude(A, eltsToRemove):
   """
   <Purpose>
      This function removes the elements of eltsToRemove from A in place.

   <arguments>

      A:
        The group from which elements will be removed.

      eltsToRemove:
        The list of elements to be removed.
        
   <Exceptions>


   <Side Effects>
      The contents of A are changed.

   <Returns>
      None.
   """
   
   for elt in eltsToRemove:
      i = 1
      while i < len(A):
         if elt ==  A[i]:
	     A[i:i+1] = []
	     i = i - 1

	 i = i+1
   







	     

def groupcomplement(groupName, A, B):
   """
   <Purpose>
      This function returns the complement of B in A (i.e. A/B, "A NOT B"), 
      the set of all elements x such that x is in A but x is not in B.
      

   <arguments>
   
      groupName:
         The name to be given to the new group.

      A:
         The complement will be taken with respect to this group.

      B:
        This function will return the complement of this group in A.
        
   <Exceptions>


   <Side Effects>
      

   <Returns>
      A new group, A/B.
   """

   newGroup = [groupName]

   i = 1
   while i < len(A):
      if B.count(A[i]) == 0:
	  newGroup.append(A[i])

      i = i + 1

   
   return newGroup





#Will work like complement
def groupsubtract(A, B):
   """
   <Purpose>
      Removes from A all elements in B.
      

   <arguments>

      A:
         The complement will be taken with respect to this group.

      B:
        This function will return the complement of this group in A.
        
   <Exceptions>


   <Side Effects>
      Changes the contents of A.

   <Returns>
      None

   """
   

   i = 1
   
   while i < len(A):
      if B.count(A[i]) > 0:
	  A[i:i+1] = []
	  i = i - 1

      i = i + 1










class GroupApp(xmlproc.Application):
    """This class parses the groups.xml file."""
    def __init__(self):
	# 
	# Do this the old way (instead of using super) because xmlproc is written using
	# old-style classes that don't work with super.
	#
	xmlproc.Application.__init__(self)
	CreateAttr(self, 'groups', {})		# Dictionary of group members
	CreateAttr(self, 'group', None)		# Current GROUP
	CreateAttr(self, 'loc', None)		# Parser locator
	CreateAttr(self, 'target', None)	# Target of INCLUDE
	CreateAttr(self, 'target1', None)	# First target of current action (e.g INTERSECT, DIFFERENCE, etc.)
	CreateAttr(self, 'target2', None)	# Second target of current action (e.g INTERSECT, DIFFERENCE, etc.)

    def set_locator(self, locator):
	self.loc = locator


    def doc_start(self):
	self.group = None


    def handle_start_tag(self, tag, attrs):
	line = self.loc.get_line()
	file = self.loc.get_current_sysid()
	if tag == "INTERSECT" or tag == "UNION" or tag == "COMPLEMENT" or tag == "DIFFERENCE":
	   self.group = attrs.get("NAME")
           if self.group in self.groups:
	      raise XMLError, "duplicate group:", self.group
	   self.groups[self.group] = [self.group]
           self.target1 = attrs.get("ARG1")
           self.target2 = attrs.get("ARG2")
	elif tag == "GROUP":
	   self.group = attrs.get("NAME")
	   if self.group in self.groups:
	      raise XMLError, "duplicate group:", self.group
	   self.groups[self.group] = [self.group]
	elif tag == "GROUPS" or tag == "INCLUDE" or tag == "EXCLUDE":
	   self.target = attrs.get("NAME")
	   pass
	else:
	   # Shouldn't happen if DTD is correct
	   raise XMLError , "invalid element: " + tag


    def handle_end_tag(self,tag):
        global glo_node
	if tag == "GROUP":
	    self.group = None
	    return
	elif tag == "GROUPS":
	    return

	
	#if self.target != None:
	#   print "self.target = " + self.target
	#if self.target1 != None:
	#   print "self.target1 = " + self.target1
	#if self.target2 != None:
	#   print "self.target2 = " + self.target2


	members = [self.target]
	if tag == "INCLUDE":
	    groupinclude(self.groups[self.group], members)
	elif tag == "INTERSECT":
	    self.groups[self.group] = groupintersect(self.group, self.groups[self.target1], self.groups[self.target2])
	elif tag == "UNION":
	    self.groups[self.group] = groupunion(self.group, self.groups[self.target1], self.groups[self.target2])
	elif tag == "DIFFERENCE":
	    self.groups[self.group] = groupcomplement(self.group, self.groups[self.target1], self.groups[self.target2])
	#elif tag == "COMPLEMENT":
	#?   
	else:
	    # Shouldn't happen if DTD is correct
	    raise XMLError , "invalid closing element: " + tag
	self.target  = None
	self.target1 = None
	self.target2 = None







def GroupFileParse(dtd, group_file_name):
   """Creates the parser for the groups.xml file and parses it.
   Returns a dictionary of group members."""
   
   arizonaconfig.init_options('arizonagroup.py', usage=usagemsg)
   #print arizonaconfig.get_option("usesignedfiles")
   try:
      # SMB - storkpackagelist.find_file() already checked the signature for
      # us, so we can assume the file is valid and extract the contents
      if arizonaconfig.get_option('usesignedfiles'):
	 #print "Reading signed file"
         temp_contents = arizonacrypt.XML_retrieve_originalfile_from_signedfile(group_file_name)
         #print temp_contents
      else:
	 #print "Reading unsigned file"
	 temp_contents = group_file_name
         
   except TypeError, e:
      arizonareport.send_error(0, str(e))
      sys.exit(1)
   
   app = GroupApp()
   parser = Validator(dtd, app)
   try:
      parser.parse_resource(temp_contents)
   except XMLError, e:
      print e
      sys.exit(1)
   
    # remove the temeporary file we created when we extracted the signed version
   try:
       os.remove(temp_contents)
   except:
       pass
   
   return app.groups









#This function was written with a poor understanding of how groups.pacman files should work,
#and may not even be necessary
def writeXMLfile(groupdictionary, filename):
   groupfile = open(filename, 'w')
   
   groupfile.write('<?xml version "1.0" encoding="ISO-8859-1" standalone="yes" ?>\n\n\n')
   
   groupfile.write('<GROUPS>\n')
   
   for groupname in groupdictionary:
      groupfile.write('<GROUP NAME="')
      groupfile.write(groupname)
      groupfile.write('">\n')
      group = groupdictionary[groupname]
      for items in group[1:]:
         groupfile.write('<INCLUDE NAME="')
         groupfile.write(items)
         groupfile.write('"/>\n')
               
      groupfile.write('</GROUP>\n')
   
   groupfile.write('</GROUPS>\n')

   groupfile.close()




#For debugging init_options
#Can probably be removed, now that it works
#def Main(path):
   
   #args = arizonaconfig.init_options(module = 'arizonagroup', usage=usagemsg)
   #print args
   #if args[0] == 'useunsignedfiles':
   #   print "Using unsigned files"
   #   global usesignedfiles
   #   usesignedfiles = False
   #   print locals()
   #   print globals()

   #GroupFileParse('groups2.dtd', 'white2.groups.pacman')




#if __name__ == '__main__':
   #Main(None)
