#! /usr/bin/env python3
#-*- coding: utf-8 -*-

import subprocess
import threading
import shlex
import urllib.request
import hashlib
import logging

import gettext

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )
gettext.install("multi-usb-creator", "/usr/share/locale")


class ExecuteCommandList(threading.Thread):

    def __init__(self, commandList, theQueue):
        super(ExecuteCommandList, self).__init__()
        self.commandList = commandList
        self.theQ = theQueue

    def run(self):
        if len(self.commandList) > 0:
            for i in range(len(self.commandList)):
                commandString = shlex.split(self.commandList[i])
                try:
                    #logging.debug("Running command: {}".format(commandString))
                    retVal = subprocess.call(commandString)
                    #logging.debug("retVal: {}".format(retVal))
                    if retVal == 0:
                        self.theQ.put(retVal)
                    else:
                        logging.debug(_("ExecuteCommandList:run: Error: {}").format(retVal))
                        self.theQ.put(_("Error returned: {}").format(retVal))
                        break
                except Exception as detail:
                    # This is a best-effort attemp to fail graciously
                    self.theQ.put(_("ExecuteCommandList:run: Error: {}").format(detail))
                    logging.debug(_("ExecuteCommandList:run: Error: {}").format(detail))
        else:
            pass


class DownLoadISO(threading.Thread):

    def __init__(self, sourceURL, sourceMD5, destFileName, theQueue):
        super(DownLoadISO, self).__init__()
        self.sourceURL = sourceURL
        self.sourceMD5 = sourceMD5
        self.destFileName = destFileName
        self.theQ = theQueue

    def run(self):
        threadLock = threading.Lock()
        theResult = False
        try:
            #logging.debug("Before the acquire")
            threadLock.acquire()
            self.theQ.put(_("Downloading File"))
            #logging.debug("After the put")
            local_filename, headers = urllib.request.urlretrieve(self.sourceURL, self.destFileName)
            #logging.debug("This is the local_filename: {}".format(local_filename))
            if local_filename == self.destFileName:
                theMD5 = self.GetMD5(self.destFileName)
                if theMD5 == self.sourceMD5:
                    theResult = True
        except Exception as detail:
            logging.debug(_("DownLoadISO:run - Exception detail: {}").format(detail))
        finally:
            self.theQ.put([theResult])
            threadLock.release()

    def GetMD5(self, theFileName):
        #logging.debug("Into GetMD5, theFileName: {}".format(theFileName))
        try:
            md5Value = hashlib.md5()
            with open(theFileName, "rb") as f:
                for chunk in iter(lambda: f.read(4 * (2 ** 20)), b""):
                    md5Value.update(chunk)
            theResult = md5Value.hexdigest()
        except Exception as detail:
            theResult = ""
            logging.debug(_("DownLoadISO:GetMD5 - Exception detail: {}").format(detail))
        finally:
            return(theResult)