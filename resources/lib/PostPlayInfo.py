import xbmc
import xbmcaddon
import xbmcgui
from platform import machine
import time
import threading

ACTION_PLAYER_STOP = 13
OS_MACHINE = machine()

PASSOUT_PROTECTION_DURATION_SECONDS = 7200
PASSOUT_LAST_VIDEO_DURATION_MILLIS = 1200000

class PostPlayInfo(xbmcgui.WindowXML):

    PREV_BUTTON_ID = 101
    NEXT_BUTTON_ID = 102

    HOME_BUTTON_ID = 201
    SPOILERS_BUTTON_ID = 202

    NEXTUP_LIST_ID = 400

    def __init__(self, *args, **kwargs):
        xbmc.log("PostPlayInfo ->  init called",level=xbmc.LOGNOTICE)
        if OS_MACHINE[0:5] == 'armv7':
            xbmcgui.WindowXML.__init__(self)
        else:
            xbmcgui.WindowXML.__init__(self, *args, **kwargs)

        xbmc.log("PostPlayInfo ->  init called 2",level=xbmc.LOGNOTICE)

        self._winID = None
        self.action_exitkeys_id = [10, 13]
        self.item = None
        self.previousitem = None
        self.upnextlist = []
        self.cancel = False
        self.autoplayed = False
        self.playAutomatically = True

        self.previous = None
        self.timeout = None
        self.showStillWatching = False
        self.addonSettings = xbmcaddon.Addon(id='pop.window.service.navigation.notification')

        xbmc.log("PostPlayInfo ->  init completed",level=xbmc.LOGNOTICE)

    def onInit(self):
        xbmc.log("PostPlayInfo ->  onInit called",level=xbmc.LOGNOTICE)
        self.upNextControl = self.getControl(self.NEXTUP_LIST_ID)
        self.spoilersControl = self.getControl(self.SPOILERS_BUTTON_ID)
        self._winID = xbmcgui.getCurrentWindowId()
        playMode = self.addonSettings.getSetting("autoPlayMode")
        if playMode == "1":
            self.playAutomatically = False

        self.setInfo()
        self.setPreviousInfo()
        self.fillUpNext()
        self.prepareSpoilerButton()
        self.prepareStillWatching()
        self.startTimer()

        if self.item is not None:
            self.setFocusId(self.NEXT_BUTTON_ID)
        else:
            self.setFocusId(self.PREV_BUTTON_ID)

        xbmcgui.Window(10000).clearProperty("NextUpNotification.AutoPlayed")

        xbmc.log("PostPlayInfo ->  onInit completed",level=xbmc.LOGNOTICE)

    def prepareSpoilerButton(self):
        showpostplayplot = self.addonSettings.getSetting("showPostPlayPlot") == "true"
        self.spoilersControl.setSelected(showpostplayplot)
        if showpostplayplot:
            self.setProperty('showplot','1')
            xbmc.log("PostPlayInfo ->  showpostplayplot true",level=xbmc.LOGNOTICE)
        else:
            self.setProperty('showplot','')
            xbmc.log("PostPlayInfo ->  showpostplayplot false",level=xbmc.LOGNOTICE)

    def setUpNextList(self, list):
        self.upnextlist = list

    def prepareStillWatching(self):
        if self.showStillWatching:
            self.setProperty('stillwatching','1')
        else:
            self.setProperty('stillwatching','')

    def fillUpNext(self):
        self.upNextControl.reset()
        self.upNextControl.addItems(self.upnextlist)

    def setInfo(self):
        if self.item is not None:
            self.setProperty(
                'background',self.item['art'].get('tvshow.fanart', ''))
            self.setProperty(
                'banner',self.item['art'].get('tvshow.banner', ''))
            self.setProperty(
                'characterart',self.item['art'].get('tvshow.characterart', ''))
            self.setProperty(
                'next.poster',self.item['art'].get('tvshow.poster', ''))
            self.setProperty(
                'next.thumb',self.item['art'].get('thumb', ''))
            self.setProperty(
                'next.clearart',self.item['art'].get('tvshow.clearart', ''))
            self.setProperty(
                'next.landscape',self.item['art'].get('tvshow.landscape', ''))
            self.setProperty(
                'next.plot',self.item['plot'])
            self.setProperty(
                'next.tvshowtitle',self.item['showtitle'])
            self.setProperty(
                'next.title',self.item['title'])
            self.setProperty(
                'next.season',str(self.item['season']))
            self.setProperty(
                'next.episode',str(self.item['episode']))
            self.setProperty(
                'next.year',str(self.item['firstaired']))
            self.setProperty(
                'next.rating',str(round(float(self.item['rating']),1)))
            self.setProperty(
                'next.duration',str(self.item['runtime'] / 60))

    def setPreviousInfo(self):

        self.setProperty(
            'clearlogo',self.previousitem['art'].get('tvshow.clearlogo', ''))
        self.setProperty(
            'previous.poster',self.previousitem['art'].get('tvshow.poster', ''))
        self.setProperty(
            'previous.thumb',self.previousitem['art'].get('thumb', ''))
        self.setProperty(
            'previous.clearart',self.previousitem['art'].get('tvshow.clearart', ''))
        self.setProperty(
            'previous.landscape',self.previousitem['art'].get('tvshow.landscape', ''))
        self.setProperty(
            'previous.plot',self.previousitem['plot'])
        self.setProperty(
            'previous.tvshowtitle',self.previousitem['showtitle'])
        self.setProperty(
            'previous.title',self.previousitem['title'])
        self.setProperty(
            'previous.season',str(self.previousitem['season']))
        self.setProperty(
            'previous.episode',str(self.previousitem['episode']))
        self.setProperty(
            'previous.year',str(self.previousitem['firstaired']))
        self.setProperty(
            'previous.rating',str(round(float(self.previousitem['rating']),1)))
        self.setProperty(
            'previous.duration',str(self.previousitem['runtime'] / 60))

    def setProperty(self, key, value):

        if not self._winID:
            self._winID = xbmcgui.getCurrentWindowId()

        try:
        xbmcgui.Window(self._winID).setProperty(key, value)
        xbmcgui.WindowXML.setProperty(self, key, value)
        except:
            pass

    def setItem(self, item):
        self.item = item
    if item is not None:
        self.setProperty('has.next', '1')

    def setPreviousItem(self, item):
        self.previousitem = item

    def setCancel(self, cancel):
        self.cancel = cancel

    def isCancel(self):
        return self.cancel

    def setStillWatching(self, stillwatching):
        self.showStillWatching = stillwatching

    def isAutoPlayed(self):
        return self.autoplayed

    def setAutoPlayed(self, autoplayed):
        self.autoplayed = autoplayed

    def onFocus(self, controlId):
        pass
    def doAction(self):
        pass
    def closeDialog(self):
        self.close()

    def onClick(self, controlID):
        self.cancelTimer()