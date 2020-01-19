from platform import machine

import xbmc
import xbmcgui

class StillWatchingInfo(xbmcgui.WindowXMLDialog):
    item = None
    cancel = False
    stillwatching = False