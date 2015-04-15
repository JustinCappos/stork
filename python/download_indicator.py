#! /usr/bin/env python

"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: download_indicator
Description:   Has a function 'download_indicator' which is used to show
               progress bar while downloading.               
Programmed by Jeffry Johnston
"""

import math
import arizonareport

glo_width = 70

def set_filename(filename):
   """
   <Purpose>
      Set the file name for download_indicator function.
      
   <Arguments>
      filename:
         it will be set and used for download_indicator to show the file
         name on the screen.
   
   <Exceptions>
      TypeError:
         If the filename passed in is not a string, TypeError is raised

   <Side Effects>
      Assign filename passed in to glo_filename.

   <Returns>
      None.
   """
   # if filename is not a string, then raise TypeError.
   if not isinstance(filename, str): 
      arizonareport.send_syslog(arizonareport.ERR, "set_filename(): 'filename' is incorrect")
      raise TypeError

   arizonareport.send_out_comma(0, filename + ":")





def get_width():
   """ Returns the currently set console width, as set by set_width() """
   return glo_width
   
   
   


def set_width(width):
   """
   <Purpose>
      Set the console width for download_indicator function.
      
   <Arguments>
      width:
         maximum width of the console text on the screen
   
   <Exceptions>
      TypeError:
         If the filename passed in is not a string, TypeError is raised

   <Side Effects>
      Assign filename passed in to glo_filename.

   <Returns>
      None.
   """
   global glo_width

   # if width is not an int, then raise TypeError.
   if not isinstance(width, int): 
      arizonareport.send_syslog(arizonareport.ERR, "set_width(): 'width' is incorrect")
      raise TypeError

   glo_width = width





def download_indicator(block_count, block_size, file_size):
   """
   <Purpose>
      Displays a progress indicator to show download progress [====     ]
      
   <Arguments>
      block_count:
         Number of blocks that have been downloaded.
         Note: Bytes downloaded = block_count * block_size.

      block_size:  
         Size of each block.  

      file_size:    
         Size of the file in bytes.  
   
   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      None.
   """
   # calculate file size in 'block_size' blocks
   #file_blocks = math.ceil(float(file_size) / float(block_size)) + 1
   
   # find bar width
   width = glo_width - (6 + 2 * len(str(file_size)))
   
   # calculate progress and amount downloaded 
   #progress = int(math.ceil(block_count / file_blocks * width))
   bytes_downloaded = block_count * block_size
   progress = int(math.ceil(width * bytes_downloaded / file_size))
   if progress > width:
      progress = width
   
   # generate progress indicator string
   st = "\r" + "[" + ("=" * progress) + (" " * (width - progress)) + \
        "] " + str(int(min(bytes_downloaded, file_size))) + "/" + \
        str(file_size) + " "
        
   # did the indicator still end up too wide?  If so, cut it off so that 
   # it does not wrap      
   if len(st) > glo_width:
      st = st[0:width - 3] + "..."

   arizonareport.send_out_comma(0, st)

