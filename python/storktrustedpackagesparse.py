#!/usr/bin/env python
"""
<Program Name>
   storktrustedpackagesparse.py

<Author>
   Justin Cappos  

<Purpose>
   Trustedpackages parser
"""

#            [option, long option,                   variable,   action,        data,     default,                                    metavar,     description]
"""arizonaconfig
    options=[["",     "--trustedpackagesdtd",        "tpdtd",      "store",       "string", "/usr/local/stork/bin/trustedpackages.dtd", "FILENAME",  "The trustedpackages DTD file"],
             ["",     "--missingtp",                 "missingtp",  "store",       "string", "exit",                                     None,        "action to take when missing a tpfile: [exit|ignore|denyall|deny]"],
             ["",     "--requiretags",               "tags",       "store",       "string", None,                                       None,        "require tags when installing packages"],
             ["",     "--tagprefrules",              "tagprefrules", "store",     "string", None,                                       None,        "rules on how tags should be preferred"]]
    includes=[]
"""

import sys
import arizonaxml
import arizonaconfig
import arizonacrypt
import storkusername
import fnmatch
import os
import arizonatransfer
import arizonageneral
import arizonareport
import storkpackagelist

# exception generated when a tp error occurs
TPFileError = "tpfileerror"

FILE_EXTENSION = ".tpfile"

# Trusted package entry dictionary entries:
#    kind            either 'FILE' for file entries, or 'USER' for user entries
#    pattern         pattern to match
#    hash            hash to match, for file entries
#    tpfilename      for USER entries, the name of the trusted packages file to read
#    action          'allow', 'deny', or 'any'
#    order-by        'default' or 'timestamp'  
#    timestamp       as set by storkutil
#    number          ordinal number of entry (0, 1, 2, ...)
#    parent-number   ordinal number of parent, used as primary sort key
#    filters         list of pattern filters from enclosing USER entries
#    tags            list of tags that are applied to the package
#    mantags         list of mandatory tags (that the user must specify)
#    requiretags     for USER entries, a list of tags that must be present in the FILE entries

class __TrustedPackagesApplication(arizonaxml.XMLApplication):
   """
   <Purpose> 
      This class parses the trustedpackages file.

   TODO finish comment         
   """
   def __init__(self,keyname,parents):
      """
      <Purpose>
         (Comment retained from John's code -- likely retained from
         example)

         Do this the old way (instead of using super) because xmlproc is
         written using old-style classes that don't work with super.

      TODO finish comment
      """
      arizonaxml.XMLApplication.__init__(self)

      # Dictionary of tp info
      arizonaxml.CreateAttr(self, 'tp_dict', {})

      # Current user
      arizonaxml.CreateAttr(self, 'user', keyname)

      # Parent list, for cycle detection. It contains the names of all tpfiles
      # that are parents of this tpfile. It is considered an error to recurse
      # from this tpfile to one that is already in the list.
      arizonaxml.CreateAttr(self, 'parent_list', parents)

   def include_tpfile(self, username, publickey):
      """
      <Purpose>
         TODO fix comment
      """

      publickey_string = publickey.string
      publickey_string_old = arizonacrypt.publickey_sl_to_fnstring_compat(publickey.sl)
      publickey_hash = publickey.hash
      longname = username + "." + publickey_string

      # If we're missing this user's trusted packages file parse it
      if not self.tp_dict.has_key(longname):
         new_parents = self.parent_list[:]
         new_parents.append(self.user)

         # Get the name of the new file
         possible_tpfilenames = []
         possible_tpfilenames.append(username + "." + publickey_hash + FILE_EXTENSION)
         possible_tpfilenames.append(username + "." + publickey_string_old + FILE_EXTENSION)

         # SMB: choose between long and short key versions based on date
         (tpfilename, tp_repo) = storkpackagelist.find_file_list("tpfiles", possible_tpfilenames, None, publickey_string)

         if not tpfilename:
            raise TPFileError, "missing"

         # Parse the new file
         self.tp_dict.update(
             TrustedPackagesFileParse(arizonaconfig.get_option("tpdtd"),
             tpfilename,
             tp_repo,
             publickey_string,
             longname,
             new_parents))

   def handle_start_tag(self, tag, attrs):
      """
      <Purpose>
         TODO fix comment
      """
      #line = self.loc.get_line()
      #file = self.loc.get_current_sysid()

      if tag == "TRUSTEDPACKAGES":
         # Make an entry for the username.publickey in the dict
         self.tp_dict[self.user] = []

      elif tag == "FILE":
         # Add the file action to the list...
         tpentry = {}
         tpentry['kind'] = "FILE"
         tpentry['pattern'] = attrs.get("PATTERN")
         tpentry['hash'] = attrs.get("HASH")
         tpentry['action'] = attrs.get("ACTION", "unspecified").lower().strip()
         tpentry['timestamp'] = attrs.get("TIMESTAMP")

         # initialze the tag lists to empty
         tpentry['tags'] = []
         tpentry['mantags'] = []

         # the tags are a comma-seperated list.
         tags = attrs.get("TAGS", "").lower().strip().split(",")
         for tag in tags:
            # if a tag starts with a "+", then it's a mandatory tag
            if tag[:1] == '+':
               tpentry['mantags'].append(tag[1:])
               tpentry['tags'].append(tag[1:])
            else:
               tpentry['tags'].append(tag)

         self.tp_dict[self.user].append(tpentry)

      elif tag == "USER":
         # We will use username.publickey as our reference, so fetch it...
         username = attrs.get("USERNAME");
         publickey_string_raw = attrs.get("PUBLICKEY");
         # publickey_string may either be an old mangled key string or a new
         # valid key string, so get versions of it such that we know what they are
         publickey_sl = arizonacrypt.fnstring_to_publickey_sl(publickey_string_raw)
         publickey = arizonacrypt.PublicKey(sl=publickey_sl)

         # when old code that only supports short keys (and always mangles keys) adds a public key
         # for a long key user, it would have mangled even long keys. mangled long keys normally aren't
         # detected by fnstring_to_publickey_sl's attempts at transparent backwards compatibility by
         # detecting keys that should be unmangled by their length and unmangling them.
         # to get around this, if we find the key we got back from fnstring_to_publickey_sl
         # is invalid, try to get it again but this time forcibly unmangling. forcibly unmangling
         # means that it will be unmangled despite the length of the key.
         if not publickey.is_valid():
             publickey_sl = arizonacrypt.fnstring_to_publickey_sl(publickey_string_raw, force_unmangling=True)
             publickey = arizonacrypt.PublicKey(sl=publickey_sl)
             if not publickey.is_valid():
                 # jsamuel - would be good to display the name of the tpfile, but I can't see right now
                 # where that is available
                 raise ValueError, "When parsing tpfile, encountered invalid USER key: " + str(publickey_string_raw)

         publickey_string = publickey.string
         publickey_string_old = arizonacrypt.publickey_sl_to_fnstring_compat(publickey.sl)
         publickey_hash = publickey.hash
         longname = username + "." + publickey_string

         if longname in self.parent_list:
            # cycle detection -- print out an error messages
            # only print the part of the filenames up to the "."
            arizonareport.send_out(1, "  WARNING: cycle detected in tpfiles (" +
                                      self.user.split(".")[0] +
                                      " references " +
                                      longname.split(".")[0] +
                                      ")" )
         else:
            # Add the user action to the list...
            tpentry = {}
            tpentry['kind'] = "USER"
            tpentry['pattern'] = attrs.get("PATTERN")
            tpentry['tpfilename'] = longname
            tpentry['action'] = attrs.get("ACTION", "unspecified").lower().strip()
            tpentry['order-by'] = attrs.get("ORDER-BY", "default").lower().strip()

            requiretags = attrs.get("REQUIRETAGS", "").lower().strip().split(",")
            requiretags = [tag for tag in requiretags if tag != '']
            tpentry['requiretags'] = requiretags

            tpentry['provides'] = attrs.get("PROVIDES")

            try:
               self.include_tpfile(username, publickey)

            except TPFileError, errMsg:
               arizonareport.send_error(0, "Failed to include trusted package file " +
                                              "user: " + username + ", keyhash: " + publickey_hash +
                                              ", error: " + errMsg)

               misstp = arizonaconfig.get_option("missingtp")
               if misstp == "ignore":
                  arizonareport.send_error(1, "Ignoring missing tpfile user: " + username)
               elif misstp == "exit":
                  arizonareport.send_error(0, "Halting due to missing tpfile user: " + username)
                  sys.exit(1)
               elif (misstp == "deny") and (tpentry['action'] == "allow"):
                  # 'deny' differs from 'denyall' in the respect that if the
                  # original rule is an 'allow', then deny turns it into a
                  # no-op, so we can just ignore the rule
                  tpentry = None
               elif (misstp == "deny") or (misstp == "denyall"):
                  # change the rule into a file deny rule
                  tpentry['kind'] = "FILE"
                  tpentry['action'] = "deny"
                  tpentry['tags'] = []
                  tpentry['mantags'] = []

            # add the rule to the current dictionary. If all went well, then
            # this is the USER rule we built above. If something went wong,
            # then it turned into a FILE:DENY rule.
            if tpentry:
               self.tp_dict[self.user].append(tpentry)

      else:
         # Shouldn't happen if DTD is correct
         raise arizonaxml.XMLError, "invalid element: " + tag





   def handle_end_tag(self, tag):
      """
      <Purpose>
         TODO fix comment
      """
      if tag == "TRUSTEDPACKAGES" or tag == "FILE" or tag == "USER":
         return
      else:
         # Shouldn't happen if DTD is correct
         raise arizonaxml.XMLError, "invalid closing element: " + tag





def TrustedPackagesFileParse(dtd, filename, repo_dict, publickey_string, keyname, parents):
   """
   <Purpose>
      Creates the parser for the trustedpackages file and parses it.
      Returns a dictionary of group members.

   <Arguments>
      dtd:
         XML dtd to use when parsing

      filename:
         filename of tpfile, including path and extension.

      repo_dict:
         repository whre filename came from; used to print message to client

      publickey_string:
         public key used to verify signature of tpfile named by filename.

      keyname:
         the name of the key where that this should be added under in the
         returned dict.

      parents:
         a list build up of the keynames of the tpfiles that are parents of
         this tpfile. used for cycle detection.

   <Returns>
      dictionary containing trusted packages entries.
   """
   if repo_dict:
      # if we know which repo the file came from, then tell the user.
      arizonareport.send_out(3, "Parsing Trusted Packages File: [" +
                                repo_dict['name'] + "] " + filename)
   else:
      arizonareport.send_out(3, "Parsing Trusted Packages File: " + filename)

   publickey_sl = arizonacrypt.fnstring_to_publickey_sl(publickey_string)
   temp_publickey_fn = arizonacrypt.sl_to_fn(publickey_sl)
   try:
      try:
         if arizonacrypt.XML_timestamp_signedfile_with_publickey_fn(filename, temp_publickey_fn):
            temp_contents = arizonacrypt.XML_retrieve_originalfile_from_signedfile(filename)
      except TypeError, e:
         arizonareport.send_error(0, str(e))
         raise TPFileError, "verification error"

   finally:
      os.remove(temp_publickey_fn)

   try:
      app = __TrustedPackagesApplication(keyname, parents)
      app = arizonaxml.XMLParse(app, dtd, temp_contents)
      return app.tp_dict
   finally:
      os.remove(temp_contents)





def init():
   """
   <Purpose>
      This function retrieves trustedpackages information from remote
      repositories.

   <Arguments>
      None (uses command line options instead)

   <Exceptions>
      None

   <Side Effects>
      Updates trustedpackages files from remote repositories

   <Returns>
      None
   """
   
   return 

   """ SMBAKER 2/28/2007
      storkpackagelist.py will be responsible for dealing with repositories. 
      we will assume storkpackagelist.init() 
   """

   if not storkpackagelist.glo_initialized:
      # the right thing to do may be to call storkpackagelist.init, but for now
      # lets just assume we have a semantic error and the code needs fixing 
      arizonareport.send_error(0, 
          "ERROR: storktrustedpackageparse.init called before storkpackagelist.init")
      sys.exit(1)    





def satisfies_tags(tpentry, tag_list):
   """
   <Purpose>
      Checks to see if a tpentry contains tags.

   <Arguments>
      tag_list:
         A list of tags to check for

   <Returns>
      True if tpenty contains all tags in tag_list. 
      False otherwise. 
   """
   tp_tags = tpentry['tags']
   for tag in tag_list:
      if not tag in tp_tags:
         return False
   return True



# global line number used when flattening the trusted packages DAG.
flatten_line_number = 0

def flatten(fn, parent_line_number, orderby, action, parents, filters, provides, requiretags):
   """
   <Purpose>
      Convert the trusted packages file from a DAG to a list.

   <Arguments>
      fn - filename key used to get entries from trustedpackages_parsing_dict
      parent_line_number - the line number of the USER entry that is the parent
         to these FILE entries.
      orderby - method to order these entries by (default, timestamp, ...)
      action - filters what type of entries will be included. 'any' means to
         include all entries, 'allow' will only include allow entries, and
         'deny' will only include deny entries.
      parents - a list of parent filenames, used to detect and avoid cycles
      filters - a list of filter strings from the USER entries that encompass
         these FILE entries

   <Globals>
      flatten_line_number - each trusted package entry is assigned a unique
         line number that starts out at zero. It is unique across all trusted
         packages files.

   <Returns>
      A list of trusted package dictionaries
   """
   global trustedpackages_parsing_dict
   global flatten_line_number

   # print "flatten("+fn+", "+str(parent_line_number)+", "+str(orderby)+", "+ \
   #                str(action)+", "+str(parents)+", "+str(filters)+", "+ \
   #               str(requiretags)+ ")"

   # a cycle would put us in an endless loop....
   if fn in parents:
      # Note: The parse code already detects cycles; the check here is redundant
      arizonareport.send_out(3, "  cycle detected in tpfiles")
      return []

   # if the file does not exist then return an empty list. An appropriate
   # error message should have been issued by the parser.
   if not fn in trustedpackages_parsing_dict:
      return []

   # start out with a list that is empty
   packlist = []

   for tpentry in trustedpackages_parsing_dict[fn]:
      flatten_line_number = flatten_line_number + 1

      # deal with the provides= list, by intersecting the provides= list for
      # this item with the provides= list from the parent
      tp_provides = tpentry.get('provides', None)
      if (not tp_provides) or (tp_provides == "*"):
         # blank of "*" indicates accept anything
         newprovides = provides
      else:
         if provides:
            # if the parent had a list of allowable provides, then intersect
            # the child with the parent
            newprovides = arizonageneral.intersect(provides, tp_provides.split(","))
            if not newprovides:
               # the intersection created an empty set. Since we treat the
               # empty set as allow-everything, change it to a special marker.
               newprovides = ["None"]
         else:
            newprovides = tp_provides.split(",")

      # 'FILE' entries specify trusted packages
      if tpentry['kind'] == "FILE":
         if not satisfies_tags(tpentry, requiretags):
            # some USER entry that is the parent of this FILE entry specified
            # tags that we don't have, so drop this entry.
            pass
         elif (action != "any") and (action != tpentry['action']):
            # the action in the tpentry doesn't match the kind of actions that
            # we want to include, so drop it
            pass
         else:
            # make a copy, because we could insert the same entry more than
            # once into the list.
            tpentry = tpentry.copy()
            tpentry['parent-number'] = parent_line_number
            tpentry['number'] = flatten_line_number
            tpentry['order-by'] = orderby
            tpentry['filters'] = filters
            tpentry['provides_filters'] = newprovides
            packlist.append(tpentry)

      # 'USER' entries specify trusted packages files to read
      elif tpentry['kind'] == "USER":
          this_orderby = tpentry['order-by']
          newpacklist = []

          # add ourself to the parents list when recursing to detect cycles
          newparents = parents[:]
          newparents.append(fn)

          # add our pattern to the list of filters so we can pass it to the
          # recursive call.
          tp_pattern = tpentry.get('pattern', None)
          if (not tp_pattern) or (tp_pattern == "*"):
             # "*" matches everything, so just leave it out
             newfilters = filters
          else:
             newfilters = filters[:]
             newfilters.append(tp_pattern)

          # add our requiretags to the list of requiretags from our parents
          if tpentry['requiretags']:
             newrequiretags = requiretags[:]
             newrequiretags.extend(tpentry['requiretags'])
          else:
             newrequiretags = requiretags

          if this_orderby == "default":
             newpacklist = flatten(tpentry['tpfilename'],
                                   flatten_line_number,
                                   this_orderby,
                                   tpentry['action'],
                                   newparents,
                                   newfilters,
                                   newprovides,
                                   newrequiretags)
          elif this_orderby == "timestamp":
             # for timestamp ordering, use our parent_line_number when
             # recursing. This effectively groups the entires that will
             # be generated by the recursive call together, so we can sort
             # them appropriately.
             newpacklist = flatten(tpentry['tpfilename'],
                                   parent_line_number,
                                   this_orderby,
                                   tpentry['action'],
                                   newparents,
                                   newfilters,
                                   newprovides,
                                   newrequiretags)
                 
          if newpacklist:
             packlist.extend(newpacklist)
                 
   return packlist



   
glo_prefer_rules = None

def compute_prefer_rules():
   """
   <Purpose>
      Create the tag preference rules from the --tagprefrules configuration
      variable.

      Tag preference rules are specified as a string "tag1<tag2", which implies
      that tag1 have higher preference (nearer the start of the tplist) than 
      tag2. The only operator that is allowed is "<".

      Multiple tags can be specified, for example "tag1<tag2<tag3"

      Multiple rules can be specified, seperated by commas. For example, 
      "tag1<tag2,tag3<tag4". When multiple rules are specified, the first rule
      has higher precedence over the lower rule.

      Packages that do not match any rules (i.e. contain no tags listed in a 
      rule) will always be assigned higher precedence than tags that do match
      the rules.
   """
   global glo_prefer_rules

   # if we've already done it, then don't do it again
   if glo_prefer_rules:
      return

   glo_prefer_rules = []

   tag_pref_str = arizonaconfig.get_option("tagprefrules")
   if not tag_pref_str:
      return
   
   # split the comma delimited list
   tag_pref_list = tag_pref_str.lower().strip().split(",")

   # JEREMY : go through the list and replace any %ARCH% tag with the
   #          firstline from /etc/issue
   arch = ""
   try:
       issuefile = open("/etc/issue")
       arch = issuefile.readline().replace("\n","")
       
       if "release 4" in arch:
           arch="planetlabv4"
       elif "release 2" in arch:
           arch="planetlabv3"

       issuefile.close()
   except IOError:
       # means file doesn't exist or permissions are screwed up
       arch = "Unknown" 

   # Go through list and replace any %arch% tags
   for num in range( len(tag_pref_list) ):
       tag_pref_list[num] = tag_pref_list[num].replace("%arch%", arch)

   # output a debug message on the "veryverbose" level
   arizonareport.send_out(3, "tag preferences: "+str(tag_pref_list))

   
   # get rid of anything that is blank
   tag_pref_list = [rule for rule in tag_pref_list if rule != '']

   for pref in tag_pref_list:
       # split the rule by the operator ("<")
       tags = pref.split("<")

       # get rid of leading or trailing space
       tags = [tag.strip() for tag in tags]

       glo_prefer_rules.append(tags)

       



def tpcompare(a, b):
   """
   <Purpose>
      Compare two trusted package entries for sorting purposes

   <Arguments>
      a - trusted packages entry
      b - trusted packages entry

   <Returns>
      -1 if a<b
      0 if a==b
      1 if a>b
   """
   a_parent = a['parent-number']
   b_parent = b['parent-number']
   a_orderby = a['order-by']
   b_orderby = b['order-by']
   global glo_prefer_rules

   # a tag preference rules is a list of tags that should be ordered. 
   # at this point, rules are ordered lists of tags [see compute_prefer_rules
   #    for a description of how config params are converted to lists]
   # for example, the rule
   #     PlanetLabV3, PlanetLabV4   ... implies that V3 packages should be 
   #                                    ranked ahead of V4 packages
   #     Stable, Testing            ... rank stable packages ahead of testing
   # packages that do not match any tags in the rules will get pushed ahead
   # of packages that do match tags
   for prefer_rule in glo_prefer_rules:
      # an index to use for packages that don't match the rules. We have two
      # choices: -1 would put unmatched packages first. Something large (1000)
      # will put unmatched packages last. 
      nomatch_index = 1000
      
      # start by assuming the packages do not have a tag in the rule
      a_index = -1
      b_index = -1

      # search the tags and find the index 
      for (i,tag) in enumerate(prefer_rule):
         if (a_index<0) and (tag in a['tags']):
            a_index = i
         if (b_index<0) and (tag in b['tags']):
            b_index = i

      # if we didn't match a tag, then set the index to the value we chose
      # for unmatched packages
      if a_index == -1:
         a_index = nomatch_index
      else:
         # we'll use this bit of information to print a warning message later
         a['matched-tag-pref-rule'] = True

      # do the same for the other package
      if b_index == -1:
         b_index = nomatch_index
      else:
         b['matched-tag-pref-rule'] = True

      # if one package should be ranked before the other, then that is our
      # sort order.
      if (a_index != b_index):
         return a_index - b_index

   # the parent number is always the primary key
   # parents are sorted from least to greatest
   if a_parent != b_parent:
      return a_parent - b_parent

   # if the items are to be ordered by timestamp, then lets compare the
   # timestamps
   if a_orderby == "timestamp" and b_orderby == "timestamp":
      # [beware that the XML parser sets a['timestamp'] to None instead of 
      # setting the default value if the timestamp attribute is not set.]
      
      a_timestamp = a.get("timestamp", 0)
      b_timestamp = b.get("timestamp", 0)

      # timestamps will be sorted from greatest to least
      if a_timestamp < b_timestamp:
         return 1
      if a_timestamp > b_timestamp:
         return -1

   # if we aren't ordered by parent or by timestamp, the we must be ordered
   # by number.
   # numbers are sorted from least to greatest
   return int(a['number'] - b['number'])

   
   


def rpcompare(a, b):
   """
   <Purpose>
      Compare two ranked packages for sorting purposes

   <Arguments>
      a - ranked package tuple (file, hash, name, tpentry)
      b - trusted packages entry (file, hash, name, tpentry)

   <Returns>
      -1 if a<b
      0 if a==b
      1 if a>b
   """
   return tpcompare(a[3], b[3])



   
    
# Set this to be uninitialized
trustedpackages_parsing_dict = None
trustedpackages_list = None
    
def TrustedPackagesOrder():
   """
   <Purpose>
      Parse the trusted packages file, flatten them from a DAG to a list, and
      finally sort them.

   <Arguments>
      None

   <Side Effects>
      The globals trustedpackages_parsing_dict and trustedpackages_list are
      filled in.

   <Returns>
      None. 
   """
   global trustedpackages_parsing_dict 
   global trustedpackages_list
   
   arizonareport.send_out(3, "Initializing trustedpackages files...")

   # compute tag preference rules. They'll be used when sorting later on
   compute_prefer_rules()

   (tpfilename, tp_repo, tp_keytuple) = storkpackagelist.find_file_kind("tpfiles", "tpfile")
   if not tpfilename:
      arizonareport.send_error(0, "Failed to locate trusted package file")
      sys.exit(1)

   # build up a dictionary of the entries of the tpfiles
   trustedpackages_parsing_dict = \
      TrustedPackagesFileParse(arizonaconfig.get_option("tpdtd"),
                               tpfilename,
                               tp_repo,
                               arizonacrypt.PublicKey(sl=tp_keytuple[2]).string,  # publickeystring
                               tp_keytuple[4],  # config_prefix
                               [])

   arizonareport.send_out(3, "Flattening trustedpackages files...")

   # flatten the DAG into a list
   flatten_line_number = 0
   trustedpackages_list = flatten(tp_keytuple[4], 0, "default", "any", [], [], [], [])




   
def tpmatch(tpentry, pack, tags=None, ignore_hash=False, ignore_mantags=False):
   """
   <Purpose>
      See if a package matches a tpentry

   <Arguments>
      tpentry - a trusted packages dictionary entry
      pack - a package tuple("file", "hash", package_db_entry)
      tags - list of tags that the package must have

   <Returns>
      True if tpentry matches pack, False if it does not
   """
   # check the pattern
   if not fnmatch.fnmatch(pack[0], tpentry['pattern']):
      # this message would overwhelm the user on --ultraverbose
      #arizonareport.send_out(4, "tp reject: " + pack[0] + \
      #                      " didn't match pattern " + tpentry['pattern'])
      return False

   # check the hash
   if not ignore_hash:
      hash = tpentry.get("hash", None)
      if hash and (not fnmatch.fnmatch(pack[1], hash)):
         arizonareport.send_out(4, "tp reject: " + pack[0] + \
                                 " didn't match hash " + hash)
         return False

   # check each one of the filters
   for filter in tpentry['filters']:
      if not fnmatch.fnmatch(pack[0], filter):
          arizonareport.send_out(4, "tp reject: " + pack[0] + \
                                 " didn't match filter " + filter)
          return False


   if pack[2]:
      pack_provides = pack[2].get("provides", None)
      tp_provides = tpentry.get("provides_filters", None)

      if pack_provides and tp_provides:
         for provide in pack_provides:
            provide = provide.split("=")[0].strip()
            found = False
            for filter in tp_provides:
               if fnmatch.fnmatch(provide, filter):
                  found = True
            if not found:
               arizonareport.send_out(4, "tp reject: " + pack[0] + \
                                         " package provide '" + provide + \
                                         "' did not match tpentry provides")
               return False

   # check to see if package contains tags the user wants
   if tags:
      if (tpentry['action'] == 'deny') and (not tepentry['tags']):
         # if a deny rule does not contain any tags, then we apply it regardless
         # of what tags the user asks for.
         pass
      else:
         for tag in tags:
            if not tag in tpentry['tags']:
               arizonareport.send_out(4, "tp reject: " + pack[0] + \
                                      " does not contain tag: '" + tag + "'")
               return False

   # check to see if user specified tags the package wants
   if not ignore_mantags:
      for tag in tpentry['mantags']:
         if (not tags) or (not tag in tags):
             arizonareport.send_out(4, "tp reject: " + pack[0] + \
                                    " requires mandatory tag: '" + tag + "'")
             return False

   arizonareport.send_out(4, "tp match: " + pack[0] + " action: " + tpentry['action'])

   return True



   

def TrustedPackagesDump(packagelist):
   """
   <Purpose>
      Dump the trusted packages list to stdout, for debugging purposes

   <Arguments>
      packagelist:
         optional - a list of packages. If None or empty, then dump all trusted
         packages entries
   """
   # If unitialized
   if trustedpackages_list == None:
      TrustedPackagesOrder()

   # Sort the packages so that the user can see the order of his rules
   # Note that this might get deny rules out of order
   sorted_list = trustedpackages_list[:]
   sorted_list.sort(tpcompare)

   # process the required tags from arizonaconfig
   tag_list = []
   cmdline_tags = arizonaconfig.get_option("tags")
   if cmdline_tags:
      tag_list = cmdline_tags.lower().strip().split(",")
      # remove any empty-string tags
      tag_list = [tag for tag in tag_list if tag != '']

   for tpentry in sorted_list:
      matched = False
      if packagelist:
         # if the user specified a list of packagenames, then restrict the
         # tpdump to that list
         for pack in packagelist:
            if tpmatch(tpentry, (pack, "nohash", None), tag_list, True):
               matched = True
      else:
         # see if the user restricted the tpdump with --requiretags. If so,
         # only list packages that match the tags
         matched = True
         for tag in tag_list:
             if not tag in tpentry['tags']:
                 matched = False

      if matched:
         print str(tpentry)





def rank_packages(package_list, tags="", ignore_mantags=False):
   """
   <Purpose>
      Compare the packages to the trusted packages list and see if they are
      allowed, denied, or unspecified.

   <Arguments>
      package_list:
              This is a list of 3-tuples.   Each tuple has a ("file",
              "hash", package) pair.   The file is the name of the
              package that the pattern in the trustedpackages file
              should match.   The hash is the secure hash of the
              package metadata.   The package is an identifier that the
              caller wants returned to identify the package (commonly
              the database entry for the package).
      tags:
              A list of tags that must be present in the packages

   <Side Effects>
      trustedpackages_parsing_dicts and trustedpackages_list created

   <Returns>
      A tuple containing three lists.  Each list is comprised of the tuple
      elements that were passed in. The tpentry that matched the package is
      appended to the tuple, so that 4-tuples are returned in the lists.
      The first list is the packages that
      are allowed by the trustedpackages file.  The second list is the
      packages that are denied.  The third list is packages that are
      unspecified. The lists are sorted such that higher-priority packages
      appear higher in the list and lesser-priority packages near the
      bottom of the list.
   """
   # If unitialized
   if trustedpackages_list == None:
      TrustedPackagesOrder()

   allow_list = []
   deny_list = []
   unspecified_list = []

   # start out with a blank list of tags
   tag_list = []

   # process the tags listed in the arguments to this func. These tags came
   # from the packagename#tags syntax.
   if tags:
      tags = tags.lower().strip().split(",")
      tag_list.extend(tags)

   # process the required tags from arizonaconfig (--requiretags option)
   cmdline_tags = arizonaconfig.get_option("tags")
   if cmdline_tags:
      cmdline_tags = cmdline_tags.lower().strip().split(",")
      tag_list.extend(cmdline_tags)

   # remove any empty-string tags
   tag_list = [tag for tag in tag_list if tag != '']

   # for each rule in the tp list, see if it matches any of our packages. If a
   # package matches a rule, then we have decided that package so we can add
   # it to the particular result list (allow, deny) and stop looking for that
   # package.

   for tpentry in trustedpackages_list:
      for pack in package_list[:]:
         if tpmatch(tpentry, pack, tag_list, False, ignore_mantags):
            # match-first-rule semantics. Since the package matched the rule,
            # remove the package from the list, so it will not match
            # subsequent rules
            package_list.remove(pack)

            action = tpentry['action']
            # print str(action)+": "+str(pack)+" ^ "+str(tpentry)
            if action == "allow":
               allow_list.append(pack + (tpentry,))
            elif action == "deny":
               deny_list.append(pack + (tpentry,))

   # anything that wasn't allowed or denied must have been unspecified
   unspecified_list = package_list

   # sort the list of allowed packages by timestamp, tag, etc
   if allow_list:
      orig_first_package_tprule = allow_list[0][3]
      allow_list.sort(rpcompare)
      new_first_package_tprule = allow_list[0][3]

      # if some package that didn't match a tag preference rule was at the top
      # of the list, and now a package that does match a tag preference rule is
      # at the top of the list, then the user may be confused, so print a
      # warning
      
      if not orig_first_package_tprule.get('matched-tag-pref-rule', False) and \
         new_first_package_tprule.get('matched-tag-pref-rule', False):
         arizonareport.send_out(0, "WARNING: Some packages in your tpfile have been reordered due to tag preference rules")

   return (allow_list, deny_list, unspecified_list)


