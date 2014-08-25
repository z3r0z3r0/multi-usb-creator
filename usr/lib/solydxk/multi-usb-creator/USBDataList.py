#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import dbus
import os
import re
import subprocess
import logging
from subprocess import check_output as qx
from configparser import ConfigParser
from ListHandler import ListHandler

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )


class USBDataListHandler(ListHandler):

    __ROW_FIELDS = dict(Device=0, MountPoint=1, DeviceSize=2, AvailableSpace=3)

    def __init__(self):
        super(USBDataListHandler, self).__init__(self.__ROW_FIELDS)
        self.clearList()

    def getDevice(self, rowIndex):
        return(self.getRowField(rowIndex, 'Device'))

    def getMountPoint(self, rowIndex):
        return(self.getRowField(rowIndex, 'MountPoint'))

    def getDeviceSize(self, rowIndex):
        return(self.getRowField(rowIndex, 'DeviceSize'))

    def getAvailableSpace(self, rowIndex):
        return(self.getRowField(rowIndex, 'AvailableSpace'))

    def getUSBComboBoxData(self):
        tempList = []
        tempList.clear()
        for i in range(len(self.getList())):
            tempList.append("{0} ({1:.2f} GiB)".format(self.getDevice(i),
                (float(self.getDeviceSize(i)) / float(2 ** 30))))
        return(tempList)

    def getUSBData(self):
        tempList = []
        tempList.clear()
        for line in (subprocess.getoutput("mount | cut -f 1,3 -d ' '")).split("\n"):
            usbData = line.split(" ")
            if "/media" in usbData[1]:
                theDevice = usbData[0]
                theMountPoint = usbData[1]

                st = os.statvfs(theMountPoint)
                availSpace = st.f_bavail * st.f_frsize
                theSize = st.f_blocks * st.f_frsize
                tempList.append([theDevice, theMountPoint, theSize, availSpace])
        if len(tempList) != 0:
            tempList.sort(key=lambda x: x[0])
            self.setList(tempList)

    #def getUSBDataHold(self):
        ## Out temporary list
        #tempList = []
        #tempList.clear()
        #bus = dbus.SystemBus()
        #ud_manager_obj = bus.get_object('org.freedesktop.UDisks2', '/org/freedesktop/UDisks2')
        #om = dbus.Interface(ud_manager_obj, 'org.freedesktop.DBus.ObjectManager')
        #for k, v in list(om.GetManagedObjects().items()):
            #drive_info = v.get('org.freedesktop.UDisks2.Block', {})
            #if drive_info.get('IdUsage') == 'filesystem' and not drive_info.get('HintSystem'):

                #p = re.compile('\d')
                #m = p.match(k[-1])
                #if m:
                    ## the Device, in the form /dev/sdg1
                    #device = '/dev/' + k[-4:]

                    ## The volume label
                    #label = "{0}".format(drive_info.get("IdLabel"))

                    ## Where is it mounted on the system
                    #info = self.udisks_info(device)
                    #mountpoint = """{mount paths}""".format_map(info)

                    ## And, the amount of space still available on the device
                    #if mountpoint != '':
                        #s = os.statvfs(mountpoint)
                        #available = int(s.f_frsize * s.f_bavail)
                    #else:
                        #available = 0

                    ## Load this device into our temporary list
                    #tempList.append([device, label, mountpoint, int(drive_info.get('Size')), available])

        ## If we got data, sort the list on the device.
        ## Again, if we got data, then we need to set our object's list to this temporary list.
        #if len(tempList) != 0:
            #tempList.sort(key=lambda x: x[0])
            #self.setList(tempList)
        #else:
            ## Since we didn't get any data, we need to make sure
            ## that out object's list is empty.
            #self.clearList()

    #def parse(self, text):
        #parser = ConfigParser()
        #parser.read_string('[DEFAULT]\n' + text)
        #return parser['DEFAULT']

    #def udisks_info(self, device):
    ## get udisks output
        #out = qx(['udisks', '--show-info', device]).decode()

        ## strip header & footer
        #out = out[out.index('\n') + 1:]
        #i = out.find('=====')
        #if i != -1:
            #out = out[:i]

        #return self.parse(out)