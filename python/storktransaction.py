"""
<Program Name>
   storktransaction.py

<Started>
   Jan 19, 2007

<Author>
   Programmed by Scott Baker.

<Purpose>
   Creation and maintenance of transaction lists. A transaction list is a list
   of packages to install, remove, and/or upgrade.

   Transaction List: A translaction list is a list of transaction entries

   Transaction entry format: A transaction is a dictionary with the following
   keys:
      trans['op']:        
         operation to perform: INSTALL, UPGRADE, or REMOVE
      trans['filename']:  
         local filename of rpm file (usually in /tmp). Used during INSTALL and
         UPGRADE operations.
      trans['conflicts']:
         list of installed package names that conflict. Used during UPGRADE 
         operations.
      trans['packname']:
         name of package. Used during REMOVE operations.

   Transaction lists are created with:
      tl = storktransaction.tl_create()

   New entries are added to the tail of the list via any of the following:
      tl = storktransaction.tl_install(tl, package_filename)
      tl = storktransaction.tl_upgrade(tl, package_filename, conflict_list)
      tl = storktransaction.tl_remove(tl, package_name)
"""

import arizonareport
import arizonageneral
import os

# these constants may be used when inspecting the 'op' field of a transaction
# entry:

INSTALL = "INSTALL"
UPGRADE = "UPGRADE"
REMOVE = "REMOVE"

def tl_create():
   """
   <Purpose>
      Creates an empty transaction list.

   <Arguments>
      None.

   <Exceptions>
      None.
      
   <Side Effects>
      None.

   <Returns>
      An empty transaction list.
   """
   return []

def tl_add(tl, transaction):
   """
   <Purpose>
      Appends a transaction entry to the tail of a transaction list

   <Arguments>
      tl - transaction list
      transaction - transaction entry

   <Exceptions>
      None.
      
   <Side Effects>
      The transaction is added to the end of the list.

   <Returns>
      None.
   """
   arizonageneral.check_type_simple(tl, "tl", list, "storktransaction.tl_add")
   
   tl.append(transaction)

def tl_install(tl, filename):
   """
   <Purpose>
      Adds an INSTALL operation to a transaction list.

   <Arguments>
      tl - transaction list
      filename - local filename of package

   <Exceptions>
      None.
      
   <Side Effects>
      Transaction is appended to the end of the list.

   <Returns>
      None.
   """
   trans = {}
   trans['op'] = INSTALL
   trans['filename'] = filename
   tl_add(tl, trans)

def tl_upgrade(tl, filename, conflict_list):
   """
   <Purpose>
      Adds an UPGRADE operation to a transaction list.

   <Arguments>
      tl - transaction list
      filename - local filename of package
      conflict_list - list of package names that conflict with this pacakge

   <Exceptions>
      None.
      
   <Side Effects>
      Transaction is appended to the end of the list.

   <Returns>
      None.
   """
   arizonageneral.check_type_simple(filename, "filename", str, "storktransaction.tl_add")
   arizonageneral.check_type_simple(conflict_list, "conflict_list", list, "storktransaction.tl_add")
   trans = {}
   trans['op'] = UPGRADE
   trans['filename'] = filename
   trans['conflicts'] = conflict_list
   tl_add(tl, trans)

def tl_remove(tl, packname):
   """
   <Purpose>
      Adds a REMOVE operation to a transaction list.

   <Arguments>
      tl - transaction list
      packname - name of installed package to remove

   <Exceptions>
      None.
      
   <Side Effects>
      Transaction is appended to end of list.

   <Returns>
      None.
   """
   trans = {}
   trans['op'] = REMOVE
   trans['packname'] = packname
   tl_add(tl, trans)

def tl_print(tl):
   """
   <Purpose>
      Print the contents of a transaction list.

   <Arguments>
      tl - transaction list

   <Exceptions>
      None.
      
   <Side Effects>
      None.

   <Returns>
      None.
   """
   arizonageneral.check_type_simple(tl, "tl", list, "storktransaction.tl_print")
   
   for trans in tl:
      arizonageneral.check_type_simple(trans, "trans", dict, "storktransaction.tl_print")
      operation = trans['op']
      print_string = "   " + operation
      if operation == INSTALL:
         print_string += " " + trans['filename']
      elif operation == REMOVE:
         print_string += ' ' + trans['packname']
      elif operation == UPGRADE:
         print_string += ' ' + trans['filename']
         if 'conflicts' in trans:
            print_string += "     will replace: " + str(trans['conflicts'])
      print print_string

def tl_get_count(tl, kind):
   count = 0
   for trans in tl:
      if (kind == None) or (trans['op'] == kind):
         count = count + 1
   return count
          
def tl_get_filename_list(tl, kind):
   filename_list = []
   for trans in tl:
      if (kind==None) or (trans['op'] == kind):
         if 'filename' in trans:
            filename_list.append(trans['filename'])
   filename_list = arizonageneral.uniq(filename_list)
   return filename_list

def tl_get_packname_list(tl, kind):
   packname_list = []
   for trans in tl:
      if (kind == None) or (trans['op'] == kind):
         if 'packname' in trans: 
            packname_list.append(trans['packname'])
   packname_list = arizonageneral.uniq(packname_list)
   return packname_list

def tl_get_conflict_list(tl, kind):
   conflict_list = []
   for trans in tl:
      if (kind == None) or (trans['op'] == kind):
         if 'conflicts' in trans: 
            conflict_list.extend(trans['conflicts'])
   conflict_list = arizonageneral.uniq(conflict_list)
   return conflict_list
