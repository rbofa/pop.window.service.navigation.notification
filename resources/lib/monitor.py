# -*- coding: utf-8 -*-
# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

from __future__ import absolute_import, division, unicode_literals
from xbmc import Monitor
from api import Api
from playbackmanager import PlaybackManager
from player import UpNextPlayer
from statichelper import from_unicode
from utils import decode_json, get_property, get_setting_bool, kodi_version_major, log as ulog


class UpNextMonitor(Monitor):
    """Service monitor for Kodi"""

    def __init__(self):
        """Constructor for Monitor"""
        self.player = UpNextPlayer()
        self.api = Api()
        self.playback_manager = PlaybackManager()
        Monitor.__init__(self)

    def log(self, msg, level=1):
        """Log wrapper"""
        ulog(msg, name=self.__class__.__name__, level=level)

    def run(self):
        """Main service loop"""
        self.log('Service started', 0)

        while not self.abortRequested():
            # check every 1 sec
            if self.waitForAbort(1):
                # Abort was requested while waiting. We should exit
                break

            if not self.player.is_tracking():
                continue

            if bool(get_property('PseudoTVRunning') == 'True'):
                self.player.disable_tracking()
                self.playback_manager.demo.hide()
                continue

            if get_setting_bool('disableNextUp'):
                # Next Up is disabled
                self.player.disable_tracking()
                self.playback_manager.demo.hide()
                continue

            # Method isExternalPlayer() was added in Kodi v18 onward
            if kodi_version_major() >= 18 and self.player.isExternalPlayer():
                self.log('Up Next tracking stopped, external player detected', 2)
                self.player.disable_tracking()
                self.playback_manager.demo.hide()
                continue


