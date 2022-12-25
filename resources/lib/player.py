# -*- coding: utf-8 -*-
# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

from __future__ import absolute_import, division, unicode_literals
from xbmc import getCondVisibility, Player, Monitor
from api import Api
from state import State


class UpNextPlayer(Player):
    """Service class for playback monitoring"""
    last_file = None
    track = False

    def __init__(self):
        self.api = Api()
        self.state = State()
        self.monitor = Monitor()
        Player.__init__(self)

    def set_last_file(self, filename):
        self.state.last_file = filename

    def get_last_file(self):
        return self.state.last_file

    def is_tracking(self):
        return self.state.track

    def disable_tracking(self):
        self.state.track = False

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
            shortplayNotification = addonSettings.getSetting("shortPlayNotification")
            shortplayLength = int(addonSettings.getSetting("shortPlayLength")) * 60

        # Try to get tvshowid by showtitle from kodidb if tvshowid is -1 like in strm streams which are added to kodi db
        if int(tvshowid) == -1:
            tvshowid = self.showtitle_to_id(title=currentshowtitle)
            self.logMsg("Fetched missing tvshowid " + str(tvshowid), 2)

        if (itemtype == "episode"):
            # Get current episodeid
            currentepisodeid = self.get_episode_id(showid=str(tvshowid), showseason=currentseasonid,
                                                   showepisode=currentepisodenumber)
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
                current_episode = self.findCurrentEpisode(result, currentFile)
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
                    totalTime = xbmc.Player().getTotalTime()
                    self.logMsg("played in a row settings %s" % str(playedinarownumber), 2)
                    self.logMsg("played in a row %s" % str(self.playedinarow), 2)
                    if int(self.playedinarow) <= int(playedinarownumber):
                        if (shortplayNotification == "false") and (shortplayLength >= totalTime) and (
                                shortplayMode == "true"):
                            self.logMsg("hiding notification for short videos")
                        else:
                            postPlayPage.setStillWatching(False)
                    else:
                        if (shortplayNotification == "false") and (shortplayLength >= totalTime) and (
                                shortplayMode == "true"):
                            self.logMsg("hiding notification for short videos")
                        else:
                            postPlayPage.setStillWatching(True)

                    self.postplaywindow = postPlayPage

    def showPostPlay(self):
        self.logMsg("showing postplay window")
        p = self.postplaywindow.doModal()
        autoplayed = xbmcgui.Window(10000).getProperty("NextUpNotification.AutoPlayed")
        self.logMsg("showing postplay window completed autoplayed? " + str(autoplayed))
        if autoplayed:
            self.playedinarow += 1
        else:
            self.playedinarow = 1
        del p

    def parse_tvshows_recommended(self, limit):
        items = []
        prefix = "recommended-episodes"
        json_query = LIBRARY._fetch_recommended_episodes()

        if json_query:
            # First unplayed episode of recent played tvshows
            self.logMsg("getting next up tvshows " + json_query, 2)
            json_query = json.loads(json_query)
            if "result" in json_query and 'tvshows' in json_query['result']:
                count = -1
                for item in json_query['result']['tvshows']:
                    if xbmc.abortRequested:
                        break
                    if count == -1:
                        count += 1
                        continue
                    json_query2 = xbmcgui.Window(10000).getProperty(prefix + "-data-" + str(item['tvshowid']))
                    if json_query2:
                        self.logMsg("getting next up episodes " + json_query2, 2)
                        json_query2 = json.loads(json_query2)
                        if "result" in json_query2 and json_query2['result'] is not None and 'episodes' in json_query2[
                            'result']:
                            for item2 in json_query2['result']['episodes']:
                                episode = "%.2d" % float(item2['episode'])
                                season = "%.2d" % float(item2['season'])
                                episodeno = "s%se%s" % (season, episode)
                                break
                            plot = item2['plot']
                            episodeid = str(item2['episodeid'])
                            if len(item['studio']) > 0:
                                studio = item['studio'][0]
                            else:
                                studio = ""
                            if "director" in item2:
                                director = " / ".join(item2['director'])
                            if "writer" in item2:
                                writer = " / ".join(item2['writer'])

                            liz = xbmcgui.ListItem(item2['title'])
                            liz.setPath(item2['file'])
                            liz.setProperty('IsPlayable', 'true')
                            liz.setInfo(type="Video", infoLabels={"Title": item2['title'],
                                                                  "Episode": item2['episode'],
                                                                  "Season": item2['season'],
                                                                  "Studio": studio,
                                                                  "Premiered": item2['firstaired'],
                                                                  "Plot": plot,
                                                                  "TVshowTitle": item2['showtitle'],
                                                                  "Rating": str(float(item2['rating'])),
                                                                  "MPAA": item['mpaa'],
                                                                  "Playcount": item2['playcount'],
                                                                  "Director": director,
                                                                  "Writer": writer,
                                                                  "mediatype": "episode"})
                            liz.setProperty("episodeid", episodeid)
                            liz.setProperty("episodeno", episodeno)
                            liz.setProperty("resumetime", str(item2['resume']['position']))
                            liz.setProperty("totaltime", str(item2['resume']['total']))
                            liz.setProperty("type", 'episode')
                            liz.setProperty("fanart_image", item2['art'].get('tvshow.fanart', ''))
                            liz.setProperty("dbid", str(item2['episodeid']))
                            liz.setArt(item2['art'])
                            liz.setThumbnailImage(item2['art'].get('thumb', ''))
                            liz.setIconImage('DefaultTVShows.png')
                            hasVideo = False
                            for key, value in item2['streamdetails'].iteritems():
                                for stream in value:
                                    if 'video' in key:
                                        hasVideo = True
                                    liz.addStreamInfo(key, stream)

                            # if duration wasnt in the streaminfo try adding the scraped one
                            if not hasVideo:
                                stream = {'duration': item2['runtime']}
                                liz.addStreamInfo("video", stream)

                            items.append(liz)

                            count += 1
                            if count == limit:
                                break
                    if count == limit:
                        break
            del json_query
        self.logMsg("getting next up episodes completed ", 2)
        return items

    def autoPlayPlayback(self):
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
            shortplayNotification = addonSettings.getSetting("shortPlayNotification")
            shortplayLength = int(addonSettings.getSetting("shortPlayLength")) * 60
            showpostplaypreview = addonSettings.getSetting("showPostPlayPreview") == "true"
            showpostplay = addonSettings.getSetting("showPostPlay") == "true"
            shouldshowpostplay = showpostplay and showpostplaypreview

            # Try to get tvshowid by showtitle from kodidb if tvshowid is -1 like in strm streams which are added to kodi db
            if int(tvshowid) == -1:
                tvshowid = self.showtitle_to_id(title=currentshowtitle)
                self.logMsg("Fetched missing tvshowid " + str(tvshowid), 2)

            if (itemtype == "episode"):
                # Get current episodeid
                currentepisodeid = self.get_episode_id(showid=str(tvshowid), showseason=currentseasonid,
                                                       showepisode=currentepisodenumber)
            else:
                # wtf am i doing here error.. ####
                self.logMsg("Error: cannot determine if episode", 1)
                return

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

                if episode is None:
                    # no episode get out of here
                    return
                self.logMsg("episode details %s" % str(episode), 2)
                episodeid = episode["episodeid"]

                if includeWatched:
                    includePlaycount = True
                else:
                    includePlaycount = episode["playcount"] == 0
                if includePlaycount and currentepisodeid != episodeid:
                    # we have a next up episode
                    nextUpPage = NextUpInfo("script-nextup-notification-NextUpInfo.xml",
                                            addonSettings.getAddonInfo('path'), "default", "1080i")
                    nextUpPage.setItem(episode)
                    stillWatchingPage = StillWatchingInfo(
                        "script-nextup-notification-StillWatchingInfo.xml",
                        addonSettings.getAddonInfo('path'), "default", "1080i")
                    stillWatchingPage.setItem(episode)
                    playedinarownumber = addonSettings.getSetting("playedInARow")
                    playTime = xbmc.Player().getTime()
                    totalTime = xbmc.Player().getTotalTime()
                    self.logMsg("played in a row settings %s" % str(playedinarownumber), 2)
                    self.logMsg("played in a row %s" % str(self.playedinarow), 2)

                    if int(self.playedinarow) <= int(playedinarownumber):
                        self.logMsg(
                            "showing next up page as played in a row is %s" % str(self.playedinarow), 2)
                        if (shortplayNotification == "false") and (shortplayLength >= totalTime) and (
                                shortplayMode == "true"):
                            self.logMsg("hiding notification for short videos")
                        else:
                            nextUpPage.show()
                    else:
                        self.logMsg(
                            "showing still watching page as played in a row %s" % str(self.playedinarow), 2)
                        if (shortplayNotification == "false") and (shortplayLength >= totalTime) and (
                                shortplayMode == "true"):
                            self.logMsg("hiding notification for short videos")
                        else:
                            stillWatchingPage.show()
                    if shouldshowpostplay:
                        self.postPlayPlayback()

                    while xbmc.Player().isPlaying() and (
                            totalTime - playTime > 1) and not nextUpPage.isCancel() and not nextUpPage.isWatchNow() and not stillWatchingPage.isStillWatching() and not stillWatchingPage.isCancel():
                        xbmc.sleep(100)
                        try:
                            playTime = xbmc.Player().getTime()
                            totalTime = xbmc.Player().getTotalTime()
                        except:
                            pass
                    if shortplayLength >= totalTime and shortplayMode == "true":
                        # play short video and don't add to playcount
                        self.playedinarow += 0
                        self.logMsg("Continuing short video autoplay - %s")
                        if nextUpPage.isWatchNow() or stillWatchingPage.isStillWatching():
                            self.playedinarow = 1
                        shouldPlayDefault = not nextUpPage.isCancel()
                    else:
                        if int(self.playedinarow) <= int(playedinarownumber):
                            nextUpPage.close()
                            shouldPlayDefault = not nextUpPage.isCancel()
                            shouldPlayNonDefault = nextUpPage.isWatchNow()
                        else:
                            stillWatchingPage.close()
                            shouldPlayDefault = stillWatchingPage.isStillWatching()
                            shouldPlayNonDefault = stillWatchingPage.isStillWatching()

                        if nextUpPage.isWatchNow() or stillWatchingPage.isStillWatching():
                            self.playedinarow = 1
                        else:
                            self.playedinarow += 1

                    if (shouldPlayDefault and not shouldshowpostplay and playMode == "0") or (
                            shouldPlayNonDefault and shouldshowpostplay and playMode == "0") or (
                            shouldPlayNonDefault and playMode == "1"):
                        self.logMsg("playing media episode id %s" % str(episodeid), 2)
                        # Signal to trakt previous episode watched
                        AddonSignals.sendSignal("NEXTUPWATCHEDSIGNAL", {'episodeid': self.currentepisodeid})

                        # if in postplaypreview mode clear the post play window as its not needed now
                        if shouldshowpostplay:
                            self.postplaywindow = None

                        # Play media
                        xbmc.executeJSONRPC(
                            '{ "jsonrpc": "2.0", "id": 0, "method": "Player.Open", '
                            '"params": { "item": {"episodeid": ' + str(episode["episodeid"]) + '} } }')
