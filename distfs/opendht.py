#!/usr/bin/env python
import sys; 
import sha; 
import optparse; 
from xmlrpclib import *

# get.py

# see http://opendht.org/servers.txt - the default is
# location near through magic DNS
GATEWAY="http://opendht.nyuld.net:5851/"

proxy = ServerProxy(opts.gateway)
maxvals = 10

pm = Binary(""); 
key = Binary(sha.new(args[0]).digest())

while True:
    vals, pm = pxy.get_details(key, maxvals, pm, "get.py")
        for v in vals: 
            hex = '0x' + ''.join(["%02x"%ord(x) for x in v[3].data[:4]])
            print v[0].data, v[1], v[2], hex


vals, pm = pxy.get(key, maxvals, pm, "get.py")
for v in vals: 
    print v.data
if (pm.data == ""): break

# rm.py        

p = optparse.OptionParser(usage="usage: %prog [options] <key> <value> <secret>")
p.add_option("-g", "--gateway", dest="gateway", metavar="GW",
             default="http://opendht.nyuld.net:5851/", 
             help="gateway URI, list at http://opendht.org/servers.txt")
p.add_option("-t", "--ttl", dest="ttl", default="3600", metavar="TTL", 
             type="int", help="must be longer than TTL remaining for value")
(opts, args) = p.parse_args()
if (len(args) < 3): p.print_help(); sys.exit(1)
pxy = ServerProxy(opts.gateway); res = {0:"Success", 1:"Capacity", 2:"Again"}
key = Binary(sha.new(args[0]).digest()); ttl = int(opts.ttl); 
vh = Binary(sha.new(args[1]).digest()); sec = Binary(args[2]) 
print res[pxy.rm(key, vh, "SHA", sec, ttl, "rm.py")]

# put.py

#!/usr/bin/env python
import sys; import sha; import optparse; from xmlrpclib import *
p = optparse.OptionParser(usage="usage: %prog [options] <key> <value>")
p.add_option("-g", "--gateway", dest="gateway", metavar="GW",
             default="http://opendht.nyuld.net:5851/", 
             help="gateway URI, list at http://opendht.org/servers.txt")
p.add_option("-t", "--ttl", dest="ttl", default="3600", metavar="TTL", 
             type="int", help="how long (in seconds) to store the value")
p.add_option("-s", "--secret", dest="secret", default="", metavar="SEC",
             help="can be used to remove the value later")
(opts, args) = p.parse_args()
if (len(args) < 2): p.print_help(); sys.exit(1)
pxy = ServerProxy(opts.gateway); res = {0:"Success", 1:"Capacity", 2:"Again"}
key = Binary(sha.new(args[0]).digest()); val = Binary(args[1]) 
ttl = int(opts.ttl); shash = Binary(sha.new(opts.secret).digest()) 
if (opts.secret == ""): print res[pxy.put(key, val, ttl, "put.py")]
else: print res[pxy.put_removable(key, val, "SHA", shash, ttl, "put.py")]
