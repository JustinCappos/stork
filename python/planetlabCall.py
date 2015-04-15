# /usr/bin/env python

"""
<Program Name>
   planetlabCall.py

<Started>
   September 16, 2007

<Author>
   Scott Baker

<Purpose>
   Stubs for PLC api functions

   Detailed information about args, the API itself, etc. is at:
   http://www.planet-lab.org/doc/plc_api and
   http://www.planet-lab.org/doc/plcapitut
"""

import planetlabAPI



def SliceListUserSlices(username):
   return planetlabAPI.doplccall("SliceListUserSlices", username)

   



def SliceNodesList(slicename):
   # TODO: check parameters
   return planetlabAPI.doplccall("SliceNodesList", slicename)





def SliceNodesAdd(slicename, nodes):
   # TODO: check parameters
   return planetlabAPI.doplccall("SliceNodesAdd", slicename, nodes)





def SliceNodesDel(slicename, nodes):
   # TODO: check parameters
   return planetlabAPI.doplccall("SliceNodesDel", slicename, nodes)

def SliceGetId(slicename):
   slice_data = {}
   slice_data['name'] = slicename
   slice_info = planetlabAPI.doplccall("GetSlices", slice_data)[0]
   return slice_info['slice_id']

def SliceGetAttributes(slice_id, attribute_name):
   filter = {}
   filter['slice_id'] = slice_id
   filter['name'] = "plc_initscript_id"

   attributes = planetlabAPI.doplccall("GetSliceAttributes", filter)

   return attributes

def SliceAddAttribute(slice_id, name, value):
   planetlabAPI.doplccall("AddSliceAttribute", slice_id, name, value)

def SliceDeleteAttribute(attribute_id):
   planetlabAPI.doplccall("DeleteSliceAttribute", attribute_id)



def SliceGetInitscripts(slicename):
   slice_id = SliceGetId(slicename)

   attributes = SliceGetAttributes(slice_id, "plc_initscript_id")

   values = []
   for attribute in attributes:
      values.append(attribute['value'])

   return values


def do_initscript_addremove(slice_name, add_id=-1, remove_id=-1):

   slice_id = SliceGetId(slice_name)

   attributes = SliceGetAttributes(slice_id, "plc_initscript_id")

   already_added = False
   for attribute in attributes:
      if attribute['value'] == str(remove_id):
         print "Deleting attribute plc_initscript_id=" + str(remove_id)
         SliceDeleteAttribute(attribute['slice_attribute_id'])
      elif attribute['value'] == str(add_id):
         print "Already have attribute plc_initscript_id=" + str(add_id)
         already_added = True

   if (add_id >= 0) and (not already_added):
      print "Adding plc_initscript_id=" + str(add_id)

      # AddSliceAttribute appears to be looking for these global variables
      global string0, string1, int2
      string0 = slice_name
      string1 = "plc_initscript_id"
      int2 = int(add_id)

      SliceAddAttribute(slice_id, "plc_initscript_id", add_id)



def AdmGetNodes():
   return planetlabAPI.doplccall("AdmGetNodes")

