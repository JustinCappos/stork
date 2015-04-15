#! /usr/bin/env python
"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: vserver_share
Description:   Provide sharing and unsharing a directory, copying a file, 
      linking and unlinking a file, and protecting a file on a vserver
"""

import os
import arizonareport
import shutil
import stat


def authenticate(conn,info_string):

   """
   <Purpose>
      Basically authenticate a user, but on vserver, we don't need this 
      procedure.
   
   <Arguments>
      conn:
         'conn' is a socket object to send a message which may be produced
         by this function. However, we do not use 'conn' here.

      info_string:
         'info_string' is a command string received from a user. Again, we
         do not use it here.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      Alway True.
   """

   return True
  

   # so there's actually no way to mount directory from client side.
   # is there no way to see it's mounted or not?
   # -r option to protect directory is not working!!!!
def share_directory(source, source_dir, client, client_dir, flags, conn):

   """
   <Purpose>
      Share a directory between a vserver server directory and a vserver
      client directory. 
      Note: Mounting a directory on a client to server does not work.
   
   <Arguments>
      source:
         'source' is not used on vserver share.

      source_dir:
         'source_dir' is a directory on a vserver, which is mounted to a 
         client directory.
         'source_dir' should be a string.

      client:
         'client' is a vserver client service that a user want to share a
         directory to. 
         If the 'client' is not on service, /vservers/'client' won't exist.
         'client' should be a string.

      client_dir:
         'client_dir' is a directory that source_dir will be mounted to.
         'client_dir' should be a string.

      flags:
         'flags' is an indicator to check the shared directory needs to be
         protected. If 'flags' is True, the directory will be protected.

      conn:
         'conn' is a socket object to send a message which may be produced
         by this function. However, we do not use 'conn' here.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      True if sharing succeeds, otherwise False.
   """

   # check the first arguments are strings
   if not isinstance(source_dir, str):
      arizonareport.send_syslog(arizonareport.ERR, "share_directory(): source_dir should be a string.")
      return False

   if not isinstance(client, str):
      arizonareport.send_syslog(arizonareport.ERR, "share_directory(): client should be a string.")
      return False

   if not isinstance(client_dir, str):
      arizonareport.send_syslog(arizonareport.ERR, "share_directory(): client_dir should be a string.")
      return False

   if not os.path.isdir(source_dir):
      arizonareport.send_syslog(arizonareport.ERR, "share_directory(): source_dir does not exist.")
      return False

   # if /vservers/client doesn't exit, client may not be on service.
   if not os.path.isdir("/vservers/" + client):
      arizonareport.send_syslog(arizonareport.ERR, "share_directory(): " + client + " does not exist.")
      return False

   # create whole path
   client_whole_path = "/vservers/" + client + "/" + client_dir
   # check the client_dir exists or not
   if not os.path.isdir(client_whole_path):
      arizonareport.send_syslog(arizonareport.ERR, "share_directory(): " + client_dir + " does not exist in " + client + ".")
      return False
   
   # set the flag
   if flags == True:
      flags = "-r "
   else:
      flags = ""

   # check inode numbers of source and client directories.
   # if they are same, then it means they are shared alreay, so do nothing.
   if os.stat(source_dir)[stat.ST_INO] == os.stat(client_whole_path)[stat.ST_INO]:
      arizonareport.send_syslog(arizonareport.ERR, "share_directory(): " + source_dir + " is already shared")
      return False

   # using mount command, share a directory
   os.system("mount " + flags + "--bind " + source_dir + " " + client_whole_path)
   
   return True


def unshare_directory(target_server, target_dir, conn):

   """
   <Purpose>
      Unshare a directory between a vserver server directory and a vserver
      client directory. 
      Note: Unsharing works on a client, too.
   
   <Arguments>
      target_server:
         'target_server' is a server which has a directory to unshare.
         'target_server' should be a string.

      target_dir:
         'target_dir' is a directory on a vserver, which will be unmounted.
         'target_dir' should be a string.            

      conn:
         'conn' is a socket object to send a message which may be produced
         by this function. However, we do not use 'conn' here.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      True if unsharing succeeds, otherwise False.
   """

   # the first two arguments should be strings
   if not isinstance(target_server, str):
      arizonareport.send_syslog(arizonareport.ERR, "unshare_directory(): target_server should be a string.")
      return False
	   
   if not isinstance(target_dir, str):
      arizonareport.send_syslog(arizonareport.ERR, "unshare_directory(): target_dir should be a string.")
      return False

   # if target_server is specified, then the target directory can be found at /vservers/ directory.
   if target_server:
      target_whole_path = "/vservers/"+target_server+"/"+target_dir   
   else:
      target_whole_path = target_dir

   if not os.path.isdir(target_whole_path):
      arizonareport.send_syslog(arizonareport.ERR, "unshare_directory(): '" + target_whole_path + "' does not exist.")
      return False
   
   # unshare a directory, using umount command
   os.system("umount " + target_whole_path)

   return True


def copy_file(source_file, dest_serv, dest_file):
   """
   <Purpose>
      Copy a file from a source file to dest_file on dest_serv
   
   <Arguments>
      source_file:
         'source_file' is a file on vserver system to copy from.
         'source_file' should be a string.

      dest_serv:
         'dest_serv' is a vserver service which a source file is copied to
         'dest_serv' should be a string.            

      dest_file:
         'dest_file' is a file on vserver system to copy to.
         'dest_file' should be a string.

   <Exceptions>
      IOError:
         If copyfile fails, then return False.

   <Side Effects>
      None.

   <Returns>
      True if a copy succeeds, otherwise False.
   """

   # check all arguments are strings
   if not isinstance(source_file, str):
      arizonareport.send_syslog(arizonareport.ERR, "copy_file(): source_file should be a string.")
      return False

   if not isinstance(dest_serv, str):
      arizonareport.send_syslog(arizonareport.ERR, "copy_file(): dest_serv should be a string.")
      return False

   if not isinstance(dest_file, str):
      arizonareport.send_syslog(arizonareport.ERR, "copy_file(): dest_file should be a string.")
      return False

   # this copy is based on the fact that a root directory of a dest_serv is mounted to /versers/dest_serv
   # so we can just simply use copying.
   try:      
      shutil.copyfile(source_file, "/vservers/"+dest_serv+"/"+dest_file)
   # error occures when files don't exit or are not permitted to copy.
   except IOError, (errno, strerror):
      arizonareport.send_syslog(arizonareport.ERR, "copy_file(): I/O error(" + str(errno) + "): " + str(strerror))	
      return False	

   return True





def share_file(source_serv, source_file, dest_serv, dest_file):
   """
   <Purpose>
      Share a file from a source file to dest_file on dest_serv
   
   <Arguments>
      source_serv:
         'source_serv' is a vserver service which a source file is shared from
         'source_serv' should be a string.            

      source_file:
         'source_file' is a file on vserver system to share from.
         'source_file' should be a string.

      dest_serv:
         'dest_serv' is a vserver service which a source file is shared to
         'dest_serv' should be a string.            

      dest_file:
         'dest_file' is a file on vserver system to share to.
         'dest_file' should be a string.

   <Exceptions>
      OSError:
         If linking fails, then return False.

   <Side Effects>
      None.

   <Returns>
      True if sharing succeeds, otherwise False.
   """

   
   arizonareport.send_syslog(arizonareport.ERR, "share_file(): Needs to account for source vserver correctly # JUSTIN TODO FIXME")
   return False

   # check all arguments are strings
   if not isinstance(source, str):
      arizonareport.send_syslog(arizonareport.ERR, "share_file(): source should be a string.")
      return False

   if not isinstance(dest_serv, str):
      arizonareport.send_syslog(arizonareport.ERR, "share_file(): dest_serv should be a string.")
      return False

   if not isinstance(dest_file, str):
      arizonareport.send_syslog(arizonareport.ERR, "share_file(): dest_file should be a string.")
      return False

   # this copy is based on the fact that a root directory of a dest_serv is mounted to /vservers/dest_serv
   # so we can just simply use linking.
   try:
      os.link(source, "/vservers/"+dest_serv+"/"+dest_file)
   # error occures when files don't exit or is alreay linked.
   except OSError, (errno, strerror):
      arizonareport.send_syslog(arizonareport.ERR, "share_file(): I/O error(" + str(errno) + "): " + str(strerror))	
      return False

   return True





def unshare_file(dest_serv, dest_file):
   """
   <Purpose>
      Unshare a dest_file on dest_serv.
   
   <Arguments>
      dest_serv:
         'dest_serv' is a vserver service.
         'dest_serv' should be a string.            

      dest_file:
         'dest_file' is a file on vserver system to be unshared.
         'dest_file' should be a string.

   <Exceptions>
      OSError:
         If unlinking fails, then return False.

   <Side Effects>
      None.

   <Returns>
      True if unsharing succeeds, otherwise False.
   """

   # check all arguments are strings
   if not isinstance(dest_serv, str):
      arizonareport.send_syslog(arizonareport.ERR, "unshare_file(): dest_serv should be a string.")
      return False

   if not isinstance(dest_file, str):
      arizonareport.send_syslog(arizonareport.ERR, "unshare_file(): dest_file should be a string.")
      return False
   
   # this copy is based on the fact that a root directory of a dest_serv is mounted to /versers/dest_serv
   # so we can just simply use unlinking.
   try:
      os.unlink("/vservers/"+dest_serv+"/"+dest_file)
   # error occures when files don't exit.
   except OSError, (errno, strerror):
      arizonareport.send_syslog(arizonareport.ERR, "unshare_file(): I/O error(" + str(errno) + "): " + str(strerror))	
      return False


   return True





def protect_file(source, source_file, conn):
   """
   <Purpose>
      Protect a source_file.
   
   <Arguments>
      source:
         'source' is not used.        

      source_file:
         'source_file' is a file on vserver system to be protected.
         'source_file' should be a string.

      conn:
         'conn' is a socket object to send a message which may be produced
         by this function. However, we do not use 'conn' here.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      True if protecting succeeds, otherwise False.
   """

   # source_file should be a string
   if not isinstance(source_file, str):
      arizonareport.send_syslog(arizonareport.ERR, "protect_file(): source_file should be a string.")
      return False
   
   # only files in current server can be protected
   if source:
      arizonareport.send_syslog(arizonareport.ERR, "protect_file(): Protecting a file not in my vserver " + filename)
      return False
   
   # check the source file exists
   if not os.path.isfile(source_file):
      arizonareport.send_syslog(arizonareport.ERR, "protect_file(): '" + source_file + "' does not exist.")
      return False
      
   
   # make the file 'immutable'
   os.system("chattr +i "+source_file)
   # make the file 'append only'
   os.system("chattr +a "+source_file)
   return True





def init_client(conn, client_name):
   """
   <Purpose>
      Basically initialize a client, but on vserver, we don't need this 
      procedure.
   
   <Arguments>
      conn:
         'conn' is a socket object to send a message which may be produced
         by this function. However, we do not use 'conn' here.

      client_name:
         'client_name' is not used here.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      Alway True.
   """
   return True




def share_name():
   """
   <Purpose>
      Return the name of this module.
   
   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      Return 'vserver' as a share name.
   """
   return 'vserver'

