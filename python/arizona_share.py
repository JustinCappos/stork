#! /usr/bin/env python

import arizonaconfig
import arizonareport
import os

#           [option, long option,  variable,   action,  data,     default,     metavar, description]
"""arizonaconfig
   options=[["",     "--nesttype", "nesttype", "store", "string", "planetlab", "NAME",  "the type of nest to be used (default planetlab)"]]
   includes=["$MAIN/share/*"]        
"""

chosen_nesttype = None





def decide_nesttype():
   global chosen_nesttype
   given_nesttype = arizonaconfig.get_option("nesttype")
   if given_nesttype == None:
      raise IOError, "nesttype has not been set"
   
   if chosen_nesttype == None or chosen_nesttype.share_name() != given_nesttype:
      try:
        # TODO possible security problem?   For example, given_nesttype="planetlab_share as chosen_nesttype; hostile code...; #"
         exec ('import share.' + given_nesttype + '_share as chosen_nesttype')
         globals()['chosen_nesttype'] = locals()['chosen_nesttype']
         chosen_nesttype.init_sharing_program()
      except ImportError, (errno):
         arizonareport.send_error(0, "decide_nesttype : Import error(%s)" % (errno))	





def init():
   """ 
   Imports the appropriate nest type and calls its init function. 
   This function isn't strictly necessary to be called, as the other 
   functions also do the init if it hasn't been.. but it allows better 
   error reporting: This can be called before creating a daemon, so an 
   error can be printed. 
   """
   decide_nesttype()





def share_directory(source, source_dir, client, client_dir, flags):
   """ like a mount... source/source_dir are the real drive /home, client/client_dir are the mapped drive /mnt/home
       source is the remote systemo or me? how do I choose?
       client is target
       
       
      source_dir = /a, and client_dir = /b, so /b is a mount point of /a
      source and client might be different slices
          
   """
   decide_nesttype()
   return chosen_nesttype.share_directory(source, source_dir, client, client_dir, flags)


def unshare_directory(target, target_dir):
   decide_nesttype()
   return chosen_nesttype.unshare_directory(target, target_dir)



def link_file(source_slice, source_file, target_slice, target_file, verify_same=False):
   """ creates a hard link (directory entry) for a file in another slice """
   decide_nesttype()
   return chosen_nesttype.link_file(source_slice, source_file, target_slice, target_file, verify_same)



def link_directory(source_slice, source_dir, target_slice, target_dir, verify_same=False):
   decide_nesttype()

   for root, dirs, files in os.walk(source_dir):
      for name in files:
         real_target_file = target_dir + os.path.join(root, name).split(source_dir)[1]
         if not (chosen_nesttype.link_file(source_slice, os.path.join(root, name), target_slice, real_target_file, verify_same)):
            return False
            
   return True
       


def unlink_file(target_slice, target_file):
   decide_nesttype()
   return chosen_nesttype.unlink_file(target_slice, target_file)



def unlink_directory(target_slice, target_dir):
   decide_nesttype()
   fn_exists = False
   try:
      fn_exists = callable(chosen_nesttype.unlink_directory)
   except AttributeError:
      pass

   if fn_exists:
      return chosen_nesttype.unlink_directory(target_slice, target_dir)
   else:
      for root, dirs, files in os.walk(source_dir):
         for name in files:
            if not (chosen_nesttype.unlink_file(target_slice, os.path.join(root, name))):
               return False
   return True



def protect_file(target_slice, target_file):
   """
   protect a file against modification
   returns True on success, False on error
   """
   decide_nesttype()
   return chosen_nesttype.protect_file(target_slice, target_file)



def protect_directory(target_slice, target_dir):
   """ protect all subdirectories and files of the given directory """
   decide_nesttype()
   fn_exists = False
   try:
      fn_exists = callable(chosen_nesttype.protect_directory)
   except AttributeError:
      pass

   if fn_exists:
      return chosen_nesttype.protect_directory(target_slice, target_dir)
   else:
      for root, dirs, files in os.walk(target_dir):
         for name in files:
            if not chosen_nesttype.protect_file(target_slice, os.path.join(root, name)):
               return False
   return True         	



def init_client(client_name):
   """ PLANETLAB ONLY assumes client created .exportdir file, tries to map their / to /children/client_name"""
   decide_nesttype()
   return chosen_nesttype.init_client(client_name)


def copy_file(source_slice, source_file, target_slice, target_file):
   decide_nesttype()
   return chosen_nesttype.copy_file(source_slice, source_file, target_slice, target_file)
   
def copy_directory(source_slice, source_dir, target_slice, target_dir):
   decide_nesttype()
   fn_exists = False
   try:
      fn_exists = callable(chosen_nesttype.copy_directory)
   except AttributeError:
      pass
   
   if fn_exists:
      chosen_nesttype.copy_directory(source_slice, source_dir, target_slice, target_dir)
   else:
      for root, dirs, files in os.walk(source_dir):
         for name in files:
            real_target_file = target_dir + os.path.join(root, name).split(source_dir)[1]
            if not (chosen_nesttype.copy_file(source_slice, os.path.join(root, name), target_slice, real_target_file)):
               return False
   return True
   


def identify(data):
   decide_nesttype()
   chosen_nesttype.identify(data)

   
def identifyready(data):
   decide_nesttype()
   temp = chosen_nesttype.identifyready(data)
   return temp


def get_identified_clientname():
   decide_nesttype()
   return chosen_nesttype.get_identified_clientname()

