#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from gi.repository import Gtk, GObject


class ComboBoxHandler(GObject.GObject):

    def __init__(self, combobox, loggerObject=None):
        GObject.GObject.__init__(self)
        self.combobox = combobox
        self.log = loggerObject

    # Clear treeview
    def clearComboBox(self):
        liststore = self.combobox.get_model()
        if liststore is not None:
            liststore.clear()
            self.combobox.set_model(liststore)
        self.setValue("")

    def fillComboBox(self, dataList, select_value=None):
        self.clearComboBox()
        liststore = self.combobox.get_model()
        if liststore is None:
            liststore = Gtk.ListStore(str)
            if self.combobox.get_has_entry():
                entry = self.combobox.get_child()
                entry.set_can_focus(True)
            else:
                cell = Gtk.CellRendererText()
                self.combobox.pack_start(cell, True)
                self.combobox.add_attribute(cell, "text", 0)
        for data in dataList:
            liststore.append([str(data)])
        self.combobox.set_model(liststore)
        if select_value is not None:
            self.selectValue(select_value)

    def selectValue(self, value, valueColNr=0):
        i = 0
        activeIndex = -1
        liststore = self.combobox.get_model()
        for data in liststore:
            if data[valueColNr] == value:
                activeIndex = i
                break
            i += 1
        if self.combobox.get_has_entry():
            self.combobox.set_entry_text_column(valueColNr)
            if activeIndex < 0:
                self.setValue(value)
        else:
            if activeIndex < 0:
                activeIndex = 0
        self.combobox.set_active(activeIndex)

    def setValue(self, value):
        if self.combobox.get_has_entry():
            entry = self.combobox.get_child()
            entry.set_text(value)

    def getValue(self):
        value = None
        if self.combobox.get_has_entry():
            entry = self.combobox.get_child()
            value = entry.get_text().strip()
        else:
            model = self.combobox.get_model()
            value = model.get_value(self.combobox.get_active_iter(), 0)
        return value

# Register the class
GObject.type_register(ComboBoxHandler)