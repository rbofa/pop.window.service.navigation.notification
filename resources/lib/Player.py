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
    addonName = clientInfo.getAddonName()
    addonId = clientInfo.getAddonId()
    addon = xbmcaddon.Addon(id=addonId)

    logLevel = 0
    currenttvshowid = None
    currentepisodeid = None
    playedinarow = 1

    fields_base = '"dateadded", "file", "lastplayed","plot", "title", "art", "playcount",'
    fields_file = fields_base + '"streamdetails", "director", "resume", "runtime",'
    fields_tvshows = fields_base + '"sorttitle", "mpaa", "premiered", "year", "episode", "watchedepisodes", "votes", "rating", "studio", "season", "genre", "episodeguide", "tag", "originaltitle", "imdbnumber"'
    fields_episodes = fields_file + '"cast", "productioncode", "rating", "votes", "episode", "showtitle", "tvshowid", "season", "firstaired", "writer", "originaltitle"'
    postplaywindow = None

    def __init__(self, *args):
        self.__dict__ = self._shared_state
    self.logMsg("Starting playback monitor service", 1)

    def logMsg(self, msg, lvl=1):
        self.className = self.__class__.__name__
    utils.logMsg("%s %s" % (self.addonName, self.className), msg, int(lvl))

    def json_query(self, query, ret):
        try:
            xbmc_request = json.dumps(query)
            result = xbmc.executeJSONRPC(xbmc_request)
            result = unicode(result, 'utf-8', errors='ignore')
            if ret:
                return json.loads(result)['result']

            else:
                return json.loads(result)
        except:
            xbmc_request = json.dumps(query)
            result = xbmc.executeJSONRPC(xbmc_request)
            result = unicode(result, 'utf-8', errors='ignore')
            self.logMsg(json.loads(result), 1)
            return json.loads(result)

    def getNowPlaying(self):
        # Get the active player
        result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}')
        result = unicode(result, 'utf-8', errors='ignore')
        self.logMsg("Got active player " + result, 2)
        result = json.loads(result)

        # Seems to work too fast loop whilst waiting for it to become active
        while not result["result"]:
            result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}')
            result = unicode(result, 'utf-8', errors='ignore')
            self.logMsg("Got active player " + result, 2)
            result = json.loads(result)

        if 'result' in result and result["result"][0] is not None:
            playerid = result["result"][0]["playerid"]

            # Get details of the playing media
            self.logMsg("Getting details of now  playing media", 1)
            result = xbmc.executeJSONRPC(
                '{"jsonrpc": "2.0", "id": 1, "method": "Player.GetItem", "params": {"playerid": ' + str(
                    playerid) + ', "properties": ["showtitle", "tvshowid", "episode", "season", "playcount","genre"] } }')
            result = unicode(result, 'utf-8', errors='ignore')
            self.logMsg("Got details of now playing media" + result, 2)

            result = json.loads(result)
            return result

    def onPlayBackStarted(self):
        # Will be called when xbmc starts playing a file
        self.postplaywindow = None
        WINDOW = xbmcgui.Window(10000)
        WINDOW.clearProperty("NextUpNotification.NowPlaying.DBID")
        WINDOW.clearProperty("NextUpNotification.NowPlaying.Type")
        # Get the active player
        result = self.getNowPlaying()
        if 'result' in result:
            itemtype = result["result"]["item"]["type"]
            if itemtype == "episode":
                itemtitle = result["result"]["item"]["showtitle"]
                WINDOW.setProperty("NextUpNotification.NowPlaying.Type", itemtype)
                tvshowid = result["result"]["item"]["tvshowid"]
                WINDOW.setProperty("NextUpNotification.NowPlaying.DBID", str(tvshowid))
                if int(tvshowid) == -1:
                    tvshowid = self.showtitle_to_id(title=itemtitle)
                    self.logMsg("Fetched missing tvshowid " + str(tvshowid), 2)
                    WINDOW.setProperty("NextUpNotification.NowPlaying.DBID", str(tvshowid))
            elif itemtype == "movie":
                WINDOW.setProperty("NextUpNotification.NowPlaying.Type", itemtype)
                id = result["result"]["item"]["id"]
                WINDOW.setProperty("NextUpNotification.NowPlaying.DBID", str(id))


    def showtitle_to_id(self, title):
        query = {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetTVShows",
            "params": {
                "properties": ["title"]
            },
            "id": "libTvShows"
        }
        try:
            json_result = json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))
            if 'result' in json_result and 'tvshows' in json_result['result']:
                json_result = json_result['result']['tvshows']
                for tvshow in json_result:
                    if tvshow['label'] == title:
                        return tvshow['tvshowid']
            return '-1'
        except Exception:
            return '-1'

    def get_episode_id(self, showid, showseason, showepisode):
        showseason = int(showseason)
        showepisode = int(showepisode)
        episodeid = 0

        query = {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetEpisodes",
            "params": {
                "properties": ["season", "episode"],
                "tvshowid": int(showid)
            },
            "id": "1"
        }
        try:
            json_result = json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))
            if 'result' in json_result and 'episodes' in json_result['result']:
                json_result = json_result['result']['episodes']
                for episode in json_result:
                    if episode['season'] == showseason and episode['episode'] == showepisode:
                        if 'episodeid' in episode:
                            episodeid = episode['episodeid']
            return episodeid
        except Exception:
            return episodeid

    def onPlayBackEnded(self):
        self.logMsg("playback ended ", 2)
        if self.postplaywindow is not None:
            self.showPostPlay()

    def findNextEpisode(self, result, currentFile, includeWatched):
        self.logMsg("Find next episode called", 1)
        position = 0
        for episode in result["result"]["episodes"]:
            # find position of current episode
            if self.currentepisodeid == episode["episodeid"]:
                # found a match so add 1 for the next and get out of here
                position += 1
                break
            position += 1
        # check if it may be a multi-part episode
        while result["result"]["episodes"][position]["file"] == currentFile:
            position += 1

        # now return the episode
        self.logMsg("Find next episode found next episode in position: " + str(position), 1)
        try:
            episode = result["result"]["episodes"][position]
        except:
            # no next episode found
            episode = None

        return episode