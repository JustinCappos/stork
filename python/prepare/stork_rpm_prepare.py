"""
<Program Name>
   stork_nest_rpm_prepare.py

<Started>
   November 22, 2005

<Author>
   Programmed by Justin Cappos

<Purpose>
   Unpacks (DOES NOT INSTALL) the RPM so that the contents are as follows:
      Files that are not configuration files get placed in $DIR/link
      Files that are configuration files get placed in $DIR/copy

   So if a rpm foo contains /bin/ls and /etc/passwd, after unpacking it 
   will have $DIR/link/bin/ls and $DIR/copy/etc/passwd
"""

import arizonareport
import arizonageneral
import os
import shutil
import stat



def prepare(filename, directory):
   """ 
      <Unpack file as specified above into directory
    This will be protected later..."""

   # are the arguments okay?
   arizonageneral.check_type_simple(filename, "filename", str, "stork_nest_rpm_prepare.prepare()")
   arizonageneral.check_type_simple(directory, "directory", str, "stork_nest_rpm_prepare.prepare()")

   #if not os.system("rpm --checksig " + filename + " &> /dev/null") == 0:
   # TODO FIXME find another way of checking rpm's
   if not filename.endswith(".rpm"):
      # TODO log this error...
      raise TypeError, "Not a recognized package in stork_nestrpm_prepare_package.prepare()"

   # Need to check if this has already been done...
   arizonareport.send_syslog(6, "preparing '" + filename + "' in '" + directory + "'")
   if os.path.exists(directory + "/link"):
      arizonareport.send_syslog(6, "previously finished '" + filename + "' in '" + directory + "'")
      return

   if not os.path.exists(directory):
      os.mkdir(directory)

   # Make a scratch dir off of this
   os.mkdir(directory + "/link")
   os.mkdir(directory + "/copy")

   # Go to the link dir
   os.chdir(directory + "/link")

   # Unpack the archive -- This puts all the files in $dir/link
   # TODO FIXME check for rpm2cpio and cpio
   (junk_child_in, child_out, junk_child_err) = os.popen3("rpm2cpio " + filename + " | cpio -i -d")

   # Get a list of permissions for the files (we want them to have the correct
   # permissions rather than the default)...
   #rpm2cpio ../$1 | cpio -i -t -v 2> /dev/null > /tmp/stork_rpm_unpack.junk.$$
   (junk_child_in, child_out, junk_child_err) = os.popen3("rpm2cpio " + filename + " | cpio -i -t -v | awk '{print $9}'") 

   permlist = []
   for line in child_out:
      if line.strip():
         permlist.append(directory + "/link/" + line.strip())


   # permlist containing the dir/file names and permissions should be created
   # here (from stdout of above command)...
   # permlist = (filename, permission) for each file

   
   # Fix the permissions on directories that aren't explicitly mentioned (/usr)
   #for item in `find .`; do if grep -q $item\$ /tmp/stork_rpm_unpack.junk.$$; then true; 
   # else echo $item >> $tempfile; fi; done
   # Pseudo code for above
   for root, dirs, files in os.walk(directory + "/link"):

      # go through and change the permissions on things not listed to be 755
      for name in files + dirs:
         rn = os.path.join(root, name)
         if os.path.exists(rn): 
            for item in permlist:
               # TODO (THIS IS PROBABLY SLOW FOR HUGE PACKAGES!!!)
               if os.path.exists(item) and os.path.samefile(rn, item):
                  # Remove the item in the list if we found it
                  permlist.remove(item)
                  break
            else:
               # set 755 on the file
               os.chmod(rn, stat.S_IRWXU + stat.S_IRGRP + stat.S_IXGRP + stat.S_IROTH + stat.S_IXOTH)


   # use stdout to get list of conf files   
   # now I have conf_list

   (junk_stdin2, child_stdout2, junk_stderr2) = os.popen3("rpm -qp --configfiles " + filename)

   # Move the configuration files to the directory/copy area...
   for line in child_stdout2:
      if line.strip():
         if not os.path.exists(os.path.dirname(directory+"/copy/" + line.strip())):
            os.makedirs(os.path.dirname(directory + "/copy/" + line.strip()))
         shutil.move(directory + "/link/" + line.strip(), directory + "/copy/" + line.strip())
 

   # Log the installation of this package
   arizonareport.send_syslog(6,"prepared '" + filename + "' in '" + directory + "'")

