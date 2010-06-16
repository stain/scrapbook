/* 
   MultiSync Empty Plugin - API demo for MultiSync
   Copyright (C) 2002-2003 Bo Lincoln <lincoln@lysator.liu.se>

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License version 2 as
   published by the Free Software Foundation;

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
   OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF THIRD PARTY RIGHTS.
   IN NO EVENT SHALL THE COPYRIGHT HOLDER(S) AND AUTHOR(S) BE LIABLE FOR ANY
   CLAIM, OR ANY SPECIAL INDIRECT OR CONSEQUENTIAL DAMAGES, OR ANY DAMAGES 
   WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN 
   ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF 
   OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

   ALL LIABILITY, INCLUDING LIABILITY FOR INFRINGEMENT OF ANY PATENTS, 
   COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS, RELATING TO USE OF THIS 
   SOFTWARE IS DISCLAIMED.
*/

/*
 *  $Id: plugin-API.c,v 1.6 2003/07/02 21:18:27 lincoln Exp $
 */

/* The MultiSync plugin API. A plugin is simply a standard shared library
   which contains at least the functions sync_connect() and
   short_name() */

#include <Python.h>
#include <stdlib.h>
#include <glib.h>
#include <multisync.h>

#define py_assert(x) {                         \
    if(PyErr_Occurred())  PyErr_Print();       \
    g_assert(x);                               \
}
// Only to be called from within nice functions with conn
#define py_assert_fail(x) {                            \
    if(PyErr_Occurred()) {                             \
        PyErr_Print();                                 \
        sync_set_requestfailed(conn->sync_pair);       \
        return;                                        \
    }                                                  \
    g_assert(x);                                       \
}                                                      


/******************************************************************
   The following functions are called by the syncengine thread, and
   syncengine expects an asynchronous answer using on of

   // Success
   sync_set_requestdone(sync_pair*);
   // General failure (equal to sync_set_requestmsg(SYNC_MSG_REQFAILED,...))
   sync_set_requestfailed(sync_pair*);
   // General failure with specific log string
   sync_set_requestfailederror(char*, sync_pair*);
   // Success with data
   sync_set_requestdata(gpointer data, sync_pair*);
   // General return (with either failure or other request)
   sync_set_requestmsg(sync_msg_type, sync_pair*);
   // General return with log string
   sync_set_requestmsgerror(sync_msg_type, char*, sync_pair*);
   // General return with data pointere
   sync_set_requestdatamsg(gpointer data, sync_msg_type, sync_pair*);

   (Yes, there are lots of them for convenience.)
   These functions do not have to be called from this thread. If
   your client uses the gtk main loop, use gtk_idle_add() to call your
   real function and let that function call sync_set_requestsomething()
   when done.
******************************************************************/

/* sync_connect()

   This is called once every time the sync engine tries to get changes
   from the two plugins, or only once if always_connected() returns true.
   Typically, this is where you should try to connect to the device
   to be synchronized, as well as load any options and so on.
   The returned struct must contain a

   client_connection commondata; 

   first for common MultiSync data.

   NOTE: Oddly enough (for historical reasons) this callback MUST
   return the connection handle from this function call (and NOT by
   using sync_set_requestdata()). The sync engine still waits for a 
   sync_set_requestdone() call (or _requestfailed) before continuing.
*/

typedef struct {
  client_connection commondata; // Data the syncengine handles for us
  sync_pair *sync_pair;         // The syncengine struct
  PyObject *handler;
} python_connection;


python_connection* sync_connect(sync_pair* handle, 
                               connection_type type,
                               sync_object_type object_types) 
{
  python_connection *conn;
  conn = g_malloc0(sizeof(python_connection));
  g_assert(conn);
  conn->sync_pair = handle;
  conn->commondata.object_types = object_types;
  
  // Prepare python module
  PyObject *pModule, *pDict, *pClass;
  pModule = PyImport_ImportModule("multisync");
  py_assert(pModule);
  pDict = PyModule_GetDict(pModule);
  py_assert(pDict);
  pClass = PyDict_GetItemString(pDict, "Multisync");
  py_assert(pClass);
  conn->handler = PyInstance_New(pClass, NULL, NULL);
  py_assert(conn->handler);
  // Do some neat connection stuff (may of course be asynchronous)
  
  sync_set_requestdone(conn->sync_pair);
  return(conn);
}


/* sync_disconnect()

   Called by the sync engine to free the connection handle and disconnect
   from the database client.
*/

void sync_disconnect(python_connection *conn) {
  sync_pair *sync_pair = conn->sync_pair;
  g_free(conn);
  sync_set_requestdone(sync_pair);
}

/* get_changes()

   The most important function in the plugin. This function is called
   periodically by the sync engine to poll for changes in the database to
   be synchronized. The function should return a pointer to a gmalloc'ed
   change_info struct (which will be freed by the sync engine after usage).
   using sync_set_requestdata(change_info*, sync_pair*).
   
   For all data types set in the argument "newdbs", ALL entries should
   be returned. This is used when the other end reports that a database has
   been reset (by e.g. selecting "Reset all data" in a mobile phone.)
   Testing for a data type is simply done by 
   
   if (newdbs & SYNC_OBJECT_TYPE_SOMETHING) ...

   The "commondata" field of the connection handle contains the field
   commondata.object_types which specifies which data types should
   be synchronized. Only return changes from these data types.

   The changes reported by this function should be the remembered
   and rereported every time until sync_done() (see below) has been 
   called with a success value. This ensures that no changes get lost
   if some connection fails.  
*/

void get_changes(python_connection *conn, sync_object_type newdbs) {
  PyRun_SimpleString("print 'get_changes() igang igjen'\n");
  GList *changes = NULL;
  sync_object_type retnewdbs = 0;
  change_info *chinfo;

  // Example, for calendars and phonebooks:
  if (conn->commondata.object_types & (SYNC_OBJECT_TYPE_CALENDAR)) {
    // Ask for calendar changes...
    // changes = empty_plugin_get_calendar_changes(changes, ...)
  }
  if (conn->commondata.object_types & SYNC_OBJECT_TYPE_PHONEBOOK) {
    // changes = empty_plugin_get_phonebook_changes(changes, ...)
  }
  
  // Allocate the change_info struct
  chinfo = g_malloc0(sizeof(change_info));
  chinfo->changes = changes;
  // Did we detect any reset databases?
  chinfo->newdbs = retnewdbs;
  sync_set_requestdata(chinfo, conn->sync_pair);
  return;
}

/* syncobj_modify() 

   Modify or add an object in the database. This is called by the sync
   engine when a change has been reported in the other end.

   Arguments:
   object     A string containing the actual data of the object. E.g. for
              an objtype of SYNC_OBJECT_TYPE_CALENDAR, this is a 
	      vCALENDAR 2.0 string (see RFC 2445).
   uid        The unique ID of this entry. If it is new (i.e. the sync engine
              has not seen it before), this is NULL.
   objtype    The data type of this object.
   returnuid  If uid is NULL, then the ID of the newly created object should
              be returned in this buffer (if non-NULL). The length of the
	      ID should be returned in returnuidlen.
*/

void syncobj_modify(python_connection *conn, 
		    char* object, char *uid,
		    sync_object_type objtype,
		    char *returnuid, int *returnuidlen) {
  // Modify/add the event to your database...
  
  PyRun_SimpleString("print 'modify() starter!'\n");
  PyObject *pValue;
  pValue = PyObject_CallMethod(conn->handler, "modify", 
                    "ssi", object, uid, objtype);
  // py_assert_fail(pValue);
  PyRun_SimpleString("print 'modify() ferdig!'\n");
  /*
  if(NULL == uid) {
      // we need a return UID, let's hope our modify method
      // supplid one
      char *value = (char*)PyString_AsString(pValue);
      *returnuidlen = PyString_Size(pValue);
      memcpy(returnuid, value, *returnuidlen);
  }
  */
  sync_set_requestdone(conn->sync_pair);
}


/* syncobj_delete() 

   Delete an object from the database. If the argument softdelete is 
   true, then this object is deleted by the sync engine for storage reasons.
*/
void syncobj_delete(python_connection *conn, char *uid,
		    sync_object_type objtype, int softdelete) {
  sync_set_requestdone(conn->sync_pair);
}


/* syncobj_modify_list() 

   If this function is present, it will replace syncobj_modify() and
   syncobj_delete().

   Do all the changes to the database at once. The "changes" argument
   is a GList of changed_object's, where the change_type decides which 
   action should be taken. The "changes" list will be freed by the sync
   engine on return.

   This function must return a GList of syncobj_modify_result's, one
   for each command in "changes". In the syncobj_modify_result, the return 
   code must be set appropriately, and if a new UID is created it must be 
   set as well. This list will be freed by the sync engine.
*/

/** disabled
void syncobj_modify_list(python_connection *conn, GList *changes) {
  GList *node = changes;
  GList *results = NULL;
  while (node) {
    changed_object *obj = node->data;
    syncobj_modify_list *results = g_malloc0(sizeof(syncobj_modify_list));
    int ret = 0;
    // Do database modifications according to obj
    results->result = ret;
    results = g_list_append(results, result);

    node = node->next;
  }
  sync_set_requestdata(results, conn->sync_pair);
}
*/

/* syncobj_get_recurring()

   This is a very optional function which may very well be removed in 
   the future. It should return a list of all recurrence instance of
   an object (such as all instances of a recurring calendar event).
   
   The recurring events should be returned as a GList of changed_objects
   with change type SYNC_OBJ_RECUR.
*/

/** disabled

void syncobj_get_recurring(python_connection *conn, 
			   changed_object *obj) {
  sync_set_requestdata(NULL,conn->sync_pair);
}

*/
/* sync_done()

   This function is called by the sync engine after a synchronization has
   been completed. If success is true, the sync was successful, and 
   all changes reported by get_changes can be forgot. If your database
   is based on a change counter, this can be done by simply saving the new
   change counter.
*/
void sync_done(python_connection *conn, gboolean success) {
  // Must still be acknowledged
  sync_set_requestdone(conn->sync_pair);
}



/***********************************************************************
 The following functions are synchronous, i.e. the syncengine
 expects an immedieate answer without using sync_set_requestsomething()
************************************************************************/

/* always_connected()
  Return TRUE if this client does not have to be polled (i.e. can be 
  constantly connected).
*/

gboolean always_connected() {
  return(FALSE);
}

/* short_name()

 Return a short plugin name for internal use.
*/

char* short_name() {
  return("pythonplugin");
}

/* long_name()

   Return a long name which can be shown to the user.
*/

char* long_name() {
  return("Python script");
}

/* plugin_info()

  Return an even longer description of what this plugin does. This will
  be shown next to the drop-down menu in the sync pair options.
*/

char* plugin_info(void) {
  return("Runs a plugin written in Python");
}

/* plugin_init()

   Initialize the plugin. Called once upon loading of the plugin (NOT
   once per sync pair).
*/

void plugin_init(void) {
  Py_Initialize();
  PyRun_SimpleString("print 'Heia fra python'\n"
                     "import sys\n"
                     "sys.path.append('/usr/lib/multisync')\n"
                     "import time\n"
                     );
  // Py_Finalize();
}

/* object_types()

   Return the data types this plugin can handle.
*/
sync_object_type object_types() {
  return(SYNC_OBJECT_TYPE_CALENDAR);
}

/* plugin_API_version() 

  Return the MultiSync API version for which the plugin was compiled.
  It is defined in multisync.h as MULTISYNC_API_VER.
  Do not use return(MULTISYNC_API_VER), though, as the plugin will then
  get valid after a simple recompilation. This may not be all that is needed.
*/

int plugin_API_version(void) {
  return(3); 
}
