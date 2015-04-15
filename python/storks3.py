#! /usr/bin/env python
"""
Stork Project (http://www.cs.arizona.edu/stork/)
Module: arizonacrypt
Description:
"""


# This sets up the options for arizonaconfig
#           [option, long option,  variable,   action,  data,     default,  metavar,    description]#
"""arizonaconfig
   options=[["",     "--awskey",         "awskey",         "store",    "string",    None,    None,  "AWS key for S3"],
            ["",     "--awssecretkey",   "awssecretkey",   "store",    "string",    None,    None,  "AWS secret key for S3"],
            ["",     "--awsbucket",      "awsbucket",      "store",    "string",    "stork",    None,  "AWS bucket name"]]
   includes=[]
"""

import sys
import re
import os.path
import tempfile
import shutil
import arizonareport
import arizonaconfig
import arizonageneral

# import the amazon S3 code
import s3.S3 as S3

glo_aws_conn = None
glo_aws_generator = None
glo_aws_bucket = None
glo_initialized = False

def init():
   global glo_aws_conn
   global glo_aws_generator
   global glo_aws_bucket
   global glo_initialized

   if glo_initialized:
       return True

   awskey = arizonaconfig.get_option("awskey")
   awssecretkey = arizonaconfig.get_option("awssecretkey")
   bucket = arizonaconfig.get_option("awsbucket")

   if (not awskey) or (not awssecretkey):
      raise TypeError, "Please configure your awskey and awssecretkey"

   glo_aws_conn = S3.AWSAuthConnection(awskey, awssecretkey)
   glo_aws_generator = S3.QueryStringAuthGenerator(awskey, awssecretkey)

   if bucket[0] == '*':
      # if the user puts a '*' as the first character, then lets assume he
      # wants to specify an absolete bucket name, and not prepend the
      # awskey
      glo_aws_bucket = bucket[1:]
   else:
      glo_aws_bucket = awskey.lower() + bucket

   # create the bucket in case it does not exist
   glo_aws_conn.create_bucket(glo_aws_bucket)

   glo_initialized = True

def dumpbuckets():
   global glo_aws_conn
   global glo_aws_bucket

   result = glo_aws_conn.list_all_my_buckets()

   if result.http_response.status != 200:
       raise TypeError, result.http_response.reason

   for entry in result.entries:
       print str(entry.name)

def dumpdir():
   entries = readdir()

   for entry in entries:
       print str(entry.key) + " " + str(entry.size)

def get_highestkey(entries):
    highestkey = None
    for entry in entries:
        if (highestkey == None) or (entry.key > highestkey):
            highestkey = entry.key
    return highestkey

def readdir():
   global glo_aws_conn
   global glo_aws_bucket

   entries = []

   # start reading from the top, so set marker=None
   marker = None
   more = True

   while more:
      # if we have a marker from the previous call to list_bucket, then we'll
      # use that marker as the place to start this readdir
      query = {}
      if marker:
          query['marker'] = marker

      result = glo_aws_conn.list_bucket(glo_aws_bucket, query)

      if result.http_response.status != 200:
          raise TypeError, result.http_response.reason

      entries.extend(result.entries)

      # is_truncated indicates that there are more entries to read. We'll get
      # the next_marker by finding the highest key that S3 returned to us.
      if result.is_truncated:
         more = True;
         marker = get_highestkey(entries)
      else:
         more = False

   return entries

def put_file(local_filename, remote_name, metadata={}):
   global glo_aws_conn
   global glo_aws_bucket

   # read the local file
   fileobj = file(local_filename,'r')
   content = fileobj.read()
   fileobj.close()

   # make a copy since we will be modifying it
   metadata = metadata.copy()

   metadata['local-filename'] = local_filename

   # create an S3 object to hold it
   obj = S3.S3Object(content, metadata)

   # the public-read acl allows us to use torrents
   headers = { 'Content-Type': 'Application/Octet',
               'x-amz-acl': 'public-read' }

   result = glo_aws_conn.put(glo_aws_bucket, remote_name, obj, headers)

   if result.http_response.status != 200:
       arizoanreport.send_error(0, "s3 error " + str(result))
       raise TypeError, result.http_response.reason

def get_file(remote_name, local_filename):
   global glo_aws_conn
   global glo_aws_bucket

   result = glo_aws_conn.get(glo_aws_bucket, remote_name)

   if result.http_response.status != 200:
       arizonareport.send_error(0, "s3: " + str(result.http_response.reason))
       raise TypeError, result.http_response.reason

   # if local_filename == None, then try to get it from the S3 metadata for
   # this object
   if not local_filename:
       local_filename = result.object.metadata.get('local-filename', None)
       if not local_filename:
           arizonareport.send_error(0, "s3: unable to determine local filename")
           raise TypeError, "unable to determine local filename"

   fileobj = file(local_filename, 'w')
   fileobj.write(result.object.data)
   fileobj.close()

   return result.object.metadata

def destroy():
   global glo_aws_conn
   global glo_aws_bucket

   entries = readdir()

   for entry in entries:
       result = glo_aws_conn.delete(glo_aws_bucket, entry.key)
       arizonareport.send_out(1, "delete: " + entry.key + " result=" + \
           str(result.http_response.status))

   result = glo_aws_conn.delete_bucket(glo_aws_bucket)
   arizonareport.send_out(1, "delete bucket result=" + \
       str(result.http_response.status))

