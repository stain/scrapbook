all:
	gcc -Xlinker --export-dynamic -Wl,-E -g -O3 -Wall -shared -I/usr/include/python2.3 -I/usr/include/multisync -I/usr/lib/glib/include -I/usr/include/gtk-1.2 -I/usr/include/glib-1.2 pythonplugin.c -lpython2.3 -o libpythonplugin.so
	cp multisync.py libpythonplugin.so /usr/lib/multisync
#RTLD_GLOBAL

# -rdynamic


