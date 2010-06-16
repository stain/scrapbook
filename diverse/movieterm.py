#!/usr/bin/env python

import whrandom,time,string

longlines = [
    'gcc -c  -DSTDC_HEADERS=1 -DHAVE_STRING_H=1 -DHAVE_FCNTL_H=1 -DHAVE_SYS_FILE_H=1 -DHAVE_ALLOCA_H=1 -g %s.c',
    'mysql     8291  0.0  0.6 35740  764 ?        SN   Apr09   0:00 /usr/sbin/mysqld --basedir=/usr --datadir=/var/lib/%s --user=mysql --pid-file=/var/run/mysqld/mysqld.pid',
    'make[2]: Leaving directory `/home/stain/avifile-0.6/%s/libmp3lame_audioenc',
    '/bin/sh ../../../libtool --silent --mode=compile gcc -DHAVE_CONFIG_H -I. -I. -I../../../include   -Wall -Wno-unused  -O2 -march=i586 -mpentium -pipe -DWIN32_PATH=\"/usr/lib/win32\" -D__WINE__ -Ddbg_printf=__vprintf  -DTRACE=__vprintf -fno-inline -fno-omit-frame-pointer -fcaller-saves  -D__NO_STRING_INLINES -c pe_%s.c',
    '  PROCEDURE_garbage_collect0 = lookupProcedure(FUNCTOR_dgarbage_collect1, m_%s);',
    '%% chpl -x my-application > header %s \nemacs header\nchpl -h header my-application',
    """ $(AWK) -F. '{ printf("#define PLVERSION %%d\n", $$1 * 10000 + %s $$2 * 100 + $$3); }' >> $@%%""",
    "return insert_message($userid, $message{'%s'}, $message{'id'});",
    "stain@blapp:~$ uptime\n 21:35:32 up 1 day, 11:17,  6 users,  %s load average: 2.03, 2.04, 1.81",
    "Apr  8 13:42:48 %s kernel: Packet log: input DENY eth0 PROTO=6 61.16.62.51:4813 195.1.156.65:53 L=60 S=0x00 I=38376 F=0x4000 T=44 SYN (#32)"
    ]

shortlines = [
    'hyper', 'intranet', 'peer-to-peer', 'blapp', 'multimedia',
    'enterprise', 'integrated', 'Per', 'multi', 'functional',
    'solution', 'scalable', 'Linux', 'hypermedia',
    'business-to-business', 'e-business', 'ASP',
    'total cost of ownership', 'synergy effect',
    'subproblem', 'redundant'
    ]

while(1):
    print string.lower(whrandom.choice(longlines)) % string.upper(whrandom.choice(shortlines))
    if(whrandom.random() > 0.2):
        time.sleep(whrandom.random() * 1)
    


