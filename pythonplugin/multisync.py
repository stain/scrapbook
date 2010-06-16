print "Dette er multisync-modulen min"

class Multisync:
    def __init__(self):
        print "En instans %s er opprettet" % id(self)
    def modify(self, object, uid, objtype):
        print "We're modify\n"
        print "Object type:", objtype
        print "Uid:", uid
        print "Object:"
        if uid==None:
            print "New UID",
            uid = "hei"
 #           uid = "%s" % random.random()
#            uid = uid.replace(".", "")
            print uid
            return uid
