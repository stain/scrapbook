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
"""Test utils.py for forgetMP3.
"""



import unittest
import utils
import os
import time
import tempfile
import shutil

class TestDir(unittest.TestCase):
    """Base class that switches home dir"""
    def setUp(self):
        # Set up a temporary home dir
        self.old_home = os.environ["HOME"]
        self.home = tempfile.mkdtemp()
        os.environ["HOME"] = self.home

    def tearDown(self):
        # Remove all of our temporary home dir
        shutil.rmtree(self.home)
        os.environ["HOME"] = self.old_home

class TestUtils(TestDir):

    def test_data_dir(self):
        # FIXME: How to test this without either hardcoding the path or
        # doing the same work as data_dir() ?
        self.assertEqual(utils.data_dir(), 
            self.home + "/Library/Application Support/ForgetMP3")
    
    def test_root_dir(self):
        # FIXME: How to test this without either hardcoding the path or
        # doing the same work as root_dir() ?
        self.assertEqual(utils.root_dir(),
            "/Users/stain/Documents/i/src/forgetmp3")

class TestConfig(TestDir):
    def setUp(self):
        TestDir.setUp(self)
        self.conf = utils.config()

    def test_load(self):
        import ConfigParser
        self.assert_(isinstance(self.conf, ConfigParser.ConfigParser))
    
    def test_music(self):
        self.assertEqual(self.conf.get("music", "library"),
                         self.home + "/Music/forgetmp3")
        
        self.assertEqual(self.conf.get("music", "itunes"),
                         self.home + "/Music/iTunes")
  
    def test_database(self):
        self.assertEqual(self.conf.get("database", "path"),
                         utils.data_dir())
    
    def test_default_create(self):
        """Might fail if user has edited file"""
        uconf = os.path.join(utils.data_dir(), "config.ini")
        # should have been created
        first_line = open(uconf).readline()
        self.assert_(first_line.startswith("# Example config for ForgetMP3"))

if __name__ == "__main__":
    unittest.main()            

