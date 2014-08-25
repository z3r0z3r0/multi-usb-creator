#!/usr/bin/env python3
#-*- coding: utf-8 -*-


import subprocess
import os
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )

myList = []
myList.clear()
for line in (subprocess.getoutput("mount | cut -f 1,3 -d ' '")).split("\n"):
    usbData = line.split(" ")
    if "/media" in usbData[1]:
        theDevice = usbData[0]
        theMountPoint = usbData[1]

        st = os.statvfs(theMountPoint)
        availSpace = st.f_bavail * st.f_frsize
        theSize = st.f_blocks * st.f_frsize
        logging.debug("Doing Append")
        myList.append([theDevice, theMountPoint, theSize, availSpace])

logging.debug(myList)


#mounts = {}

#for line in subprocess.check_output(['mount', '-l']).split('\n'):
    #parts = line.split(' ')
    #if len(parts) > 2:
        #mounts[parts[2]] = parts[0]

#print((mounts))


#tempList = []
#tempList.clear()
#for line in (subprocess.getoutput("mount | cut -f 1,3 -d ' '")).split("\n"):
    #logging.debug("Before line.split, {}".format(tempList))
    #parts = line.split(' ')
    #if "/media/" in parts[1]:
        #logging.debug("in If:{}".format(tempList))
        #theDevice = parts[0]
        #theMountPoint = parts[1]

        #st = os.statvfs(theMountPoint)
        #availSpace = st.f_bavail * st.f_frsize
        #theSize = st.f_blocks * st.f_frsize
        #logging.debug("Doing Append")
        #tempList.append([theDevice, theMountPoint, theSize, availSpace])

    #print((tempList))

#for line i

#tempList.append([device, label, mountpoint, int(drive_info.get('Size')), available])
#from gi.repository import Gio
#vm = Gio.VolumeMonitor.get()
#for v in vm.get_volumes():
    #print(("Name: {}".format(v.get_name())))

#for m in vm.get_mounts():
    #print(("Mount: {}".format(m.get_name())))

#for d in vm.get_connected_drives():
    #print(("Drives: {}".format(d.get_name())))


#import os
#from collections import namedtuple

#_ntuple_diskusage = namedtuple('usage', 'total used free')

#def disk_usage(path):
    #"""Return disk usage statistics about the given path.

    #Returned valus is a named tuple with attributes 'total', 'used' and
    #'free', which are the amount of total, used and free space, in bytes.
    #"""
    #st = os.statvfs(path)
    #free = st.f_bavail * st.f_frsize
    #total = st.f_blocks * st.f_frsize
    #used = (st.f_blocks - st.f_bfree) * st.f_frsize
    #return _ntuple_diskusage(total, used, free)

#>>> substring = "please help me out"
#>>> string = "please help me out so that I could solve this"
#>>> substring in string
#True