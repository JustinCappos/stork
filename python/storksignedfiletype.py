#! /usr/bin/env python

"""
<Program Name>
   storksignedfiletype.py

<Started>
   Nov 16, 2006

<Author>
   Programmed by Jeremy Plichta

<Purpose>
    The repository needs to know whether or not a file
    that someone uploads is actually what they say it is
    (ex: tpfile, pacmanfile, )
    
    We will just try to guess what type of file it is
    by searching for key words in the contents of the
    file. We will print out what type of file we think
    it is that way the user of this program knows what
    to do with it.
    
"""
import os
import sys

def main():
    
    if len(sys.argv)<2:
        print "usage: storksignedfiletype.py <filename>"
        sys.exit(1)
    
    filename = sys.argv[1]
    
    if not os.path.isfile(filename):
        print "error: "+filename+" is not a file."
        sys.exit(1)
        
        
    #open the file up
    file = open(filename, 'r')
    filestring = file.read()
    
    if "/TRUSTEDPACKAGES" in filestring:
        print "trustedpackage"
    elif "/PACKAGES" in filestring:
        print "pacman"
    elif "/GROUPS" in filestring:
        print "pacman"
    else:
        print "other"
    
    file.close()





if __name__ == "__main__":
    main()