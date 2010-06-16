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

"""ForgetSQL - SQL to object database wrapper.

NOTE: 
This version 2 of forgetSQL is NOT backwards compatible with
version 0.5.1. This is the reason it is called forgetsql2.py - so that
it can co-exist with the old version.

You should only need to use the generate() function to generate the
classes mapping to your tables, which will be subclasses of the 
Table class.


Example usage::

    import MySQLdb, forgetsql2
    # Connect to MySQLdb using keyword parameters
    db = forgetsql2.generate(MySQLdb, {db='fish'})

    # Iterate through generated class from the table "postal"
    for postal in db.Postal:
        # Print normal fields
        print postal.postal_no, postal.postal_name, postal.municipal_id
        # Follow the foreign key municipal_id to retrieve the entry
        # from the Municipal class
        municipal = postal.get_municipal()    
        print municipal.municipal_name
        
    # Retrieve by primary key
    rogaland = db.County(county_id=11)    
    # Iterate over municipals that have foreign keys to rogaland
    for municipal in rogaland.get_municipals():
        print municipal.municipal_name
   
"""


import sys
import os
import types
import StringIO
import logging
from sets import Set
from itertools import izip, count
import re 
try:
    import threading
except ImportError:
    threading = None    

from doc_exception import DocstringException, ProgrammingError

# Valid column names for WHERE sentences
_col_pat = re.compile(r"\$([a-zA-Z][a-zA-Z0-9_-]*)")

def _sql_bool(value):
    """Convert SQL bool value to Python True/False"""
    if isinstance(value, bool): 
        return value
    value = str(value)
    value = value.lower()
    if value in ("t", "true", "1"):
        return True
    elif value in ("f", "false", "0"):
        return False
    else:
        raise TypeError, value

class error(DocstringException):
    """Generic table error"""

class NotFoundError(error):
    """Could not find"""

class PrimaryKeyError(error, ProgrammingError):
    """Missing/wrong primary keys"""

class UnsupportedDBError(error, ProgrammingError):    
    """Unsupported db module"""

class DBConnect(object):
    """Database connection.

    In addition to connecting to the database and providing cursors, this
    class will guess information such as the database type (mysql,
    postgresql, sqlite) and parameter style.
    """

    def __init__(self, module, connect_info):
        """Construct and initialize database connection.

        Parameters:
            module          
                a DB API 2.0 compilent database module object
            connect_info    
                connect info for module.connect()
                * If the parameter is a string it will be passed directly
                  to module.connect(connect_info).
                * If a tuple or a list, it will be passed as positional
                  arguments as module.connect(*connect_info)
                * If a dictionary, it will be passed as keyword arguments as
                  module.connect(**connect_info).
        """           
        # The actual DB module
        self.module = module
        # parameters for connecting
        self.connect_info = connect_info
        # connection object - made by connect()
        self.connection = None
        # db type, "mysql", "postgresql" or "sqlite" - determined by guess_db_info()
        self.type = None
        # parameter style, "?" or "%s" - determined by guess_db_info()
        self.param = None
        # Connect to the database
        self.connect()
    
    def _set_connection(self, connection):
        """Set the database connection.
        The connection is as returned by self.module.connect().
        
        If the current database module is not threadsafe on connection
        level, each thread will require a separate connection. This
        property ensures this feature.
        """
        
        if self.module.threadsafety < 2 and threading: 
            # Not thread safe on connection level, store the connection
            # in the current thread
            name = "forgetsql_conn_%s" % id(self)
            setattr(threading.currentThread(), name, connection)
        else:
            # store normally
            self._connection = connection            
    def _get_connection(self):
        if self.module.threadsafety < 2 and threading: 
            name = "forgetsql_conn_%s" % id(self)
            return getattr(threading.currentThread(), name, None)
        else:
            return self._connection
    connection = property(_get_connection, _set_connection)
            
    
    def connect(self):
        """Connect to the database.
        
        The connection object as returned by self.module.connect()
        is stored in self.connection. In addition, guess_db_info() is
        called after connecting.
        """
        if isinstance(self.connect_info, dict):
            # dict etc, kwargs style, connect(a=x1, b=x2)
            connection = self.module.connect(**self.connect_info)
        elif isinstance(self.connect_info, (tuple, list)):
            # tuple etc, args style  connect(a, b)
            connection = self.module.connect(*self.connect_info)
        else:
            # probably strings (URIs etc.)   connect(a)
            connection = self.module.connect(self.connect_info)    
        self.connection = connection    
        # DB info should not change between connects, but you never know
        self.guess_db_info()
        if self.type == "postgresql":
            # FIXME: AVOID AUTOCOMMIT!! 
            #connection.autocommit(1)
            pass
        self.prepare_db_types() 
     
    def prepare_db_types(self):
        """Prepare type casting in database results.
        
        Currently this makes sure that booleans are returned as real
        True/False objects.
        """  
        if self.type == "postgresql":
            if not "psycopg" in str(self.module):
                return
            c = self.cursor()
            c.execute("SELECT TRUE")
            if isinstance(c.fetchone()[0], bool):
                # Already registered
                return
            bool_type_oid = c.description[0][1]        
            bool_type = self.module.new_type((bool_type_oid,), 
                                         "BOOLEAN", 
                                         _sql_bool)
            self.module.register_type(bool_type) 
        if self.type == "sqlite" and "detect_types" in str(self.connect_info):
            # Add detect_types=sqlite.PARSE_DECLTYPES to connect info
            # for type conversion
            self.module.converters["bool"] = _sql_bool
     
    def guess_db_info(self):      
        """Guess database type and parameter style.
        
        self.type is determined to "mysql", "postgresql" or "sqlite"
        
        self.param is "?" or "%s" and denotes how query parameters to be
        expanded by cursor.execute(sql, params) is to be expressed in
        the sql.
        """
        try:     
            db_name = self.module.__name__.lower()    
        except AttributeError:
            db_name = str(self.module)
        if "mysql" in db_name:
            self.type = "mysql"      
        elif "sqlite" in db_name:
            self.type = "sqlite"     
        elif "psycopg" in db_name:
            self.type = "postgresql"    
        else:
            raise UnsupportedDBError, self.module
        if self.module.paramstyle == "qmark":
            self.param = "?"
            # FIXME: Should support named parameters $fish
        elif self.module.paramstyle == "format":
            self.param = "%s"
        elif self.module.paramstyle == "pyformat":
            # FIXME: Should support named parameters %(fish)s 
            self.param = "%s"
        else:    
            raise UnsupportedDBError, "paramstyle=%s" % self.module.paramstyle

    def cursor(self):
        """Fetch a cursor. Reconnect if needed."""
        if not self.connection:
            self.connect()
        try:
            c = self.connection.cursor()    
            # Connection errors won't show until we query something
            c.execute("SELECT 1+1")
            assert c.fetchone() == (2,)
            return c
        except self.module.Error, e:
            # Usually because of timeouts
            logging.warning("Reconnecting database due to %s",
                            e.__class__)
            # Reconnect and try again
            self.connect()
            c = self.connection.cursor()    
            c.execute("SELECT 1+1")
            assert c.fetchone() == (2,)
            return c
    
    def close(self):
        """Close the connection. 
        Any pending transactions will be rolled back.""" 
        if self.connection:
            self.connection.close()           
            self.connection = None    

class Database(object):
    """Base class for objects that uses the database. 
    
    Provides class methods for executing and querying SQL against the
    database.
    
    Note that the _db *class attribute* must have been set to a
    DBConnect instance before any of these methods can be used. Normally
    this is done by subclassing::

        class MyDatabase(Database):
            _db = DBConnect(db_module, connect_info)
    """
    # a DBConnect instance, which holds the actual connection, and more
    # important to us, the cursor() method.
    _db = None
    
    def _execute(cls, sql, parameters={}):
        """Execute SQL and return cursor"""
        cursor = cls._db.cursor()
        if cls._db.type == "mysql" or cls._db.type == "postgresql":
            # FIXME: Avoid regex-hack-fixing this param crap
            sql = _col_pat.sub(r"%(\1)s", sql)
        elif cls._db.type == "sqlite":
            pass
        else:
            raise UnsupportedDBError, cls._db.type
        logging.debug("%s %r", sql, parameters)
        cursor.execute(sql, parameters)
        return cursor
    _execute = classmethod(_execute)      
    
    def _iter_cursor(cls, cursor):
        """Provide iterator of cursor results.

        If the cursor does provide an iterator, provide that.
        Otherwise, return a generator that yield rows by using repeted
        calls to fetchmany().
        """
        try:
            return iter(cursor)
        except TypeError:
            def iterator():
                rows = cursor.fetchmany()
                while rows:
                    for row in rows:
                        yield row
                    rows = cursor.fetchmany()
            return iterator() 
                
    _iter_cursor = classmethod(_iter_cursor)
    
    def _query(cls, sql, parameters={}):
        """Execute SQL and yield dictionaries.

        The optional parameters argument can be used for variable
        expansions as explained in PEP 249 .execute().
        """
        cursor = cls._execute(sql, parameters)
        if not cursor.description:
            # Should only happen when there is no data to yield
            for row in cls._iter_cursor(cursor):
                # so if there *is* something anyway, raise an exception
                raise ProgrammingError, \
                    "Could not find description for sql", sql
            return
        fields = [d[0] for d in cursor.description]
        for row in cls._iter_cursor(cursor):
            yield dict(izip(fields, row))
    _query = classmethod(_query)         
         

    def _query_one(cls, sql, parameters={}):
        """Execute SQL as with _query(), but return first row.

        Return None if no rows were returned.  If more than one row is
        returned, a warning is logged, and only the first row is
        returned.
        """
        res = cls._query(sql, parameters)
        try:
            result = res.next()
        except StopIteration:
            return None    
        # Log if there is more than one    
        try:
            res.next()    
        except StopIteration:
            pass
        else:        
            logging.warning('More than one hit returned for "%s" %% %s',
                            sql, parameters)
        return result
    _query_one = classmethod(_query_one)
        
class metaclass_table(type):
    """Metaclass for Table allowing iteration.
    
    Example:

        # Assume generated class County
        for county in County:
            print county.county_name
    """
    def __iter__(cls):
        for elem in cls.where():
            yield elem

class Table(Database):
    """Representation of a table.
    
    Instances of this class represent a row in the table, and can be
    retrieved in several ways. In the examples below, the subclass Thing
    is assumed.

    - By calling the constructor with a primary key::

        # thing with primary key thing_id=1447
        thing = Thing(thing_id=1447)

    - By iterating over the the class::

        # all things
        for thing in Thing:
            pass    

    - By iterating over a filtered subset using SQL where::

        # All things with thing.value > 13
        for thing in Thing.where("value > $value", value=13):
            pass
    
    - By following a foreign key from another table::

        # the thing with thing_id = person.thing_id
        thing = person.get_thing()
    
    - By iterating over rows who have a foreign key to another table::
        
        # all things which have thing.box_id = box.box_id
        for thing in box.get_things():
            pass
    """
    # To get __iter__ behavour 
    __metaclass__ = metaclass_table
    
    def __init__(self, _db_row=None, **primary):
        """Instanciate a new or existing database row.

        If no parameters are given, a new, blank instance is created,
        which will be INSERT-ed when save() is called.

        Else, if keyword arguments are supplied, they must match the
        primary keys in _primary, and will be used for loading an
        existing row. In such a case, the instance can be UPDATE-d by
        calling save() - or restored to the database values by calling
        undo().

        Mostly for internal usage, if _db_row is provided, it is assumed
        to be a dictionary of row values as returned from cls.query(),
        from which the object values will be loaded instead.
        """
        if primary and Set(primary) != Set(self._primary):
            raise PrimaryKeyError, primary
        if not (primary or _db_row):
            # Don't fetch anything, we're new and blank 
            return
        self._load(_db_row=_db_row, **primary)

    def where(cls, where=None, **parameters):
        """Yield all instances limited by ``where`` clause.

        Use $field in where clause and supply values in the optional
        dict parameter ``**parameters`` or as keyword arguments.
        Parameters will be properly escaped.

        If you supply keyword parameters, but not a where-clause, a
        where clause "WHERE x=$x AND y=$y" will be generated from the
        keywords.

        Example::
            
            # Assume generated class County
            for county in County.where("county_name=$name"
                                       name="Oslo"):
                print county                            

            for county in County.where(county_name="Oslo"):
                print county                            

        """
        sql = "SELECT * FROM %s" % cls._table_name
        if where:
            sql += " WHERE %s" % where
        if where is None and parameters:
            sql += " WHERE "    
            sql += " AND ".join(["%s=$%s" % (key, key) for key in parameters])
        for row in cls._query(sql, parameters):
            yield cls(_db_row=row)
    where = classmethod(where)         
    
    def get(cls, where=None, **parameters):
        """Like where(), but returns first instance or None."""
        for elem in cls.where(where, **parameters):
            return elem
        return None    
    get = classmethod(get)    
    
    def _where_primary(cls):
        """Get WHERE part for primary key.
        
        Note that the fields are prefixed with p__ to avoid
        mixup when used by UPDATE.
        """
        where = ["%s=$p__%s" % (key, key) for key in cls._primary]
        where = " AND ".join(where)
        return where
    _where_primary = classmethod(_where_primary)     
        
    def _load(self, _db_row=None, reload=False, **primary):
        """Load from database.

        If _db_row is supplied, it is assumed to be a dict as returned
        by _query, and the instance will be loaded without any new
        database calls.

        If reload is True, the saved primary keys in the attribute
        _primary_values will be used to reload all attributes.

        Else, if keyword arguments are supplied, they must match the
        primary keys in _primary, and will be used for loading a unique
        row.
        """ 
        
        if reload:
            params = self._primary_values
        elif _db_row:    
            params = None    
        elif primary:
            # Convert to p__ style keynames as required by
            # _where_primary
            params = dict([("p__"+field, value)
                           for field,value in primary.items()])
        else:
            raise ProgrammingError, "Missing parameter for _load()"     
        if not _db_row:
            # Fetch from database
            where = self._where_primary()
            sql = "SELECT * FROM %s WHERE %s" % (
                  self._table_name, where)   
            _db_row = self._query_one(sql, params)
            if not _db_row:
                raise NotFoundError, primary
            
        for field in self._fields:
            setattr(self, field, _db_row[field])    
        self._save_primary()
                

    def __repr__(self):
        primaries = ["%s=%s" % (key, getattr(self, key, "?"))
                     for key in self._primary]
        primaries = " ".join(primaries)                 
        return "<%s %s>" % (self.__class__.__name__, primaries)
    
    def undo(self):
        """Undo changed attributes.
        
        If this instance represent an existing row, the instance will be
        reloaded to the *current* database values.

        If this is a new instance not yet inserted to the database, 
        all database related attributes are removed.
        """
        if hasattr(self, "_primary_values"):
            self._load(reload=True)
        else:    
            for field in self._fields:
                try:
                    delattr(self, field)
                except AttributeError:
                    continue    
    
    def save(self):
        """Save changes to database.

        Return number of rows updated/inserted, normally 1. 
        (This is database dependant, sqlite will often return 0)"""
        params = {}
        if hasattr(self, "_primary_values"):
            # it's an UPDATE.
            fields = []
            for field in self._fields:
                try:
                    params[field] = getattr(self, field)
                except AttributeError:
                    # Blank values we assume will get default values
                    # from the database.. for instance "current date"
                    # etc.
                    continue
                else:
                    fields.append("%s=$%s" % (field, field))
            fields = ",".join(fields)
        
            params.update(self._primary_values)
            sql = "UPDATE %s SET %s WHERE %s" % (
                  self._table_name, fields, self._where_primary())
        else:
            # it's an INSERT
            fields = []
            values = []
            for field in self._fields:
                try:
                    params[field] = getattr(self, field)
                except AttributeError:
                    continue
                else:
                    fields.append(field)
                    values.append("$%s" % field)
            fields = ",".join(fields)        
            values = ",".join(values)        
            sql = "INSERT INTO %s(%s) VALUES (%s)" % (
                   self._table_name, fields, values)
        curs = self._execute(sql, params)
        
        if len(self._primary) == 1 and \
            getattr(self, self._primary[0], None) is None:
            # It's one of those fetch-id-after-inserting-databases 
            # NOTE: We cannot assume this for multi-valued primary
            # keys, as it is often legal to have a primary key with one
            # of the values NULL. 

            if self._db.type == "mysql":
                id = self._query_one("SELECT LAST_INSERT_ID() AS id")["id"]
            elif self._db.type == "sqlite":     
                id = self._query_one("SELECT last_insert_rowid() AS id")["id"]
            elif self._db.type == "postgresql":     
                # Assume SERIAL and auto generated sequence name 
                # table_field_seq
                seq_name = "%s_%s_seq" % (self._table_name, self._primary[0])
                id = self._query_one("SELECT currval('%s') AS id" % seq_name)["id"]
            else:
                # Other databases would probably use sequences BEFORE
                # inserting.
                raise UnsupportedDBError, self._db.type
            setattr(self, self._primary[0], id) 

        # Set/Update _primary_values so we can do a reload
        self._save_primary()
        self._load(reload=True)
        return curs.rowcount 

    def _save_primary(self):      
        """Store a copy of current primary keys.
        
        The attribute _primary_values will be updated with the current
        primary key values. These will be used for reload-ing and
        updates in case the normal attributes are changed.

        The attributes are saved as a dictionary with p__fieldname as
        keys, to match the WHERE clause generated by _where_primary().
        """
        primary = dict([("p__"+field, getattr(self,field))
                       for field in self._primary])
        self._primary_values = primary

    # Will be used by all generated _get_something() methods
    def _get_foreign(self, _foreign):
        """Fetch foreign key as instance"""
        table = self._foreigns[_foreign]
        if getattr(self, _foreign) is None:
            return None
        if isinstance(_foreign, unicode):
            # We can't (shouldn't) have unicode kw args!
            _foreign = _foreign.encode("ascii", "ignore")
        primary = {_foreign: getattr(self, _foreign)}
        return table(**primary)

    # Will be used by all generated _set_something() methods
    def _set_foreign(self, value, _foreign):
        """Set foreign key by instance"""
        table = self._foreigns[_foreign]
        if not isinstance(value, table) and value is not None:
            raise ProgrammingError, "Unsupported foreign type %s" % value    
        if value is None:
            setattr(self, _foreign, None)
        else:   
            # Fetch the foreign primary key 
            primary = getattr(value, _foreign)
            setattr(self, _foreign, primary)

    # Will be used by all generated _get_somethings() methods
    def _get_children(self, _Child, _child_field, _my_field):
        """Yield all children as instances. 
        
        A child is someone whose foreign keys point to us.
        """
        sql = "SELECT * FROM %s WHERE %s=%s" % (
              _Child._table_name, _child_field, self._db.param)
        params = (getattr(self, _my_field), )
        for row in self._query(sql, params):
            yield _Child(_db_row=row)


class TableBuilder(Database):
    """Build Table subclasses by investigating database.
    
    As with the Database class, remember to subclass in the DBConn
    instance in the _db class attribute.
    
    The table builder will list all tables in the connected database and
    generate Table instances, one for each table. 

    In addition to figuring out column names and primary keys, the table
    builder will also guess foreign keys and add methods like
    get_something(), set_something() and get_somethings().
    """
    def __init__(self, TableBase=Table):
        """Build tables using provided TableBase as a base class.

        If the parameter TableBase is not provided, Table will be used
        as a superclass.

        If the base table does not have a valid _db attribute (ie. a
        DBConn connetion), it will be inherited from the TableBuilder
        class.
        """
        # Base of built classes 
        if not TableBase._db:
            class TableBase(TableBase):
                _db = self._db
        self.TableBase = TableBase

    def all_tables(self):
        """Find all table names in active database.
        
        Depending on the database type, this function will find the list
        of all table names and store them in self.table_names.

        Table names ending in _seq are not included, but are placed in
        self.sequences instead.
        """
        c = self._db.cursor()
        if self._db.type == "mysql":
            c.execute("SHOW TABLES")
        elif self._db.type == "sqlite":     
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        elif self._db.type == "postgresql":
            # FIXME: Support other schemas and tablespaces, views, etc.
            c.execute("""SELECT tablename FROM pg_catalog.pg_tables 
                     WHERE schemaname=pg_catalog.current_schema()""")
        else: 
            raise UnsupportedDBError, self._db.type
        tables = [t for (t,) in c.fetchall()]    
        self.table_names = [t for t in tables if not t.endswith("_seq")]
        self.sequences = [t for t in tables if t.endswith("_seq")]

    def build_class(self, table_name):
        """Build the (empty) subclass for table_name.

        The generated class will have a Pythonish version of table_name
        as the official class name. For instance, the class for my_table
        will be MyTable.
        """
        class table(self.TableBase):
            _table_name = table_name
            _children = []
        if isinstance(table_name, unicode):
            table_name = table_name.encode("ascii", "ignore")
        table.__name__ = table_name.capitalize()    
        return table

    def add_fields(self, table):
        """Find the fields and primary keys"""
        table_name = table._table_name
        fields = {}
        primary = []
        c = self._db.cursor()
        if self._db.type == "mysql":
            c.execute("DESCRIBE %s" % table_name)
            for field, type, is_null, key, default, extra in c.fetchall():
                fields[field] = type
                if key == "PRI": 
                    primary.append(field)
        elif self._db.type == "sqlite":
            c.execute("PRAGMA table_info(%s)" % table_name)     
            for cid, field, type, is_null, default, key in c.fetchall():
                fields[field] = type
                if key:
                    primary.append(field)    
        elif self._db.type == "postgresql":
            # We could do it through pg_.* but it is a bit complicated
            # compared to this approach
            c.execute("SELECT * FROM %s LIMIT 0" % table_name)
            for field, _a,_b,_c,_d,_e,_f in c.description:
                fields[field] = _a  # type-oid ?
            # find primary keys will have to do it the pg_ way :/
            c.execute("""SELECT index.indexrelid 
                    FROM pg_catalog.pg_index index
                    JOIN pg_catalog.pg_class i ON (index.indexrelid = i.oid) 
                    JOIN pg_catalog.pg_class u ON (index.indrelid = u.oid)
                    WHERE index.indisprimary AND u.relname = %s
                    """, (table_name,))
            index_oid = c.fetchone()          
            if index_oid:
                for n in count(1):
                    c.execute("SELECT pg_get_indexdef(%s, %s, FALSE)",
                              (index_oid[0], n))
                    field = c.fetchone()[0]
                    if not field:
                        break
                    primary.append(field)
        else:    
            raise UnsupportedDBError, self._db.type

        # If we don't have a primary, we will have to
        # match on ALL fields for UPDATE/DELETE.
        if not primary:
            primary = fields.keys()
        table._fields = fields    
        table._primary = primary
    
    def find_foreign(self, table): 
        """Guess foreign keys. 

        Basically a field fish_id is assumed a foreign key for the table
        fish - if it exists.

        Note that build_table() must have been called on all tables
        first in order to compare foreign keys with primary keys.
        """
        table._foreigns = {}
        for field in table._fields.keys():
            if not field.endswith("_id"):
                continue
            # Chop of _id
            table_name = field[:-3]
            if table_name == table._table_name:
                continue
            if not table_name in self.table_names:
                continue    
            foreign = self.tables[table_name]      
            if not field in foreign._primary:
                continue
            table._foreigns[field] = foreign
            # And add a reverse mapping 
            # his_table, his_field, my_field
            foreign._children.append((table, field, field))
    
    def build_table(self, table_name):
        """Build a table class and find all fields.
        """
        table = self.build_class(table_name)
        self.add_fields(table)    
        return table
    
    def generate_foreign_methods(self, table):
        """Generate get/set-methods for foreign keys.
        
        The method names will be named like get_other() for the
        table class Other.
        """
        for foreign,Foreign in table._foreigns.items():
            get_name = "get_" + Foreign.__name__.lower()
            def _get_foreign(self, _foreign=foreign):
                return super(table, self)._get_foreign(_foreign)
            if sys.version_info > (2,4,None,None,None):
                _get_foreign.__name__ = get_name 
            setattr(table, get_name, _get_foreign)    

            set_name = "set_" + Foreign.__name__.lower()
            def _set_foreign(self, value, _foreign=foreign):
                super(table, self)._set_foreign(value, _foreign)
            if sys.version_info > (2,4,None,None,None):
                _set_foreign.__name__ = set_name 
            setattr(table, set_name, _set_foreign)    
   
    def generate_children_methods(self, table):
        """Generate get-methods for retrieving foreign key children.

        The method names will be named like get_others() for the table
        class Other.
        """
        for (Child, child_field, my_field) in table._children:
            # transform name, ie. "car" -> "get_cars"
            child_name = "get_" + Child.__name__.lower() + "s"
            def _get_children(self, _Child=Child,
                             _child_field=child_field,
                             _my_field=my_field):
                return super(table, self)._get_children(_Child,
                              _child_field, _my_field)
            if sys.version_info > (2,4,None,None,None):
                _get_children.__name__ = child_name 
            setattr(table, child_name, _get_children)

    def build_tables(self):
        """Fully generate the list of table classes.
        
        This is the main method which will retrieve all tables, generate
        the Table subclasses and finally generate foreign key methods.

        The generated table classes will be available in self.tables
        using the SQL table name as a key.
        """
        self.all_tables()
        self.tables = {}
        for table_name in self.table_names:     
            table = self.build_table(table_name)
            self.tables[table_name] = table
        for table in self.tables.values():
            self.find_foreign(table)
        for table in self.tables.values():
            self.generate_foreign_methods(table)    
            self.generate_children_methods(table)    


def generate(db_module, connect_info, globals=None):
    """Generate forgetSQL classes and return as a module object.

    The db_module can be MySQLdb or sqlite2. This parameter must be
    the actual module object, imported by the caller.

    The connect_info is provided to db_module.connect() and can be
      - a dictionary (sent as keyword arguments)
      - a tuple/list (sent as positional arguments)
      - a string (sent as 1st argument)
    
    If the optional parameter ''globals'' is provided, instead of
    generating a new module, generated classes will be inserted into 
    the namespace dictionary, usually as provided by globals().

    Example::

        # simple usage
        import MySQLdb, forgetsql2
        db = forgetsql2.generate(MySQLdb, {db='fish'})
        for postal in db.Postal:
            print postal.postal_no, postal.postal_name
        
        # export symbols to this module
        import MySQLdb, forgetsql2
        forgetsql2.generate(MySQLdb, {db='fish'}, globals())
        for postal in Postal:
            print postal.postal_no, postal.postal_name
    
    The second variant can be used in a seperate module for bigger
    projects, for instance database.py. Other modules can then do::

        import database
        for postal in database.Postal:
            print postal.postal_no
    """
    # subclass in the _db connection
    class TB(TableBuilder):
        _db = DBConnect(db_module, connect_info)
    builder = TB()
    builder.build_tables()    
    module = None
    if globals is None:
        # Generate a module object. Note that it is not adviced to add
        # this module object to sys.modules. Even though that would make
        # "import mymodule" work in other modules, it would only work
        # after generate() has been called. In a complicated module
        # hierarchy such an assumption is not always easy to ensure.
        module = types.ModuleType("forgetsql2.generated")
        globals = module.__dict__
    for table in builder.tables.values():
        globals[table.__name__] = table
    # And export general purpose database methods    
    globals['execute'] = TB._execute    
    globals['query'] = TB._query    
    globals['query_one'] = TB._query_one    
    globals['db'] = TB._db
    return module     
    
