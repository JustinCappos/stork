import os
import time
import sys

def sort(fn_in, fn_out):
    result = os.system("sort -n < " + fn_in + " > " + fn_out)
    if result != 0:
        raise IOError

def uniq(fn_in, fn_out):
    result = os.system("uniq < " + fn_in + " > " + fn_out)
    if result != 0:
        raise IOError

def mergelist(fnlist_in, fn_out):
    args = " ".join(fnlist_in)
    result = os.system("cat " + args + " > " + fn_out)
    if result != 0:
        raise IOError

def uniqify(fn_list, dest_fn):

    # if we only have one filename, then it is already unique, so ignore it
    if len(fn_list) <= 1:
        return

    print "uniqify: " + str(len(fn_list)) + " files --> " + dest_fn

    temp_fn = "/data/tmp/uniqify.tmp"
    backup_fn = None

    # remove temp_fn if it already exists
    if os.path.exists(temp_fn):
        os.remove(temp_fn)

    # merge the files into a single big file
    mergelist(fn_list, temp_fn)

    # sort it, and remove duplicate entries
    sort(temp_fn, temp_fn + ".sorted")
    uniq(temp_fn + ".sorted", temp_fn + ".uniq")

    # backup dest_fn if it exists
    if os.path.exists(dest_fn):
        backup_fn = dest_fn + ".old"
        # remove the old backup if it exists
        try:
            os.remove(backup_fn)
        except:
            pass
        os.rename(dest_fn, backup_fn)

    try:
        os.rename(temp_fn + ".uniq", dest_fn)
    except:
        print "failed to rename " + temp_fn + " to " + dest_fn
        # if we failed, restore the backup back to the original filename
        if backup_fn:          
           os.rename(backup_fn, dest_fn)
        return

    # invariants:
    #   all data from the original files is present in dest_fn
    #   original filenames can be safely deleted

    # remove the original filenames
    for fn in fn_list:
        if fn != dest_fn:
            os.remove(fn)

def isnumber(x):
    try:
       int(x)
       return True
    except:
       return False

def get_file_size(fn):
    try:
       return os.stat(fn)[6]
    except:
       return 0

def uniqify_dir(dir):
    print "getting filename list from " + dir

    # get a sorted list of filenames

    # ls doesn't work because it's very slow on nr05 (is this because new files
    # being written to the directory cause it to re-read?)
#    tmp_out = os.popen("ls " + dir + " 2>&1")

    # use our own directory reader -- would python's directory read & sort work?
    tmp_out = os.popen("./dumpdir " + dir + " 100000 | sort")

    filenames = tmp_out.readlines()
    filenames = [fn.strip() for fn in filenames]

    print "sleeping 60 seconds to wait for any pending transfers to complete"
#    time.sleep(60)

    work_list = []
    work_prefix = None
    work_bytes = 0
    work_count = 0

    for fn in filenames:
        # make sure the filename ends in either .uniq or .<number>
        suffixPos = fn.rfind(".")
        if suffixPos == -1:
            continue
        prefix = fn[:suffixPos]
        suffix = fn[suffixPos+1:]
        if not suffix:
            continue
        if not (suffix == "uniq") and not (isnumber(suffix)):
            continue

        if (work_prefix != prefix) or ((work_count>1) and (work_bytes>5000000)):
            if work_list:
                work_list = [os.path.join(dir, tmpfn) for tmpfn in work_list]
                print "bytes = " + str(work_bytes)
                uniqify(work_list, os.path.join(dir, work_prefix + ".uniq"))

            work_list = []
            work_prefix = prefix
            work_bytes = 0
            work_count = 0

        work_list.append(fn)
        work_bytes = work_bytes + get_file_size(os.path.join(dir, fn))
        work_count = work_count + 1

def main():
    args = sys.argv[:]

    # get rid of the program name
    args = args[1:]

    if len(args)<1 or args[0]=='help':
       print "syntax: uniqify <dir>"
       print "example: uniqify /home/logging/logs/strace"
       sys.exit(1)

    uniqify_dir(args[0])

if __name__ == "__main__":
    main()

