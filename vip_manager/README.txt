VIP manager for LVS
===================

:Abstract: For people doing load balancing with LVS and VIP, it might
    be important on the real servers to only activate network interfaces
    that are currently enabled in keepalived.conf. This script manages
    this, if you manage to supply it with an updated keepalived.conf

Manages VIP interfaces according to keepalived.conf.
Parses keepalived.conf to find active VIP (virtual_server) addresses
that should be active for a real_server (RIP).

Activates current VIPs on dummy interface, and disactivates
no longer active IPs.

Download
--------
Download the `source <vip_manager.tar.gz>`__, last updated 2006-04-10.
See the website http://soiland.no/software/vip_manager

                 
Usage:: 

    vip_manager.py [-d] [real_ip]
        -d       Show debug messages
        real_ip  Manually set real_server IP
                 (default: resolve from hostname)

Copyright (c) 2004-2006::

    Stian Soiland <stian@soiland.no>
    Magnus Nordseth <magnus@nordseth.net>
    Lasse Karstensen <lkarsten@samfundet.no>

vip_manager is distributed under a MIT license.    

See the site http://www.soiland.no/software/vip_manager/ for updates.

Target
------
Who is this script for? If you're using LVS to do several real_servers
on several virtual_servers, and not all real_servers serve all
virtual_servers at the same time, and it could be that a real_server
needs to connect to a virtual_server. 

If it varies which real_servers serve which virtual_server, the simple
solution is to have all virtual_servers open on a dummy interface on
every real_server. This could pose some problems though, and this is
what vip_manager tries to solve.

Example: 
You have several web domains hosted by several servers. Due to
NFS dependencies, you have seperated the domains from different file
servers to different real_servers. It might vary which real_server
serves which domain. One of the domains contains the APT software
archive, and a real_server not serving that virtual_server at the moment
is to download software updates.


Requirements
------------

* Python 2.2 or later
* sets.py from Python 2.3 (if py 2.2)   (included)
* `systemArgs.py </software/systemArgs>`__ by Stian Soiland
  (included) 
* 'ip' command, from iproute2
* a seperate dummy interface to be managed 

Why
---

Q: What's the use of this script? Couldn't we do one of these?

   a) Serve everything on every real_server

   b) Don't change which VIPs a real_server listens to

   c) Let all real_servers have all VIPs, even if they don't serve
      them all

A: 
   a) To decrease traffic load patterns, seperate for security
      reasons, decrease complexibility and dependencies, it might be
      smart to have different real_servers do different stuff.

   b) One of the features of using LVS is the flexibility of changing
      the use of a real_server by just changing the configuration on
      the LVS directors. To do this, all real_servers should be easy
      to interchange without much/any local configuration.

   c) We've tried that, the problem is that you cannot contact
      any of the "outside" VIP addresses, since an active VIP
      interface will eat everything. This messes up when the VIP isn't
      actually served from the real_server.  Intra-connections tend to
      be needed in complex web applications, and surely in other
      situations as well.  We can live with the fact that we serve our
      self if we can, but we need to avoid that if we *can't*.


Presumption
-----------

All the real_servers need a copy of your keepalived.conf.
Your configuration system (rdist, cfengine, rsync) should give you a
way to distribute it to the real_servers.

keepalived.conf must have structure somewhat like this::

    ...
    virtual_server 129.241.56.90 80 {
        ...
        real_server 129.241.56.129 80 {
           ....
        } 
        ...
    }
    virtual_server 129.241.56.91 80 {
        ...
        real_server 129.241.56.128 80 {
           ....
        } 
        real_server 129.241.56.129 80 {
           ....
        } 
        ...
    }
    ...

(what's important is that real_server lines follow below 
virtual_server lines - your config file probably
looks like this already.)



Other
-----

vip_manager also turns on 'hidden' for the dummy interface and 'all' in
/proc.  If this does not work, the script turns of the dummy interface
for security reasons, such a failure usually indicates a wrong kernel
version.

How dows it work?
-----------------
The script, run on a real_server, reads through keepalived.conf and
recognizes which virtual_servers should be served by him. A dummy
interface (ie. dummy0) then gets all those virtual_servers IP addresses
added, so that Linux will recognize packages for those IPs and pass them
on to the server process, ie. Apache. Unknown addresses on the specified
dummy interface will be disabled. 

This means that if you update keepalived.conf, distribute it, and then
run vip_manager, the dummy interface will be updated. Outgoing
connections to other virtual_server IPs will then work as they should.

Note that it isn't possible to seperate on port level. So if you have
one real_server listening on port 80 on virtual_server 1.2.3.4, and
another real listening on port 443 on virtual 1.2.3.4, this script won't
help you. If the first real_server tries to connect to 1.2.3.4 port 443,
it will still end up on localhost.


Bugs and cautions
-----------------

**Caution** - the operations are done at a IP level. That means if you
have a VIP with both HTTP and HTTPS, but one of the a real servers only
has HTTP, he won't be able to reach the others on HTTPS, he will fail on
connecting to himself.

