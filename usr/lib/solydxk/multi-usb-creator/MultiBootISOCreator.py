#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from gi.repository import Gtk, GLib, GObject
import logging
import config
import os
import re
import uuid
from queue import Queue
import gettext
from os.path import abspath, dirname, join, basename
from combobox import ComboBoxHandler
from treeview import TreeViewHandler

from InstalledFilesList import InstalledFilesListHandler
from ServerISOList import ServerISOListHandler
from USBDataList import USBDataListHandler
from USBCreatorDialogBox import USBCreatorDialogBox
from USBThreading import ExecuteCommandList, DownLoadISO

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )

gettext.install("multi-usb-creator", "/usr/share/locale")

# Need to initiate threads for Gtk
GObject.threads_init()


# class for the main window
class USBCreator(Gtk.Window):

    def __init__(self):
        super(USBCreator, self).__init__()

        # Where do we live?
        self.scriptDir = abspath(dirname(__file__)) + "/"

        # Now, get our configuration data
        self.settingsData = config.Config(join(self.scriptDir,
                "files/multi-usb-creator.conf"))

        # Get the path to our dialog glade file and then
        # create the object

        self.dialogBox = USBCreatorDialogBox(join(self.scriptDir, self.settingsData.getValue("localfiles", "icon-path")))

        self.builder = Gtk.Builder()
        self.builder.add_from_file(join(self.scriptDir,
                self.settingsData.getValue("localfiles", "glade-file")))

        # Main window objects
        go = self.builder.get_object
        self.USBCreatorWindow = go("USBCreatorWindow")
        self.btnClose = go("btnClose")
        self.btnExecute = go("btnExecute")
        self.btnHelp = go("btnHelp")
        self.btnListDownLoadISOs = go("btnListDownLoadISOs")
        self.btnRefresh = go("btnRefresh")
        self.btnSelectISOFile = go("btnSelectISOFile")
        self.cmbSelectedUSBDevice = go("cmbSelectedUSBDevice")
        self.cmbDeleteISO = go("cmbDeleteISO")
        self.cmbDownLoad = go("cmbDownLoad")
        self.lblAvailable = go("lblAvailable")
        self.lblRequired = go("lblRequired")
        self.lblUSBCreatorWindowTitle = go("lblUSBCreatorWindowTitle")
        self.rbAddISO = go("rbAddISO")
        self.rbCleanUSB = go("rbCleanUSB")
        self.rbDelete = go("rbDelete")
        self.rbDownLoad = go("rbDownLoad")
        self.txtAvailable = go("txtAvailable")
        self.txtISOFileName = go("txtISOFileName")
        self.txtRequired = go("txtRequired")
        self.pbCopy = go("pbCopy")
        self.lblIServerSOListWindowTitle = go("lblIServerSOListWindowTitle")

        # Cleaning the USB device is a function only available to
        # user running as (or logged in as) root. Of course, a note
        # to this effect is in the help!
        self.rbCleanUSB.set_sensitive(bool(os.getuid() == 0))

        # FileChooserDialog objects
        self.FileChooserDialog = go("FileChooserDialog")
        self.btnFileChooserDialogCancel = go("btnFileChooserDialogCancel")
        self.btnFileChooserDialogOpen = go("btnFileChooserDialogOpen")

        # The Server ISO List window
        self.ServerISOListWindow = go("ServerISOListWindow")
        self.lblIServerSOListWindowTitle = go("lblIServerSOListWindowTitle")
        self.btnServerISOListWindowClose = go("btnServerISOListWindowClose")
        self.tvServerISOData = go("tvServerISOData")

        # Help window objects
        self.HelpWindow = go("HelpWindow")
        self.lblHelpWindowTitle = go("lblHelpWindowTitle")
        self.lblHelpWindowHelpText = go("lblHelpWindowHelpText")

        # Create our handlers
        # First, our ComboBox handlers
        self.cmbHandlerSelectUSB = ComboBoxHandler(self.cmbSelectedUSBDevice, None)
        self.cmbHandlerDownLoad = ComboBoxHandler(self.cmbDownLoad, None)
        self.cmbHandlerDeleteISO = ComboBoxHandler(self.cmbDeleteISO, None)
        self.tvHandlerServerISOData = TreeViewHandler(self.tvServerISOData, None)
        self.cmbHandlerServerISO = ComboBoxHandler(self.cmbDownLoad, None)

        # Now, the data handlers
        self.usbDataHandler = USBDataListHandler()
        self.installedFilesHandler = InstalledFilesListHandler()
        self.serverISOHandler = ServerISOListHandler()

        # Might as well get the server ISO list while we're here
        self.serverISOHandler.getServerISOList(self.settingsData.getValue("url", "solydxk-iso-list-URL"), self.settingsData.getValue("localfiles", "local-iso-list"))
        # And populate the Server ISO TreeView
        self.tvHandlerServerISOData.fillTreeview(contentList=self.serverISOHandler.getTreeViewList(),
            columnTypesList=["str", "str", "str", "str", "str", "str"], firstItemIsColName=True)

        self.cmbHandlerDownLoad.fillComboBox(self.serverISOHandler.getComboBoxList())
        if self.serverISOHandler.rowCount > 0:
            self.cmbDownLoad.set_active(0)

        # Get the USB data because it all starts with the USB devices
        # and, then, populate the USB ComboBox
        #self.usbDataHandler.getUSBData()
        self.RefreshUSBSelector()

        # Translations
        self.USBCreatorWindow.set_title(_("SolydXK Multi-Boot USB Creator"))
        self.rbAddISO.set_label(_("Add ISO"))
        self.rbDownLoad.set_label(_("Down Load"))
        self.rbDelete.set_label(_("Delete"))
        self.rbCleanUSB.set_label(_("Clean USB"))
        self.lblAvailable.set_label(_("Space Available (GiB):"))
        self.lblRequired.set_label(_("Required:"))
        self.lblIServerSOListWindowTitle.set_label(_("ISOs Available for Download"))

        self.HelpWindow.set_title(_("Multi-Boot Help"))
        self.lblHelpWindowTitle.set_label(_("Multi-Boot Help"))
        self.HelpWindowPopulateText()

        # Finally, we can connect our signals, hide the FileChooserDialog
        # (just in case) # and show our main window.
        self.FileChooserDialog.hide()
        self.HelpWindow.hide()
        theHeight = self.USBCreatorWindow.get_size()[1]
        #theWidth = self.USBCreatorWindow.get_size()[0]
        self.USBCreatorWindow.resize(626, theHeight)
        self.pbCopy.set_visible(False)

        self.theQ = Queue(-1)

        self.builder.connect_signals(self)
        self.USBCreatorWindow.show()
        Gtk.main()

    ##########################################
    #
    # USBCreatorWindow Event Handlers
    #
    ##########################################
    def IsEnoughSpace(self):
        if self.requiredSpace > self.availableSpace:
            self.dialogBox.infoDialog(_("Insufficient Space Available"),
            _("The selected USB device has insuffiecient\nspace for the indicate operation."))
            return(False)
        else:
            return(True)

    def on_btnExecute_clicked(self, widget):
        if self.cmbSelectedUSBDevice.get_active() == -1:
            self.dialogBox.infoDialog(_("No USB Device"),
                (_("Please select a USB device to which to copy the .iso file")))
        else:
            if self.rbAddISO.get_active():
                if self.IsEnoughSpace():
                    self.DoISOAdd()

            elif self.rbDownLoad.get_active():
                if self.IsEnoughSpace():
                    self.DoISODownLoad()

            elif self.rbDelete.get_active():
                self.DoISODelete()

            elif self.rbCleanUSB.get_active():
                self.CleanTheUSBDevice()
            else:
                logging.debug(_("Problem with Radio Buttons"))

    def on_btnHelp_clicked(self, widget):
        self.HelpWindow.show()

    def on_btnListDownLoadISOs_clicked(self, widget):
        self.ServerISOListWindow.show()

    def on_btnRefresh_clicked(self, widget):
        self.usbDataHandler.getUSBData()
        self.RefreshUSBSelector()
        self.rbAddISO.set_active(True)

    def on_btnSelectISOFile_clicked(self, widget):
        self.FileChooserDialog.show()

    def on_cmbDeleteISO_changed(self, widget):
        self.rbDelete.set_active(True)
        #self.on_RadioButton_toggled(self.rbDelete)

    def on_cmbDownLoad_changed(self, widget):
        self.rbDownLoad.set_active(True)
        #self.on_RadioButton_toggled(self.rbDownLoad)

    def on_cmbSelectedUSBDevice_changed(self, widget):
        self.DoNewUSBSelected()
        self.rbAddISO.set_active(True)
        #self.on_RadioButton_toggled(self.rbAddISO)

    def on_RadioButton_toggled(self, widget):
        if widget.get_active():
            if self.rbAddISO.get_active():
                # Get the filename from the text entry control (if there is one).
                # Check to see if the text is the path to a file. If it is,
                # then get the size of the file and show it to the user.
                theFileName = self.txtISOFileName.get_text()
                if os.path.isfile(theFileName):
                    self.requiredSpace = int(os.path.getsize(theFileName))
                    self.txtRequired.set_text(self.Convert2Gigs(self.requiredSpace))

            elif self.rbDownLoad.get_active():
                # Get the index of the ComboBox, use that as a pointer to the data
                if self.cmbDownLoad.get_active() != -1:
                    self.requiredSpace = int(self.serverISOHandler.getFileSize(self.cmbDownLoad.get_active()))
                    self.txtRequired.set_text(self.Convert2Gigs(self.requiredSpace))

            elif self.rbDelete.get_active():
                pass
            elif self.rbCleanUSB.get_active():
                pass
            else:
                logging.debug(_("Unknown RadioButton selected"))

    def on_USBCreatorWindow_destroy(self, widget):
        Gtk.main_quit()

    ##########################################
    #
    # USBCreatorWindow utility functions
    #
    ##########################################

    # Clean the USB device indicated in the cmbSelectedUSBDevice
    def CleanTheUSBDeviceCheck(self):
        if self.theThread.is_alive():
            retVal = True
            self.pbCopy.pulse()
            if not self.theQ.empty():
                lst = self.theQ.get(False)
                if lst:
                    if isinstance(lst[0], str):
                        self.dialogBox.errorDialog(_("Error Encountered"),
                            _("MultiBootISOCreator:CleanTheUSBDeviceCheck - Error: {}").format(lst[0]))
                self.theQ.task_done()
        else:
            retVal = False
            try:
                if not self.theQ.empty():
                    lst = self.theQ.get(False)
                    if lst:
                        if isinstance(lst[0], str):
                            self.dialogBox.errorDialog(_("Error Encountered"),
                                _("MultiBootISOCreator:CleanTheUSBDeviceCheck - Error: {}").format(lst[0]))
                        else:
                            if bool(lst[0]):
                                self.dialogBox.infoDialog(_("Cleaning Is Complete"),
                                    _("The USB Device has been re-initialized.\nIt is safe to remove it and re-insert it for\nISO file copy/download operations."))
                            else:
                                self.dialogBox.errorDialog(_("Error Encountered"),
                                    _("MultiBootISOCreator:CleanTheUSBDeviceCheck\n - Error encountered during cleaning operation."))
            except Exception as detail:
                logging.debug(_("Error Encountered"),
                        _("MultiBootISOCreator:CleanTheUSBDeviceCheck - Error: {}").format(detail))
                self.dialogBox.errorDialog("MultiBootISOCreator:CleanTheUSBDeviceCheck - Error: {}".format(detail))
            finally:
                # Save our current index
                localActiveIndex = self.cmbSelectedUSBDevice.get_active()

                # Relaod all the USB related data
                self.RefreshUSBSelector()

                # Point our ComboBox back where it was
                if localActiveIndex <= self.usbDataHandler.rowCount:
                    self.cmbSelectedUSBDevice.set_active(localActiveIndex)
                elif self.usbDataHandler.rowCount > 0:
                    self.cmbSelectedUSBDevice.set_active(0)
                else:
                    self.cmbSelectedUSBDevice.set_active(-1)

                self.DoNewUSBSelected()

                self.rbAddISO.set_active(True)
                self.on_RadioButton_toggled(self.rbAddISO)

                self.SetButtonsSensitive(True)

        return(retVal)

    def CleanTheUSBDevice(self):
        if self.usbDataHandler.rowCount <= 0:
            self.dialogBox.infoDialog(_("Ummm ... No USB device"),
                _("Did you forget to mount a USB device with which we can play?"))
        else:
            response = self.dialogBox.warningDialog(_("Please confirm"),
                _("Please confirm you wish to re-initialize\nthe device\n\n{}").format(self.usbDataHandler.getDevice(self.cmbSelectedUSBDevice.get_active())))
            if response != Gtk.ResponseType.OK:
                self.dialogBox.infoDialog(_("Operation Cancelled"),
                    _("Operation to re-initialize the\n" +
                    "USB device has been cancelled."))
            else:
                theCommandList = []
                theCommandList.clear()

                # The device in the data comes back with the partition number on it.
                theDevice = self.usbDataHandler.getDevice(self.cmbSelectedUSBDevice.get_active())[:-1]

                # This is where we are going to mount the device to install grub. We need to
                # ensure that whatever mount point we choose is not already in use. One way
                # to do that is to create it and then blow it away when we are done.
                while True:
                    rootMountPoint = "/media/{}".format((uuid.uuid1()).hex)
                    if not os.path.exists(rootMountPoint):
                        os.makedirs(rootMountPoint)
                        break

                # The device is mounted at /media/<user>/<usb label>. We want to unmount that puppy so
                # we can do our thang to it.
                theCommandList.append("umount {}".format(self.usbDataHandler.getMountPoint(self.cmbSelectedUSBDevice.get_active())))
                theCommandList.append("dd if=/dev/zero of={} bs=4M count=25".format(theDevice))
                theCommandList.append("parted -a optimal -s {} mklabel msdos".format(theDevice))
                theCommandList.append("parted -a optimal -s {} mkpart primary fat32 0% 100% set 1 boot on".format(theDevice))
                theCommandList.append("mkdosfs -F32 -n 'SOLYDXK' -I {}1".format(theDevice))

                # OK, now mount it where we can find it.
                theCommandList.append("mount {0}1 {1}".format(theDevice, rootMountPoint))
                theCommandList.append("tar zxf {0}/files/solydxk-usb.tar.gz  -C {1}".format(self.scriptDir, rootMountPoint))
                theCommandList.append("grub-install --root-directory={0} --no-floppy --recheck --force {1}".format(rootMountPoint, theDevice))
                theCommandList.append("umount {}1".format(theDevice))
                theCommandList.append("rmdir {0}".format(rootMountPoint))

                self.theThread = ExecuteCommandList(theCommandList, self.theQ)
                self.theThread.daemon = True
                self.theThread.start()
                self.theQ.join()
                self.pbCopy.set_text(_("Cleaning Device"))
                self.pbCopy.set_show_text(True)
                self.SetButtonsSensitive(False)
                GLib.timeout_add(100, self.CleanTheUSBDeviceCheck)

    def Convert2Gigs(self, theSize):
        return("{:.2f}".format((float(theSize) / float(2 ** 30))))

    def CopyCheck(self, destFileName):
        if self.theThread.is_alive():
            retVal = True
            self.pbCopy.pulse()
            if not self.theQ.empty():
                lst = self.theQ.get(False)
                if lst:
                    if isinstance(lst[0], str):
                        self.dialogBox.errorDialog(_("Error Encountered"),
                            _("MultiBootISOCreator:CopyCheck - Error: {}").format(lst[0]))
                        removeFile = True
                self.theQ.task_done()
        else:
            removeFile = False
            retVal = False
            try:
                if not self.theQ.empty():
                    lst = self.theQ.get(False)
                    if lst:
                        if isinstance(lst[0], str):
                            self.dialogBox.errorDialog(_("Error Encountered"),
                                _("MultiBootISOCreator:CopyCheck - Error: {}").format(lst[0]))
                            removeFile = True
                        else:
                            if bool(lst[0]):
                                self.txtISOFileName.set_text("")
                                self.dialogBox.infoDialog(_("Copy Is Complete"),
                                    _("The USB Device has been updated.\n" +
                                    "It is safe to unmount and remove it."))
                            else:
                                self.dialogBox.errorDialog(_("Error Encountered"),
                                    _("MultiBootISOCreator:CopyCheck - Error encountered during copy."))
                                removeFile = True
                    self.theQ.task_done()

            except Exception as detail:
                logging.debug(_("MultiBootISOCreator:CopyCheck - Error: {}").format(detail))
                self.dialogBox.errorDialog(_("Error Encountered"),
                    _("MultiBootISOCreator:CopyCheck - Error: {}").format(detail))
                removeFile = True

            finally:
                if removeFile:
                    if os.path.isfile(destFileName):
                        os.remove(destFileName)
                del self.theThread

                # Save our current index
                localActiveIndex = self.cmbSelectedUSBDevice.get_active()

                # Relaod all the USB related data
                self.RefreshUSBSelector()

                # Point our ComboBox back where it was
                if localActiveIndex <= self.usbDataHandler.rowCount:
                    self.cmbSelectedUSBDevice.set_active(localActiveIndex)
                elif self.usbDataHandler.rowCount > 0:
                    self.cmbSelectedUSBDevice.set_active(0)
                else:
                    self.cmbSelectedUSBDevice.set_active(-1)

                self.DoNewUSBSelected()
                self.UpdateUSBGrubConfig()

                self.rbAddISO.set_active(True)
                self.on_RadioButton_toggled(self.rbAddISO)

                self.SetButtonsSensitive(True)

        return(retVal)

    def CopyFile(self, theFileName):
        commandList = []
        commandList.clear()
        commandList.append("cp {0} {1}".format(self.txtISOFileName.get_text(), theFileName))
        self.theThread = ExecuteCommandList(commandList, self.theQ)
        self.theThread.daemon = True
        self.theThread.start()
        self.theQ.join()
        self.pbCopy.set_text(_("Copying File"))
        self.pbCopy.set_show_text(True)
        self.SetButtonsSensitive(False)
        GLib.timeout_add(100, self.CopyCheck, theFileName)

    def DownLoadCheck(self, destFileName):
        if self.theThread.is_alive():
            retVal = True
            self.pbCopy.pulse()
            if not self.theQ.empty():
                lst = self.theQ.get(False)
                if lst:
                    self.pbCopy.set_text(lst[0])
                    self.pbCopy.set_show_text(True)
                self.theQ.task_done()
        else:
            retVal = False
            removeFile = False
            try:
                if not self.theQ.empty():
                    lst = self.theQ.get(False)
                    if lst:
                        if isinstance(lst[0], str):
                            # We have an error message
                            self.dialogBox.errorDialog(_("Error Encountered"),
                                _("Error encountered during download: {}").format(lst[0]))
                            removeFile = True
                        else:
                            # Take care of the results of the MD5Sum calculation
                            if lst[0]:
                                # All is right in the world
                                self.dialogBox.infoDialog(_("Download Is Complete"),
                                    _("The USB Device has been updated.\nIt is safe to unmount and remove it."))
                            else:
                                # Bad MD5Sum
                                self.dialogBox.errorDialog(_("MD5Sum is not a match"),
                                _("Download complete but appears to be\n" +
                                "corrupted. The computed MD5Sum does\n" +
                                "not match the value from the server.\n\n" +
                                "The file has been removed from the USG device."))
                                removeFile = True

            except Exception as detail:
                logging.debug(_("MultiBootISOCreator:DownLoadCheck - exception: {}").format(detail))
                self.dialogBox(_("Error in DownLoad."), _("MultiBootISOCreator:DownLoadCheck - exception: {}").format(detail))
                removeFile = True

            finally:
                self.theQ.task_done()
                del self.theThread

                if removeFile:
                    if os.path.isfile(destFileName):
                        os.remove(destFileName)

                # No matter whether we were successful or not, we need to clean
                # up our mess and set the controls back to their rightful state.
                # Save our current index
                localActiveIndex = self.cmbSelectedUSBDevice.get_active()

                # Relaod all the USB related data
                self.RefreshUSBSelector()

                # Point our ComboBox back where it was
                if localActiveIndex <= self.usbDataHandler.rowCount:
                    self.cmbSelectedUSBDevice.set_active(localActiveIndex)
                elif self.usbDataHandler.rowCount > 0:
                    self.cmbSelectedUSBDevice.set_active(0)
                else:
                    self.cmbSelectedUSBDevice.set_active(-1)

                self.DoNewUSBSelected()
                self.UpdateUSBGrubConfig()

                self.rbDownLoad.set_active(True)
                self.on_RadioButton_toggled(self.rbDownLoad)

                self.SetButtonsSensitive(True)

        return(retVal)

    def DownLoadFile(self):
        sourceURL = self.serverISOHandler.getDownLoadURL(self.cmbDownLoad.get_active())
        theMD5 = self.serverISOHandler.getMD5Sum(self.cmbDownLoad.get_active())
        destFileName = "{0}/{1}.iso".format(self.usbDataHandler.getMountPoint(self.cmbSelectedUSBDevice.get_active()),
            self.serverISOHandler.getSpinID(self.cmbDownLoad.get_active()))
        self.theThread = DownLoadISO(sourceURL, theMD5, destFileName, self.theQ)
        self.theThread.daemon = True
        self.theThread.start()
        self.theQ.join()

        self.pbCopy.set_show_text(True)
        self.SetButtonsSensitive(False)
        GLib.timeout_add(100, self.DownLoadCheck, destFileName)

    def DoISOAdd(self):
        if self.txtISOFileName.get_text() != "":
            theMessage = _("Please confirm you wish to copy the file\n\n\"{0}\"\n\nto the selected USB device.").format(self.txtISOFileName.get_text())
            response = self.dialogBox.warningDialog("Please Confirm ISO Copy", theMessage)

            if response == Gtk.ResponseType.OK:
                thePattern = re.compile(self.settingsData.getValue("regex-patterns", "solydxk-iso-file-pattern"))
                theBaseName = basename(self.txtISOFileName.get_text())
                if not thePattern.match(theBaseName):
                    self.dialogBox.infoDialog(_("Not a Known SolydXK ISO"),
                        _("The filename supplied does not match that\n" +
                        "of a known SolydXK ISO file.\n\n" +
                        "Please check your information and try again."))
                else:
                    theBaseName = theBaseName[:8] + ".iso"
                    theFileName = "{0}/{1}".format(self.usbDataHandler.getMountPoint(self.cmbSelectedUSBDevice.get_active()), theBaseName)
                    if os.path.isfile(theFileName):
                        response = self.dialogBox.questionDialog(_("Over-Write File?"),
                            _("The selected file already exists on the USB device.\n\nOver-write this file?"))
                    else:
                        response = Gtk.ResponseType.YES

                    if response == Gtk.ResponseType.YES:
                        self.CopyFile(theFileName)
        else:
            self.dialogBox.infoDialog(_("No file selected"),
            _("Please select a file to be copied to the selected USB Device"))

    def DoISODownLoad(self):
        if self.cmbDownLoad.get_active() == -1:
            self.dialogBox.infoDialog(_("No file selected"),
                _("Please select a file to be downloaded to the USB device"))
        else:
            self.DownLoadFile()

    def DoISODelete(self):
        localActiveIndex = self.cmbDeleteISO.get_active()
        if localActiveIndex == -1:
            self.dialogBox.infoDialog(_("No file selected"),
                _("Please select a file to be deleted from the USB device."))
        else:
            theFileName = "{0}/{1}".format(self.usbDataHandler.getMountPoint(self.cmbSelectedUSBDevice.get_active()),
                self.installedFilesHandler.getFileName(localActiveIndex))
            response = self.dialogBox.questionDialog(_("Please confirm file deletion"),
                _("Please confirm you wish to delete the file\n\n{}\n\nfrom the selected USB device.").format(theFileName))
            if response == Gtk.ResponseType.YES:
                if os.path.isfile(theFileName):
                    os.remove(theFileName)

                    # Rebuild all our USB data
                    localActiveIndex = self.cmbSelectedUSBDevice.get_active()
                    self.RefreshUSBSelector()
                    self.cmbSelectedUSBDevice.set_active(localActiveIndex)
                    self.UpdateUSBGrubConfig()
                    self.dialogBox.infoDialog(_("Operation complete"), _("The selected file has been deleted."))
                else:
                    self.dialogBox.errorDialog(_("File not found."),
                        _("The indicated file was not found on the USB device."))

    def DoNewUSBSelected(self):
        if(len(self.usbDataHandler.getList())) > 0:
            self.installedFilesHandler.buildInstalledFilesList(self.usbDataHandler.getMountPoint(self.cmbSelectedUSBDevice.get_active()))
            self.cmbHandlerDeleteISO.fillComboBox(self.installedFilesHandler.getFilesListComboBoxData())
            if self.installedFilesHandler.rowCount > 0:
                self.cmbDeleteISO.set_active(0)

            self.availableSpace = int(self.usbDataHandler.getAvailableSpace(self.cmbSelectedUSBDevice.get_active()))
            self.txtAvailable.set_text(self.Convert2Gigs(self.availableSpace))
            self.requiredSpace = 0
            self.txtRequired.set_text("")
        else:
            self.txtAvailable.set_text("")
            self.availableSpace = int(0)

    # Refresh the cmbSelectedUSBDevice and associated data
    def RefreshUSBSelector(self):
        self.usbDataHandler.getUSBData()
        if len(self.usbDataHandler.getList()) > 0:
            self.cmbHandlerSelectUSB.fillComboBox(self.usbDataHandler.getUSBComboBoxData())
            self.cmbSelectedUSBDevice.set_active(0)
            self.DoNewUSBSelected()
        else:
            self.cmbHandlerSelectUSB.clearComboBox()
            self.DoNewUSBSelected()

    def SetButtonsSensitive(self, newState):
        self.pbCopy.set_visible(not newState)
        self.btnClose.set_sensitive(newState)
        self.btnExecute.set_sensitive(newState)
        self.btnHelp.set_sensitive(newState)
        self.btnListDownLoadISOs.set_sensitive(newState)
        self.btnRefresh.set_sensitive(newState)
        self.btnSelectISOFile.set_sensitive(newState)

    def UpdateUSBGrubConfig(self):
        if self.installedFilesHandler.rowCount <= 0:
            self.dialogBox.infoDialog(_("No USB Device found."), _("It appears you forgot to mount a USB device!"))
        else:
            self.SetButtonsSensitive(False)

            theGrubFile = "{0}/boot/grub/grub.cfg".format(self.usbDataHandler.getMountPoint(self.cmbSelectedUSBDevice.get_active()))
            if os.path.isfile(theGrubFile):
                os.remove(theGrubFile)

            with open(theGrubFile, "w") as outFile:
                outFile.write("# Set the paths to the iso files\n")
                for i in range(self.installedFilesHandler.rowCount):
                    theFileName = self.installedFilesHandler.getFileName(i)
                    outFile.write("set {0}=\"/{1}\"\n".format(theFileName[:-4], theFileName))

                outFile.write("\n# Seconds to wait until starting the default menu entry\n")
                outFile.write("set timeout=10\n\n")
                outFile.write("# Default menu entry (0 = first)\nset default=0\n\n")
                outFile.write("loadfont /boot/grub/fonts/unicode.pf2\n")
                outFile.write("set gfxmode=auto\n")
                outFile.write("#set gfxmode=1024x768\n")
                outFile.write("insmod efi_gop\n")
                outFile.write("insmod efi_uga\n")
                outFile.write("insmod gfxterm\n")
                outFile.write("set gfxpayload=keep\n")
                outFile.write("terminal_output gfxterm\n\n")

                outFile.write("insmod png\n")
                outFile.write("background_image -m stretch /boot/grub/grubbg.png\n")
                outFile.write("set menu_color_normal=white/black\n")
                outFile.write("set menu_color_highlight=dark-gray/white\n\n")
                outFile.write("# Create the menu entries here:\n")

                # This block of code is for the way SolydXK names the various spins, as of 23AUG2014.
                # At some time in the future, Debian will promote Jessie to stable and SolydXK
                # will be changing the names of the spins. At that time, this block of code should
                # be removed from the application and the next (commented) block should be uncommented
                # and tested.
                for i in range(self.installedFilesHandler.rowCount):
                    theFileName = self.installedFilesHandler.getFileName(i)[:-4]

                    if theFileName[-2:] == "be":
                        theEdition = _("Business Edition 64-bit")
                    elif theFileName[-2:] == "bo":
                        theEdition = _("Back Office 64-bit")
                    else:
                        theEdition = _("Home Edition ") + theFileName[-2:] + "-bit"

                    if theFileName[-3:-2] == "k":
                        theDeskTop = "KDE"
                    else:
                        theDeskTop = "Xfce"

                    outFile.write("menuentry \"Solyd{0} {1} (with {2} desktop)\" {3}\n".format(theFileName[-3:-2], theEdition, theDeskTop, "{"))
                    outFile.write("bootoptions=\"findiso=${0} boot=live config username=solydxk hostname=solydxk quite splash\"\n".format(theFileName))
                    outFile.write("search --set -f ${0}\n".format(theFileName))
                    outFile.write("loopback loop ${0}\n".format(theFileName))
                    outFile.write("linux (loop)/live/vmlinuz $bootoptions\n")
                    outFile.write("initrd (loop)/live/initrd.img\n}\n")

                # This is the block of code that should be uncommented when Jessie is promoted to stable.
                # This block assumes that the first two columns of iso-data.csv file will be formatted as:
                # solydk32	SolydK 32-bit
                # solydk64	SolydK 64-bit
                # solydx32	SolydX 32-bit
                # solydx64	SolydX 64-bit
                # solydkbo	SolydK BO 64-bit
                # solydkee32	SolydK EE 32-bit
                # solydkee64	SolydK EE 64-bit
                # solydxee32	SolydX EE 32-bit
                # solydxee64	SolydX EE 64-bit

                #for i in range(self.installedFilesHandler.rowCount):
                    #theFileName = self.installedFilesHandler.getFileName(i)[:-4]

                    #if theFileName[-2:] == "be":
                        #theEdition = _(" Back Office Edition")
                        #theArch = "64"
                    #else:
                        #theArch = theFileName[-2:]
                        #if theFileName[-4:-2] == "ee":
                            #theEdition = _(" Enthusiast's Edition")
                        #else:
                            #theEdition = ""

                    #if theFileName[-3:-2] == "k":
                        #theDeskTop = "KDE"
                    #else:
                        #theDeskTop = "Xfce"

                    #outFile.write("menuentry \"Solyd{} {}-bit (with {} desktop\" {}".format(theEdition, theArch, theDeskTop, "{"))
                    #outFile.write("bootoptions=\"findiso=${0} boot=live config username=solydxk hostname=solydxk quite splash\"\n".format(theFileName))
                    #outFile.write("search --set -f ${0}\n".format(theFileName))
                    #outFile.write("loopback loop ${0}\n".format(theFileName))
                    #outFile.write("linux (loop)/live/vmlinuz $bootoptions\n")
                    #outFile.write("initrd (loop)/live/initrd.img\n}\n")

            self.dialogBox.infoDialog(_("GRUB re-write complete"),
                _("Please remove the USB device.\n\n" +
                "Please re-insert the USB device\n" +
                "If you wish to install ISO files.\n"))
            self.SetButtonsSensitive(True)

    ##########################################
    #
    # FileChooserDialog Event Handlers
    #
    ##########################################
    def on_FileChooserDialog_cancel(self, widget):
        self.txtISOFileName.set_text("")
        self.FileChooserDialog.hide()
        self.rbAddISO.set_active(True)
        self.on_RadioButton_toggled(self.rbAddISO)

    def on_FileChooserDialog_open(self, widget):
        self.txtISOFileName.set_text(self.FileChooserDialog.get_filename())
        self.FileChooserDialog.hide()
        self.rbAddISO.set_active(True)
        self.on_RadioButton_toggled(self.rbAddISO)

    def on_btnHelpWindowOK_clicked(self, widget):
        self.HelpWindow.hide()

    def on_HelpWindow_destroy(self, widget):
        self.HelpWindow.hide()

    def HelpWindowPopulateText(self):
        self.lblHelpWindowHelpText.set_label(
_("""-  Select USB - Using the ComboBox, select the USB device to be used as the Multi-Boot device.

-  Refresh - Clicking this button will cause the list of  USB devices to be refreshed. This can be useful if one starts the application before inserting the intended  target USB device.

-  Add ISO - This option allows for the copying of an already downloaded SolydXK .iso file to the target USB device.

-  File - This button opens a FileChooserDialog to be used to select the source .iso file. The path to the selected .iso file will be written to the TextEntry control.

-  Down Load - This option allows for downloading a SolydXK .iso file from the distro servers. The downloaded file will be written directly to the selected USB device.

-  Information - Opens a window showing a list of all the .iso files available for download, with associated metadata (size, m35sum, etc).

-  Delete - Use this option to remove an .iso file from the target USB device. Can be useful if there are old files there and you need more space for a new file ... or to over-write an old file with an updated version.

-  Clean USB - It sometimes happens that a USB device will need to be completely and thoroughly erased before the created USB will successfully boot. This option (available only run application is run as root) allows the user to completely re-initialize the USB device. All data will be deleted, a new partition table, a new data partition created, all required files written, and grub installed.

-  USB Space - This line indicates the amount of spaces available on the target USB device and the amount of space required to write the selected .iso file to the target USB device.

-  Help - This message

-  Execute - Perform the user selected operation.

-  Close - Exit the program."""))

    ##########################################
    #
    # ServerISOListWindow Event Handlers
    #
    ##########################################
    def on_btnServerISOListWindowClose_clicked(self, widget):
        self.ServerISOListWindow.hide()

if __name__ == "__main__":
    try:
        USBCreator()
        #Gtk.main()
    except KeyboardInterrupt:
        pass
