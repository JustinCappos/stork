#! /usr/bin/env python

"""
<Program Name>
   storkvalidatepublickey.py

<Started>
   Nov 16, 2006

<Author>
   Programmed by Jeremy Plichta

<Purpose>
   The repository needs to know if a public key someone
   uploads is actually a valid public key. We need to 
   do more then name checking (ex: see if the filename
   contains .pubkey) so someone can't "accidently"
   rename /bin/ls to mykey.pubkey and then try to
   upload it.
   
   This will use the arizonacrypt functions to check
   and see if the publickey contained within a file
   is valid.
"""

#           [option, long option,      variable,       action,  data,     default,                           metavar, description]
"""arizonaconfig
   options=[
            ["-C",   "--configfile",   "configfile",   "store", "string", "/usr/local/stork/etc/stork.conf", "FILE", "use a different config file (/usr/local/stork/etc/stork.conf is the default)"]
          ]
   includes=[]        
"""

import sys
import os
import arizonacrypt
import arizonageneral
import arizonaconfig
import arizonareport

def main():
    args = arizonaconfig.init_options("storkvalidatepublickey.py")
  
    
    if len(args) != 1:
        arizonareport.send_error(1, "usage: storkvalidatepublickey.py <potential public key>")
        sys.exit(1)
        
    
    if not os.path.isfile(args[0]):
        arizonareport.send_error(1, "error: " + args[0] + " is not a file.")
        sys.exit(1)
        
    
    # use arizonacrypt to see if this filecontains a valid pubkey
    (isvalidkey, keycontents) = arizonacrypt.publickey_fn_to_sl(args[0],"rsa")
    
    if( isvalidkey ):
        arizonareport.send_out(1, args[0] + " is a valid public key file")
        sys.exit(0)
    else:
        arizonareport.send_error(1, args[0] + " is NOT a valid public key file")
        sys.exit(1)


if __name__ == "__main__":
    main()
