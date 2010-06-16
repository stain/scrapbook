#!/bin/bash

# Creates an APT compatible directory structure from
# different SLES CDs. Requires that $APT and $SUSE
# are on the same media, to do hard linking.

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

APT="/srv/www/vhosts/apt.s11.no/htdocs/apt"
SUSE="/srv/www/vhosts/apt.s11.no/htdocs/sles9"

# Exit immediately on errors
set -e

mkdir --parents $APT/sles9/
cd $APT/sles9/
cat >README.txt <<EOF
apt archive of SuSE Enterprise Linux 9 (SLES9)
----------------------------------------------

NOTE:
Use of SLES requires a valid license. Contact
support@s11.no for any questions regarding s11s
apt archive.

This archive is only available to NTNU hosts.
DO NOT REDISTRIBUTE.

The proper URL to this archive is 
http://apt.s11.no/apt/


Architecture: i586


Directory structure:

    production           s11-approved 'production' level

        RPMS.base        SLES9 core CDs

        RPMS.updates     s11-approved patches from SuSE

        RPMS.contrib     3rd party RPMs for SLES (like Postgresql)

        RPMS.s11         s11-built RPMs for SLES (like cfengine)


    testing              Patches and versions under testing by s11

        RPMS.updates     Patches from SuSE under testing

        RPMS.contrib     New 3rd party RPMs under testing

        RPMS.s11         s11-built RPMs under testing


    incoming             Patches and versions not yet tested by s11
                         (mirrored)

        RPMS.updates     Upstream patches from SuSE (updated nightly)

        RPMS.contrib     Mirrored 3rd party RPMs


If you don't care about s11's approval routines, but just want's SuSEs
patches fast, you can rely on incoming/RPMS.updates alone. This will
always contain all patched RPMs available from SuSE. 



-- 
Chief Technical Officer, s11
2004-11-15
cto@s11.no
EOF


# SuSE Enterprise Linux (SLES)
mkdir --parents $APT/sles9/production/RPMS.base
cd $APT/sles9/production/RPMS.base
rm -f *
for x in $SUSE/sles9-i386/CD*/suse/i*/*rpm ; do ln $x . ; done  
ln $SUSE/sles9-i386/CD*/suse/noarch/*rpm .
mkdir --parents $APT/sles9/production/SRPMS.base
cd $APT/sles9/production/SRPMS.base
rm -f *
ln $SUSE/sles9-i386/CD*/suse/src/*rpm .




# Empty dirs for other to fill up
mkdir --parents $APT/sles9/production/RPMS.updates
mkdir --parents $APT/sles9/production/SRPMS.updates
mkdir --parents $APT/sles9/testing/RPMS.updates
mkdir --parents $APT/sles9/incoming/RPMS.updates
mkdir --parents $APT/sles9/incoming/SRPMS.updates

mkdir --parents $APT/sles9/production/RPMS.contrib
mkdir --parents $APT/sles9/production/SRPMS.contrib
mkdir --parents $APT/sles9/testing/RPMS.contrib
mkdir --parents $APT/sles9/incoming/RPMS.contrib
mkdir --parents $APT/sles9/incoming/SRPMS.contrib

mkdir --parents $APT/sles9/production/RPMS.s11
mkdir --parents $APT/sles9/production/SRPMS.s11
mkdir --parents $APT/sles9/testing/RPMS.s11

mkdir --parents $APT/sles9/denied/RPMS.updates
mkdir --parents $APT/sles9/outdated/RPMS.updates

# Make initial apt files
genbasedir --flat --progress $APT/sles9/production
genbasedir --flat --progress $APT/sles9/testing
genbasedir --flat --progress $APT/sles9/incoming
