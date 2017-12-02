import xbmcaddon
import xbmc
import xbmcgui
import library
import sys
from ClientInformation import ClientInformation

if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

LIBRARY = library.LibraryFunctions()
# service class for playback monitoring
class Player(xbmc.Player):
    # Borg - multiple instances, shared state
    _shared_state = {}

    xbmcplayer = xbmc.Player()
    clientInfo = ClientInformation()

    def __init__(self, *args):
        self.__dict__ = self._shared_state
    self.logMsg("Starting playback monitor service", 1)
