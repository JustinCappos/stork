#! /usr/bin/env python
"""
<Program Name>
   arizonaconfig.py

<Started>
   June 6, 2005

<Author>
   Programmed by Jeffry Johnston under the direction of Justin Cappos.

<Purpose>
   Configuration file, command-line, and run-time options manager.  Finds
   used source files in a tree to only include the necessary options.
"""

#---------------------------------------------------------------------
# Imports
#---------------------------------------------------------------------
import os
import sys
import glob
import optparse
import arizonageneral
import traceback

#---------------------------------------------------------------------
# Globals
#---------------------------------------------------------------------
# Storage for found modules during recursive search in __build_options()
# Although the list of modules could be passed and returned with each
# recursive call, storing it globally should be much faster.
found_modules = []

# A list of all the options found so far (during the recursive search).
# After the program (command line) options are parsed, a copy is made as
# program_options.  Then, it is further expanded to include all possible
# options (for successful parsing of the config file options).
found_options = []

# A dictionary containing all found program variables (from found
# arizonaconfig blocks in Python files), and their set values (from the
# command line program, config file, or the default value).
program_variables = None

# The version string passed in by init_options, or None.
version_string = None

# To store option parser for print_help()
glo_option_parser = None

glo_section = None

# List of parsed modules
parsed_modules = []

# Debugging mode (0 = off)
glo_debug = 0

# Config filename that was read or attempted to be read
glo_config_filename = None
glo_append_override_default = False

class SectionableOption (optparse.Option):
   ACTIONS = optparse.Option.ACTIONS + ("sectionstart", "sectionstop", )
   STORE_ACTIONS = optparse.Option.STORE_ACTIONS + ("sectionstart", )
   TYPED_ACTIONS = optparse.Option.TYPED_ACTIONS + ("sectionstart", )

   def take_action(self, action, dest, opt, value, values, parser):
      global glo_append_override_default

      # specified_options is a list of options that were specified by the
      # user/config file. i.e. it is options that are not defaults.
      specified_options = values.ensure_value("specified_options", [])

      if action == "sectionstart":
         setattr(values, "cursection", value)
         optparse.Option.take_action(self, "append", dest, opt, value, values, parser)
      elif action == "sectionstop":
         setattr(values, "cursection", None)
      elif action == "append" and glo_append_override_default:
         # when processing config files, we have this unusual semantics where
         # specifying and option that uses 'append' causes the default to be
         # dropped, rather than appending to the default.
         if not dest in specified_options:
             setattr(values, dest, [])
         optparse.Option.take_action(self, action, dest, opt, value, values, parser)
      else:
         if hasattr(values, "cursection"):
            section = getattr(values, "cursection")
            if section and dest:
               dest = section + "." + dest
         optparse.Option.take_action(self, action, dest, opt, value, values, parser)

      specified_options.append(dest)

def is_storable(x):
   return x == "store" or x == "append" or x == "sectionstart"

def is_append(x):
   return (x == "append") or (x == "sectionstart")

def init_options(module="*", path=".", alt_paths=[], usage=None, version=None, configfile_optvar=None, debug=0):
   """
   <Purpose>
      Returns all options for the specified module, including imported
      modules (recursively).  Looks for an options block in the following
      format:

      ""'arizonaconfig
         options=[
                  [option, long option, variable, action, data, default,
                   metavar, description],
                  ...
                 ]
         includes=[
                   "path/module"
                   ...
                  ]
      ""'

      The code within the triple quoted string will be loaded with exec,
      so it must consist of valid Python statements.  The first line must
      start with "arizonaconfig" (no quotes), for this function to
      recognize it as an arizonaconfig options block.

      Description of options list:
      option:
              Short option string, example: "-f".  If a short option is
              not desired, use "".
      long option:
              Long option string, example: "--file".  If a long option is
              not desired, use "".
      variable:
              Variable name for the option, will be used in the function
              get_option("variable").
      action:
              One of the following strings:
              "store"        Store this option's argument in 'variable'.
                             See 'data' and 'metavar'.
              "append"       Append this option's argument to the list
                             'variable'.  See 'data' and 'metavar'.
              "store_const"  Store the integer value 'data' in 'variable'.
                             The string 'metavar' must be None.
              "store_true"   Store True in 'variable'.  Both 'metavar' and
                             'data' must be None.
              "store_false"  Store False in 'variable'.  Both 'metavar'
                             and 'data' must be None.
      data:
              * If the action is "store" or "append", use one of the
                following strings:
                "string"       Take any string as the option.
                "int"          Accept an integer value as the option.
                "long"         As "int", but for a long integer.
                "float"        As "int", but for a float.
                "complex"      As "int", but for a complex number.
              * If the action is "store_const", specify the integer
                constant to store into 'variable' if the option is
                given.
              * Otherwise, use None.
      default:
              The default value to store if the option is not given.  If
              the action is "help", must be None.  If the action is
              "append" this must either be a list or None.
      metavar:
              * If the action is "store" or "append", specify an alternate
                variable name to show in --help, or None to use 'variable'
                for the metavar.
              * Otherwise, must be None.
      description:
              Helpful description of the option, for use in --help.
              Specify None to hide the option from the --help listing.

      Decription of includes list:
             See module in Arguments section for a description of this.
             If this string contains $MAIN, it will be replaced by the
             path where the main (starting module) existed on disk.  This
             is helpful to not have to hardcode an absolute path to a
             module, if it is always in the same place, relative to where
             the main module is.
             Note that init_options scans the module code for import
             statements and adds discovered modules automatically, so most
             modules do not need to be specified in this way.  These
             includes can be useful for dynamically importing any found
             modules in a certain directory.

   <Arguments>
      module:
             (default="*")
             Specifies the module in which to recursively find all valid
             program options.  This is usually just the filename of the
             module calling init_options.  It may contain a path to the
             module.  Include the .py filename extension if there is one.
             The standard *nix glob characters *, ?, and [ ] may be used
             to specify multiple modules at once.
      path:
             (default=".")
             Path to the module.
      alt_paths:
             (default=[])
             A list of alternate paths that will be searched if a module
             could not be found via the default path.  These paths must be
             absolute (must start with `/').
      usage:
             (default=None)
             Command-line usage string for module --help.  The default
             None will generate a generic usage statement.
      version:
             (default=None)
             The program version, as a string.  If None is given, the
             --version option will not be accepted on the command line, so
             no version information will be available to the user.
      configfile_optvar:
             (default=None)
             If None, no configuration file will be parsed.  Otherwise,
             should be a string containing the name of a configuration
             option variable (see "variable" in the Purpose section).
             The contents of the given variable will be examined to
             determine the configuration file filename.

             For example, consider the following example arizonaconfig
             option line:

             ["-c", "--configfile", "conffile", "store", "string",
              "/etc/myconfig.txt", "FILE",
              "Configuration file to use (default: /etc/myconfig.txt)"]

             The string to be passed for configfile_optvar is "conffile".
             The default config file read by arizonaconfig will be
             "/etc/myconfig.txt".  But, if the user specifies the -c or
             --configfile options, the configuration file they specified
             will be read instead.
      debug:
             (default=0)
             If set to 1, will print a debug listing for arizonaconfig.
             This listing will give the name of the file containing the
             arizonaconfig options block where the option was first found.

             If set to 2, will print an alternate debug listing, showing 
             the recursive steps taken to find the modules.
             
             If set to 3, shows output for both 1 and 2.

   <Exceptions>
      TypeError: options having a type other than expected.

   <Side Effects>
      Sets up (modifies) program_variables.

   <Returns>
      A list of non-option command line arguments that remained after
      option parsing.
   """
   # check params
   arizonageneral.check_type_simple(module, "module", str, "init_options")
   arizonageneral.check_type_simple(path, "path", str, "init_options")
   arizonageneral.check_type_stringlist(alt_paths, "alt_paths", "init_options")
   arizonageneral.check_type_simple(usage, "usage", str, "init_options", noneok=True)
   arizonageneral.check_type_simple(version, "version", str, "init_options", noneok=True)
   arizonageneral.check_type_simple(configfile_optvar, "configfile_optvar", str, "init_options", noneok=True)
   arizonageneral.check_type_simple(debug, "debug", int, "init_options")

   global program_variables
   global version_string
   global glo_option_parser                                                                                  
   global glo_debug
   global glo_section
   global glo_append_override_default

   # SMB: if the user (i.e. one of us developers) set a PYTHONPATH environment
   # variable, then make sure it is added to the alt_paths list
   pythonpath = os.environ.get("PYTHONPATH", None)
   if pythonpath:
      search_paths = pythonpath.split(":")
      for search_path in search_paths:
         if not search_path in alt_paths:
            alt_paths.append(search_path)

   # SMB: because arizonalib is now in a site-packages directory, ensure
   # that we can find the modules.
   for search_path in sys.path:
       if search_path.find("site-packages") >= 0:
           if not search_path in alt_paths:
               alt_paths.append(search_path)

   # clear any existing state
   reset()
   glo_debug = debug
   glo_section = None

   # build generic usage line, if needed
   if usage == None:
      usage = "usage: " + module + " [options]"

   # initialize options parsers
   if version == None:
      program_parser = OptionParser(usage=usage, option_class=SectionableOption)
   else:
      program_parser = OptionParser(usage=usage, version="%prog " + version, option_class=SectionableOption)
      version_string = version

   # display debugging output, if requested
   if glo_debug & 2:
      print "<Recursive module import listing for the program>"

   # build an options list for the program
   __build_options(path, alt_paths, module)

   # display debugging output, if requested
   if glo_debug & 2:
      print "-" * 70

   program_options = found_options[:]
   for option in program_options:
      __add_option(program_parser, option)

   # display debugging output, if requested
   if glo_debug & 1:
      __debug_output(program_options)

   # Store option parser for print_help()
   glo_option_parser = program_parser

   # process command line for program
   (program_variables, args) = program_parser.parse_args()

   # process config file options
   config_parser = OptionParser(option_class=SectionableOption)
   if configfile_optvar != None:
      # get the option variable name for the config file filename
      try:
         configfile = getattr(program_variables, configfile_optvar)
      except AttributeError:
         raise AttributeError, "Did not find variable '" + configfile_optvar + \
                               "' needed for the config file filename."
         sys.exit(1)

      # display debugging output, if requested
      if glo_debug & 2:
         print "<Recursive module import listing for all files in the current directory>"

      # get ALL options for the config file (not just the run module, this
      # will grab options for all files in the module's run directory

      # SMB: Set ignore_duplicates to True, to prevent needless error messages
      # when two modules use the same option (but both modules are not used by
      # the run module)

      __build_options(path, alt_paths, ignore_duplicates=True)
      for option in found_options:
         __add_option(config_parser, option)

      # if configfile option was given on the command line, parse the
      # specified config file, otherwise use the default config file
      # filename.
      if configfile == None:
         configfile = __default(configfile_optvar)

      glo_append_override_default = True

      # parse the config file and get any set options
      config_variables = __read_config_file(configfile, config_parser)

      # includes= is a special variable that specifies what addition config
      # files to read. If it is set, then expand it using glob and read all of
      # those config files
      if config_variables:
         includes = getattr(config_variables, "include", [])
         if includes:
            for include in includes:
               files = glob.glob(include)
               for file in files:
                 config_variables = __read_config_file(file, config_parser, config_variables)

      glo_append_override_default = False

   else:
      config_variables = None

   # display debugging output, if requested
   if glo_debug & 2:
      print "-" * 70

   # Merge config_variables into program_variables.
   # Situations:
   # 1) Option was specified on the command line, and is already included
   #    in program_variables at this point.  Result: Already included.
   # 2) Option was specified both on command line and config file, and is
   #    an append action.  Result: maintain previous setting and append
   #    newly found option to the end.
   # 3) Option was not specified on the command line, but was in the
   #    config file.  Result: use config file setting.
   # 4) Option was not specified on the command line or the config file,
   #    but is used by the program.  Result: use default value.

   if config_variables:
      # at this point, we have the config file variables in config_variables.
      # we need to re-parse the command line, so that command-line variables can
      # override the config file variables
      (program_variables, args) = config_parser.parse_args(None, config_variables)

   if glo_debug & 1:
      __debug_variable_output()

   # return program non-option args to caller
   return args





def get_option(variable, section = None):
   """
   <Purpose>
      Returns the value associated with the given variable.  The variables
      are set by options found by init_options, and are specified in the
      arizonaconfig options blocks.

   <Arguments>
      variable:
              The name of the variable to retrieve a value from, as a
              string.
      section:
              The name of the section containing the variable. If section.variable
              does not exist, then this func will try to default back to
              variable.

   <Exceptions>
      TypeError: variable missing or not a string.

   <Side Effects>
      None.

   <Returns>
      The value associated with the specified variable.  Returns None if
      the variable could not be found.
   """
   # check params
   arizonageneral.check_type_simple(variable, "variable", str, "get_option")

   if section:
      result = getattr(program_variables, section + "." + variable, None)
      if result:
         return result

   return getattr(program_variables, variable, None)





# TODO: deprecated, use get_option instead
def get_option_section(variable, section = None):
   return get_option(variable, section)





def get_sections(variable):
   # check params
   arizonageneral.check_type_simple(variable, "variable", str, "get_sections")

   if not program_variables:
      return []

   dict = getattr(program_variables, "specified_options", None)
   if not dict:
      return []

   list = []
   for var in dict:
      dot = var.find(".")
      if (dot >= 0) and (var[dot+1:] == variable):
         list.append(var[:dot])

   return list


         


def set_option(variable, value):
   """
   <Purpose>
      Sets the value associated with the given variable.

   <Arguments>
      variable:
              The name of the variable to set the value of, as a string.
      value:
              The new value for the variable.

   <Exceptions>
      TypeError: variable missing or not a string.

   <Side Effects>
      Updates program_variables by setting variable to the desired value.

   <Returns>
      None.
   """
   # check params
   arizonageneral.check_type_simple(variable, "variable", str, "set_option")

   if not program_variables:
      raise UnboundLocalError, "Must call init_options before set_option"

   setattr(program_variables, variable, value)
   return





def get_version():
   """
   <Purpose>
      Returns the program version as set by the init_options function.

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      Returns the program version as set by the init_options function, or
      None if it has not been set.
   """
   return version_string





def print_help(stream=sys.stdout):
   """
   <Purpose>
      Prints the program help to the specified file, or defaults to 
      sys.stdout.

   <Arguments>
      None.

   <Exceptions>
      None.

   <Side Effects>
      None.

   <Returns>
      None.
   """
   glo_option_parser.print_help(stream)





def reset():
   """
   <Purpose>
      Resets all internal state of arizonaconfig.  Only needed for testing
      purposes.

   <Arguments>
      Mone.

   <Exceptions>
      None.

   <Side Effects>
      Resets all globals to their defaults

   <Returns>
      None.
   """   
   global found_modules
   global found_options
   global program_variables
   global version_string
   global glo_option_parser
   global parsed_modules
   global glo_debug

   # clear any existing state
   found_modules = []
   found_options = []
   program_variables = None
   version_string = None
   glo_option_parser = None
   parsed_modules = []
   glo_debug = 0





def __debug_output(program_options):
   """
   <Purpose>
      Prints debug output for the given program options.

   <Arguments>
      program_options:
              List of program options to display.

   <Exceptions>
      TypeError: variable missing or not a string.

   <Side Effects>
      Exits the program with status 0.

   <Returns>
      None.
   """
   global program_variables

   # check params
   arizonageneral.check_type_simple(program_options, "program_options", list, "__debug_output")

   print "<Module Locations of arizonaconfig Configuration Options>"

   # find the longest long option to make things line up
   longest_optname = 0
   for option in program_options:
      if len(option.longoption) > longest_optname:
         longest_optname = len(option.longoption)

   # print column headings
   if longest_optname < 10:
      longest_optname = 10
   print "Opt Long Option" + " " * (longest_optname - 9) + "From File"
   print "--- -----------" + " " * (longest_optname - 9) + "---------"

   # display the help lines and exit
   for option in program_options:
      if option.option != "":
         print option.option + " ",
      if option.longoption != "":
         if option.option == "":
            print "   ",
         print option.longoption,
      print " " * (longest_optname - len(option.longoption)) + " " + option.module
   print "-" * 70


def __debug_variable_output():
   if program_variables:
      longest_var = 0
      for var in program_variables.__dict__:
         if len(var) > longest_var:
            longest_var = len(var)

      for var in program_variables.__dict__:
         print var,
         print " " * (longest_var - len(var)) + " " + str(program_variables.__dict__[var])





def __default(variable):
   """
   <Purpose>
      Returns the default value for an option.  If the option is not
      found, raises a TypeError.

   <Arguments>
      variable:
              Name of the option variable with the desired default value.

   <Exceptions>
      TypeError, if there are bad parameters or if the option is not 
      found.

   <Side Effects>
      None.

   <Returns>
      Default value for the option variable.  Can be None.
   """
   # check params
   arizonageneral.check_type_simple(variable, "variable", str, "__default")

   global found_options

   found = False
   for option in found_options:
      if option.variable == variable:
         found = True
         if option.default != None:
            return option.default
   if not found:
      raise TypeError, "Asked for default of unknown option variable: `" + str(variable) + "'" 
   return None





def __read_config_file(filename, config_parser, values = None):
   """
   <Purpose>
      Parses the configuration file specified by filename.  Adds any
      previously missing options to the config_parser.  Returns a list of
      set options.

   <Arguments>
      filename:
              Filename of the configuration file.
      config_parser:
              OptionParser for the configuration file.

   <Exceptions>
      TypeError, if there are bad parameters.

   <Side Effects>
      Modifies config_parser by adding additional found options.
      Exits the program if the config file could not be found.

   <Returns>
      A dictionary of variables, with values either None or the value
      set in the config file.
   """
   global glo_config_filename
   # check params
   arizonageneral.check_type_simple(filename, "filename", str, "__read_config_file")
   filename = filename.strip()
   if filename[:2] == '~/':
      envHome = ''
      if 'HOME' in os.environ:
      	envHome = os.environ['HOME']
      elif 'HOMEDRIVE' in os.environ and 'HOMEPATH' in os.environ:
	envHome = os.path.join(os.environ['HOMEDRIVE'],os.environ['HOMEPATH'])
      filename = envHome + filename[1:]
   if not isinstance(config_parser, OptionParser):
      raise TypeError, "The parameter 'config_parser' of the function '__read_config_file' must be an OptionParser."

   # this global is used by pacman/storktrackusage to track what configuration
   # file was read (or was attempted to be read). It should be set regardless
   # of whether or not the file was opened and read.
   glo_config_filename = filename

   try:
      config_file = file(filename,"r")
   except IOError:
      print >> sys.stderr, "Warning: cannot open configuration file: " + filename
      return {}

   # dictionary to hold set configuration file options
   config_variables = {}

   # a list of all the arguments in the config file
   config_args = []

   # process the config file one line at a time
   for origline in config_file:
      line = origline

      # Ignore anything after #, it is a comment
      linebr = line.split('#')
      line = linebr[0].strip()
      if not line:
         # If the line is empty continue
         continue

      # set up the usage message
      error_msg = "The config file " + filename + " has an invalid line:\n" + origline
      config_parser.set_error(error_msg)

      # Prepend '--' and remove '='s to make a long command line option
      line = "--" + line

      # JAC: Bug fix.   All '=' were changed to ' '.   This should be more
      # selective.   There are four cases when this should happen:
      # a=b
      # a = b
      # a= b
      # a =b

      if line.split()[0].find('=')>0:
         # case a=b and a= b
         line = line.replace('=', ' ',1)
      else:
         # case a = b and a =b
         if len(line.split()) > 1 and line.split()[1][0] == '=':
            line = line.replace('=', ' ',1)


      # Detect options that do not exist and issue a warning, rather than
      # letting config_parser error and exit.
      optname = line.split()
      if optname:
         optname = optname[0]
         if not config_parser.has_option(optname):
             print "WARNING: Unknown option: '" + optname[2:] + "' in " + filename
             continue

      # Handle the comma case in a config file.  For example, expand
      # an option such as --x a,b,c into --x a --x b --x c.
      linelist = line.split(',')
      if len(linelist) > 1:
         front = line.split()[0]
         parselist = linelist[0].strip().split(None, 1)
         for item in linelist[1:]:
            parselist.append(front.strip())
            parselist.append(item.strip())

         # JAC: I added the parselist code in this area to fix a bug.
         # The code used to assume that everything that looked like an option
         # was an option (i.e. if you had an option "--sshopts" that might
         # be set to: "-n -i ./id_rsa_ebay -o StrictHostKeyChecking=no" the
         # program would actually treat most of these as separate options
         # I think it actually was broken for any arguments that would be
         # broken in two by "split".
         #
         # Even now I think the "strip()" commands above are unnecessary and
         # may even cause problems, but I'm not certain so I left them in
         # rather than potentially break compatibility with the prior
         # implementation.
      else:
         parselist = line.split(None,1)

      config_args.extend(parselist)

   # The option line has now been prepared.  Parse it.
   (val, args) = config_parser.parse_args(args=config_args, values=values)

   # If there are args, then this was a mistyped or invalid option
   # line in the config file.  Report the error.

   # JRP - 11/5/06
   # the print_usage() message (as defined in the python
   # OptionParser class should print the error message
   # that has been set instead of the usage message. Even
   # Though we are setting the error message a few lines
   # up it is defaulting to printing the default usage
   # message. So we will just print our error_msg
   # instead.
   if args:
      #config_parser.print_usage()
      print error_msg
      sys.exit(1)

   return val





def __build_options(path=None, alt_paths=[], module="*", depth=0, ignore_duplicates=False):
   """
   <Purpose>
      Recursively finds and gets the options for any imported modules.

   <Arguments>
      path:
              Path to the module.
      alt_paths:
              A list of alternate absolute paths to modules.
      module:
              The name of the module to start with.  Can contain wildcards
              to specify multiple modules. Cannot contain a path. 

   <Exceptions>
      TypeError, if there are bad parameters.

   <Side Effects>
      Modifies found_options and found_modules.

   <Returns>
      None.
   """
   # check params
   arizonageneral.check_type_simple(module, "module", str, "__build_options")

   global found_options
   global found_modules
   global parsed_modules

   # print "XXX __build_options", path

   # if the caller specified a pathname as the module parameter, then split
   # it into path and filename parts
   if os.path.dirname(module):
      # it is an error to pass in a path and a pathname 
      assert(path=="." or path==None)
      path = os.path.dirname(module)
      module = os.path.basename(module)

   if path == None or path == '.':
      path = arizonageneral.get_main_module_path()

   path = os.path.abspath(path)

   paths = [path]
   paths.extend(alt_paths)

   # print "XXX __build_options", path, alt_paths, module, depth

   # get a list of modules
   if ("*" in module):
      globpath = os.path.join(path, module)
      modules = [os.path.basename(fn) for fn in glob.glob(globpath)]
   else:
      # SMB: If there were not glob characters in the module name, then don't
      # try to glob it (if we glob it, and it's in one of the alt_paths, then
      # we won't find it)
      modules = [module]

   # print "XXX modules", modules

   # display debugging output, if requested
   if glo_debug & 2:
      print " " * depth + globpath

   # process each module
   for filename in modules:
      # skip this module if it has already been parsed
      if filename in parsed_modules:
         continue

      # smbaker: skip backup files
      if filename.endswith("~") or filename.endswith(".~py") or filename.endswith(".pyc"):
         continue

      # display debugging output, if requested
      if glo_debug & 2:
         print " " * (depth + 2) + filename

      # open the module
      # print "XXX looking for ", filename
      for prefix in paths:
         pathname = os.path.join(prefix, filename)
         # print "XXX trying",pathname
         try:
            module_file = file(pathname)
            break
         except IOError:
            pass
      else:
         # ignore errors (there will be some, because modules like sys
         # won't be found in the current directory.
         continue
      # print "XXX found ", module_file

      # build the options_block string
      options_block = __build_options_block(module_file)

      includes = []

      # process the options block
      if (options_block != None):
         # exec the options string to build the options / includes lists
         options = None
         includes = None
         try:
            exec(options_block)
         except:
            raise TypeError, "\nModule " + filename + ": The arizonaconfig options block is invalid.\n" + \
                             "It must be of the form:\n" + \
                             "\"\"\"arizonaconfig\n" + \
                             "   options=[]\n" + \
                             "   includes=[]\n" + \
                             "\"\"\"\n\n" + \
                             "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])) + \
                             "Check for mismatched brackets, missing commas, or unclosed strings."

         # check for the options and includes lists
         if options == None:
            raise TypeError, "\nModule " + filename + ": The arizonaconfig options block is missing an options list."
         if includes == None:
            raise TypeError, "\nModule " + filename + ": The arizonaconfig options block is missing an includes list."

         # check the validity of the options list
         try:
            option = None
            try:
               arizonageneral.check_type_simple(options, "", list, "")
            except TypeError:
               raise TypeError, "Options block must be a list"
            for option in options:
               __check_option(option)
         except TypeError, error:
            error_str = "\nModule " + filename + ": The arizonaconfig options block has an invalid options list\n\n"
            if (option == None):
               error_str += "Options list: " + str(options)
            else:
               error_str += "Option: " + str(option)
            error_str += "\n\nError: " + str(error)
            raise TypeError, error_str

         # check the validity of the includes list
         try:
            arizonageneral.check_type_stringlist(includes, "", "arizonaconfig.__build_options")
         except TypeError, error:
            raise TypeError, "\nModule " + filename + ": The arizonaconfig options block has an invalid includes list\n\n" + \
                             "Includes list: " + str(includes) + "\n\n" + \
                             "Error: " + str(error)

         # process options= line
         # add each option to the master list
         for option in options:
            # store the filename with the option for the debug listing
            option = OptionName(option, filename)

            if option.description == None:
               option.description = optparse.SUPPRESS_HELP

            # see if the short or long option already exists
            for found_option in found_options:
               if found_option == "":
                  continue
               if (option.option != "" and option.option == found_option.option) \
                  or (option.longoption != "" and option.longoption == found_option.longoption):
                  # an option name matched.  Does everything else match? (except module name)
                  if option.option == found_option.option \
                     and option.longoption == found_option.longoption \
                     and option.variable == found_option.variable \
                     and option.action == found_option.action \
                     and option.data == found_option.data \
                     and option.default == found_option.default \
                     and option.metavar == found_option.metavar \
                     and option.description == found_option.description or \
                         (option.description == None and found_option == optparse.SUPPRESS_HELP):
                     # yes, just skip this option (it already exists)
                     break
                  else:
                     # SMB: if ignore_duplicates is set, then ignore the duplicate
                     # option. This is used when __build_options is called when
                     # processing the config file (which reads all modules, even
                     # those that are not referenced by the current program)
                     if ignore_duplicates:
                        break
                     error_str = "File " + filename + ": Tried to redefine existing option (" + \
                                 str(found_option.option) + ", " + str(found_option.longoption) + "), from " + \
                                 str(found_option.module) + ", but options were not identical:\n\n"
                     if option.option != found_option.option:
                        error_str += "Existing 'option': " + str(option.option) + "  Redefined as:" + str(found_option.option) + "\n"
                     if option.longoption != found_option.longoption:
                        error_str += "Existing 'long option': " + str(option.longoption) + "  Redefined as:" + str(found_option.longoption) + "\n"
                     if option.variable != found_option.variable:
                        error_str += "Existing 'variable': " + str(option.variable) + "  Redefined as:" + str(found_option.variable) + "\n"
                     if option.action != found_option.action:
                        error_str += "Existing 'action': " + str(option.action) + "  Redefined as:" + str(found_option.action) + "\n"
                     if option.data != found_option.data:
                        error_str += "Existing 'data': " + str(option.data) + "  Redefined as:" + str(found_option.data) + "\n"
                     if option.default != found_option.default:
                        error_str += "Existing 'default': " + str(option.default) + "  Redefined as:" + str(found_option.default) + "\n"
                     if option.metavar != found_option.metavar:
                        error_str += "Existing 'metavar': " + str(option.metavar) + "  Redefined as:" + str(found_option.metavar) + "\n"
                     if option.description != found_option.description or \
                        (found_option == optparse.SUPPRESS_HELP and option.description != None):
                        error_str +=  "Existing 'description': " + str(option.description) + "  Redefined as:" + str(found_option.description) + "\n"

                     raise TypeError, error_str
            else:
               # nothing matched, add the option
               found_options.append(option)

         raw_includes = includes
         includes = []

         # print "XXX raw_includes=", raw_includes
         # process includes= line
         for include in raw_includes:
            # replace $MAIN with the path to the main run module
            include = include.replace("$MAIN", arizonageneral.get_main_module_path())
            include = include.replace("$SELF", os.path.dirname(pathname))

            # add the module to the list if it wasn't already included
            # before in the master list
            if not (include in found_modules):
               includes.append(include)
               found_modules.append(include)

         # print "XXX includes=", includes

      # find import statements in the module
      module_file.seek(0)
      for line in module_file:
         line = line.lstrip()
         if line.startswith("import"):
            # find the name of the imported module(s), ignore the rest of the line
            include_line = line.split(" ", 1)[1].split(",")
            for include in include_line:
               include = include.strip()

               # remove comments
               i = include.find("#")
               if i != -1:
                  include = include[:i].rstrip()

               # convert special case "x.y" to "x/y"
               # Note: * means pass a list as individual arguments
               include = os.path.join(*include.split("."))

               # convert special case "x as y" to "x"
               include = include.split(" ")[0]

               # add the module to the list if it wasn't already included
               # before in the master list
               if not (include in found_modules):
                  includes.append(include + ".py")
                  found_modules.append(include)

      # done searching the module, close it
      module_file.close()

      # this module is done.. add it to the list of parsed modules
      parsed_modules.append(filename)

      # print "XXX module", module, "includes", includes

      # call __build_options() recursively for each import
      # base case: if includes = [], no recursive call is made
      for include in includes:
         # general case: handle each included/imported module
         if os.path.dirname(include):
            # if we have something with an absolute path, then break it into
            # path and filename parts
            __build_options(os.path.dirname(include), alt_paths, os.path.basename(include), depth + 4, ignore_duplicates=ignore_duplicates)
         else:
            __build_options(path, alt_paths, include, depth + 4, ignore_duplicates=ignore_duplicates)

   # done with this module
   return





def __check_option(option):
   """
   <Purpose>
      Checks the validity of an option line.

   <Arguments>
      option:
              List containing option items that will be checked.

   <Exceptions>
      TypeError, if there was a problem with the option.

   <Side Effects>
      None.

   <Returns>
      None.
   """
   try:
      arizonageneral.check_type_simple(option, "", list, "")
   except TypeError:
      raise TypeError, "Option line must be a list"
      
   if len(option) != 8:
      raise TypeError, "Option line must contain exactly 8 items, only detected " + str(len(option))
   arizonageneral.check_type_simple(option[0], "option", str, "arizonaconfig.__check_option")
   arizonageneral.check_type_simple(option[1], "long option", str, "arizonaconfig.__check_option")
   arizonageneral.check_type_simple(option[2], "variable", str, "arizonaconfig.__check_option")
   arizonageneral.check_type_simple(option[3], "action", str, "arizonaconfig.__check_option")
   arizonageneral.check_type(option[4], "data", [str, None, int], "arizonaconfig.__check_option")
   arizonageneral.check_type_simple(option[6], "metavar", str, "arizonaconfig.__check_option", noneok=True)
   arizonageneral.check_type_simple(option[7], "description", str, "arizonaconfig.__check_option", noneok=True)
   if option[2].strip() == "" or option[2].strip() != option[2]:
      raise TypeError, "Invalid variable: '" + str(option[2]) + "'\nShould either be None, or a non-empty string with no leading or trailing spaces"
   if option[3] != "store" and option[3] != "append" and option[3] != "store_const" \
      and option[3] != "store_true" and option[3] != "store_false" \
      and option[3] != "sectionstart" and option[3] != "sectionstop":
      raise TypeError, "action must be one of: 'store', 'append', 'store_const', 'store_true', 'store_false'"
   if option[3] == "help" and option[5] != None:
      raise TypeError, "default must be None when action is 'help'"
   if option[3] == "store":
      if option[4] == "string":
         arizonageneral.check_type_simple(option[5], "default", str, "arizonaconfig.__check_option", noneok=True)
      elif option[4] == "int":
         arizonageneral.check_type_simple(option[5], "default", int, "arizonaconfig.__check_option")
      elif option[4] == "long":
         arizonageneral.check_type_simple(option[5], "default", long, "arizonaconfig.__check_option")
      elif option[4] == "float":
         arizonageneral.check_type_simple(option[5], "default", float, "arizonaconfig.__check_option")
      elif option[4] == "complex":
         arizonageneral.check_type_simple(option[5], "default", complex, "arizonaconfig.__check_option")
      else:
         raise TypeError, "data must be one of 'string', 'int', 'long', 'float', 'complex' when action is either 'store' or 'append'"
   elif option[3] == "append" or option[3] == "sectionstart":
      if option[4] == "string":
         arizonageneral.check_type(option[5], "default", [[list, str], None], "arizonaconfig.__check_option")
      elif option[4] == "int":
         arizonageneral.check_type(option[5], "default", [[list, int], None], "arizonaconfig.__check_option")
      elif option[4] == "long":
         arizonageneral.check_type(option[5], "default", [[list, long], None], "arizonaconfig.__check_option")
      elif option[4] == "float":
         arizonageneral.check_type(option[5], "default", [[list, float], None], "arizonaconfig.__check_option")
      elif option[4] == "complex":
         arizonageneral.check_type(option[5], "default", [[list, complex], None], "arizonaconfig.__check_option")
      else:
         raise TypeError, "data must be one of 'string', 'int', 'long', 'float', 'complex' when action is either 'store' or 'append'"
   elif option[3] == "store_const":
      arizonageneral.check_type_simple(option[4], "data", int, "arizonaconfig.__check_option")
      arizonageneral.check_type_simple(option[5], "default", int, "arizonaconfig.__check_option")
   elif option[3] == "store_true" or option[3] == "store_false":
      arizonageneral.check_type_simple(option[5], "default", bool, "arizonaconfig.__check_option")
   else:
      if option[4] != None:
         raise TypeError, "data must be None, unless action is one of 'store', 'append', 'store_const'"
   if option[6] != None and option[3] != "store" and option[3] != "append" and option[3] != "sectionstart":
      raise TypeError, "metavar must be None unless action is either 'store' or 'append'"  
   if option[6] != None and (option[6].strip() == "" or option[6].strip() != option[6]):
      raise TypeError, "Invalid metavar: '" + option[2] + "'\nShould either be None, or a non-empty string with no leading or trailing spaces"
   




def __build_options_block(module_file):
   """
   <Purpose>
      Scans a file for the arizonaconfig options block and returns it as
      a string.

   <Arguments>
      module_file:
              Open file that will be scanned for triple quoted strings
              starting as "" "arizonaconfig (no spaces).  This file is
              expected to be open and ready to read.

   <Exceptions>
      TypeError, if there are bad parameters.

   <Side Effects>
      None.

   <Returns>
      The found options block string, or None if an option block could
      not be found.
   """
   # check params
   arizonageneral.check_type_simple(module_file, "module_file", file, "__build_options_block")

   # build the options_block string
   options_block = None
   append_block = False
   for line in module_file:
      # clean up the line for easier processing
      line = line.strip()

      # the options block must start with (3 quotes)arizonaconfig
      # if this is found, set to start adding lines to the block
      if line.startswith("\"\"\"arizonaconfig"):
         # set to add lines to the block. Doesn't add the first line,
         # because it is just the block identifier.
         append_block = True
         options_block = ""
      # if it's set to add options, add each line to the block
      elif append_block:
         # if the trailing triple quote was found, the block is done.
         if line.endswith("\"\"\""):
            # stop adding lines to the block
            append_block = False

            # strip off trailing triple quotes
            line = line[0:len(line) - 3]

         # add the line to the options block
         options_block += line + "\n"

   return options_block





def __add_option(parser, option):
   """
   <Purpose>
      Add an option to the option parser.

   <Arguments>
      parser:
              OptionParser to add an option to.
      option:
              OptionName with the option information.

   <Exceptions>
      None.

   <Side Effects>
      OptionParser is changed to include a new option.

   <Returns>
      None.
   """
   # check params
   if not isinstance(parser, OptionParser):
      raise TypeError, "The parameter 'parser' of the function '__add_option' must be an OptionParser."
   if not isinstance(option, OptionName):
      raise TypeError, "The parameter 'option' of the function '__add_option' must be an OptionName."

   # clear unused option line entries.
   option_type = None
   option_const = None

   if is_storable(option.action):
      # only 'store' and 'append' use 'type='
      option_type = option.data
   else:
      option.metavar = None
   if option.action == "store_const":
      # only 'store_const' uses 'const='
      option_const = option.data

   # add option line to parser
   # Note: "default=option.default" is not added.
   # Reason: We first must check the config file for any specified
   #         options.  Then, only if it's not in the config file can the
   #         default be used.
   parser.add_option(option.option, option.longoption, dest=option.variable,
                     action=option.action, type=option_type,
                     const=option_const, metavar=option.metavar,
                     help=option.description, default=option.default)
   return





class OptionName:
   """
   <Purpose>
      Data structure for holding all the date for a single option line

   <Variables>
      See the init_options functions for more details on these variables.
      option:
              Short option string.
      long option:
              Long option string.
      variable:
              Variable name for the option.
      action:
              "store", "append", "store_const", "store_true",
              "store_false".
      data:
              "string", "int", "long", "float", "complex", None.
      default:
              The default value to store if the option is not given.
      metavar:
              An alternate variable name to show in --help, or None.
      description:
              Helpful description of the option, for use in --help.
      module:
              Name of the module that the option was in.

   <Functions>
      None.
   """
   option = None
   longoption = None
   variable = None
   action = None
   data = None
   default = None
   metavar = None
   description = None
   module = None

   def __init__(self, options, module_name):
      """
      <Purpose>
         OptionName constructor.  Sets initial values for the internal
         variables.

      <Arguments>
         options:
                 List of options.  Must have 8 elements.
         module:
                 Name of the module the options came from.

      <Exceptions>
         None.

      <Side Effects>
         Sets variables: option, longoption, variable, action, data,
         default, metavar, description, module.

      <Returns>
         None.
      """
      # check params
      arizonageneral.check_type_simple(options, "options", list, "OptionName.__init__")
      arizonageneral.check_type_simple(module_name, "module_name", str, "OptionName.__init__")

      self.option = options[0]
      self.longoption = options[1]
      self.variable = options[2]
      self.action = options[3]
      self.data = options[4]
      self.default = options[5]
      self.metavar = options[6]
      self.description = options[7]
      self.module = module_name
      return





class OptionParser(optparse.OptionParser):
   """
   <Purpose>
      Overrides optparse.OptionParser.error to extend its functionality.

   <Parent>
      optparse.OptionParser
   """

   custom_error = None

   def error(self, msg):
      """
      <Purpose>
         Overrides optparse.OptionParser.error to print an extra line
         offering --help.

      <Arguments>
         msg:
                 The error message to be displayed.

      <Exceptions>
         None.

      <Side Effects>
         None.

      <Returns>
         None.
      """
      if self.custom_error != None:
         print >> sys.stderr, self.custom_error
      else:
         self.print_usage()

      print >> sys.stderr, msg

      if self.custom_error == None:
         print >> sys.stderr, "Try '--help' for an informative help message"

      sys.exit(1)
      return


   def set_error(self, error_message):
      """
      <Purpose>
         Saves the given error message, which will be displayed instead of
         a usage line.  Also, suppresses printing of the "Try --help"
         text.  This is used to display parsing errors in the config file.

      <Arguments>
         error_message:
                 The error message to be displayed.

      <Exceptions>
         None.

      <Side Effects>
         The class variable custom_error is set.

      <Returns>
         None.
      """
      self.custom_error = error_message
      return


