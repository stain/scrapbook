#!/usr/bin/env python
# *-* encoding: utf8
# 
# Copyright (c) 2005-2006 Stian Soiland
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Author: Stian Soiland <stian@soiland.no>
# URL: http://soiland.no/i/src/forgetmp3/
# License: GPL
#
"""Utility functions and data for forgetMP3.
"""



PROGRAM="ForgetMP3"
VERSION="0.62"

import sys
import os
import logging
from ConfigParser import ConfigParser
    
def data_dir():
    """Return the path for keeping user data and configuration"""
    if os.uname()[0] == "Darwin":
        ext = "Library/Application Support/%s" % PROGRAM
    else:
        ext = ".%s" % PROGRAM.lower()
    #FIXME: win32 support
    path = os.path.join(home(), ext)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def root_dir():
    """Get the path for program files."""
    return os.path.abspath(os.path.dirname(sys.argv[0]))

def home():
    home = os.environ.get("HOME")
    if not home:
        import pwd
        home = pwd.getpwuid(os.geteuid()).pw_dir
    return home     

def config():
    default_file = os.path.join(root_dir(), "default_config.ini")

    defaults = {}
    defaults["home"] = home()
    defaults["data"] = data_dir()
    defaults["root"] = root_dir()
    conf = ConfigParser(defaults)
    conf.read(default_file)
    cfile = os.path.join(data_dir(), "config.ini")   
    
    if not os.path.exists(cfile):
        # First time, write out the default config
        # in a commented style
        out = open(cfile, "w")
        out.write("# Example config for %s v%s\n" %(PROGRAM, VERSION))
        out.write("# The defaults are shown commented, to change a line,\n")
        out.write("# uncomment it.\n")
        out.write("\n")
        for line in open(default_file):
            if (line and not line.startswith("[") and 
                not line.startswith("#")):
                out.write("#")
            out.write(line)
    else:
        # Override defaults with anything specified by user
        conf.read(cfile)
    # Cache the returned value in our function object    
    return conf

def db_name():
    fname = os.path.join(config().get("database", "path"), 
                         "database")
    return fname

