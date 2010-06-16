apt-get with SuSE SLES9
=======================
:Abstract: 
    Although SuSE Linux Enterprise Server 9 (SLES9) enables software
    installation through AutoYaST and YOU, it isn't as easy to script,
    extend and use as apt-get. Provided is a way to create your private
    apt-archive of SLES9.

.. contents::
.. section-numbering::

Quick intro
===========
Scripts to create an APT archive of SLES9. See the download links to the
right. Remember to change paths for the web server etc. (Tip: Search for
``s11``). In ``update-sles9``, remember to fill in the correct SuSE
username and password to be able to download patches. In this document,
``apt.s11.no`` will refer to your virtual host of the local APT archive.


Why use apt?
============

* APT is a set of tools known from Debian for package 
  management. APT is easy to script and understand. Compared
  to YaST with a local YOU server, apt is faster and gives 
  you a common framework to manage both 
  software to be installed on a server and patches 
  to be applied.

* APT makes it easy to add your own packages. Doing the 
  same with YaST proves to be almost impossible. Don't 
  even think about creating your own SuSE-like patches.
 
* APT is free. SuSE recommends buying RedCarpet to 
  manage software and patches.  If you have already 
  invested in SLES9 - this might be too expensive.

* APT is used all over the world. By using APT, your 
  SLES servers can be handled in the same way as computers
  running Fedora, Debian, Redhat 9
  and the normal SuSE distributions. All these distributions
  support apt in one way or another. Why shouldn't your SLES
  servers be able to join the fun?


Why create your own archive?
============================

It might not be legal according to the SLES license to
distribute freely the SuSE RPMs (although the source code 
might be free to distribute). Instead of investigating the
legal matters and create an SLES9 apt-archive for the 
world, it's easy to just create a local archive.

Anyway, having a local archive makes it easier to have 
control. You are certain of good response times and 
bandwith usage, and in addition, it makes it possible 
to be more careful with patches by doing release
management.


Prerequisites
=============

* SLES 9 license (username/password to get SLES patches)
* A web server, and preferable a seperate virtual host, 
  like ``apt.s11.no``
* The `APT tools <http://linux01.gwdg.de/apt4rpm/>`__ for 
  SuSE 9.0
* A server running SLES9 or similar that is able
  to run the APT tools and access the document root of
  the web server
* The ISO images of SLES9, downloaded from 
  `Novell <http://www.suse.de/en/business/products/server/sles/eval.html>`__


Where to I begin?
=================

The first thing to do is to extract files from the downloaded ISOs. It
is not neccessary to burn the CD images. 

Extracting
----------
Modify `mk-sles9.sh <mk-sles9.sh>`__ to suit your paths and domain
names, and run it. A directory structure will be formed in
``/srv/www/apt.s11.no/htdocs/sles9``

Create a ``.htaccess`` file in ``/srv/www/apt.s11.no/htdocs``
to limit access to your known hosts (subnet). Here is an
example::

  IndexOptions NameWidth=*
  IndexIgnore README.txt
  Order Allow,Deny
  Allow from 129.241.

The reason for this is to not get shot by SuSE by them finding your APT
archive open to the world. Only your licensed SLES9 servers should use
your APT archive.

Remember, SuSE is the good guys, they make all the patches and stuff,
even if they didn't create a good enough installation tool. 


Using as a installation source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*NOTE:* I have not tested this myself. Report any bugs.

It is possible to boot SLES9 from netboot or the first CD and do the
main installation from the web directory just created.

To use this directory as an installation source, several modifications
must be done. See the `autoinstall guide
<http://www.suse.de/~nashif/autoinstall/multiplesource.html>`__ for more
information.

Since that guide is related to SLES8, here are the modifications that
must be done, roughly:

In these paragraphs, the installation root
``/srv/www/apt.s11.no/htdocs/sles9`` will be referred to as ``/``.

Procedure::

 Copy installation CD (CD1) to /sles9/CD1
 Copy core CDs (CD2-CD6) to /core9/CD[1-5]

 Copy /sles9/CD1/yast to /
 Copy /sles9/CD1/boot to /
 Copy /sles9/CD1/media.1 to /
 Copy /sles9/CD1/content to /

 mkdir -p /yast/sles9/suse

 Copy /sles9/CD1/media.1 to /yast/sles9
 Copy /sles9/CD1/content to /yast/sles9
 Copy /sles9/CD1/suse/setup to /yast/sles9/suse

 Edit /yast/order  (Here, / is really /):
   /yast/sles9     /sles9/CD1
   /yast/core9     /core9/CD1

 Edit /yast/instorder likewise:
   /yast/sles9
   /yast/core9

In ``yast/`` you could also save the installation XML file 
created by Yast. Call it ``generic.xml`` or something.

Now to boot and install, you could use these kernel parameters using the CD::

  initrd=/sles9/initrd
  autoyast=http://apt.s11.no/sles9/yast/generic.xml
  install=http://apt.s11.no/sles9


Creating the APT archive
------------------------

Make sure the APT tools are installed, including the develparts. Try to
run ``genbasedir`` to see if it is installed.

Modify `mk-apt-sles9.sh <mk-apt-sles9.sh>`__ for the correct paths. Run it. 

An APT structure should be installed. If you have a SLES9 box running,
you could test it now.

On the SLES9 box, install the APT tools. Do **not** run ``apt-get
update``. If you do, SUSE 9 rpms will be installed, and you will no
longer be running SLES9.

Edit ``/etc/apt/sources.list`` so that it contains::

  rpm http://apt.s11.no/apt sles9/production base updates
  rpm http://apt.s11.no/apt sles9/production contrib s11
  rpm-src http://apt.s11.no/apt sles9/production base updates
  rpm-src http://apt.s11.no/apt sles9/production contrib s11

Now run ``apt-get update``. Try to install something with ``apt-get
install vim``.


Getting patches
---------------

Modify `update-sles9.sh <update-sles9.sh>`__ for your paths and SuSE
password. Run it. It should print out lots of stupid wget stuff while
mirroring all SLES9 patches from SuSE. This will take a while since this
is the very first time.

update-sles9.sh will put the patches in a special APT branch
``incoming``. The thought is that you might want to review the patches
before rolling them out. If you want to use them directly, add to
sources.list::

  rpm http://apt.s11.no/apt sles9/incoming updates

..or change the script to place them in ``sles9/production``. Remember
that ``genbasedir`` must always be run after adding packages, this
creates the index files that APT uses.


Doing patch management
======================

*NOTE:* This program is to be considered alpha level. 

The simple solution is to include the ``sles9/incoming`` line in
sources.list, and run ``apt-get update && apt-get -y dist-upgrade`` in
cron on all your hosts.

However, if your servers do real work, and you're worried that SuSE
approved patches might actually break anything (for instance if you use
any third-party programs that are *not* produced by SuSE), it might be a
good idea to have a little control with the patches.

The supplied `patchman.py <patchman.py>`__ will do just that. It is not
complete, and probably has some bugs. But it's a good starting point.

The idea is to have three levels:
  
==========  ==============================================
level       meaning
==========  ==============================================
incoming    Patches downloaded from SuSE. Updated nighly.
            Normally, no servers use these patches.
testing     Patches that you have selected for testing.
            Rolled out to selected servers in "test".
production  Patches that have been approved for rollout
            on all servers
denyed      Patches that are not approved after "testing"
            phase.
==========  ==============================================

A patched RPM is always present in incoming and one of testing,
production or denyed. If it is not, it is considered a "new" patch and
will show up in reports from ``patchman``.  The way this is done is by
hardlinking. 

What patchman does is to find new patches, and report them. 
Patchman also reads the patches files from SuSE to find
small descriptions of what has been fixed.

Patchman can help you approve patches by doing the linking for you. You
can specify a patch either by RPM package name, or by SuSE patch number.

See ``patchman --help`` for more details.


Bugs
====
I have not yet tested the software after doing modifications for
publishing. There might be problems with paths and stuff like that.
Please report any bugs at all to the author at stian@soiland.no.

The software should work with SLES8 with small modifications.

