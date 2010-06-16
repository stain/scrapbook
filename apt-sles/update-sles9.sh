#!/bin/bash

# Fetch updates from SuSE and integrate them into the APT archive

# Copyright (c) 2004 Stian Soiland
# 
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# Author: Stian Soiland <stian@soiland.no>
# License: MIT
# URL: http://soiland.no/software

set -e # abort on any errors

# Where to mirror to
UPDATE="/srv/www/vhosts/apt.s11.no/htdocs/incoming/suse-updates/sles9"
# Where APT wants his RPMs
APT="/srv/www/vhosts/apt.s11.no/htdocs/apt/sles9/incoming/"

# Remember to update --cut-dirs below to the number of directories
# to skip from URL
WGET="wget --mirror --no-parent --no-host-directories --cut-dirs=5"

mkdir --parents $UPDATE
cd $UPDATE
# This weird  way of entering URL is one way to not expose
# the username and password.
# (one other way is to use .wgetrc, which we wouldn't like here)

$WGET --input-file=/dev/stdin <<EOF
http://suseuser:susepassword@sdb.suse.de/download/i386/update/SUSE-CORE/9/
EOF

# Delete stupid index.html-files, they will mess up
# directory listings
cd $UPDATE
find -name index.html\* -exec rm {} \;



# Make sure exist
cd $APT/RPMS.updates
find -type f -exec rm {} \;
cd $APT/SRPMS.updates
find -type f -exec rm {} \;

cd $UPDATE/rpm/
find -name \*rpm -exec ln {} $APT/RPMS.updates \;
cd $UPDATE/sources/
find -name \*src.rpm -exec ln {} $APT/SRPMS.updates \;

# Remove stupid dupilcate version-less files that were probably symlinks
cd $APT/RPMS.updates
shopt -s extglob
rm !(*-[0-9]*)
rm *patch.rpm

cd $APT/SRPMS.updates
rm !(*-[0-9]*)


genbasedir --flat $APT
