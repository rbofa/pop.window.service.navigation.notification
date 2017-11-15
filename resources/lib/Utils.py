import xbmc
import xbmcgui
import xbmcaddon
import inspect
import sys
if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

addonSettings = xbmcaddon.Addon(id='pop.window.service.navigation.notification')
language = addonSettings.getLocalizedString
KODI_VERSION = int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0])

def logMsg(title, msg, level=1):
    logLevel = int(addonSettings.getSetting("logLevel"))
    WINDOW = xbmcgui.Window(10000)
    WINDOW.setProperty('logLevel', str(logLevel))
    if logLevel >= level:
        if logLevel == 2:  # inspect.stack() is expensive
            try:
                xbmc.log(title + " -> " + inspect.stack()[1][3] + " : " + str(msg),level=xbmc.LOGNOTICE)
            except UnicodeEncodeError:
                xbmc.log(title + " -> " + inspect.stack()[1][3] + " : " + str(msg.encode('utf-8')),level=xbmc.LOGNOTICE)
        else:
            try:
                xbmc.log(title + " -> " + str(msg),level=xbmc.LOGNOTICE)
            except UnicodeEncodeError:
                xbmc.log(title + " -> " + str(msg.encode('utf-8')),level=xbmc.LOGNOTICE)
