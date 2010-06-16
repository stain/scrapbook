#!/usr/bin/env python

import BaseHTTPServer
from elementtree import ElementTree as ET
from ns import DAV
import fs

FS = fs.dummies()

def properties(resource):
#<D:response xmlns:lp1="DAV:"
#xmlns:lp2="http://apache.org/dav/props/">
#    <D:href>/</D:href>
#    <D:propstat>
#    <D:prop>
#        <lp1:resourcetype><D:collection/></lp1:resourcetype>
#        <lp1:creationdate>2006-06-18T13:48:07Z</lp1:creationdate>
#        <lp1:getlastmodified>Sun, 18 Jun 2006 13:48:07 GMT</lp1:getlastmodified>
#        <lp1:getetag>"7dcb79-1000-4167fe64853c0"</lp1:getetag>
#        <D:supportedlock>
#            <D:lockentry>
#            <D:lockscope><D:exclusive/></D:lockscope>
#            <D:locktype><D:write/></D:locktype>
#            </D:lockentry>
#            <D:lockentry>
#            <D:lockscope><D:shared/></D:lockscope>
#            <D:locktype><D:write/></D:locktype>
#            </D:lockentry>
#        </D:supportedlock>
#        <D:lockdiscovery/>
#        <D:getcontenttype>httpd/unix-directory</D:getcontenttype>
#    </D:prop>
#    <D:status>HTTP/1.1 200 OK</D:status>
#    </D:propstat>
#    </D:response>
    response = ET.Element(DAV.response)
    href = ET.SubElement(response, DAV.href)
    href.text = resource.path()
    propstat = ET.SubElement(response, DAV.propstat) 
    prop = ET.SubElement(propstat, DAV.prop)
    
    resourcetype = ET.SubElement(prop, DAV.resourcetype)
    if isinstance(resource, fs.Directory):
        ET.SubElement(resourcetype, DAV.collection)
        ct = ET.SubElement(prop, DAV.getcontenttype)
        ct.text = "httpd/unix-directory"
        
    supportedlock = ET.SubElement(prop, DAV.supportedlock)
    lockentry = ET.SubElement(supportedlock, DAV.lockentry)    
    scope = ET.SubElement(lockentry, DAV.lockscope)
    ET.SubElement(scope, DAV.exclusive)
    locktype = ET.SubElement(lockentry, DAV.locktype)
    ET.SubElement(locktype, DAV.write)
    
    creationdate = ET.SubElement(prop, DAV.creationdate)
    creationdate.text = resource.creationdate.strftime("%Y-%m-%dT%H:%M:%SZ")

    getlastmodified = ET.SubElement(prop, DAV.getlastmodified)
    getlastmodified.text = resource.lastmodified.strftime("%Y-%m-%dT%H:%M:%SZ")

    if hasattr(resource, "size"):
        getcontentlength = ET.SubElement(prop, DAV.getcontentlength)
        getcontentlength.text = str(resource.size)
    
    etag = ET.SubElement(prop, DAV.getetag)
    etag.text = '"%s"' % resource.identifier    

    

    status = ET.SubElement(propstat, DAV.status)
    status = "HTTP/1.1 200 OK"
    return response


class DavServer(BaseHTTPServer.HTTPServer):
    pass

class DavHandler(BaseHTTPServer.BaseHTTPRequestHandler):    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('DAV', "1,2")
        #self.send_header("DAV", "version-control,checkout,working-resource")
        #self.send_header("DAV", "merge,baseline,activity,version-controlled-collection")
        self.send_header("DAV", "<http://apache.org/dav/propset/fs/1>")
        self.send_header("MS-Author-Via", "DAV")
        self.send_header("Allow",
            "OPTIONS,GET,HEAD,POST,DELETE,TRACE,PROPFIND,PROPPATCH,COPY,MOVE,LOCK,UNLOCK,MKCOL")
        self.send_header("Content-Length", "0")
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        print "Options", self.path
    
    def do_PROPFIND(self):
        self.debug()
        length = self.headers.get("Content-Length")
        if length and length != "0":
            data = self.rfile.read(int(length))
            print "Received:", data

        multistatus = ET.Element(DAV.multistatus)

        try:
            resource = FS.get(self.path)
        except KeyError:
            self.send_response(404)
            self.end_headers()
            return
        # FIXME: should handle depth
        multistatus.append(properties(resource))
        if isinstance(resource, fs.Directory):
            for child in resource.children.values():
                child_desc = properties(child)
                multistatus.append(child_desc)
        response = '<?xml version="1.0" encoding="utf-8"?>\n'
        response += ET.tostring(multistatus)
        self.send_response(207)
        self.send_header("Content-Length", str(len(response)))
        self.send_header("Content-Type", 'text/xml; charset="utf-8"')
        self.end_headers()
        self.wfile.write(response)

    
    def ignore(self):
        self.debug()
        length = self.headers.get("Content-Length")
        if length and length != "0":
            data = self.rfile.read(int(length))
            print "Received:", data
        self.send_response(200)    
        self.send_header("Content-Length", "0")
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
   
    def debug(self):     
        print self.command, self.path, self.request_version 
        print self.headers
        #print "Content:", repr(self.rfile.read())
        #print "--"

    def do_GET(self):
        self.debug()
        try:
            resource = FS.get(self.path)
        except KeyError:
            self.send_response(404)
            self.end_headers()
            return
        f = resource.open()   
        data = f.read()
        print "Sending", data
        self.send_response(200)    
        self.send_header("Content-Length", len(data))
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        self.ignore()

    def do_PUT(self):
        self.debug()
        parent_path, name = self.path.rsplit("/", 1)
        try:
            parent = FS.get(parent_path)
        except KeyError:
            self.send_response(409)
            self.end_headers()
            return
        if name in parent.children:    
            self.send_response(201)
            file = parent.children[name]
        else:     
            file = fs.File(name, parent)
            self.send_response(204)
        length = self.headers.get("Content-Length")
        if length and length != "0":
            f = file.open()
            data = self.rfile.read(int(length))
            print "Received:", data
            f.write(data)
        self.end_headers()
        if name == "eval":
            try:
                parent.remove("result")
            except KeyError:
                pass    
            resfile = fs.File("result", parent)
            try:
                result = eval(data)
            except Exception, e:
                result = repr(e)    
            resfile.open().write(str(result) + "\r\n")
             
    def do_MKCOL(self):
        parent_path, name = self.path.rsplit("/", 1)
        try:
            parent = FS.get(parent_path)
        except KeyError:
            self.send_response(409)
            self.end_headers()
            return
        dir = fs.Directory(name, parent)     
        self.send_response(204)
        self.end_headers()
        
             
    def do_HEAD(self):
        self.ignore()

    def do_DELETE(self):
        parent_path, name = self.path.rsplit("/", 1)
        try:
            parent = FS.get(parent_path)
        except KeyError:
            self.send_response(409)
            self.end_headers()
            return
        parent.remove(name) 
        self.send_response(204)    
        self.end_headers()
    
    def do_TRACE(self):
        self.ignore()
    def do_PROPPATCH(self):
        self.ignore()
    def do_COPY(self):
        self.ignore()

    def do_MOVE(self):
        self.debug()
        dest = self.headers.get("Destination")
        print "Move to", dest

    def do_LOCK(self):
        self.ignore()
    def do_UNLOCK(self):
        self.ignore()
    def do_CHECKOUT(self):
        self.ignore()                        

if __name__ == "__main__":
    server_address = ('', 8000)
    httpd = DavServer(server_address, DavHandler) 
    httpd.serve_forever()    

