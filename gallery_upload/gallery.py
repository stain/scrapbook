#!/usr/bin/env python

####
# Copyright (C) 2004 John Sutherland
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
# 
# you can contact me at: <garion@twcny.rr.com>
# http://garion.tzo.com/python/
#
####

import urllib2_file # REQUIRED for uploading pictures. Original source from:
                    # http://fabien.seisen.org/python/
import urllib2
import urllib
import string
import StringIO
import sys

# this implements the gallery2 protocal
class Gallery:
    def __init__(self, url):
        self.url = url
        self.loggedIn = 0
        self.cookie = ''
        self.protocol_version = '2.7'
        
    def _doRequest(self, request):
        
        if self.cookie != '':
            headers = {'Cookie': self.cookie}
            req = urllib2.Request( self.url + "/gallery_remote2.php", request, headers )
            response = urllib2.urlopen( req )
        else:    
            response = urllib2.urlopen( self.url + "/gallery_remote2.php", request )
                
        
        info = response.info()
        self.cookie = ''
        
        if info.has_key('set-cookie'):
            self.cookie = info['set-cookie'].split(';')[0]
        
        data = response.read()
        
        response = self._parseResponse( data )
        
        #print data           
        
        if response[ 'status' ] != '0':
            raise response[ 'status_text' ]
            
        return response
        
    def _parseResponse(self, response):
        myStr = StringIO.StringIO( response )
        
        for line in myStr:
            if string.find( line, '#__GR2PROTO__' ) != -1:
                break
                                            
        # make sure the 1st line is #__GR2PROTO__
        if string.find( line, '#__GR2PROTO__' ) == -1:
            raise "Bad response: \r\n" + response
            
        resDict = {}
        
        for myS in myStr:
            strList = string.split( myS, '=', 2 )
                
            try:
                resDict[ strList[0] ] = strList[ 1 ][:-1]
            except:
                resDict[ strList[0] ] = ''
                
        return resDict         
               
    def _get(self,response, kwd):
        try:
            retval = response[ kwd ]
        except:
            retval = ''
                        
        return retval            
                                
    def login(self, user, password):
        request = {} 
        request[ 'cmd' ] = 'login'
        request[ 'protocol_version' ] = self.protocol_version
        request[ 'uname' ] = user
        request[ 'password' ] = password
        
        response = self._doRequest( request )
        
        # as long as it comes back here without an exception, we're ok.
        self.loggedIn = 1
        
        
    def fetchAlbums(self):
        request = {} 
        request[ 'cmd' ] = 'fetch-albums'
        request[ 'protocol_version' ] = self.protocol_version
        
        response = self._doRequest( request )
        
        # as long as it comes back here without an exception, we're ok.
        albums = []
        
        for x in range( 1, int( response[ 'album_count' ] ) + 1 ):
            album = {}
            album[ 'name' ]                     = self._get( response, 'album.name.' + str( x ) )
            album[ 'title' ]                    = self._get( response,'album.title.' + str( x ) )
            album[ 'summary' ]                  = self._get( response,'album.summary.' + str( x ) )
            album[ 'parent' ]                   = self._get( response,'album.parent.' + str( x ) )
            album[ 'resize_size' ]              = self._get( response,'album.resize_size.' + str( x ) )
            album[ 'perms.add' ]                = self._get( response,'album.perms.add.' + str( x ) )
            album[ 'perms.write' ]              = self._get( response,'album.perms.write.' + str( x ) )
            album[ 'perms.del_item' ]           = self._get( response,'album.perms.del_item.' + str( x ) )
            album[ 'perms.del_alb' ]            = self._get( response,'album.perms.del_alb.' + str( x ) )
            album[ 'perms.create_sub' ]         = self._get( response,'album.perms.create_sub.' + str( x ) )
            album[ 'perms.info.extrafields' ]   = self._get( response,'album.info.extrafields' + str( x ) )
            
            albums.append( album )
        
        return albums
        
    def fetchAlbumsPrune(self):
        request = {} 
        request[ 'cmd' ] = 'fetch-albums-prune'
        request[ 'protocol_version' ] = self.protocol_version
        
        response = self._doRequest( request )
        
        # as long as it comes back here without an exception, we're ok.
        albums = []
        
        for x in range( 1, int( response[ 'album_count' ] ) + 1 ):
            album = {}
            album[ 'name' ]                     = self._get( response, 'album.name.' + str( x ) )
            album[ 'title' ]                    = self._get( response,'album.title.' + str( x ) )
            album[ 'summary' ]                  = self._get( response,'album.summary.' + str( x ) )
            album[ 'parent' ]                   = self._get( response,'album.parent.' + str( x ) )
            album[ 'resize_size' ]              = self._get( response,'album.resize_size.' + str( x ) )
            album[ 'thumb_size' ]               = self._get( response,'album.thumb_size.' + str( x ) )
            album[ 'perms.add' ]                = self._get( response,'album.perms.add.' + str( x ) )
            album[ 'perms.write' ]              = self._get( response,'album.perms.write.' + str( x ) )
            album[ 'perms.del_item' ]           = self._get( response,'album.perms.del_item.' + str( x ) )
            album[ 'perms.del_alb' ]            = self._get( response,'album.perms.del_alb.' + str( x ) )
            album[ 'perms.create_sub' ]         = self._get( response,'album.perms.create_sub.' + str( x ) )
            album[ 'perms.info.extrafields' ]   = self._get( response,'album.info.extrafields' + str( x ) )
            
            albums.append( album )
        
        return albums
        
    def addItem(self, album, filename, caption ):
        request = {} 
        request[ 'cmd' ] = 'add-item'
        request[ 'protocol_version' ] = self.protocol_version
        request[ 'set_albumName' ] = album
        request[ 'userfile' ] = open(filename)
        request[ 'userfile_name' ] = filename
        request[ 'caption' ] = caption        
        
        response = self._doRequest( request )
            
        # if we get here, everything went ok.
        
    def albumProperties(self, album):
        request = {} 
        request[ 'cmd' ] = 'album-properties'
        request[ 'protocol_version' ] = self.protocol_version
        request[ 'set_albumName' ] = album
        
        response = self._doRequest( request )
        
        resDict = {}
        
        if response.has_key( 'auto_resize' ):
            resDict[ 'auto_resize' ] = response[ 'auto_resize' ]
        if response.has_key( 'add_to_beginning' ):
            resDict[ 'add_to_beginning' ] = response[ 'add_to_beginning' ]
        
        return resDict
        
    def newAlbum(self, parent, name=None, title=None, desc=None):
        request = {} 
        request[ 'cmd' ] = 'new-album'
        request[ 'protocol_version' ] = self.protocol_version
        request[ 'set_albumName' ] = parent
        if name != None:
            request[ 'newAlbumName' ] = name
        if title != None:
            request[ 'newAlbumTitle' ] = title
        if desc != None:
            request[ 'newAlbumDesc' ] = title
        
        response = self._doRequest( request )
        
        return response[ 'album_name' ]
        
    def fetchAlbumImages(self, album):
        # Note: Does not support extrafields!
        request = {} 
        request[ 'cmd' ] = 'fetch-album-images'
        request[ 'protocol_version' ] = self.protocol_version
        request[ 'set_albumName' ] = album
        
        response = self._doRequest( request )
        
        # as long as it comes back here without an exception, we're ok.
        images = []
        
        for x in range( 1, int( response[ 'image_count' ] ) + 1 ):
            image = {}
            image[ 'name' ]                     = self._get( response, 'image.name.' + str( x ) )
            image[ 'raw_width' ]                = self._get( response, 'image.raw_width.' + str( x ) )
            image[ 'raw_height' ]               = self._get( response, 'image.raw_height.' + str( x ) )
            image[ 'resizedName' ]              = self._get( response, 'image.resizedName.' + str( x ) )
            image[ 'resized_width' ]            = self._get( response, 'image.resized_width.' + str( x ) )
            image[ 'resized_height' ]           = self._get( response, 'image.resized_height.' + str( x ) )
            image[ 'thumbName' ]                = self._get( response, 'image.thumbName.' + str( x ) )
            image[ 'thumb_width' ]              = self._get( response, 'image.thumb_width.' + str( x ) )
            image[ 'thumb_height' ]             = self._get( response, 'image.thumb_height.' + str( x ) )
            image[ 'raw_filesize' ]             = self._get( response, 'image.raw_filesize.' + str( x ) )
            image[ 'caption' ]                  = self._get( response, 'image.caption.' + str( x ) )
            image[ 'clicks' ]                   = self._get( response, 'image.clicks.' + str( x ) )
            image[ 'capturedate.year' ]         = self._get( response, 'image.capturedate.year' + str( x ) )
            image[ 'capturedate.mon' ]          = self._get( response, 'image.capturedate.mon' + str( x ) )
            image[ 'capturedate.mday' ]         = self._get( response, 'image.capturedate.mday' + str( x ) )
            image[ 'capturedate.hours' ]        = self._get( response, 'image.capturedate.hours' + str( x ) )
            image[ 'capturedate.minutes' ]      = self._get( response, 'image.capturedate.minutes' + str( x ) )
            image[ 'capturedate.seconds' ]      = self._get( response, 'image.capturedate.seconds' + str( x ) )
            
            images.append( image )
            
        return images        
        
        
    def moveAlbum(self, source, destination):
        request = {} 
        request[ 'cmd' ] = 'fetch-album-images'
        request[ 'protocol_version' ] = self.protocol_version
        request[ 'set_albumName' ] = source
        request[ 'set_destalbumName' ] = destination
        
        response = self._doRequest( request )
        
if __name__ == '__main__':
    gallery = Gallery( 'http://garion.tzo.com/gallery' )
    
    gallery.login( 'user', 'password' )
    #gallery.addItem( 'temp', '/home/garion/missingparts.jpg', 'test!' )
    #print gallery.newAlbum( 0, "temp2" )
    print gallery.fetchAlbumImages('temp')
    
    
    
    
    
