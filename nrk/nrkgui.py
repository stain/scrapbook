#!/usr/bin/env pythonw

import os

print "Logging in to nrk.no"

from nrk import NRK
nrk = NRK()

print "Starting GUI"

from anygui import *
app = Application()
win = Window()
app.add(win)

catbox = ListBox()
catbox.width = 150
categories = nrk.get_categories()
catbox.items = categories

projects = []
cuts = []

def category_select(event):
    global projects
    source = event.source
    selection = source.selection
    category = categories[selection]
    print "Selected category", category
    projects = category.get_projects()
    projbox.items = projects
    

link(catbox, category_select)    
win.add(catbox, left=4, top=4)


projbox = ListBox()
projbox.width = 150

def project_select(event):
    global cuts
    source = event.source
    selection = source.selection
    project = projects[selection]
    print "Selected project", project
    cuts = project.get_cuts(flatten=True)
    cutbox.items = cuts


link(projbox, project_select)
win.add(projbox, left=200, top=4)


cutbox = ListBox()
cutbox.width = 150

def cut_select(event):
    source = event.source
    selection = source.selection
    cut = cuts[selection]
    print "Selected cut", cut
    # Play it!!
    asx = nrk.get_cut(cut.id, cut.index)
    filename = "/tmp/nrk.asx"
    open(filename, "w").write(asx)
    PROGRAM="/Applications/Windows Media Player.app"
    os.system("open -a '%s' '%s'" % (PROGRAM, filename))

link(cutbox, cut_select)
win.add(cutbox, left=4, top=150)


#from threading import Thread
#from code import InteractiveConsole
#i = InteractiveConsole(locals())
#
#if 0:
#    t = Thread(target=i.interact)
#    print "Starting console thread"
#    t.start()
#    app.run()
#else:
#    t1 = Thread(target=app.run)
#    t2 = Thread(target=i.interact)
#    print "Starting console thread"
#    t2.start()
#    t1.start()


app.run()
