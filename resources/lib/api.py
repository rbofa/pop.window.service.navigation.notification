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

    @staticmethod
    def play_kodi_item(episode):
        jsonrpc(method='Player.Open', id=0, params=dict(item=dict(episodeid=episode.get('episodeid'))))

    @staticmethod
    def _get_playerid(playerid_cache=[None]):  # pylint: disable=dangerous-default-value
        """Function to get active player playerid"""

        # We don't need to actually get playerid everytime, cache and reuse instead
        if playerid_cache[0] is not None:
            return playerid_cache[0]

        # Sometimes Kodi gets confused and uses a music playlist for video content,
        # so get the first active player instead, default to video player.
        result = jsonrpc(method='Player.GetActivePlayers')
        result = [
            player for player in result.get('result', [{}])
            if player.get('type', 'video') in Api.PLAYER_PLAYLIST
        ]

        playerid = get_int(result[0], 'playerid') if result else -1

        if playerid == -1:
            return None

        playerid_cache[0] = playerid
        return playerid

    @staticmethod
    def get_playlistid(playlistid_cache=[None]):  # pylint: disable=dangerous-default-value
        """Function to get playlistid of active player"""

        # We don't need to actually get playlistid everytime, cache and reuse instead
        if playlistid_cache[0] is not None:
            return playlistid_cache[0]

        result = jsonrpc(
            method='Player.GetProperties',
            params={
                'playerid': Api._get_playerid(playerid_cache=[None]),
                'properties': ['playlistid'],
            }
        )
        result = get_int(
            result.get('result', {}), 'playlistid', Api.PLAYER_PLAYLIST['video']
        )

        return result

    def queue_next_item(self, episode):
        next_item = {}
        if not self.data:
            next_item.update(episodeid=episode.get('episodeid'))
        elif self.data.get('play_url'):
            next_item.update(file=self.data.get('play_url'))

        if next_item:
            jsonrpc(
                method='Playlist.Add',
                id=0,
                params=dict(
                    playlistid=Api.get_playlistid(),
                    item=next_item
                )
            )

        return bool(next_item)
