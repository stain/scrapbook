#!/bin/bash

# Extracts SLES9 ISO images into a directory structure to be
# published on web, to be able to create an APT archive of the 
# provided packages.

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


# Where to extract
SUSE="/srv/www/vhosts/apt.s11.no/htdocs/sles8"
ISO="/home/admin/linux/SLES9/"
MKDIR="mkdir --parents"
CP="cp -a"
MNT="/mnt"

# Extracts SuSE SLES 9 installation files from ISO images
# to make a net-installable structure
# Run as root (to mount images) on webdata.stud.ntnu.no

# Exit immediately on errors
set -e

for nr in 1 2 3 4 5 6 ; do
#    DEST=$(($a+1))
    DEST="$SUSE/CD$nr"
    $MKDIR $DEST
    #LOFI=`lofiadm -a $ISO/SLES-9-i386-RC5-CD$nr.iso`
    #sleep 2
    #mount -F hsfs -o ro $LOFI $MNT
    mount $ISO/SLES-9-i386-RC5-CD$nr.iso $MNT -o loop
    $CP $MNT/* $DEST/
    umount $MNT
    #lofiadm -d $LOFI
done    
