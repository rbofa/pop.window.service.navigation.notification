import xbmc
import xbmcgui
from platform import machine

ACTION_PLAYER_STOP = 13
OS_MACHINE = machine()


class NextUpInfo(xbmcgui.WindowXMLDialog):
    item = None
    cancel = False
    watchnow = False

    def __init__(self, *args, **kwargs):
        if OS_MACHINE[0:5] == 'armv7':
            xbmcgui.WindowXMLDialog.__init__(self)
        else:
            xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

    def onInit(self):
        self.action_exitkeys_id = [10, 13]

        image = self.item['art'].get('tvshow.poster', '')
        thumb = self.item['art'].get('thumb', '')
        clearartimage = self.item['art'].get('tvshow.clearart', '')
        landscapeimage = self.item['art'].get('tvshow.landscape', '')
        fanartimage = self.item['art'].get('tvshow.fanart', '')
        overview = self.item['plot']
        tvshowtitle = self.item['showtitle']
        name = self.item['title']
        playcount = self.item['playcount']

        season = self.item['season']
        episodeNum = self.item['episode']
        episodeInfo = str(season) + 'x' + str(episodeNum) + '.'

        rating = str(round(float(self.item['rating']),1))
        year = self.item['firstaired']
        info = year

        # set the dialog data
        self.getControl(3000).setLabel(name)
        self.getControl(3001).setText(overview)
        self.getControl(3002).setLabel(episodeInfo)
        self.getControl(3004).setLabel(info)