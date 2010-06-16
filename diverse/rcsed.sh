#!/bin/bash
# 
# Stupid RCS-commit style editor
# 
# Copyright (c) 2004, NTNU ITEA systemdrift. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# Neither the name of NTNU nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# KNOWN BUGS:
#  - Should really be under GNU license due to all the options
#  - Backspace should print ^H


if [ "$1" == "-h" -o "$1" == "--help" ]; then
    echo "Usage: rcsed [-q] [FILE]"
    echo "       rcsed [-h | -v]"
    echo "Stupid RCS-commit style editor."
    echo "If FILE is not given, prints to STDOUT"
    echo "Options:"
    echo "  -h  --help     Print this help message"
    echo "  -v  --version  Print version information" 
    echo "  -q  --quiet    Disables guidance" 
    exit 0
fi

if [ "$1" == "-v" -o "$1" == "--version" ]; then
    echo "rcsed 2.04g"
    exit 0
fi

if [ "$1" == "-q" -o "$1" == "--quiet" ]; then
    quiet=1
    # Replaces $1 with $2
    shift
else
    quiet=0
    echo "enter log message, terminated with single '.' or end of file:" >&2
fi    


if [ $1 ]; then
    FILE="$1"
    echo -n '' > $FILE
else 
    FILE=/dev/stdout
fi

readline() {
    read -p '>>> ' line || {
        echo >&2
        line='.'
    }
}

readline
while [ "$line" != "." ] ; do
    echo $line >> $FILE
    readline
done    

if [ $quiet == 0 ] ; then
    echo done >&2
fi

