#!/usr/bin/env python

import re
from HTMLParser import HTMLParser
import sys
import os
from urllib import urlencode
try: #python2.4 and above
    from urllib2 import build_opener, HTTPCookieProcessor, Request
    from cookielib import DefaultCookiePolicy, MozillaCookieJar
except ImportError:
    # Needs http://wwwsearch.sourceforge.net/ClientCookie
    try:
        from ClientCookie import build_opener, HTTPCookieProcessor, Request
        from ClientCookie import DefaultCookiePolicy, MozillaCookieJar
    except ImportError:
        print "Use Python2.4 or install ClientCookie"
        print "  http://wwwsearch.sourceforge.net/ClientCookie"
        sys.exit(1)


USER="spam@soiland.no"
PW="fish"
SPEED="535" # kbit

class URL:
    login = "https://www7.nrk.no/brukerbase/logginnavspiller.aspx?avspiller=avspiller&produktid=1000016&retururl=http%3a%2f%2fwww7.nrk.no%2fnrkplayer%2floggetinn.aspx"
    BASE = "http://www7.nrk.no/nrkplayer/"
    set_speed = BASE + "h_hastighet.aspx?action=lagre"
    test = BASE + "testnettleser.aspx?hovedkategori_id=2&prosjekt_id=0&kategori_id=0&klipp_id=0&indeks_id=0&oppgave_id=0&sok=&ref=&artikkel_id="
    start = BASE + "default.aspx"
    kategori = BASE + "kategorimeny.aspx?Sesjon=Hovedkategori_Id&Verdi=%s"
    prosjekt = BASE + "prosjektmeny.aspx?Prosjekt_Id=%s"
    generator = BASE + "generator.aspx?klipp_id=%s&indeks_id=%s"
    avspiller = BASE + "avspiller.aspx?Hovedkategori_id=1&Prosjekt_id=0&Kategori_id=0&Klipp_id=0&Indeks_id=0&Oppgave_id=0&Sok=dal&Artikkel_Id="

def u2i(s):
    """Convert from utf8 to iso8859-1"""
    #a = s.decode("utf8").encode("iso8859-1", "ignore")
    a = s
    a.replace("\n", " ")
    a.replace("\r", "")
    return a.strip()

class AvspillerParser(HTMLParser):
    NAME=1
    DESCR=2
    def __init__(self):
        HTMLParser.__init__(self)
        self.current = None
        self.categories = []
        
    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return # ignore structure, just find visProsjekt links
        attrs = dict(attrs)
        if "onclick" not in attrs:
            self.current = None
            return
        onclick = attrs["onclick"]    
        if not "visProsjekt" in onclick:
            self.current = None
            return
        descr = attrs["title"]
        # Note that NRK names categories "project" here even though
        # what's listed here are categories (containing projects)
        id = re.search(r"visProsjekt\('[^']*','([0-9]+)'", onclick)
        if not id:
            self.current = None
            return
        id = id.group(1)    
        self.current = [id, "", descr] # id, name, descr
        # Will find name inside <a> element in handle_data()

    def handle_data(self, data):
        if self.current:
            self.current[self.NAME] += data
    
    def handle_endtag(self, tag):
        if tag == "a" and self.current:
            id, name, descr = self.current
            name = u2i(name).capitalize()
            descr = u2i(descr)
            self.categories.append((id, name, descr))

class CategoryParser(HTMLParser):
    NAME=1
    DESCR=2
    def __init__(self):
        HTMLParser.__init__(self)
        self.current = None
        self.currentData = None
        self.projects = []
        
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs = dict(attrs)
            if "onclick" not in attrs:
                self.current = None
                return
            onclick = attrs["onclick"]    
            if not "visKategori" in onclick:
                self.current = None
                return
            # Note that NRK names categories "project" here even though
            # what's listed here are categories (containing projects)
            id = re.search(r"visKategori\(([0-9]+)\)", onclick)
            if not id:
                self.current = None
                return
            id = id.group(1)    
            self.current = [id, "", ""] # id, name, descr
            # Will find rest inside <a> element in handle_data()
            self.currentData = None

        # We'll fill up the NAME position or DESCR position
        # depending on which tag we are inside.
        elif tag == "b" and self.current:
            self.currentData = self.NAME
        elif tag == "span" and self.current:
            self.currentData = self.DESCR 
        else:
            self.currentData = None

    def handle_data(self, data):
        if self.current and self.currentData is not None:
            self.current[self.currentData] += data    
    
    def handle_endtag(self, tag):
        if tag == "a" and self.current:
            id, name, descr = self.current
            if not name and not descr:
                return # ignore <img> links
            #name = name.capitalize()
            self.projects.append((id, u2i(name), u2i(descr)))

class Category:

    def __init__(self, id, name, descr, nrk):
        self.id = id
        self.name = name
        self.descr = descr
        self.nrk = nrk # backref to NRK

    def __str__(self):
        return self.descr

    def __repr__(self):
        return "<Category %s %s>" % (self.id, self.name)    
    
    def get_projects(self):
        parser = CategoryParser()
        r = self.nrk.opener.open(URL.kategori % self.id)
        html = r.read()
        #print html
        parser.feed(html)
        projects = [Project(id, name, descr, self.nrk) for
            (id, name, descr) in parser.projects]
        return projects

class Folder(list):
    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)  
        self.title = ""
    def __repr__(self):
        #  Chop of []
        content = list.__repr__(self)[1:-1]
        return "<%s %s>" % (self.title, content)   

    def _print(self, indent=0):
        result = []
        result.append("  "*indent + "+" + self.title)
        for child in self:
            if isinstance(child, Folder):
                result.append(child._print(indent+1))
            elif isinstance(child, Cut):
                result.append("  "*(indent+1) + " %s" % child)
            else:
                (id, index, name, title) = child
                result.append("  "*(indent+1) + " %s/%s %s" % (id,index, name) )
        return str.join("\n", result)
    
    def __str__(self):
        return self._print()
   
 
               

class Stack(list):
    def push(self, elem):
        """Pushes elem to stack. Use pop() to pop off"""
        self.append(elem)
    def top(self):
        """Top of stack, item to be popped next. None if stack empty"""
        if not self:
            return None
        return self[-1]        

class ProjectParser(HTMLParser):
    NAME=1
    DESCR=2
    def __init__(self):
        HTMLParser.__init__(self)
        self.root = Folder()
        self.cur_folder = self.root
        self.cur_title = None
        self.cur_data = None
        self.stack = Stack()
        
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div":
            self.stack.push((tag, attrs, self.cur_folder))

            if "title" in attrs:
                self.cur_title = attrs["title"]

            if "mappe" in attrs.get("class", ""):
                # New subfolder
                folder = Folder()
                self.cur_folder.append(folder)
                self.cur_folder = folder
                if self.cur_title:
                    folder.title = self.cur_title

        elif tag == "span":
            self.stack.push((tag, attrs, self.cur_folder))
            if "onclick" in attrs:    
                self.cur_data = ""

    def handle_data(self, data):
        if self.cur_data is not None:
            self.cur_data += data    
    
    def handle_endtag(self, tag):
        if tag in ("div", "span"):
            oldtag = None
            while oldtag != tag:
                oldtag, attrs, par_folder = self.stack.pop()
                # If it's an empty folder, just remove it        
                if tag == "div" and "mappe" in attrs.get("class", ""):
                    if not self.cur_folder:
                        par_folder.remove(self.cur_folder)
                self.cur_folder = par_folder

        if tag == "span":
            if "onclick" in attrs:
                title = u2i(self.cur_title)
                name = u2i(self.cur_data)
                match = re.search(r"StartKlipp\('[^']*', '([0-9]+)', '([0-9]+)'", 
                               attrs["onclick"])
                if not match:
                    return
                id = match.group(1)
                index = match.group(2)
                self.cur_folder.append( (id, index, name, title) )

                # Set title for any unnamed folder following
                self.cur_title = name
                self.cur_data = None
                   
            
class Project:

    def __init__(self, id, name, descr, nrk):
        self.id = id
        self.name = name
        self.descr = descr
        self.nrk = nrk # backref to NRK

    def __str__(self):
        if self.descr:
            return "%s (%s)" % (self.name, self.descr)
        return self.name    

    def __repr__(self):
        return "<Project %s %s>" % (self.id, self.name)    
    
    def get_cuts(self, flatten=False):
        parser = ProjectParser()
        r = self.nrk.opener.open(URL.prosjekt % self.id)
        html = r.read()
        #print html
        parser.feed(html)
        def cutify(folder):
            newlist = []
            for child in folder:
                if isinstance(child, Folder):
                    cutify(child)  
                    if flatten:
                        newlist.extend(child)
                    else:
                        newlist.append(child)    
                else:
                    (id, index, name, title) = child
                    child = Cut(id, index, name, title, self.nrk)
                    newlist.append(child)    
            # replace our content with the new list   
            folder[:] = newlist

        cutify(parser.root)
        return parser.root    

class Cut:
    def __init__(self, id, index, name, descr, nrk):
        self.id = id
        self.index = index
        self.name = name
        self.descr = descr
        self.nrk = nrk # backref to NRK

    def __str__(self):
        return self.name     

class NRK:
    def __init__(self):
        policy = DefaultCookiePolicy(
            rfc2965=True, strict_ns_domain=DefaultCookiePolicy.DomainStrict)
        self.cj = MozillaCookieJar(".cookies", policy)

        try:
            self.cj.load()
        except IOError, e:
            if e.errno != 2:
                raise e
            # else: Ignore "File not found"    
        self.opener = build_opener(HTTPCookieProcessor(self.cj))
        self.init()
        #self.login()
        self.setspeed()
    
    def init(self):
        # get the bhCookieSess-cookie and session cookie
        req = Request(URL.test)
        #req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; U; PPC Mac OS X Mach-O; nb-NO; rv:1.7.5) Gecko/20041108 Firefox/1.0")
        r = self.opener.open(req)

    def login(self):
        # Get the hidden form fields
        r = self.opener.open(URL.login)
        if r.url.count("/loggetinn.aspx"):
            # We got redirected, and our session and stuff are still valid
            return
        html = r.read()
        # OK, we know these field data
        data = {}
        data["txtBrukernavn"] = USER
        data["txtPassord"] = PW
        data["chkLagre"] = "On"
        data["btnLoggInn"] = "Logg inn"

        data["__EVENTTARGET"] = ""
        data["__EVENTARGUMENT"] = ""
        # This crap we don't know what is, but it was a 
        # hidden field, so we could pass it on
        #viewstate = re.search(r'<input type="hidden" name="__VIEWSTATE" value="([^"]+)" />', html)
        # but it does work without        
        #data["__VIEWSTATE"] = viewstate.group(1)

        request = Request(URL.login, data=urlencode(data))
        request.add_header("Referer", URL.login)
        r = self.opener.open(request, data=urlencode(data))
        self.cj.save()
        
    def setspeed(self):
        data = urlencode([("speed", SPEED)])
        r = self.opener.open(URL.set_speed, data=data)
        self.cj.save()

    def get_categories(self):
        parser = AvspillerParser()
        r = self.opener.open(URL.avspiller)
        data = r.read()
        # I don't know why NRK does this stupid illegal thing
        data = data.replace('\\"', '"')
        parser.feed(data)
        categories = [Category(id, name, descr, self) for 
                      (id, name, descr) in parser.categories]
        return categories
   
    def get_cut(self, id, index=0):
        r = self.opener.open(URL.generator % (id, index))
        html = r.read()
        match = re.search(r'<PARAM NAME="filename" VALUE="([^"]+)">', html)
        #print html
        url = match.group(1)
        r = self.opener.open(URL.BASE + url)
        asx = r.read()
        return asx
    
    def get_mms(self, id, index=0):
        asx = self.get_clip(id, index)      
        match = re.search(r'', asx)
        return match


if __name__ == "__main__":
    nrk = NRK()       
    CATEGORY, PROJECT,ID,INDEX = None, None, None, 0
    if len(sys.argv) > 1:
        if sys.argv[1].isdigit():
            ID=sys.argv[1]
        else:    
            CATEGORY = sys.argv[1]
    if len(sys.argv) > 2:
        if sys.argv[2].isdigit():
            INDEX=sys.argv[2]
        else:
            PROJECT = sys.argv[2]     

    if ID:
        asx = nrk.get_clip(ID, INDEX)
        filename = "/tmp/nrk.asx"
        open(filename, "w").write(asx)
        PROGRAM="/Applications/Windows Media Player.app"
        os.system("open -a '%s' '%s'" % (PROGRAM, filename))
    else:    
        for cat in nrk.get_categories():
            if not CATEGORY or CATEGORY.lower()==cat.name.lower():
                print cat
                print "---"
                for proj in cat.get_projects():
                    if not PROJECT or PROJECT.lower()==proj.name.lower():
                        print proj
                    if PROJECT and PROJECT.lower()==proj.name.lower():
                        for f in proj.get_cuts():
                            print f
                print ""    
