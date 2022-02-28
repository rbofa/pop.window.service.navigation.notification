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

    @staticmethod
    def dequeue_next_item():
        """Remove unplayed next item from video playlist"""
        jsonrpc(
            method='Playlist.Remove',
            id=0,
            params=dict(
                playlistid=Api.get_playlistid(),
                position=1
            )
        )
        return False

    @staticmethod
    def reset_queue():
        """Remove previously played item from video playlist"""
        jsonrpc(
            method='Playlist.Remove',
            id=0,
            params=dict(
                playlistid=Api.get_playlistid(),
                position=0
            )
        )

    def get_next_in_playlist(self, position):
        result = jsonrpc(method='Playlist.GetItems', params=dict(
            playlistid=Api.get_playlistid(),
            # limits are zero indexed, position is one indexed
            limits=dict(start=position, end=position + 1),
            properties=['art', 'dateadded', 'episode', 'file', 'firstaired', 'lastplayed',
                        'playcount', 'plot', 'rating', 'resume', 'runtime', 'season',
                        'showtitle', 'streamdetails', 'title', 'tvshowid', 'writer'],
        ))

        item = result.get('result', {}).get('items')

        # Don't check if next item is an episode, just use it if it is there
        if not item:  # item.get('type') != 'episode':
            self.log('Error: no next item found in playlist', 1)
            return None
        item = item[0]

        # Playlist item may not have had video info details set
        # Try and populate required details if missing
        if not item.get('title'):
            item['title'] = item.get('label', '')
        item['episodeid'] = get_int(item, 'id')
        item['tvshowid'] = get_int(item, 'tvshowid')
        # If missing season/episode, change to empty string to avoid episode
        # formatting issues ("S-1E-1") in UpNext popup
        if get_int(item, 'season') == -1:
            item['season'] = ''
        if get_int(item, 'episode') == -1:
            item['episode'] = ''

        self.log('Next item in playlist: %s' % item, 2)
        return item


def play_addon_item(self):
    if self.data.get('play_url'):
        self.log('Playing the next episode directly: %(play_url)s' % self.data, 2)
        jsonrpc(method='Player.Open', params=dict(item=dict(file=self.data.get('play_url'))))
    else:
        self.log(
            'Sending %(encoding)s data to add-on to play: %(play_info)s' % dict(encoding=self.encoding, **self.data), 2)
        event(message=self.data.get('id'), data=self.data.get('play_info'), sender='upnextprovider',
              encoding=self.encoding)

    def handle_addon_lookup_of_next_episode(self):
        if not self.data:
            return None
        self.log('handle_addon_lookup_of_next_episode episode returning data %(next_episode)s' % self.data, 2)
        return self.data.get('next_episode')

    def handle_addon_lookup_of_current_episode(self):
        if not self.data:
            return None
        self.log('handle_addon_lookup_of_current episode returning data %(current_episode)s' % self.data, 2)
        return self.data.get('current_episode')

    def notification_time(self, total_time=None):
        # Alway use metadata, when available
        if self.data.get('notification_time'):
            return int(self.data.get('notification_time'))

        # Some consumers send the offset when the credits start (e.g. Netflix)
        if total_time and self.data.get('notification_offset'):
            return total_time - int(self.data.get('notification_offset'))
        # Use a customized notification time, when configured
        if total_time and get_setting_bool('customAutoPlayTime'):
            if total_time > 60 * 60:
                return get_setting_int('autoPlayTimeXL')
            if total_time > 40 * 60:
                return get_setting_int('autoPlayTimeL')
            if total_time > 20 * 60:
                return get_setting_int('autoPlayTimeM')
            if total_time > 10 * 60:
                return get_setting_int('autoPlayTimeS')
            return get_setting_int('autoPlayTimeXS')

        # Use one global default, regardless of episode length
        return get_setting_int('autoPlaySeasonTime')
