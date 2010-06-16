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
"""Test database bindings db.py for forgetMP3.
"""



import unittest
import utils
import os
import time
import tempfile
import shutil

from testutils import TestDir

class TestCreated(TestDir):
    def testDatabaseInCorrectPlace(self):
        # Should be safe to import now that HOME is set
        import db; reload(db)
        # And confirm that the database now lives in /tmp somewhere 
        self.assert_(db.db.connect_info["database"].startswith(self.home))
   
    def testVersion(self):
        import db; reload(db)
        self.assertEqual(db.meta.version, utils.VERSION)     

        

class TestExported(TestDir):
    def testDatabaseTables(self):
        import db; reload(db)
        self.assert_(not hasattr(db, "Meta"))
        self.assert_(hasattr(db, "meta"))
        self.assert_(hasattr(db, "Folder"))
        self.assert_(hasattr(db, "Song"))
        self.assert_(hasattr(db, "Id3"))
        self.assert_(hasattr(db, "Songinfo"))
        self.assert_(hasattr(db, "execute"))
        self.assert_(hasattr(db, "query"))
        self.assert_(hasattr(db, "query_one"))
    
    def testReload(self):
        import db; reload(db)
        # Should NOT build tables (which would fail because table exists)
        reload(db)
        # Should NOT build tables (which would fail because table exists)
        db._prepare()
             

if __name__ == "__main__":
    unittest.main()            

