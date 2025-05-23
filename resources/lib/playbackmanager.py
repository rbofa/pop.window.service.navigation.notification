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

        # Dequeue and stop playback if not playing next file
        if not play_next and self.state.queued:
            self.state.queued = self.api.dequeue_next_item()
        if not keep_playing:
            self.log('Stopping playback', 2)
            self.player.stop()

        self.api.reset_addon_data()

        def launch_popup(self, episode, source=None):
            episode_id = episode.get('episodeid')
            no_play_count = episode.get('playcount') is None or episode.get('playcount') == 0
            include_play_count = True if self.state.include_watched else no_play_count
            if not include_play_count or self.state.current_episode_id == episode_id:
                # play_next = False
                # keep_playing = True
                # return play_next, keep_playing
                # Don't play next file, but keep playing current file
                return False, True

        # Add next file to playlist if existing playlist is not being used
        if source != 'playlist':
            self.state.queued = self.api.queue_next_item(episode)

        # We have a next up episode choose mode
        if get_setting_int('simpleMode') == 0:
            next_up_page = UpNext('script-upnext-upnext-simple.xml', addon_path(), 'default', '1080i')
            still_watching_page = StillWatching('script-upnext-stillwatching-simple.xml', addon_path(), 'default', '1080i')
        else:
            next_up_page = UpNext('script-upnext-upnext.xml', addon_path(), 'default', '1080i')
            still_watching_page = StillWatching('script-upnext-stillwatching.xml', addon_path(), 'default', '1080i')

        showing_next_up_page, showing_still_watching_page = self.show_popup_and_wait(episode,
                                                                                     next_up_page,
                                                                                     still_watching_page)
        should_play_default, should_play_non_default = self.extract_play_info(next_up_page,
                                                                              showing_next_up_page,
                                                                              showing_still_watching_page,
                                                                              still_watching_page)
        if not self.state.track:
            self.log('exit launch_popup early due to disabled tracking', 2)
            # play_next = False
            # keep_playing = showing_next_up_page
            # return play_next, keep_playing
            # Don't play next file
            # Stop if Still Watching? popup was shown to prevent unwanted playback when using FF or skip
            return False, showing_next_up_page
        play_item_option_1 = (should_play_default and self.state.play_mode == 0)
        play_item_option_2 = (should_play_non_default and self.state.play_mode == 1)
        if not play_item_option_1 and not play_item_option_2:
            # play_next = False
            # keep_playing = next_up_page.is_cancel() if showing_next_up_page else still_watching_page.is_cancel()
            # keep_playing = keep_playing and not get_setting_bool('stopAfterClose')
            # return play_next, keep_playing
            # Don't play next file, and stop current file if no playback option selected
            return False, (
                (next_up_page.is_cancel() if showing_next_up_page else still_watching_page.is_cancel())
                and not get_setting_bool('stopAfterClose')
            )

        self.log('playing media episode', 2)
        # Signal to trakt previous episode watched
        event(message='NEXTUPWATCHEDSIGNAL', data=dict(episodeid=self.state.current_episode_id), encoding='base64')
        if source == 'playlist' or self.state.queued:
            # Play playlist media
            if should_play_non_default:
                # Only start the next episode if the user asked for it specifically
                self.player.playnext()
        elif self.api.has_addon_data():
            # Play add-on media
            self.api.play_addon_item()
        else:
        # Play local media
        self.api.play_kodi_item(episode)

        # play_next = True
        # keep_playing = True
        # return play_next, keep_playing
        # Play next file, and keep playing current file untill
        return True, True
