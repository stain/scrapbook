class NS(object):
    NS = ""
    tags = ""
    class __metaclass__(type):
        def __new__(cls, name, bases, dict):
            if not ("tags" in dict and "NS" in dict):
                raise "Cannot create NS class without defining tags and NS"
            ns = dict["NS"]
            for tag in dict["tags"].split():
                dict[tag] = "{%s}%s" % (ns, tag)
            return type.__new__(cls, name, bases, dict)


class DAV(NS):
    NS = "DAV:"
    tags = """multistatus response href propstat prop
              resourcetype creationdate getlastmodified
              getetag supportedlock lockentry lockscope locktype
              lockdiscovery getcontenttype getcontentlength
              status collection shared exclusive write"""

class ApacheProps(NS):
    NS = "http://apache.org/dav/props/"
    tags = "executable"

