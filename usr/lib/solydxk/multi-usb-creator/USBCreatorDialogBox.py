#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from gi.repository import Gtk


class USBCreatorDialogBox(Gtk.Dialog):

    def __init__(self, iconPath):
        super(USBCreatorDialogBox, self).__init__()
        self.iconPath = iconPath

    def infoDialog(self, theFirstLine, theMessage):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, theFirstLine)

        dImage = Gtk.Image()
        dImage.set_from_file(self.iconPath + "dialog-information.svg")
        dialog.set_image(dImage)

        dialog.format_secondary_text(theMessage)
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def errorDialog(self, theFirstLine, theMessage):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, theFirstLine)

        dImage = Gtk.Image()
        dImage.set_from_file(self.iconPath + "dialog-error.svg")
        dialog.set_image(dImage)

        dialog.format_secondary_text(theMessage)
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def warningDialog(self, theFirstLine, theMessage):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK_CANCEL, theFirstLine)

        dImage = Gtk.Image()
        dImage.set_from_file(self.iconPath + "dialog-warning.svg")
        dialog.set_image(dImage)

        dialog.format_secondary_text(theMessage)
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
        return(response)

    def questionDialog(self, theFirstLine, theMessage):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, theFirstLine)

        dImage = Gtk.Image()
        dImage.set_from_file(self.iconPath + "dialog-question.png")
        dialog.set_image(dImage)

        dialog.format_secondary_text(theMessage)
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
        return(response)