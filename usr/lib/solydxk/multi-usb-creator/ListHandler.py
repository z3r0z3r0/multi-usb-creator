#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import gettext

gettext.install("multi-usb-creator", "/usr/share/locale")


class ListHandler():

    __ROW_FIELDS = {}
    __ROW_DATA = []

    def __init__(self, rowFields):
        super(ListHandler, self).__init__()
        self.__ROW_FIELDS = rowFields
        self.rowCount = 0

    def clearList(self):
        self.__ROW_DATA.clear()

    def getList(self):
        return(self.__ROW_DATA)

    def getRow(self, rowIndex):
        if rowIndex >= 0 and rowIndex <= len(self.__ROW_DATA):
            try:
                return(self.__ROW_DATA[rowIndex])
            except:
                raise ValueError(_("Index out of range"))

    def getRowField(self, rowIndex, fieldName):
        if rowIndex >= 0 and rowIndex <= len(self.__ROW_DATA):
            try:
                return(self.__ROW_DATA[rowIndex][self.__ROW_FIELDS[fieldName]])
            except KeyError:
                return(_("Not a Field"))

            except NameError:
                return(_("Not A Field"))
        else:
            raise ValueError(_("Index out of range"))

    def setList(self, theList):
        self.__ROW_DATA.clear()
        self.__ROW_DATA = theList
        self.rowCount = len(theList)