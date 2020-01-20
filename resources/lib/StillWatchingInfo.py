from platform import machine

import xbmc
import xbmcgui

class StillWatchingInfo(xbmcgui.WindowXMLDialog):
    item = None
    cancel = False
    stillwatching = False

    def __init__(self, *args, **kwargs):
        self.action_exitkeys_id = [10, 13]
        if OS_MACHINE[0:5] == 'armv7':
            xbmcgui.WindowXMLDialog.__init__(self)