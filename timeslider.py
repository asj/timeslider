# File: timeslider.py
#
# version 0.1
# by AJ
####################################################################
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public
#  License v2 as published by the Free Software Foundation.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
# 
#  You should have received a copy of the GNU General Public
#  License along with this program; if not, write to the
#  Free Software Foundation, Inc., 59 Temple Place - Suite 330,
#  Boston, MA 021110-1307, USA.
####################################################################

import pygtk
import gobject
import gtk
import gtk.glade
import urllib
import re
import os
import gnome
import commands
import math
import signal
import time
import sys
import nautilus
from time import gmtime, strftime
from gtk import gdk
from pprint import pprint
from signal import SIGTERM, SIGKILL


# Read the snapshot for a given tuple parent and subvol
def read_snaplist(self):
        self.snaplist=[]
        self.snaplist_cnt = 0
        #Get the list snapshots available for this self.subvol.
        statout = commands.getstatusoutput(("btrfs sub list -c -t parent=%s %s" % (self.subvol,self.subvol)))
        if statout[0] != 0:
            print "btrfs su li Command failed"
            return -1

        if len(statout[1]) != 0:
            l = statout[1].split(',')
            for i in range(len(l)/4):
                tn = i*4
                etstr = int(time.mktime(time.strptime(l[tn+1])))
                sstuple = l[tn+0].strip('\n'), l[tn+1], l[tn+2], l[tn+3], etstr
                self.snaplist.append(sstuple)
            self.snaplist_cnt = len(self.snaplist)
            self.snaplist.sort(key=lambda tup: tup[4],reverse=True)
        
        return 0

# Prepares the list of tags avaialble for the give subvol
def read_taglist(self):
    self.taglist=[]
    s="btrfs au show -t %s" % (self.subvol)
    statout = commands.getstatusoutput(s)
    if statout[0] != 0:
        print "btrfs failed to get taglist"
        return -1
    if statout[1] == "There is nothing":
        return 0
    for s in statout[1].split():
        if s != "Freq/Tag":
            self.taglist.append(s)
    return 0

# Filter the snapshot list by its tag 
def create_snaplist_bytag(self, tag):
        self.snaplist_bytag = list(self.snaplist)
        if tag != "All":
            if tag == "-notag-":
                tag = ""
            repeat=1
            while repeat == 1 :
                for i in range(len(self.snaplist_bytag)):
                    if self.snaplist_bytag[i][3] != tag:
                        repeat=1
                        self.snaplist_bytag.pop(i)
                        break
                    else:
                        repeat=0
                if (len(self.snaplist_bytag) == 0):
                    break
        self.snaplist_bytag_cnt = len(self.snaplist_bytag)
        return

# Fill up the drop down menu containint the tags
def update_combobox(self, tag):
        model = self.combobox1.get_model()
        #self.combobox1.set_model(None)
        model.clear()
        #for entry in desired_entries:
        #    model.append([entry])
        #    combo_box.set_model(model)
        self.combobox1.append_text('All')
        for i in self.taglist:
                self.combobox1.append_text(i)
        self.combobox1.append_text('-notag-')
        
        if tag != "All":
            if self.taglist.count(tag) is 1:
                self.combobox1.set_active(self.taglist.index(tag))
                self.tag = tag
            else:
                pass # TODO actually do refresh
                #self.refresh(self.pos,self.tag)
        else:
            self.combobox1.set_active(0)
            self.tag = "All"
        return

# Mark the scale with the creation time of the snapshot list
def mark_scale(self, pos):
        self.hscale1.clear_marks()
        self.midpoint = int(math.floor((self.snaplist_bytag_cnt+1)/2))
        self.adj1.set_upper(self.snaplist_bytag_cnt+1)
        for i in range(self.snaplist_bytag_cnt+1):
            self.hscale1.add_mark(i,gtk.POS_BOTTOM,"")
        self.hscale1.add_mark(0, gtk.POS_BOTTOM, "Now")
        if (pos < self.midpoint):
            self.hscale1.add_mark(self.snaplist_bytag_cnt, gtk.POS_BOTTOM, self.snaplist_bytag[self.snaplist_bytag_cnt-1][1])        
        if pos is not 0:
            if self.tag == "All":
                s = self.snaplist_bytag[pos-1][1] + "\n("+self.snaplist_bytag[pos-1][3]+")"
                self.hscale1.add_mark(pos, gtk.POS_BOTTOM, s)
            else:
                self.hscale1.add_mark(pos, gtk.POS_BOTTOM, self.snaplist_bytag[pos-1][1])
        self.adj1.set_value(pos)
        self.pos = pos
        return

# This will display the go to location bar on the nautilus. 
def load_new_uri(self):
        self.window.emit("prompt-for-location",self.pwd_in_ss)
        # This code should work but we might need to patch nautilus itself.
        event = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
        event.time = 0
        event.keyval = gtk.keysyms.Return
        #self.window.propagate_key_event(event)
        self.window.emit('key_press_event', event)
        return
    
# Refresh all the gui part on the nautilus
def refresh(self, pos, tag, update_flag):
    if pos != self.pos:
        self.adj1.set_value(pos)
        self.pos = pos
        
    if tag != self.tag:
        self.tag = tag
        if update_flag != "all":
            update_flag = update_flag+"|combobox"
            
    if update_flag == "all":
        update_flag = "snaplist|taglist|combobox|snaplist|scale|sensitive"

    if "snaplist" in update_flag:
        if read_snaplist(self) is -1:
            print "snapshot_scale failed"
            return
    if "taglist" in update_flag:
        read_taglist(self)
    if "combobox" in update_flag:
        update_combobox(self,self.tag)
    if "snaplist_bytag" in update_flag:
        create_snaplist_bytag(self, self.tag)
    if "scale" in update_flag:
        mark_scale(self,self.pos)
    if "sensitive" in update_flag:
        set_sensitive(self, self.pos, self.tag)
    return
    
# especially buttons and drop down menu sensitivity varies by the state of scale
def set_sensitive(self,pos,tag):
        if pos == 0:
            self.button1.set_sensitive(False)
            if tag == "All" or tag == "-notag-":
                self.button2.set_sensitive(False)
            else:
                self.button2.set_sensitive(True)
        else:
            self.button2.set_sensitive(False)
            self.button1.set_sensitive(True)
        return

# display on the status bar with in the timeslider widget
def write_display_bar(self, s):
        self.label2.set_text(s)

# When user is with in the subvol in a sub dir, the location
# bar should show the same subdir in the snapshot.
def get_pwd_in_ss(self, pos):
        self.snap = self.snaplist_bytag[pos-1][0]
        if os.path.exists(self.snap) is True:
            ss_pwd = os.path.join(self.snap, self.pwd_from_subvol)
            if os.path.exists(ss_pwd) is False:
                ss_pwd = self.snap
        else:
            refresh(self, 0,"All","all")
            return -1
        self.pwd_in_ss = ss_pwd
        return 0

# check if a exe is present
def is_exe(cmd):
    for path in os.environ["PATH"].split(os.pathsep):
        efile = os.path.join(path, cmd)
        if os.path.exists(efile) and os.access(efile, os.X_OK):
            return True
    return None

# gets the right sudo for the env.
def set_auth_cmd(self):
        self.auth_cmd="None"
        auth_cmd = ["gksu", "beesu"]
        for i in auth_cmd:
            if is_exe(i) is not None:
                self.auth_cmd = i

# the main class for the nautilus.
class TimeSlide(nautilus.LocationWidgetProvider, nautilus.MenuProvider):
    """ Provides Slider with snapshot in a chronological order on the X axis """ 
    def __init__(self):
        self.init = True
        if not os.geteuid() == 0:
            sys.exit('Timeslider: must be run as root')
            self.init = False
            return
        #remove if root check when btrfs-progs is ready for non root 
        set_auth_cmd(self)
        if self.auth_cmd is None:
            print "Not a sudoer. timeslide initialization failed."
            self.init = False
            return
        
        self.nau = nautilus
        self.gui = gtk.Builder()
        self.gui.add_from_file("timeslider.glade")
        self.win1      = self.gui.get_object("window1")
        self.vbox1     = self.gui.get_object("vbox1")
        self.hbox1     = self.gui.get_object("hbox1")
        self.hscale1   = self.gui.get_object("hscale1")
        self.adj1      = self.gui.get_object("adj1")
        self.label1    = self.gui.get_object("label1")
        self.label2    = self.gui.get_object("label2")
        self.button1   = self.gui.get_object("button1")
        self.button2   = self.gui.get_object("button2")
        self.hbox4     = self.gui.get_object("hbox4")
        self.combobox1 = gtk.combo_box_new_text()
        self.hbox4.add(self.combobox1)
        self.combobox1.set_title("Tags")
        self.hbox4.show_all()
        self.gui.connect_signals(self)
        self.combobox1.connect("changed", self.on_combobox1_changed)
        self.pos = 0
        self.tag = "All"
        self.subvol_old = ""
        self.vbox1.set_no_show_all(True)
        print "Initializing timeslide"
        return
    
    # Calls when in a new URI
    def get_widget(self, uri, window):
        if self.init is False:
            return
        self.window  = window
        if uri[:7] == "file://":
            self.pwd = urllib.url2pathname(uri[7:])
        else:
            self.pwd = os.environ.get("HOME")

        if re.search(".auto-snapshot", self.pwd):
            #print "Timeslider doesn't handle .auto-snapshot directory yet"
            return
        # list of possible paths in the given path
        slist=[]
        for i, c in enumerate(self.pwd):
            if c == "/":
                if i != 0:
                        slist.append((self.pwd[:i]))
        slist.append(self.pwd)
        
        # find subvol
        for i in range(len(slist),0,-1):
            cmdstr = self.auth_cmd + " btrfs su list -p %s" % (slist[i-1])
            statout = commands.getstatusoutput(cmdstr)
            if statout[0] == 0:
                break
        if statout[0] != 0:
            print "btrfs su list -p failed" 
            return
        self.subvol = slist[i-1]
        
        #find pwd from subvol
        if self.subvol != self.pwd:
            self.pwd_from_subvol = self.pwd.split(self.subvol+"/").pop()
        else:
            self.pwd_from_subvol = ""      

        # Find mnt
        for i in range(0,len(slist),1):
            statout = commands.getstatusoutput(("btrfs sub list -p %s" % (slist[i])))
            if statout[0] == 0:
                break
        if statout[0] != 0:
            print "btrfs su list -p failed" 
            return
        self.mnt = slist[i]
        
        if self.subvol != self.subvol_old:
            write_display_bar(self, "")
            #self.autosnap_dir = os.path.join(self.subvol,".auto-snapshot")
            self.autosnap_dir = os.path.join(self.mnt,".autosnap")
            if os.path.isdir(self.autosnap_dir) is False:
                print "Error: No auto snapshot are available"
                return
            refresh(self, 0,"All","all")
            self.subvol_old = self.subvol

        self.vbox1.unparent()
        return self.vbox1

    # edit -> Timeslider show/hide callback routine
    def menu_activate_cb_single(self, file):
        if self.vbox1.get_no_show_all() is True:
            self.vbox1.set_no_show_all(False)
            self.vbox1.hide_all()
        else:
            self.vbox1.show_all()
            self.vbox1.set_no_show_all(True)
        pass
    
    #Nautilus entry point
    def get_file_items(self, window, files):
        mitem = nautilus.MenuItem('Nautilus::Timeslider', 'Timeslider show/hide','')
        mitem.connect('activate', self.menu_activate_cb_single)
        items=[]
        items.append(mitem)
        return items
    
    # Time scale
    def on_adj1_value_changed(self, val=-1):
        self.pos = int(math.ceil(self.adj1.get_value()))
        self.adj1.set_value(self.pos)

        #if the slide is at home
        if self.pos is not 0:
            if get_pwd_in_ss(self, self.pos) == 0:
                s = "snapshot\n"+self.pwd_in_ss
                write_display_bar(self,s)
                set_sensitive(self, self.pos, self.tag)
                mark_scale(self, self.pos)
            else:
                refresh(self, self.pos, self.tag, "all")
        else:
            s = self.label2.get_text()
            if "destroyed" not in s:
                s=""
                write_display_bar(self,s)
            set_sensitive(self, self.pos, self.tag)
            mark_scale(self, self.pos)
            self.pwd_in_ss = self.pwd
        load_new_uri(self)
        return

    #Destroy button
    def on_button1_clicked(self, what):
        if self.button1.get_label() == "Confirm Destroy":
            self.button1.set_label("Destroy")
            cmdstr = self.auth_cmd + " btrfs su delete %s" % (self.snap)
            status = commands.getstatusoutput(cmdstr)
            
            #status = commands.getstatusoutput("beesu -m " + "btrfs su delete %s" % (self.snap))
            if status[0] == 0:
                s = self.label2.get_text()+"\ndestroyed"
                write_display_bar(self, s)
                #refresh(self, 0, self.tag, "all")
                read_snaplist(self)
                create_snaplist_bytag(self,self.tag)
                mark_scale(self, 0)
                set_sensitive(self,self.pos, self.tag)
            else:
                s = self.label2.get_text()+"\nError: %s" % (status[1])
                write_display_bar(self, s)
        else:
            self.button1.set_label("Confirm Destroy")

        return
    
    #Take a Snapshot button
    def on_button2_clicked(self,what):
        status = commands.getstatusoutput("btrfs au now -t %s %s" % (self.tag, self.subvol))
        if status[0] == 0:
            s = "%s tag:%s" % (status[1],self.tag)
            write_display_bar(self, s)
            read_snaplist(self)
            create_snaplist_bytag(self,self.tag)
            mark_scale(self, 0)
            set_sensitive(self,self.pos, self.tag)
            #refresh(self, 0, self.tag, "snaplist|snaplist_bytag|scale|sensitive")
        else:
            s = "Error: %s" % (status[1])
            write_display_bar(self, s)
        return
    
    #Drop down menu with tags
    def on_combobox1_changed(self, what):
        self.tag = self.combobox1.get_active_text()
        self.pos = 0
        #refresh(self, 0, self.tag, "snaplist_bytag|scale|sensitive")
        create_snaplist_bytag(self, self.tag)
        set_sensitive(self, self.pos, self.tag)
        mark_scale(self,self.pos)
        return
