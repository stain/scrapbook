#!/usr/bin/python
"""
Manages SuSE patches in APT archive.

Copyright (c) 2004 Stian Soiland

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Author: Stian Soiland <stian@soiland.no>
License: MIT
URL: http://soiland.no/software
"""


# Root of our APT archive
APT="/srv/www/vhosts/apt.s11.no/htdocs/apt/sles9/"
# SuSE patch descriptions
PATCHES="/srv/www/vhosts/apt.s11.no/htdocs/incoming/suse-updates/sles9/patches"
APTNAME="updates" # as in RPMS.updates
INCOMING="incoming" # as in $APT/incoming/RPMS.updates
TESTING="testing"
PRODUCTION="production"
DENY="denied"
#OBSOLETE="obsolete" # as in $APT/obsolete/RPMS.updates


import os
import time
import re
import popen2
import glob
import getopt
import sys

def check_updates(verbose=False, maxlist=10, details=False):
    """Checks for any unprocessed updates"""
    path = os.path.join(APT, INCOMING, 'RPMS.' + APTNAME)
    os.chdir(path)
    new = [file for file in os.listdir('.') if 
           file.endswith(".rpm") and 
           os.stat(file).st_nlink == 2]
    
    if not new:
        if verbose:
            print "No unprocessed updates."
        return

    # Find newest patch
    dates = [(os.stat(file).st_mtime, file) for file in new]
    dates.sort()
    dates.reverse()
    newest_time, newest_file = dates[0]
    newest = newest_file.replace(".rpm", "")
    newest_date = time.strftime("%Y-%m-%d", time.localtime(newest_time))
    print "%s unprocessed updates. Newest patch %s from %s." % (
          len(new), newest, newest_date)

    if verbose:
        patchinfo([f for f in dates], maxlist, details)

def patchinfo(files, maxlist=10, details=False):
    patches = read_patches()
    p_patches = package_patches(patches)
    
    for (f_time, f_name) in files[:maxlist]:
        date = time.strftime("%Y-%m-%d", time.localtime(f_time))
        info = rpminfo(f_name)
        print date,
        if not info:
            print "(could not read RPM: %s)" % f_name
            continue
        version = info['Version'] + '-' + info['Release']
        name = info['Name']
        try:
            patchversions = p_patches[name][version]
        except KeyError:
            patchnr = "?"
            kind = "(unknown)"
            desc = "(Unknown patch for RPM)"
            longdesc = ""
        else:
            patchversions.sort()    
            # Always pick the FIRST patch (later patches with the same
            # version don't describe what's fixed, but are probably
            # service packs) 
            patchnr = patchversions[0]
            patch = patches[patchnr]
            kind = patch.get("Kind", "(unknown)")
            desc = patch.get("Shortdescription.english", "(unknown)").strip()
            longdesc = patch.get("Longdescription.english", "")
        # Dirty hack to make name and version overlap columnway    
        # example::
        #   mod_ssl        12.8.10-160
        #   mod_ssl-patchs 12.8.10-160    (mod_ssl-patchsystem wrapped)
        #   mod_php4-servlet 4.2.2-479
        #   php4             4.2.2-479

        name_and_version = name.ljust(25)
        name_and_version = name_and_version[:25-len(version)]
        name_and_version += " " + version
        print "%-3s %5s %-26s %s" % (kind[:3], patchnr[:5], name_and_version, desc)
        if details and longdesc: 
                print "-"*70
                print longdesc
                print "-"*70
                print ""
    if len(files) > maxlist:
        print "(.. %s more RPMs)" % (len(files)-maxlist)

def rpminfo(filename):
    info = {}
    rpm,_,_ = popen2.popen3(["rpm", "-qp", filename,
            "--queryformat", "%{NAME}\n%{VERSION}\n%{RELEASE}"])
    try:
        info['Name']  = rpm.readline().strip()
        info['Version']  = rpm.readline().strip()
        info['Release']  = rpm.readline().strip()
        return info
    except:
        return None    

def read_patches():
    """Returns all SuSE patches as dictionaries"""
    patches = {}
    for filename in os.listdir(PATCHES):
        if not filename.startswith('patch-'):
            continue
        patchnr = filename.replace('patch-', '')    
        patch = open(os.path.join(PATCHES, filename))
        patches[patchnr] = read_patch(patch)
    return patches        

def package_patches(patches):
    """Find all patches related to all packages.
    Returns a dictionary of package names, each package
    containing another dictionary of different versions,
    each version containing the related patchnr

    This would give an idea of the relation between a
    patch and a RPM version.
    """
    packages = {}
    for (patchnr, patch) in patches.items():
        for package in patch.get("Packages", ()):
            name = package.get("Filename")
            version = package.get("Version")
            if not (name and version):
                continue
            name = name.replace(".rpm", "")    
            # The other versions of this package, if any 
            versions = packages.setdefault(name, {})
            related_patches = versions.setdefault(version, [])
            related_patches.append(patchnr)
    return packages            

re_keyword = re.compile(r"^([A-Z][A-Za-z0-9.-]*):\s(.*)")
def read_patch(file, _packages=False):
    """Parses SuSEs patch-files. Returns a large dictionary"""
    kw = {}
    key = None
    data = ""
    line = True
    while line:
        line = file.readline()
        if line.startswith("#"):
            continue
        match = re_keyword.match(line)
        if not match:
            # Not anything new, just add this line
            data += line
            continue
            
        # New key, store old data first
        if isinstance(data, str): 
            data = data.rstrip() 
        if key: kw[key] = data
        key = match.group(1)
        data = match.group(2)

        # Hmm.. we shouldn't get duplicates, this must be a new
        # package
        if _packages and key in kw:
            # Rewind (!!). Isn't this Turbo Pascal? =)
            file.seek(-len(line), 1)
            return kw

        # Near end of file (just the signature left)
        if key == "Segakcap":
            if _packages:
                # Rewind (!!). Isn't this Turbo Pascal? =)
                file.seek(-len(line), 1)
            # Just return anyway, this is not important.    
            return kw

        if key == "Packages" and not _packages:
            # Subsection "Packages:" started, will recurse to find
            # package keywords
            data = []
            while True:
                package = read_patch(file, _packages=True)
                if not package:
                    break    
                data.append(package)

    if isinstance(data, str):
        data = data.rstrip() 
    # Last key, store data
    if key: kw[key] = data
    return kw


def approve_patch(patchnr, target):
    try:
        patchnr = str(int(patchnr))
    except ValueError:
        print "Invalid patchnr %s" % patchnr
        return    
    patches = read_patches()
    try:
        patch = patches[patchnr]
    except ValueError:
        print "Invalid patch number %s" % patchnr
        return    

    # Find files to approve
    files = []
    for package in patch.get("Packages", ()):
        name = package.get("Filename")
        version = package.get("Version")
        if not (name and version):
            continue
        name = name.replace(".rpm", "")
        path = os.path.join(APT, INCOMING, 'RPMS.' + APTNAME)
        pattern = "%s-*%s.*rpm" % (name, version)
        files.extend(glob.glob1(path, pattern))
    # glob might have matched more..    
    files = unique(files)
    for file in files:
        approve_rpm(file, target)

def unique(items):
    """Removes duplicates from a list. 
       Items must be hashable. List order not retained."""
    set = {}
    for item in items:
        set[item] = None                     
    return set.keys()    
                   
def approve_rpm(filename, target):
    path1 = os.path.join(APT, INCOMING, 'RPMS.' + APTNAME, filename)
    path2 = os.path.join(APT, target, 'RPMS.' + APTNAME, filename)
    try:
        os.link(path1, path2)
        print filename, "->", target
    except OSError, e:
        print "Could not link", path2, e.strerror   

def view_patch(patchnr, with_desc=True):
    try:
        patchnr = str(int(patchnr))
    except ValueError:
        print "Invalid patchnr %s" % patchnr
        return    
                   
    patches = read_patches()
    try:
        patch = patches[patchnr]
    except KeyError:
        print "Unknown patch %s" % patchnr
        return
    
    kind  = patch.get("Kind", "")
    header = "SuSE %spatch #%s" % (kind, patchnr)
    print header
    print "=" * len(header)

    print patch.get("Shortdescription.english", "").strip() + "\n"
    print "Packages:"
    for pack in patch.get("Packages", ()):
        print "  ", pack.get("Filename", "").replace(".rpm", ""),
        print pack.get("Version", "") 
    if with_desc:    
        print ""    
        print "Description:"    
        print patch.get("Longdescription.english", "")


def usage():
    print "Manages SuSE patches in APT archive"
    print "(c) Stian Søiland 2004 <stian@soiland.no>"
    print ""
    print "USAGE: patchman [-h] [-u] [-v PATCH] [-a|-x] [-d] [-t TARGET] <patches>"
    print "  -h        --help          This help"
    print "  -u        --updates       Displays unprocessed updates"
    print "  -q        --quiet         Don't be very verbose"
    print "  -d        --desc          Include long descriptions in patch info"
    print "  -a        --approve       Approve patches given"
    print "  -x        --deny          Deny patches given"
    print "  -v PATCH  --view=PATCH    View details on a patch number"
    print "  -t TARGET --target=TARGET Target for approval (default: %s)" % TESTING
    print "  <patches>                 Zero or more patches to approve."
    print "                            A patch can be a patch number or a"
    print "                            (relative) RPM filename."
    print "Typical usage cycle:"
    print "  patchman -u                     Is there anything not yet processed?"
    print "  patchman -u -t testing          What's currently on testing?"
    print "  patchman -v 2929                What is patch 2929, really?"
    print "  patchman -a 2929                Approve patch 2929 for testing"
    print "  patchman -a program-1.2.3.rpm   (or) Approve RPM for testing"
    print "  patchman -t production -a 2929  After a day, approve for production"
    print "  patchman -d program-1.2.3.rpm   (or) Deny RPM program-1.2.3.rpm"


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "huqdaxv:t:", 
                               ["help", "updates", "quiet", "desc",
                               "approve", "deny", "view=", "target="])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    updates = False
    desc = False
    quiet = False
    view = None
    target = None
    approve = False
    deny = False
    patches = args
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
        if o in ('-u', '--updates'):
            updates = True
        if o in ('-q', '--quiet'):
            quiet = True    
        if o in ('-d', '--desc'):
            desc = True    
        if o in ('-a', '--approve'):
            approve = True
        if o in ('-x', '--deny'):
            deny = True
        if o in ('-v', '--view'):
            view = a
        if o in ('-t', '--target'):
            target = a    
 
    if updates:
        check_updates(verbose=not quiet, details=desc)
    if deny:
        target = DENY    
    elif approve and target is None: 
        target = TESTING
    if approve or deny:
        for patch in args:
            if patch.count(".rpm"):
                rpm = os.path.basename(patch)
                approve_rpm(rpm, target)
            else:    
                approve_patch(patch, target)
        
if __name__ == "__main__":
    #approve_patch(9171)
    #check_updates(verbose=True)
    #view_patch(9171)
    main()
    

