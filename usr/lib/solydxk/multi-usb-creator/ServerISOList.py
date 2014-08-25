#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import urllib.request
import csv
from ListHandler import ListHandler
import gettext

gettext.install("multi-usb-creator", "/usr/share/locale")


class ServerISOListHandler(ListHandler):

    __ROW_FIELDS = dict(SpinID=0, SpinName=1, Version=2, DownLoadURL=3, FileSize=4, MD5Sum=5)

    def __init__(self):
        super(ServerISOListHandler, self).__init__(self.__ROW_FIELDS)
        self.clearList()

    def getSpinID(self, rowIndex):
        return(self.getRowField(rowIndex, "SpinID"))

    def getSpinName(self, rowIndex):
        return(self.getRowField(rowIndex, "SpinName"))

    def getVersion(self, rowIndex):
        return(self.getRowField(rowIndex, "Version"))

    def getDownLoadURL(self, rowIndex):
        return(self.getRowField(rowIndex, "DownLoadURL"))

    def getFileSize(self, rowIndex):
        return(self.getRowField(rowIndex, "FileSize"))

    def getMD5Sum(self, rowIndex):
        return(self.getRowField(rowIndex, "MD5Sum"))

    def getComboBoxList(self):
        tempList = []
        tempList.clear()
        for i in range(len(self.getList())):
            tempList.append("{0} ({1:.2f} GiB)".format(self.getSpinName(i), (float(self.getFileSize(i)) / float(2 ** 30))))
        return(tempList)

    def getServerISOList(self, theDataFileURL, theLocalFileName):
        try:
            tempList = []
            tempList.clear()
            # This is one test to see if the user has Internet connection
            # The first line is a test for failure. If it fails, an
            # exception will be thrown ...
            #response = urllib.request.urlopen("192.168.1.255")
            #urllib.request.urlopen("http://www.google.com")

            # Now to get the data
            urllib.request.urlretrieve(theDataFileURL, theLocalFileName)

            # Now, load the data into our list
            with open(theLocalFileName, "r") as isoFile:
                reader = csv.reader(isoFile, delimiter=",")
                # Toss the CSV header row - it's garbage to us!
                next(reader, None)
                for row in reader:
                    tempList.append(row)

            self.setList(tempList)
        except:
            self.clearList()

    def getTreeViewList(self):
        tempList = []
        tempList.clear()
        tempList.append([_("Spin ID"), _("Spin Name"), _("Version"), _("Download URL"), _("File Size (GiB)"), _("MD5Sum")])
        for i in range(self.rowCount):
            tempList.append([self.getSpinID(i), self.getSpinName(i), self.getVersion(i), self.getDownLoadURL(i),
                "{:.2f}".format((float(self.getFileSize(i)) / float(2 ** 30))), self.getMD5Sum(i)])

        return(tempList)