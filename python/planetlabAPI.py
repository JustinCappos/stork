# /usr/bin/env python

"""
<Program Name>
   planetlabAPI.py

<Started>   
   September 16, 2007

<Author>
   Justin Cappos

<Purpose>
   Wraps all of the PLC authentication calls.   Hopefully I can make this less
   of a mess than the old code for this.

   Detailed information about args, the API itself, etc. is at: 
   http://www.planet-lab.org/doc/plc_api and 
   http://www.planet-lab.org/doc/plcapitut
"""



import arizonaconfig
import xmlrpclib

# Only need this for exception handling
import socket

#           [option, long option,      variable,  action,        data,  default, metavar, description]
"""arizonaconfig
   options=[["",  "--PLauthtype",  "PLauthtype", "store",    "string","https://", None, "The protocol used for auth (default https://)"],
            ["",  "--PLauthsite",  "PLauthsite", "store",    "string","www.planet-lab.org", None, "The authentication web site (default www.planet-lab.org)"],
            ["",  "--PLauthport",  "PLauthport", "store",   "int", 443, None, "The port to use for authentication (default 443)"],
            ["",  "--PLauthpath",  "PLauthpath", "store",    "string", "PLCAPI", None, "The path to use for authentication (default PLCAPI)"],
            ["",  "--PLusername", "PLusername", "store",     "string",     None,    None, "The username for PLC actions"],
            ["",  "--PLpassword", "PLpassword", "store",     "string",     None,    None, "The password for PLC actions"]]
   includes=[] 
"""




PLlogindata = {}


def PlanetLablogout():
   """
   <Purpose>
      Unsets the global PLlogindata for PLC.   

   <Arguments>   
      None

   <Exceptions>
      None

   <Side Effects>
      Unsets the PLlogindata.

   <Returns>
      None
   """
   global PLlogindata
   PLlogindata = {}
   




   




def PlanetLablogin(username = None, password = None, authtype = None, authsite = None, authport = None, authpath = None):
   """
   <Purpose>
      Try to login to a PLC.   

   <Arguments>   
      username:   A string with the username to try 
      password:   A string with the password to try
      authtype:   The first part of the URL; the type of protocol
      authsite:   The DNS name (or IP) where the data should be sent
      authport:   The TCP port where data should be sent
      authpath:   The path on the server (i.e. the path in the URL)

   <Exceptions>
      ValueError: This is thrown for most types of problems (bad username, bad
                  password, etc.).   
      I don't intentially try to pass other exceptions through.   I'm not sure
      what xmlrpclib will raise.

   <Side Effects>
      Sets PLlogindata.   This is implicitly used throughout.

   <Returns>
      None (Exception thrown on failure)
   """

   global PLlogindata

   if username == None:
      username = arizonaconfig.get_option("PLusername") 
      if not username:
         raise ValueError, "Must set PlanetLab username (PLusername)"

   if password == None:
      password = arizonaconfig.get_option("PLpassword")
      if not password:
         raise ValueError, "Must set PlanetLab password (PLpassword)"

   if password == "prompt":
      password = raw_input("password:")
      if not password:
         raise ValueError, "Must set PlanetLab password (PLpassword)"

   if authtype == None:
      authtype = arizonaconfig.get_option("PLauthtype")
   if authsite == None:
      authsite = arizonaconfig.get_option("PLauthsite") 
   if authport == None:
      authport = arizonaconfig.get_option("PLauthport") 
   if authpath == None:
      authpath = arizonaconfig.get_option("PLauthpath")

   # Build the authorization dict
   PLlogindata['auth'] = { 'Username': username, 'AuthMethod': "password", 
              'AuthString': password, 'Role': 'user'}

   myurl = authtype+authsite+":"+str(authport)+"/"+authpath+"/"
   
   try:
     PLlogindata['server'] = xmlrpclib.Server(myurl, verbose = 0, allow_none=True)
   except IOError, errormessage:
     # perhaps the protocol is wrong?
     raise ValueError, errormessage


   try:
     PLlogindata['server'].AdmAuthCheck(PLlogindata['auth'])
   except xmlrpclib.Fault, errormessage:
     errormessagestring = str(errormessage)
     if errormessagestring.startswith("<Fault 103: ':") and errormessagestring.endswith("'>"):
        raise ValueError, errormessagestring[14:-2]
     else:
        raise
   
   except socket.gaierror, errormessage:
     # if I can't resolve the name of the website (for example)
     errormessagestring = str(errormessage)
     if errormessagestring.startswith("(7, '") and errormessagestring.endswith("')"):
        raise ValueError, errormessagestring[5:-2]
     elif errormessagestring.startswith("(-2, '") and errormessagestring.endswith("')"):
        raise ValueError, errormessagestring[6:-2]
     else:
        raise

   except socket.error, errormessage:
     # Connection error, etc.
     errormessagestring = str(errormessage)
     if errormessagestring.startswith("(61, '") and errormessagestring.endswith("')"):
        raise ValueError, errormessagestring[6:-2]
     elif errormessagestring.startswith("(113, '") and errormessagestring.endswith("')"):
        raise ValueError, errormessagestring[7:-2]
     elif errormessagestring.startswith("(110, '") and errormessagestring.endswith("')"):
        raise ValueError, errormessagestring[7:-2]
     else:
        raise


   except xmlrpclib.ProtocolError, errormessage:
     # bad path
     raise ValueError, errormessage




def doplccall(commandname,*args):
   """
   <Purpose>
      Perform a PLC call with *args and return the return data.   
      THIS FUNCTION USES EVAL IN A NON-SAFE WAY (assuming malicious input)!!!

   <Arguments>   
      *args:   The arguments for the call
      

   <Exceptions>
      ValueError: I try to throw this for most types of problems (bad 
      PLlogindata, etc.).    I don't intentially try to pass other exceptions
      through.   I'm not sure what xmlrpclib will raise.

   <Side Effects>
      Contacts PLC and may change the site state.

   <Returns>
      Depends on the calling function
   """

   if not PLlogindata:
      raise ValueError, "Non-existant PLserver authentication (must log in first)"

   arglist = ["PLlogindata['auth']"] 
   for arg in args:
      arglist.append(repr(arg))
   
   try:
     retval = eval("PLlogindata['server']."+commandname+"(" + ",".join(arglist) + ")")
   except xmlrpclib.Fault, errormessage:
     errormessagestring = str(errormessage)
     if errormessagestring.startswith("<Fault 100: '") and errormessagestring.endswith("'>"):
        raise ValueError, errormessagestring[13:-2]
     elif errormessagestring.startswith("<Fault 102: '") and errormessagestring.endswith("'>"):
        raise ValueError, errormessagestring[13:-2]
     else:
        raise
   except xmlrpclib.ProtocolError, errormessage:
     errormessagestring = str(errormessage)
     # xmlrpclib.ProtocolError: <ProtocolError for www.planet-lab.org:443/PLCAPI/: 500 Internal Server Error>
     # I'll just raise this instead of trying to parse
     raise ValueError, errormessagestring
   except socket.error, errormessage:
     # socket.error: (110, 'Connection timed out')
     raise ValueError, "socket.error"+str(errormessage)

   return retval




def getUserData():
   """
   <Purpose>
      Perform a PLC call with *args and return the return data.
      THIS FUNCTION USES EVAL IN A NON-SAFE WAY (assuming malicious input)!!!

   <Arguments>
      *args:   The arguments for the call


   <Exceptions>
      ValueError: I try to throw this for most types of problems (bad
      PLlogindata, etc.).    I don't intentially try to pass other exceptions
      through.   I'm not sure what xmlrpclib will raise.

   <Side Effects>
      Contacts PLC and may change the site state.

   <Returns>
      Depends on the calling function
   """

   global PLlogindata

   if not PLlogindata:
      raise ValueError, "Non-existant PLserver authentication (must log in first)"

   try:
     retval = PLlogindata['server'].AdmGetPersons(PLlogindata['auth'], [PLlogindata['auth']['Username']], ['first_name', 'last_name'])
   except xmlrpclib.Fault, errormessage:
     errormessagestring = str(errormessage)
     if errormessagestring.startswith("<Fault 100: '") and errormessagestring.endswith("'>"):
        raise ValueError, errormessagestring[13:-2]
     elif errormessagestring.startswith("<Fault 102: '") and errormessagestring.endswith("'>"):
        raise ValueError, errormessagestring[13:-2]
     else:
        raise
   except xmlrpclib.ProtocolError, errormessage:
     errormessagestring = str(errormessage)
     # xmlrpclib.ProtocolError: <ProtocolError for www.planet-lab.org:443/PLCAPI/: 500 Internal Server Error>
     # I'll just raise this instead of trying to parse
     raise ValueError, errormessagestring
   except socket.error, errormessage:
     # socket.error: (110, 'Connection timed out')
     raise ValueError, "socket.error"+str(errormessagestring)

   return retval
