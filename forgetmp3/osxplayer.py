#!/usr/bin/env python
# *-* encoding: utf8
# 
# Copyright (c) 2006 Stian Soiland
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
"""OS X player for forgetMP3 using Quicktime bindings.

"""



from Carbon import QuickTime
from Carbon import Qt
import time
import threading

DEBUG=False

class OSXPlayer(object):
    def __init__(self, filename=None):
        # Is the thread to continue? 
        self.playloop = False
        self._reset()
        Qt.EnterMovies()
        if filename:
            self.open(filename)
        else:
            self.movie = None    
    
    def __del__(self):
        try:
            self.close()
        except:
            pass            
    
    def close(self):
        self.movie.StopMovie()
        Qt.CloseMovieFile(self.fp)
    
    def _reset(self):
        self.started = False
        # Total duration in seconds
        self.duration = 0.0
        # Total played in seconds
        self.played = 0.0
        # percentage done, 0.0 -> 1.0, ie played/duration
        self.complete = 0.0
        # Speed 1.0 is normal, -1.0 is reverse. 0 is stop. anything else
        # left as an exercise to the reader.
        self._speed = 1.0
        # Should the play_loop thread continue?
        self.playloop = False
    
    def open(self, filename):
        self._reset()
        self.fp = Qt.OpenMovieFile(filename, 1)
        movie,_,_, = Qt.NewMovieFromFile(self.fp, 0, QuickTime.newMovieActive)                
        self.movie = movie
        self.movie.GoToBeginningOfMovie()
        # preroll not needed when using StartMovie
        #self.movie.PreRollMovie()

    def _time_stats(self):
        scale = float(self.movie.GetMovieTimeScale())
        self.duration = self.movie.GetMovieDuration() / scale
        t,_ = self.movie.GetMovieTime() 
        self.played = t/scale
        self.complete = self.played / self.duration

    def _start(self):
        self.playloop = True
        if not self.movie:
            raise "No movie open"
        if not self.started:
            self.movie.StartMovie()
            self.started = True    
    
    def pause(self):
        self.movie.SetMovieRate(0.0)
    
    def unpause(self):
        self.movie.SetMovieRate(self.speed)    
    
    def stop(self):
        self.playloop = False
        self.close()
    
    def play_some(self):
        self._start()
        if not self.movie.IsMovieDone():
            self.movie.MoviesTask(0)
            self._time_stats()
    
    def play_loop(self, period=0.05):
        self._start()
        while self.playloop and not self.movie.IsMovieDone():
            self.movie.MoviesTask(0)
            self._time_stats()
            if DEBUG:
                print "%0.1f/%0.1f (%0.1f %%)" % (self.played, self.duration, self.complete * 100)
            time.sleep(period)
        self.complete = 1.0
    
    def play_thread(self):
        # FIXME: How to stop the thread? How to avoid many threads?
        self.thread = threading.Thread(target=self.play_loop)
        self.thread.start()
    
    def _set_speed(self, speed):
        self._speed = speed
        self.movie.SetMovieRate(speed)      

    def _get_speed(self):
        return self._speed
    
    speed = property(_get_speed, _set_speed)    
    
