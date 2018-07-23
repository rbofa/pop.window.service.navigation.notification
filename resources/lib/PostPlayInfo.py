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