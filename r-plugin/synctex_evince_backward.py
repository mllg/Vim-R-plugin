
# The code in this files is borrowed from Gedit Synctex plugin.
#
# Copyright (C) 2010 Jose Aliste
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public Licence as published by the Free Software
# Foundation; either version 2 of the Licence, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public Licence for more
# details.
#
# You should have received a copy of the GNU General Public Licence along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# Street, Fifth Floor, Boston, MA  02110-1301, USA

# Modified to Vim-R-plugin by Jakson Aquino

import dbus, subprocess, time
import dbus.mainloop.glib, sys, os, logging
from gi.repository import GObject

RUNNING, CLOSED = range(2)

EV_DAEMON_PATH = "/org/gnome/evince/Daemon"
EV_DAEMON_NAME = "org.gnome.evince.Daemon"
EV_DAEMON_IFACE = "org.gnome.evince.Daemon"

EVINCE_PATH = "/org/gnome/evince/Evince"
EVINCE_IFACE = "org.gnome.evince.Application"

EV_WINDOW_IFACE = "org.gnome.evince.Window"

class EvinceWindowProxy:
    """A DBUS proxy for an Evince Window."""
    daemon = None
    bus = None

    def __init__(self, uri, spawn = False, logger = None):
        self._log = logger
        self.uri = uri
        self.spawn = spawn
        self.status = CLOSED
        self.dbus_name = ''
        self._handler = None
        try:
            if EvinceWindowProxy.bus is None:
                EvinceWindowProxy.bus = dbus.SessionBus()

            if EvinceWindowProxy.daemon is None:
                EvinceWindowProxy.daemon = EvinceWindowProxy.bus.get_object(EV_DAEMON_NAME,
                                                EV_DAEMON_PATH,
                                                follow_name_owner_changes=True)
            EvinceWindowProxy.bus.add_signal_receiver(self._on_doc_loaded, signal_name="DocumentLoaded", 
                                                      dbus_interface = EV_WINDOW_IFACE, 
                                                      sender_keyword='sender')
            self._get_dbus_name(False)

        except dbus.DBusException:
            if self._log:
                self._log.debug("Could not connect to the Evince Daemon")
                loop.quit()

    def _on_doc_loaded(self, uri, **keyargs):
        if uri == self.uri and self._handler is None:
            self.handle_find_document_reply(keyargs['sender'])
        
    def _get_dbus_name(self, spawn):
        EvinceWindowProxy.daemon.FindDocument(self.uri,spawn,
                     reply_handler=self.handle_find_document_reply,
                     error_handler=self.handle_find_document_error,
                     dbus_interface = EV_DAEMON_IFACE)

    def handle_find_document_error(self, error):
        if self._log:
            self._log.debug("FindDocument DBus call has failed")

    def handle_find_document_reply(self, evince_name):
        if self._handler is not None:
            handler = self._handler
        else:
            handler = self.handle_get_window_list_reply
        if evince_name != '':
            self.dbus_name = evince_name
            self.status = RUNNING
            self.evince = EvinceWindowProxy.bus.get_object(self.dbus_name, EVINCE_PATH)
            self.evince.GetWindowList(dbus_interface = EVINCE_IFACE,
                          reply_handler = handler,
                          error_handler = self.handle_get_window_list_error)

    def handle_get_window_list_error (self, e):
        if self._log:
            self._log.debug("GetWindowList DBus call has failed")

    def handle_get_window_list_reply (self, window_list):
        if len(window_list) > 0:
            window_obj = EvinceWindowProxy.bus.get_object(self.dbus_name, window_list[0])
            self.window = dbus.Interface(window_obj,EV_WINDOW_IFACE)
            self.window.connect_to_signal("Closed", self.on_window_close)
            self.window.connect_to_signal("SyncSource", self.on_sync_source)
        else:
            #That should never happen. 
            if self._log:
                self._log.debug("GetWindowList returned empty list")

    def on_window_close(self):
        self.window = None
        self.status = CLOSED

    def on_sync_source(self, input_file, source_link, timestamp):
        if vimnm == "nvim":
            print input_file + "|" + str(source_link[0]) + "\n"
            sys.stdout.flush()
        else:
            os.system(vimexec + ' --servername ' + vimnm + ' --remote-expr "' + "SyncTeX_backward('" + input_file + "', " + str(source_link[0]) + ')"')


path_output = os.getcwd() + '/' + sys.argv[1]
if not os.path.isfile(path_output):
    print "Error file not found: " + path_output

vimnm = sys.argv[2]
if vimnm != "nvim":
    if vimnm.find("GVIM") == 0:
        vimexec = "gvim"
    else:
        vimexec = "vim"
    time.sleep(1)
    os.system(vimexec + ' --servername ' + vimnm + ' --remote-expr "SyncTeX_SetPID(' + str(os.getpid()) + ')"')


dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
logger = logging.getLogger("evince_dbus")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch.setFormatter(formatter)

logger.addHandler(ch)    
a = EvinceWindowProxy('file://' + path_output, True,logger=logger)

loop = GObject.MainLoop()
loop.run() 

