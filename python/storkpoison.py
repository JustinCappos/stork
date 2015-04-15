#! /usr/bin/env python
"""
<Program Name>
   storkpoison.py

<Started>
   Jan 9, 2008

<Author>
   Programmed by Scott Baker.

<Purpose>
   Routines for keeping track of poisoned keys.
"""

#           [option, long option,               variable,    action,        data,     default,                            metavar,      description]
"""arizonaconfig
   options=[
            ["",     "--poisondir",             "poisondir", "store",       "string", "/usr/local/stork/var/poisonkeys",  "dir",        "location of local poisoned keys (default /usr/local/stork/var/poisonkeys)"]]

   includes=[]
"""

import os
import arizonaconfig
import arizonacrypt
import arizonageneral




def is_poison_timestamp(timestamp):
   """
   <Purpose>
      Determines if a timestamp contains the poison value
   <Arguments>
      timestamp
         a timestamp value
   <Returns>
      True if timestamp contains poison value, false otherwise
   """
   if timestamp == -1:
      return True
   else:
      return False





def is_poisoned(key=None, string=None, file=None):
   """
   <Purpose>
      Checks to see if a key is poisoned
   <Arguments>
      one of the following should be specified:
         key - publickey object (see arizonacrypt.publickey)
         string - publickey string
         file = file containing public key
   """

   if not key:
      if string:
         key = arizonacrypt.PublicKey(string = string)
      elif file:
         key = arizonacrypt.PublicKey(file = file)

   assert(key)

   hash = key.hash;
   dir = arizonaconfig.get_option("poisondir")
   fn = os.path.join(dir, hash)

   if os.path.exists(fn):
      return True
   else:
      return False






def set_poisoned(key=None, string=None, file=None):
   """
   <Purpose>
      Sets a key as poisoned
   <Arguments>
      one of the following should be specified:
         key - publickey object (see arizonacrypt.publickey)
         string - publickey string
         file = file containing public key
   <Side Effects>
      Create files in poison subdirectory
   """

   if not key:
      if string:
         key = arizonacrypt.PublicKey(string = string)
      elif file:
         key = arizonacrypt.PublicKey(file = file)

   assert(key)

   hash = key.hash;
   dir = arizonaconfig.get_option("poisondir")
   fn = os.path.join(dir, hash)

   arizonageneral.makedirs_existok(dir)

   file = open(fn, "w")
   file.write(key.string)
   file.close()






def remove_poisoned(key=None, string=None, file=None):
   """
   <Purpose>
      Removes a poisoned key
   <Arguments>
      one of the following should be specified:
         key - publickey object (see arizonacrypt.publickey)
         string - publickey string
         file = file containing public key
   <Side Effects>
      Removes files in poison subdirectory
   """

   if not key:
      if string:
         key = arizonacrypt.PublicKey(string = string)
      elif file:
         key = arizonacrypt.PublicKey(file = file)

   assert(key)

   hash = key.hash;
   dir = arizonaconfig.get_option("poisondir")
   fn = os.path.join(dir, hash)

   try:
      os.remove(fn)
   except OSError:
      pass


