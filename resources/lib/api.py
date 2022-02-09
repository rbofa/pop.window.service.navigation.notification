# -*- coding: utf-8 -*-
# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

from __future__ import absolute_import, division, unicode_literals
from xbmc import sleep, PLAYLIST_VIDEO, PLAYLIST_MUSIC
from utils import event, get_int, get_setting_bool, get_setting_int, jsonrpc, log as ulog


class Api:
    """Main API class"""
    _shared_state = {}

    PLAYER_PLAYLIST = {
        'video': PLAYLIST_VIDEO,  # 1
        'audio': PLAYLIST_MUSIC  # 0
    }

    def __init__(self):
        """Constructor for Api class"""
        self.__dict__ = self._shared_state
        self.data = {}
        self.encoding = 'base64'

    def log(self, msg, level=2):
        """Log wrapper"""
        ulog(msg, name=self.__class__.__name__, level=level)

    def has_addon_data(self):
        return self.data

    def reset_addon_data(self):
        self.data = {}

    def addon_data_received(self, data, encoding='base64'):
        self.log('addon_data_received called with data %s' % data, 2)
        self.data = data
        self.encoding = encoding

