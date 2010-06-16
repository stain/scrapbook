
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
"""Music library functionallity for forgetMP3.
"""



import utils
import db
import commands
import os
import sys
import logging
import datetime
import time
from sets import Set
import re

def scan_dir(path=None, full_update=False):
    """Scan given dir (or default library) for music files.

    Songs are stored in the db using "song:/Some/Filename" as
    the key, and id3-info from id3v2() as the value.

    If full_update is set, all files will be scanned, otherwise 
    only previously unknown files will be scanned.
    """

    # FIXME: DIRTY SHIT!
    #db.execute("pragma synchronous = off")
        
    music = {}
    if not path:
        path = utils.config().get("music", "library")
    
    path = os.path.abspath(path)
    folder = db.Folder.get(path=path)
    if not folder:
        folder = db.Folder()
        folder.path = path
        folder.managed = False
        folder.save()
     
    print "Updating database for songs from", path 
    # To get relative pathnames in dirpath, which matches song.path
    old_dir = os.getcwd()
    try:
        os.chdir(path)
        for dirpath,dirnames,filenames in os.walk("."):
            sys.stdout.write(":")
            sys.stdout.flush()
            for file in filenames:
                ext = os.path.splitext(file)[1].lower()
                if not ext in (".mp3",):
                    # FIXME: support other file types 
                    continue
                filepath = os.path.join(dirpath, file)
                print "Checking", filepath
                stat = os.stat(filepath)
                # Only care about this part of stat
                song = db.Song.get(path=filepath, folder_id=folder.folder_id)
                if not song:
                    # New one
                    song = db.Song()
                    song.added = datetime.datetime.now()
                    song.path = filepath
                    song.set_folder(folder)
                    song.save()
                # New ones don't have mtime
                if not full_update and hasattr(song, "mtime"):
                    # Check if we should re-scan id3-info or not
                    if song.mtime == stat.st_mtime and \
                       song.ctime == stat.st_ctime and \
                       song.size == stat.st_size:
                        # OK, assume it has not changed
                        # (to force update anyway, set full_update)
                        continue
                        
                song.format = ext[1:] # ie "mp3"
                song.mtime = stat.st_mtime
                song.ctime = stat.st_ctime
                song.size = stat.st_size
                song.save()
                id3_info = id3v2(filepath)
                db.execute("DELETE FROM id3 WHERE song_id=$song_id",
                           {'song_id': song.song_id})
                for field,value in id3_info.items():
                    id3 = db.Id3()
                    id3.set_song(song)
                    id3.field = field
                    # FIXME: Support multi-values better than this
                    id3.value = "\n".join(value)
                    id3.save()
                song.scanned = datetime.datetime.now()
                song.save()

        db.commit()
    finally:
        # Just to be kind! (in case our argument is relative)
        os.chdir(old_dir)
        #db.execute("pragma synchronous = full")

def id3v2(file):
    """Scan music file for id3v2 information etc.

    Return dictionary of id3v2 keys with lists
    containing 1 or more entries.
    """ 
    info = {}
    file = commands.mkarg(file)
    id3 = commands.getoutput("id3v2 -l %s" % file)
    # FIXME: Is this true?
    id3 = id3.decode("utf8", "ignore")
    v2 = False
    for line in id3.split("\n"):
        # Skip lines before "id3v2 tag info for.."
        if not v2:
            v2 = line.startswith("id3v2 tag info for")
            # This will include id3v*1* info that stupid id3v2 prints
            logging.debug("id3v2: %s", line)
            continue    
        try:
            field, value = line.split(": ", 1)      
            # Strip away " (Title/songname/content description)"  
            field,field_desc = field.split(" ", 1)
        except ValueError:
            logging.warn("id3v2: %s", line)    
            continue
        if not field in info:
            info[field] = []
        info[field].append(value)
    return info      

def find_derived():
    for song in db.Song:
        info = db.Songinfo.get(song_id=song.song_id)
        if not info:
            info = db.Songinfo()
            info.set_song(song)
        info.derived = datetime.datetime.now()
        for id3 in song.get_id3s():
            # FIXME: TPE4 might override TPE1 value! Should prioritize 
            if id3.field in ("TP1", "TPE1", "TPE2", "TPE3", "TPE4"):      
                info.artist = id3.value
            elif id3.field in ("TAL", "TALB"):
                info.album = id3.value
            elif id3.field in ("TIT2", "TT2"):
                info.title = id3.value
            elif id3.field in ("TYER", "TYE"):
                try:
                    info.year = int(id3.value)
                except ValueError:
                    logging.warning("Could not set year %r for %s",
                                    id3.value, song)
                    info.year = None
            elif id3.field in ("TRK", "TRCK"):
                track = id3.value.split("/",1)[0]
                try:
                    info.track = int(track)
                except ValueError:
                    logging.warning("Could not set track %r for %s",
                                    track, song)
                    info.track = None
                if "/" in id3.value:    
                    track_total = id3.value.split("/", 1)[1]        
                    try:
                        info.track_total = int(track_total)
                    except ValueError:    
                        logging.warning("Could not set track_total %r for %s",
                                  track_total, song)
            elif id3.field in ("TCO", "TCON"):
                info.genre = id3.value        
            else:
                logging.info("Unknown id3 field %s=%r for %s",
                              id3.field, id3.value, song)
        info.save()
        # OK, now update the search terms for the song    
        db.execute("DELETE FROM term WHERE song_id=$song_id",
                   {"song_id": song.song_id})        
        terms = Set()
        for field in ("artist", "album", "title", "genre"):
            value = getattr(info, field)
            if not value:
                continue
            # FIXME: find a better way to find "words"
            terms.update(value.split(" []()./-\"'@#%=&?`+"))
        if u"" in terms:    
            terms.remove(u"")
        for term in terms:
            t = db.Term()
            t.set_song(song)
            t.term = term
            t.save()
    db.commit()

if __name__ == "__main__":
    if sys.argv[1:]:
        path = sys.argv[1]
    else:
        path = None    
    try:
        try:
            scan_dir(path)
            print ""
        except KeyboardInterrupt:
            print "Aborted"    
    finally:
        print "Goodbye"
