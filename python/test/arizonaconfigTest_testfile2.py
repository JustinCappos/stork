#! /usr/bin/env python

#           [option, long option,  variable,   action,  data,     default,     metavar, description]
"""arizonaconfig
   options=[["",     "--nesttype", "nesttype", "store", "string", "planetlab", "NAME",  "the type of nest to be used (default planetlab)"],
            ["",     "--transfermethod",  "transfermethod", "append", "string", ["ftp", "http"], "program", "use this method to transfer files (default ftp, http)"],
            ["",     "--transfertempdir", "transfertempdir", "store", "string", "/tmp/stork_trans_tmp", "PATH", "use this path to save transferd files temporary (default is /tmp/stork_trans_tmp)"],
            ["",     "--metafilecachetime", "metafilecachetime", "store", "int", 60, None, "seconds to cache metafile without re-requesting"]]
            
   includes=["test/arizonaconfigTest_testfile3.py"]
"""

