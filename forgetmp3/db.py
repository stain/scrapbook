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
"""Database bindings for forgetMP3.

Uses forgetSQL2 - available from http://soiland.no/i/src/forgetsql2/
"""



# FIXME: Should select db module by config file
from pysqlite2 import dbapi2 as sqlite
import forgetsql2
import utils
from doc_exception import DocstringException

class IncompatibleDatabaseException(DocstringException):
    """Incompatible database format"""

def _generate():
    _args = {"database": utils.db_name(), 
             # uncomment for autocommit, which is really slow
             #"isolation_level": None,
             # to get datetime types 
             "detect_types": sqlite.PARSE_DECLTYPES
            }
    # Export to module name space all Table classes, and execute/query
    # functions
    forgetsql2.generate(sqlite, _args, globals())

def _upgrade_tables():
    if meta.version < "0.5":
        raise IncompatibleDatabaseException, meta.version
    # Reserved for future work, to do table inserts, modifications, etc.    
    if meta.version < "0.61":
        execute("""CREATE TABLE term (
                    song_id INTEGER NOT NULL,
                    term VARCHAR(254),
                    PRIMARY KEY (song_id, term)
                   )""")
    if meta.version < "0.62":
        execute("""ALTER TABLE songinfo RENAME TO songinfo_old
                """)
        execute("""CREATE TABLE songinfo (
                song_id INTEGER NOT NULL PRIMARY KEY,
                derived timestamp NOT NULL,
                artist VARCHAR(254),
                title VARCHAR(254),
                album VARCHAR(254),
                genre VARCHAR(254),
                track INTEGER,
                track_total INTEGER,
                disc INTEGER,
                year INTEGER
               )""")
        execute("""INSERT INTO songinfo 
        (song_id, derived, artist, title, album, genre, track, disc, year) 
        SELECT song_id, derived, artist, title, album, genre, track, disc, year
        FROM songinfo_old""")
        execute("""DROP TABLE songinfo_old""")
        

    # And finally, mark database as most recent version 
    meta.version = utils.VERSION
    meta.save()
    commit()

def _build_tables():
    # Meta-info on the database.
    execute("""CREATE TABLE meta (
                meta_id INTEGER NOT NULL PRIMARY KEY,
                version VARCHAR(64)
               )""") 
    execute("INSERT INTO meta(meta_id, version) VALUES(1, $version)", 
            {"version":utils.VERSION})
    # A folder is a repository of songs that share a common 
    # base directory. This directory can be managed by forgetMP3
    # ("managed") or by the user ("not managed")
    execute("""CREATE TABLE folder (
                folder_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,  
                path VARCHAR(255) NOT NULL,
                managed BOOL NOT NULL
               )""")

    # A song belongs to a base folder, with a relatative pathname that
    # may and may not include intermediate directories.
    # 
    # When the file has been examined, information like size (in bytes),
    # last modified date and (if in a non-managed folder) md5 hash is
    # extracted so that the file might be recognized if renamed or
    # updated. In addition, song-specific information like format
    # ("ogg", "mp3", "aac", etc) and length in seconds is extracted.
    execute("""CREATE TABLE song (
                song_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                folder_id INTEGER NOT NULL,
                added timestamp,
                scanned timestamp,
                path VARCHAR(255) NOT NULL,
                size INTEGER,
                mtime integer,
                ctime integer,
                md5 VARCHAR(32),
                format VARCHAR(20),
                length INTEGER
               )""")
    # Actual id3 tags as read from file at the time song.scanned
    # If the song is not in id3, or the song.file_date is later than
    # song.scanned, it is to be (re)examined.
    execute("""CREATE TABLE id3 (
                song_id INTEGER NOT NULL,
                field VARCHAR(4),
                value VARCHAR(1023), 
                PRIMARY KEY(song_id, field)
               )""")
    # Derived song information. This table is considered a "cache", 
    # if a song is not in songinfo yet, its id3 fields will have to be
    # examined. As for instance several id3 fields can be considered
    # "artist", this has to be derived from the different candidates
    execute("""CREATE TABLE songinfo (
                song_id INTEGER NOT NULL PRIMARY KEY,
                derived timestamp NOT NULL,
                artist VARCHAR(254),
                title VARCHAR(254),
                album VARCHAR(254),
                genre VARCHAR(254),
                track INTEGER,
                track_total INTEGER,
                disc INTEGER,
                year INTEGER
               )""")
    
    # Search terms for a song. Usually all words present in artist,
    # title, album and genre, but also comments, etc.
    execute("""CREATE TABLE term (
                song_id INTEGER NOT NULL,
                term VARCHAR(254),
                PRIMARY KEY (song_id, term)
               )""")
    
    commit()
    
def commit():
    db.connection.commit()
    
def rollback():        
    db.connection.rollback()

def _prepare():
    _generate()        
    # Build tables
    if not "Meta" in globals():
        # First time! build it
        _build_tables()
        _generate()        
    # Meta is a singleton, expose it and hide the class
    global meta, Meta
    meta = Meta.get()
    del Meta
    if meta.version < utils.VERSION:
        _upgrade_tables()
        _generate()        

_prepare()
