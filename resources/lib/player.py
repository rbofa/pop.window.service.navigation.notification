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

    def enable_tracking(self):
        self.state.track = True

    def reset_queue(self):
        if self.state.queued:
            self.api.reset_queue()
            self.state.queued = False

    def _check_video(self):
        self.monitor.waitForAbort(5)
        if not getCondVisibility('videoplayer.content(episodes)'):
            return
        self.state.track = True
        self.reset_queue()

    if callable(getattr(Player, 'onAVStarted', None)):
        def onAVStarted(self):  # pylint: disable=invalid-name
            """Will be called when Kodi has a video or audiostream"""
            self._check_video()
    else:
        def onPlayBackStarted(self):  # pylint: disable=invalid-name
            """Will be called when kodi starts playing a file"""
            self._check_video()

    def onPlayBackPaused(self):  # pylint: disable=invalid-name
        self.state.pause = True

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
