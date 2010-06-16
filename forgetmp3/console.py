#!/usr/bin/env python2.4
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
"""Curses console for forgetMP3.

"""




import time
import sys
import random
import os
import threading
import random
try:
    set()
except NameError:    
    # Python 2.3-compatibility
    from sets import Set as set

import urwid
import urwid.curses_display
import urwid.web_display

# and from forgetmp3, import
import utils
import music_db
import db
from osxplayer import OSXPlayer


UNSTABLE=0.1
MAX_UNSTABLE=0.2
SHOW_STATUS=1
MAX_SPEEDING=12
SPEED_DOWN=3
SPEED_UP=2

class Curses:
    palette = [
        ('body','default', 'default'),
        ('reveal focus','default', 'dark blue'),
        ('foot','dark cyan', 'dark blue', 'bold'),
        ('time','dark cyan', 'dark blue', 'bold'),
        ('head','dark cyan', 'dark blue', 'bold'),
        ('key','light cyan', 'dark blue', 'underline'),
        ('progress', 'dark cyan', 'black', 'bold'),
        ('progress_complete', 'black', 'dark cyan', 'bold'),
        ]

    searchbox = urwid.AttrWrap(urwid.Edit("Search: "), "head")
    header_text = ('head', [
     "%s v%s" % (utils.PROGRAM, utils.VERSION),
    ])
    footer_text = ('foot', "Loading database..")
    body = []

    def __init__(self):
        self.paused = False
        self.search_active = False
        self.search_thread = None
        self.last_status = 0
        self.speeding = False
        self.unstable = False
        self.player = OSXPlayer()
        self.current = None
        self.progress = urwid.ProgressBar("progress", "progress_complete", 0)
        self.header  = urwid.AttrWrap(urwid.Text(self.header_text),
                                      "head")
        self.header_columns = urwid.AttrWrap(urwid.Columns(
                     [self.header, self.searchbox]), "head")
        self.footer = urwid.AttrWrap(urwid.Text(self.footer_text),
                                     "foot")
        self.time = urwid.AttrWrap(urwid.Text("", align="right"), "time")
        self.listbox = urwid.ListBox(self.body)
        self.footer_columns = urwid.AttrWrap(urwid.Columns([self.footer, 
                                ('fixed', 10, self.progress),
                                    ('fixed', 8, self.time),
                                    ('fixed', 1, urwid.Text(""))]),
                                "foot")
        self.view = urwid.Frame(self.listbox, self.header_columns,
                                self.footer_columns)

        if urwid.web_display.is_web_request():
            self.ui =  urwid.web_display.Screen()
        else:
            self.ui = urwid.curses_display.Screen()
        self.ui.register_palette(self.palette)
        try:
            self.ui.run_wrapper(self.run)
        finally:
            try:
                self.player.stop()
            except:
                pass    
   
    def update_footer(self):
        # Show status messages for a little while first
        if self.current and self.player.complete < 1:
            self.progress.set_completion(self.player.complete * 100)     
            
            totsecs = int(self.player.played)
            hours = totsecs / 3600
            mins = totsecs / 60 % 60
            secs = totsecs % 60
            timestr = "%02d:%02d" % (mins, secs)
            if hours: # No leading 0 on hours
                timestr = "%s:%s" % (hours, timestr)
            self.time.set_text(timestr)    
        else:
            self.progress.set_completion(0)
            self.time.set_text("")
            # FIXME: This should not be the place to reset self.current !! 
            previous = self.current
            self.current = None
            # HACK: 
            # Try to find next song
            playlist = iter(self.body)
            for row in playlist:
                if hasattr(row, "song") and row.song == previous:
                    try:
                        self.play_song(playlist.next().song)
                    except StopIteration:
                        pass    
                    except AttributeError:
                        pass    
                    break
            
                
        if time.time() - self.last_status < SHOW_STATUS:
            return
        if not self.current:
            self.footer.set_text("Select a song to play")
        else:
            songinfo = self.current
            # Fixme: Should have a general method for getting the song
            # name
            self.footer.set_text(["Now playing: ",
                 (songinfo.artist or "").encode("utf8"),
                 "-", (songinfo.title or "").encode("utf8")])
              
    def search(self, terms):
        results = None
        for term in terms.split():
            songs = set()
            q_term = "%" + term + "%"
            for t in db.Term.where("term like $term", term=q_term):
                songinfo = db.Songinfo(song_id=t.song_id)
                songs.add(songinfo) 
            if results is None:
                results = songs
            else:
                results.intersection_update(songs)              
        # If there are no terms, music_listings() will be called, which
        # will give all songs        
        self.music_listing(results)
 
    def searcher(self):
        """Thread that updates searchbox by the current search"""
        old_terms = None
        while self.search_active:
            terms = self.searchbox.get_edit_text()
            if terms != old_terms:
                old_terms = terms
                self.search(terms)
            time.sleep(0.1)
   
    def music_listing(self, songs=None):
        rows = []
        if songs is None:
            songs = db.Songinfo
        # Note: Weights are RELATIVE    
        columns = [(40,"title"), (30,"artist"), (30,"album")]    
        for song in songs: 
            row = []
            for weight,col in columns:
                data = getattr(song, col) or ""
                #FIXME: Don't hardcode encoding
                edit = urwid.Edit(edit_text=data.encode("utf8"),
                                  edit_pos=0)
                # FIXME: Make readonly in a better way!
                # Ignore keypresses!
                edit.keypress = lambda (maxcol,),k: k
                row.append(('weight', weight, edit))
            urwidrow = urwid.Columns(row)    
            urwidrow.song = song
            rows.append(urwidrow)
        self.body[:] = rows
            
    def redraw(self):      
        canvas = self.view.render(self.size, focus=True)
        self.ui.draw_screen(self.size, canvas)
    
    def status(self, message):
        self.footer.set_text(message)
        self.last_status = time.time()
        self.redraw()
    
    def play_song(self, songinfo):
        self.paused = False
        song = songinfo.get_song()
        filename = os.path.join(song.get_folder().path, song.path)
        self.status("Loading song %s" % song.path.encode("utf8"))    
        self.current = songinfo
        self.player.open(filename)
        self.player.play_thread()
    
    def fast_forward(self):    
        self.paused = False
        self.status("Fast-forwarding")
        self.speeding = MAX_SPEEDING
        if self.player.speed < self.speeding:
            self.player.speed += random.uniform(0, SPEED_UP)
        self.status("Fast-forwarding %1.1f" % self.player.speed)
        #time.sleep(0.05)
    
    def unstable_tape(self):
        if self.paused:
            return
        change = random.uniform(-UNSTABLE, UNSTABLE)
        if self.player.speed > 1+MAX_UNSTABLE:
            change = -abs(change)
        elif self.player.speed < 1-MAX_UNSTABLE:
            change = abs(change)
        self.player.speed += change    
    
    def not_ff(self):
        if self.paused:
            return
        if self.player.speed > 1:
            self.player.speed -= random.uniform(0, SPEED_DOWN)
        if self.player.speed <= 1:
            self.player.speed = 1    
            self.speeding = False
        self.status("Resuming normal play %1.1f" % self.player.speed)
       
        
    def run(self):      
        # So that clock will look like it is going in correct speed
        self.ui.set_input_timeouts(0.2)
        self.size = self.ui.get_cols_rows()
        self.body.append(urwid.Text("Loading song database.."))
        self.redraw()
        self.music_listing()

        while True:
            keys = None
            while not keys:
                keys = self.ui.get_input()
                self.update_footer()    
                self.redraw()
                if not keys and self.speeding:
                    self.not_ff()
                if self.unstable:
                    self.unstable_tape()
            for k in keys:
                if k == "window resize":
                    self.size = self.ui.get_cols_rows()
                    continue    
                #elif      
                if self.view.focus_part == "header":
                    if k == "enter":
                        # Terminate searcher-thread
                        self.search_active = False
                        self.search_thread.join()
                        # But make sure we actually perform the search
                        # with the newest entries
                        terms = self.searchbox.get_edit_text()
                        self.search(terms)
                        self.view.set_focus("body")
                    k = self.view.keypress(self.size, k)
                    continue

                if k == "enter":
                        (widget,b) = self.listbox.get_focus()    
                        songinfo = getattr(widget, "song", None)
                        if not songinfo:
                            continue
                        self.play_song(songinfo)    
                        continue
                        
                elif k == "+":
                    self.paused = False
                    self.player.speed += 0.1    
                    self.status("Speed: %1.1f"% self.player.speed)
                    continue
                elif k == "-":
                    self.paused = False
                    self.player.speed -= 0.1    
                    self.status("Speed: %1.1f" % self.player.speed)
                    continue
                elif k == "f":
                    self.fast_forward()
                    continue    
                elif self.speeding:
                    self.not_ff()
                elif k == "u":
                    self.unstable = not self.unstable    
                    if self.unstable:
                        self.status("Warning: Tape loose")
                    else:
                        self.status("Stabilized loose tape")
                        self.player.speed = 1.0
                elif k == "r":
                    if self.player.speed > 0:
                        self.status("Reversing tape")
                    else:
                        self.status("Normal direction")    
                    self.player.speed *= -1
                elif k in ("p", "."):
                    if self.paused :
                        self.player.unpause()
                        self.paused = False
                    else:   
                        self.player.pause()
                        self.paused = True
                        self.status("Paused")
                elif k == "s":
                    self.view.set_focus("header")
                    self.header_columns.set_focus(self.searchbox)
                    if self.search_active and self.search_thread:
                        logging.warning("Search thread already active, terminating")
                        self.search_active = False
                        self.search_thread.join()
                    self.search_active = True
                    self.search_thread = threading.Thread(target=self.searcher)
                    self.search_thread.start()
                    continue
                        
                k = self.view.keypress(self.size, k)


def main():
    urwid.web_display.set_preferences("Urwid Tour")
    # try to handle short web requests quickly
    if urwid.web_display.handle_short_request():
        return
    display = Curses()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write("Exiting\n")
        sys.exit(1)    
