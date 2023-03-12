# -*- coding: utf-8 -*-
# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

from __future__ import absolute_import, division, unicode_literals
from xbmc import sleep
from api import Api
from demo import DemoOverlay
from player import Player
from playitem import PlayItem
from state import State
from stillwatching import StillWatching
from upnext import UpNext
from utils import addon_path, calculate_progress_steps, clear_property, event, get_setting_bool, get_setting_int, \
    log as ulog, set_property


class PlaybackManager:
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state
        self.api = Api()
        self.play_item = PlayItem()
        self.state = State()
        self.player = Player()
        self.demo = DemoOverlay(12005)

    def log(self, msg, level=2):
        ulog(msg, name=self.__class__.__name__, level=level)

    def handle_demo(self):
        if get_setting_bool('enableDemoMode'):
            self.log('Up Next DEMO mode enabled, skipping automatically to the end', 0)
            self.demo.show()
            try:
                total_time = self.player.getTotalTime()
                self.player.seekTime(total_time - 15)
            except RuntimeError as exc:
                self.log('Failed to seekTime(): %s' % exc, 0)
        else:
            self.demo.hide()

    def launch_up_next(self):
        enable_playlist = get_setting_bool('enablePlaylist')
        episode, source = self.play_item.get_next()
        self.log('Playlist setting: %s' % enable_playlist)
        if source == 'playlist' and not enable_playlist:
            self.log('Playlist integration disabled', 2)
            return
        if not episode:
            # No episode get out of here
            self.log('Error: no episode could be found to play next...exiting', 1)
            return
        self.log('episode details %s' % episode, 2)
        play_next, keep_playing = self.launch_popup(episode, source)
        self.state.playing_next = play_next