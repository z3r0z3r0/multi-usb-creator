#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import logging
import os
import glob
from ListHandler import ListHandler

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )


class InstalledFilesListHandler(ListHandler):

    # filename        :    Full path to the file
    # filesize        :    Full (numeric) file size
    __ROW_FIELDS = dict(FileName=0, FileSize=1)

    def __init__(self):
        super(InstalledFilesListHandler, self).__init__(self.__ROW_FIELDS)
        self.clearList()

    # thePath - This is the mount point of our USB device
    #           from which we are to get the list of files.
    def buildInstalledFilesList(self, thePath):
        tempList = []
        tempList.clear()
        if os.path.isdir(thePath):
            curDir = os.getcwd()
            os.chdir(thePath)
            for myFile in glob.glob("*.iso"):
                metadata = os.stat(myFile)
                tempList.append([myFile, int(metadata.st_size)])

            os.chdir(curDir)
        if len(tempList) > 0:
            self.setList(tempList)
        else:
            self.clearList()

    def getFileName(self, rowIndex):
        return(self.getRowField(rowIndex, 'FileName'))

    def getFileSize(self, rowIndex):
        return(self.getRowField(rowIndex, 'FileSize'))

    def getFilesListComboBoxData(self):
        tempList = []
        tempList.clear()
        if len(self.getList()) > 0:
            for i in range(len(self.getList())):
                tempSize = float(self.getFileSize(i)) / float(2 ** 30)
                tempList.append("{0} ({1:.2f} GiB)".format(self.getFileName(i), tempSize))
        return(tempList)
