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

    def findCurrentEpisode(self, result, currentFile):
        self.logMsg("Find current episode called", 1)
        position = 0
        for episode in result["result"]["episodes"]:
            # find position of current episode
            if self.currentepisodeid == episode["episodeid"]:
                # found a match so get out of here
                break
            position += 1

        # now return the episode
        self.logMsg("Find current episode found episode in position: " + str(position), 1)
        try:
            episode = result["result"]["episodes"][position]
        except:
            # no next episode found
            episode = None

        return episode

    def displayRandomUnwatched(self):
        # Get the active player
        result = self.getNowPlaying()
        if 'result' in result:
            itemtype = result["result"]["item"]["type"]
            if itemtype == "episode":
                # playing an episode so find a random unwatched show from the same genre
                genres = result["result"]["item"]["genre"]
                if genres:
                    genretitle = genres[0]
                    self.logMsg("Looking up tvshow for genre " + genretitle, 2)
                    tvshow = utils.getJSON('VideoLibrary.GetTVShows', '{ "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"genre", "value":"%s"}, {"operator":"is", "field":"playcount", "value":"0"}]}, "properties": [ %s ],"limits":{"end":1} }' % (genretitle, self.fields_tvshows))
                if not tvshow:
                    self.logMsg("Looking up tvshow without genre", 2)
                    tvshow = utils.getJSON('VideoLibrary.GetTVShows', '{ "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"}]}, "properties": [ %s ],"limits":{"end":1} }' % self.fields_tvshows)
                self.logMsg("Got tvshow" + str(tvshow), 2)
                tvshowid = tvshow[0]["tvshowid"]
                if int(tvshowid) == -1:
                    tvshowid = self.showtitle_to_id(title=itemtitle)
                    self.logMsg("Fetched missing tvshowid " + str(tvshowid), 2)
                episode = utils.getJSON('VideoLibrary.GetEpisodes', '{ "tvshowid": %d, "sort": {"method":"episode"}, "filter": {"and": [ {"field": "playcount", "operator": "lessthan", "value":"1"}, {"field": "season", "operator": "greaterthan", "value": "0"} ]}, "properties": [ %s ], "limits":{"end":1}}' % (tvshowid, self.fields_episodes))

                if episode:
                    self.logMsg("Got details of next up episode %s" % str(episode), 2)
                    addonSettings = xbmcaddon.Addon(id='pop.window.service.navigation.notification')
                    unwatchedPage = UnwatchedInfo("script-nextup-notification-UnwatchedInfo.xml",
                                                  addonSettings.getAddonInfo('path'), "default", "1080i")
                    unwatchedPage.setItem(episode[0])
                    self.logMsg("Calling display unwatched", 2)
                    unwatchedPage.show()
                    monitor = xbmc.Monitor()
                    monitor.waitForAbort(10)
                    self.logMsg("Calling close unwatched", 2)
                    unwatchedPage.close()
                    del monitor

    def postPlayPlayback(self):
        currentFile = xbmc.Player().getPlayingFile()

    # Get the active player
    result = self.getNowPlaying()
    if 'result' in result:
        itemtype = result["result"]["item"]["type"]
        addonSettings = xbmcaddon.Addon(id='pop.window.service.navigation.notification')
        playMode = addonSettings.getSetting("autoPlayMode")
        currentepisodenumber = result["result"]["item"]["episode"]
        currentseasonid = result["result"]["item"]["season"]
        currentshowtitle = result["result"]["item"]["showtitle"]
        tvshowid = result["result"]["item"]["tvshowid"]
        shortplayMode = addonSettings.getSetting("shortPlayMode")
        shortplayNotification= addonSettings.getSetting("shortPlayNotification")
        shortplayLength = int(addonSettings.getSetting("shortPlayLength")) * 60

    # Try to get tvshowid by showtitle from kodidb if tvshowid is -1 like in strm streams which are added to kodi db
    if int(tvshowid) == -1:
        tvshowid = self.showtitle_to_id(title=currentshowtitle)
        self.logMsg("Fetched missing tvshowid " + str(tvshowid), 2)

        if (itemtype == "episode"):
            # Get current episodeid
            currentepisodeid = self.get_episode_id(showid=str(tvshowid), showseason=currentseasonid, showepisode=currentepisodenumber)
        else:
            # wtf am i doing here error.. ####
            self.logMsg("Error: cannot determine if episode", 1)
            return

        self.currentepisodeid = currentepisodeid
        self.logMsg("Getting details of next up episode for tvshow id: " + str(tvshowid), 1)
        if self.currenttvshowid != tvshowid:
            self.currenttvshowid = tvshowid
            self.playedinarow = 1

        result = xbmc.executeJSONRPC(
            '{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"tvshowid": %d, '
            '"properties": [ "title", "playcount", "season", "episode", "showtitle", "plot", '
            '"file", "rating", "resume", "tvshowid", "art", "firstaired", "runtime", "writer", '
            '"dateadded", "lastplayed" , "streamdetails"], "sort": {"method": "episode"}}, "id": 1}'
            % tvshowid)

        if result:
            result = unicode(result, 'utf-8', errors='ignore')
            result = json.loads(result)
            self.logMsg("Got details of next up episode %s" % str(result), 2)
            xbmc.sleep(100)

            # Find the next unwatched and the newest added episodes
            if "result" in result and "episodes" in result["result"]:
                includeWatched = addonSettings.getSetting("includeWatched") == "true"
                episode = self.findNextEpisode(result, currentFile, includeWatched)
                current_episode = self.findCurrentEpisode(result,currentFile)
                self.logMsg("episode details %s" % str(episode), 2)
                episodeid = episode["episodeid"]

                if current_episode:
                    # we have something to show
                    postPlayPage = PostPlayInfo("script-nextup-notification-PostPlayInfo.xml",
                                                addonSettings.getAddonInfo('path'), "default", "1080i")
                    postPlayPage.setItem(episode)
                    postPlayPage.setPreviousItem(current_episode)
                    upnextitems = self.parse_tvshows_recommended(6)
                    postPlayPage.setUpNextList(upnextitems)
                    playedinarownumber = addonSettings.getSetting("playedInARow")
                    playTime = xbmc.Player().getTime()
                    totalTime =  xbmc.Player().getTotalTime()
                    self.logMsg("played in a row settings %s" % str(playedinarownumber), 2)
                    self.logMsg("played in a row %s" % str(self.playedinarow), 2)
                    if int(self.playedinarow) <= int(playedinarownumber):
                        if (shortplayNotification == "false") and (shortplayLength >= totalTime) and (shortplayMode == "true"):
                            self.logMsg("hiding notification for short videos")
                        else:
                            postPlayPage.setStillWatching(False)
                    else:
                        if (shortplayNotification == "false") and (shortplayLength >= totalTime) and (shortplayMode == "true"):
                            self.logMsg("hiding notification for short videos")
                        else:
                            postPlayPage.setStillWatching(True)

                    self.postplaywindow = postPlayPage