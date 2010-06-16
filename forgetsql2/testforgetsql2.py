#!/usr/bin/env python
# *-* encoding: utf8
# 
# Copyright (c) 2005-2006 Stian Soiland
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#
# Author: Stian Soiland <stian@soiland.no>
# URL: http://soiland.no/i/src/forgetsql2/
# License: LGPL
#
"""Tests for forgetSQL2.

By itself this module will test using temporary sqlite databases and the
accompanied test-data.sql.

Testing with MySQL host=localhost user=stain pw=(blank) db=test:
    ./testforgetsql2.py --mysql localhost,stain,,test

Testing with PostgreSQL host=localhost
    ./testforgetsql2.py --postgresql 'host=localhost' 
"""


import sys
import os
import codecs
import unittest
import StringIO
import logging
import re
import gc
from sets import Set
from doc_exception import ProgrammingError

from forgetsql2 import Database, TableBuilder, DBConnect
from forgetsql2 import NotFoundError, generate

gc.disable()
            
class TestFramework(unittest.TestCase):
    # Change to "mysql" to test against mysql database
    db_mod = "sqlite"
    # if db_mod=="mysql", set this to mysql.connect() parameters 
    db_connect = None
    prepared = False
    def setUp(self):
        self.prepareLogger()
        self.prepareDatabase()
        self.prepareTables()
        self.prepareClasses()

    def tearDown(self):
        self.assertEqual(self.lastLog(), "")
        if self.db_mod == "sqlite":
            try:
                os.unlink(self.db_connect["database"])
            except OSError:
                pass
        self.db_c.close()
    
    def prepareClasses(self):
        """Prepare subclasses of Database and TableBuilder.

        The reason for this is to introduce the _db-class method
        without modifying the actual Database class.

        The new subclasses are accessible as self.Database and
        self.TableBuilder.
        """
        self.db_c = DBConnect(self.db, self.db_connect)
        class DB(Database):
            _db = self.db_c
        self.Database = DB
        class TB(TableBuilder):
            _db = self.db_c
        self.TableBuilder = TB
    
    # Copied from the Cerebrum project Ceresync
    # (It should be OK since we make this module GPL)
    def prepareLogger(self):
        """Make logger use a buffer instead of stderr. 
       
        The lines logged (format: "WARNING: asdlksldk") can be
        fetched with the method lastLog.
        """
        self.logbuf = StringIO.StringIO()
        logger = logging.getLogger()
        loghandler = logging.StreamHandler(self.logbuf)
        loghandler.setLevel(logging.INFO)
        loghandler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        del logger.handlers[:] # any old ones goodbye
        logger.addHandler(loghandler)
        logger.setLevel(logging.INFO)

    def lastLog(self):
        """Returns what's been logged since last call."""
        last = self.logbuf.getvalue()
        self.logbuf.seek(0)
        self.logbuf.truncate()
        return last

    def prepareDatabase(self):
        if self.db_mod == "sqlite":
            self.prepareDatabaseSqlite()
        elif self.db_mod == "mysql":
            self.prepareDatabaseMysql()
        elif self.db_mod == "postgresql":
            self.prepareDatabasePostgresql()
        else:
            raise "Unknown db_mod", self.db_mod

    def prepareDatabaseMysql(self):
        import MySQLdb as db
        self.db = db
        assert self.db_connect

    def prepareDatabasePostgresql(self):
        import psycopg as db
        self.db = db
        assert self.db_connect

    def prepareDatabaseSqlite(self):
        # FIXME: Should also do all the tests with mysql
        import tempfile
        try:
            from pysqlite2 import dbapi2 as db
        except ImportError, e:
            print >>sys.stderr, "Need pysqlite2 for db testing"    
            sys.exit(2)
        self.db = db
        # Include db.PARSE_DECLTYPES to support boolean conversion
        self.db_connect = dict(database=tempfile.mktemp(),
                               detect_types=db.PARSE_DECLTYPES)
 
    def prepareTables(self):
        # First connect raw
        if isinstance(self.db_connect, dict):
            db = self.db.connect(**self.db_connect) 
        else:    
            db = self.db.connect(*self.db_connect) 
        if self.db_mod == "postgresql":
            db.autocommit(1)
        try:
            c = db.cursor()
            if "sqlite" in str(db).lower(): 
                # Ignore sync-checks for faster import
                c.execute("pragma synchronous = off")
            # Find our root by inspecting our own module
            import testforgetsql2
            root = os.path.dirname(testforgetsql2.__file__)
            file = os.path.join(root, "test-data.sql")
            sql = codecs.open(file, encoding="utf8").read()

            # DROP TABLE
            if self.db_mod == "mysql":
                for table in ("county", "municipal", "postal", "insertion", 
                              "shop", "changed"):
                    c.execute("DROP TABLE IF EXISTS %s" % table)
            elif self.db_mod == "postgresql":
                c.execute("""SELECT tablename FROM pg_catalog.pg_tables 
                                 WHERE schemaname=pg_catalog.current_schema()""")        
                existing = c.fetchall()
                for table in ("county", "municipal", "postal", "insertion", 
                              "shop", "changed"):
                    if (table,) in existing:
                        c.execute("DROP TABLE %s" % table)                  
            elif self.db_mod == "sqlite":            
                # No need to drop tables in sqlite, we blank out the db each
                # time
                pass
            else:
                raise "Unknown db", self.db_mod

            # CREATE TABLE // EXECUTE
            if self.db_mod == "sqlite":
                # We have to fake since sqlite does not support the
                # fancy "bool" type.
                sql = sql.replace("FALSE", "0")
                sql = sql.replace("TRUE", "1")
                c.executescript(sql)
            elif self.db_mod in ("mysql", "postgresql"):
                for statement in sql.split(";"):
                    if not statement.strip():
                        continue # Skip empty lines
                    c.execute(statement.encode("utf8"))

            # Create database specific table "insertion"
            if self.db_mod == "sqlite":
                # This one is seperate because of "AUTOINCREMENT" vs "AUTO_INCREMENT"
                c.execute("""
                    CREATE TABLE insertion (
                      insertion_id INTEGER PRIMARY KEY AUTOINCREMENT,
                      value VARCHAR(15)
                    )""")
            elif self.db_mod == "mysql":                 
                c.execute("""
                    CREATE TABLE insertion (
                      insertion_id INTEGER PRIMARY KEY AUTO_INCREMENT,
                      value VARCHAR(15)
                    )""")
            elif self.db_mod == "postgresql":
                c.execute("""
                    CREATE TABLE insertion (
                      insertion_id SERIAL PRIMARY KEY,
                      value VARCHAR(15)
                    )""")
            else:
                raise "Unknown db", self.db_mod
            db.commit()    
        finally:
            db.rollback()         
            

class TestTestFramework(TestFramework):
    def testLog(self):
        logging.error("Hello")
        self.assertEqual(self.lastLog(), "ERROR: Hello\n")
        self.assertEqual(self.lastLog(), "")
        
    def testDatabase(self):
        self.assert_(os.path.exists, self.db)
        if isinstance(self.db_connect, dict):
            db = self.db.connect(**self.db_connect) 
        else:    
            db = self.db.connect(*self.db_connect) 
        try:
            c = db.cursor()
            # Check that data got imported
            c.execute("SELECT count(*) FROM county")
            self.assertEqual(c.fetchone(), (22,))
            c.execute("SELECT * FROM municipal WHERE municipal_id=1103")
            self.assertEqual(list(c.fetchall()), 
                            [(1103, "Stavanger", 11)])
            c.execute("SELECT * FROM postal WHERE postal_no=4042")
            # FIXME: BOOL with mysql might not equal False
            self.assertEqual(c.fetchone(),
                            (4042, "HAFRSFJORD", 1103, False))
            # Check if wtf-8 worked fine. Note that the line
            # -*- coding: utf-8 -*- must be present at the top of
            # this file for the u"Østfold" thingie to work
            c.execute("SELECT county_name FROM county WHERE county_id=1")
            a = c.fetchone()[0]
            if not isinstance(a, unicode):
                a = a.decode("utf8")
            self.assertEqual(a, u"Østfold")
        finally:
            db.rollback()

class TestDBConnect(TestFramework):

    def testConstructor(self):
        d = DBConnect(self.db, self.db_connect)
        self.assertEqual(d.module, self.db)
        self.assertEqual(d.connect_info, self.db_connect)
        self.assert_(d.connection)
        self.assert_(d.connection.cursor())
    
    def testCursor(self):
        cursor = self.Database._db.cursor()
        cursor.execute("SELECT 1+1")    
        self.assertEqual(cursor.fetchone(), (2,))
        self.assertEqual(self.lastLog(), "")
    
    def testCursorReconnect(self):
        d = self.Database()
        # Nasty!
        d._db.connection.close()
        # should reconnect 
        cursor = d._db.cursor()    
        cursor.execute("SELECT 1+1")    
        self.assertEqual(cursor.fetchone(), (2,))
        self.assert_(self.lastLog().startswith(
                "WARNING: Reconnecting database due to "))
    
    def testSameConnection(self):
        d1 = self.Database()     
        d2 = self.Database()
        class Subclass(self.Database):
            pass
        d3 = Subclass()
        self.assertEqual(d1._db, self.Database._db)
        self.assertEqual(d2._db, self.Database._db)
        self.assertEqual(d3._db, self.Database._db)
        d1._db.cursor()
        self.assertEqual(d1._db, self.Database._db)
        self.assertEqual(d2._db, self.Database._db)
        # OK.. and if we close/lose the connection, will we
        # also replace it all over the place?
        old_conn = id(d1._db.connection) 
        self.assertEqual(old_conn, id(d2._db.connection)) 
        d3._db.connection.close()
        d1._db.cursor()
        self.assert_(self.lastLog().startswith(
                "WARNING: Reconnecting database due to "))
        self.assertNotEqual(old_conn, id(d2._db.connection)) 
        self.assertEqual(d1._db.connection, 
                        self.Database._db.connection)
        self.assertEqual(d2._db.connection, 
                        self.Database._db.connection)
        self.assertEqual(d3._db.connection, 
                        self.Database._db.connection)


class TestDatabase(TestFramework):
    
    def testQuery(self):
        res = self.Database._query("SELECT 1+1 AS mysum")
        self.assertEqual(list(res), [{'mysum': 2}])
        res = self.Database._query("SELECT 1+1 AS mysum, 5+3 AS other")
        self.assertEqual(list(res), [{'mysum': 2, "other": 8}])

        res = self.Database._query("SELECT county_id FROM county "
                               "ORDER BY county_id")
        #  Norwegian counties are numbered 1 till 24, but not 13
        should_be = [{"county_id": x} for x in range(1,24) if x != 13]
        self.assertEqual(list(res), should_be)

    def testQueryOne(self):
        res = self.Database._query_one("SELECT 1+1 AS mysum")
        self.assertEqual(res, {'mysum': 2})
        res = self.Database._query_one("SELECT 1+1 AS mysum, 5+3 AS other")
        self.assertEqual(res, {'mysum': 2, "other": 8})

        res = self.Database._query_one("SELECT * FROM postal WHERE "
                                   "postal_no=%s" %
                                   self.Database._db.param, (4001,))
        self.assertEqual(res, {
            "postal_no": 4001,
            "postal_name": "STAVANGER",
            "municipal_id": 1103,
            "is_pobox": 1,
        })
        sql = "SELECT * FROM postal WHERE postal_no > %s"
        sql %= self.Database._db.param
        self.Database._query_one(sql, (4001,))
        #FIXME: Not %s in error
        self.assertEqual(self.lastLog(), 'WARNING: More than one hit '
            'returned for "%s" %% (4001,)\n' % sql)

class TestTableBuilder(TestFramework):
    def setUp(self):
        super(TestTableBuilder, self).setUp()
        self.builder = self.TableBuilder()
    
    def testAllTables(self):
        self.builder.all_tables()
        for table in ("postal", "municipal", "county"):
            self.assert_(table in self.builder.table_names) 
    
    def testBuildTable(self):
        t = self.builder.build_table("postal")
        self.assertEqual(t.__name__, "Postal")
        fields = Set(t._fields)
        self.assertEqual(fields, 
            Set(('is_pobox', 'municipal_id', 'postal_name', 'postal_no')))
        self.assertEqual(t._primary, ["postal_no"]) 
    
    def testBuildTables(self):
        self.builder.build_tables()      
        tables = Set(self.builder.tables)
        names = Set(self.builder.table_names)
        # Make sure all tables have been built
        self.assertEqual(tables, names)
    
    def testFindForeign(self):
        self.builder.build_tables()      
        Postal = self.builder.tables["postal"]
        Municipal = self.builder.tables["municipal"]
        County = self.builder.tables["county"]
        # Called by build_tables
        #self.builder.find_foreign(Postal)
        self.assertEqual(Postal._foreigns,
                         {"municipal_id": Municipal}) 
        # FIXME: Should test a table with several foreigns
        self.assertEqual(Set(Municipal._foreigns),
                         Set(("county_id",)))

class TestBuiltClass(TestFramework):
    def setUp(self):
        super(TestBuiltClass, self).setUp()
        self.builder = self.TableBuilder()
        self.builder.build_tables()

    def testLoad(self):
        Postal = self.builder.tables["postal"]
        # Fetch Stavanger 
        svg = Postal(postal_no=4001)
        self.assertEqual(svg.postal_no, 4001)
        self.assertEqual(svg.postal_name, "STAVANGER")
        self.assertEqual(svg.municipal_id, 1103)
        self.assertEqual(svg.is_pobox, 1)

    def testNotFound(self):
        Postal = self.builder.tables["postal"]
        self.assertRaises(NotFoundError,
                          Postal, postal_no=9999)

    def testPrimaryFails(self):
        Postal = self.builder.tables["postal"]
        self.assertRaises(ProgrammingError, 
                          Postal, postal_name="STAVANGER")
   
    def testUndo(self):
        Postal = self.builder.tables["postal"]
        # Fetch Stavanger 
        svg = Postal(postal_no=4001)
        svg.postal_name = "Fisk"
        self.assertEqual(svg.postal_name, "Fisk")
        svg.undo()
        self.assertEqual(svg.postal_name, "STAVANGER")

        new = Postal()
        new.postal_name = "Fjosk"
        self.assert_(hasattr(new, "postal_name"))
        new.undo()
        self.failIf(hasattr(new, "postal_name"))
   
    def testForeigns(self):
        Postal = self.builder.tables["postal"]
        # Fetch Stavanger 
        svg = Postal(postal_no=4001)
        municipal = svg.get_municipal()
        self.assertEqual(municipal.municipal_id, 1103)
        self.assertEqual(municipal.municipal_name, "Stavanger")
        self.assertEqual(municipal.county_id, 11)
        county = municipal.get_county()
        self.assertEqual(county.county_name, "Rogaland")

        # Temporary set to some other value so we can test
        # the generated set_method   
        municipal.county_id = 12
        self.assertEqual(municipal.county_id, 12)
        municipal.set_county(county)
        self.assertEqual(municipal.county_id, 11)
    
    def testForeignsNone(self):
        Postal = self.builder.tables["postal"]
        # Fetch Stavanger 
        svg = Postal(postal_no=4001)
        svg.set_municipal(None)
        self.assertEqual(svg.municipal_id, None)
        self.assertEqual(svg.get_municipal(), None)
    
    def testRepr(self):
        Postal = self.builder.tables["postal"]
        svg = Postal(postal_no=4001)
        self.assertEqual(repr(svg), "<Postal postal_no=4001>")
    
    def testChildren(self):
        Municipal = self.builder.tables["municipal"]
        municipal = Municipal(municipal_id=1103) # Stavanger
        postals = list(municipal.get_postals())
        # Should be something inbetween
        self.assert_(40 < len(postals) < 100)
  
    def testIterate(self):
        County = self.builder.tables["county"]
        # the county IDs are 1 till 24, but not 13
        x = range(1,24)
        for county in County:
            x.remove(county.county_id)
        self.assertEqual(x, [13])         
    
        all_counties = list(County)
        self.assertEqual(len(all_counties), 22)
    
    def testWhere(self):
        County = self.builder.tables["county"]      
        result = []
        for county in County.where("county_name=$name",
                                   name="Oslo"):
            result.append(county.county_id)                           
        # Only one row, and it should be county_id=3    
        self.assertEqual(result, [3])

    def testWhereKeywords(self):
        County = self.builder.tables["county"]      
        result = []
        for county in County.where(county_name="Oslo"):
            result.append(county.county_id)                           
        # Only one row, and it should be county_id=3    
        self.assertEqual(result, [3])

    def testGet(self):
        County = self.builder.tables["county"]      
        county = County.get("county_name=$name",
                            name="Oslo")
        self.assertEqual(county.county_id, 3)
        county = County.get(county_name="Oslo")
        self.assertEqual(county.county_id, 3)

        county = County.get("county_name=$name",
                            name="Not Found")
        self.assertEqual(county, None)
        county = County.get(county_name="Not Found")
        self.assertEqual(county, None)



class TestSave(TestFramework):
    def setUp(self):
        super(TestSave, self).setUp()
        self.builder = self.TableBuilder()
        self.builder.build_tables()
        self.Postal = self.builder.tables["postal"]
        self.Insertion = self.builder.tables["insertion"]
    
    def tearDown(self):
        # Roll back those stupid changes we might make
        self.builder._execute("UPDATE postal SET postal_name='STAVANGER'" 
                              " WHERE postal_no=4001")
        self.builder._execute("DELETE FROM postal WHERE postal_no=9998")
        self.builder._execute("DELETE FROM postal WHERE postal_no=9999")
        super(TestSave, self).tearDown()
    
    def testUpdate(self):
        # Fetch Stavanger 
        svg = self.Postal(postal_no=4001)
        self.assertEqual(svg.postal_name, "STAVANGER")
        svg.postal_name = "Nesten Stavanger"
        self.assertEqual(svg.save(), 1)
        # Reload as a new object and check that it was stored
        svg = self.Postal(postal_no=4001)
        self.assertEqual(svg.postal_name, "Nesten Stavanger")
   
    def testSave(self):
        p = self.Postal()
        p.postal_no = 9999
        p.postal_name = "Ingenmannsland"
        p.municipal_id = 1103
        self.assertEqual(p.save(), 1)
        p1 = self.Postal(postal_no=9999)
        self.assertEqual(p1.postal_name, "Ingenmannsland")
        self.assertEqual(p1.municipal_id, 1103)
        # Should get default values        
        self.assertEqual(p1.is_pobox, 0)
        
    def testSaveExists(self):
        p = self.Postal()
        p.postal_no = 4001
        p.postal_name = "Ingenmannsland"
        # Will collide with 4001 STAVANGER  
        self.assertRaises(p._db.module.Error, p.save)
    
    def testSaveAutoincrement(self):
        ins = self.Insertion()
        ins.value = "fish"
        self.assert_(not hasattr(ins, "insertion_id"))
        ins.save()
        self.assert_(ins.insertion_id > 0)

    def testUpdatePrimary(self):     
        p = self.Postal()
        p.postal_no = 9999
        p.postal_name = "Ingenmannsland"
        p.municipal_id = 1103
        self.assertEqual(p.save(), 1)
        p1 = self.Postal(postal_no=9999)
        p1.postal_no = 9998
        self.assertEqual(p1.save(), 1)
        p2 = self.Postal(postal_no=9998)

    def testUpdateWasDeleted(self):
        Postal = self.builder.tables["postal"]
        p = Postal()
        p.postal_no = 9999
        p.postal_name = "Ingenmannsland"
        p.municipal_id = 1103
        p.save()
        self.builder._execute("DELETE FROM postal WHERE postal_no=9999")
        # Should fail
        self.assertRaises(NotFoundError, p.save)

class TestGenerate(TestFramework):
    def testGenerate(self):
        db = generate(self.db, self.db_connect)
        self.assert_(hasattr(db, "Postal"))
        self.assert_(hasattr(db, "Municipal"))
        self.assert_(hasattr(db, "County"))

        svg = db.Postal(postal_no=4001)
        self.assertEqual(svg.postal_name, "STAVANGER")

        db.query_one("SELECT 1+1")
        db.query("SELECT * FROM postal")
        db.execute("DELETE FROM postal WHERE postal_no=9999")
        db.db.cursor()


def main():    
    if "--mysql" in sys.argv:
        TestFramework.db_mod = "mysql"
        pos = sys.argv.index("--mysql")
        db_args = sys.argv[pos+1]
        db_args = db_args.split(",")
        TestFramework.db_connect = db_args
        del sys.argv[pos+1]
        del sys.argv[pos]
    elif "--postgresql" in sys.argv:
        TestFramework.db_mod = "postgresql"
        pos = sys.argv.index("--postgresql")
        db_args = sys.argv[pos+1]
        TestFramework.db_connect = [db_args]
        del sys.argv[pos+1]
        del sys.argv[pos]
    unittest.main()

if __name__ == "__main__":
    main()

