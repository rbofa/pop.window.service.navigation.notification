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

    def onPlayBackResumed(self):  # pylint: disable=invalid-name
        self.state.pause = False

    def onPlayBackStopped(self):  # pylint: disable=invalid-name
        """Will be called when user stops playing a file"""
        self.reset_queue()
        self.api.reset_addon_data()
        self.state = State()  # Reset state

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
