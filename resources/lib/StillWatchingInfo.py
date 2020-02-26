from platform import machine

import xbmc
import xbmcgui

class StillWatchingInfo(xbmcgui.WindowXMLDialog):
    item = None
    cancel = False
    stillwatching = False

    def __init__(self, *args, **kwargs):
        self.action_exitkeys_id = [10, 13]
        if OS_MACHINE[0:5] == 'armv7':
            xbmcgui.WindowXMLDialog.__init__(self)
        else:
            xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

    def onInit(self):
        image = self.item['art'].get('tvshow.poster', '')
        thumb = self.item['art'].get('thumb', '')
        landscape = self.item['art'].get('tvshow.landscape', '')
        fanartimage = self.item['art'].get('tvshow.fanart', '')
        clearartimage = self.item['art'].get('tvshow.clearart', '')
        name = self.item['label']
        rating = str(round(float(self.item['rating']), 1))
        year = self.item['firstaired']
        overview = self.item['plot']
        season = self.item['season']
        episodeNum = self.item['episode']
        title = self.item['title']
        playcount = self.item['playcount']
        # set the dialog data
        self.getControl(4000).setLabel(name)
        self.getControl(4006).setText(overview)

        try:
            posterControl = self.getControl(4001)
            if posterControl is not None:
                self.getControl(4001).setImage(image)
        except:
            pass

        try:
            thumbControl = self.getControl(4002)
            if thumbControl is not None:
                self.getControl(4002).setImage(thumb)
        except:
            pass
        self.getControl(4003).setLabel(rating)
        self.getControl(4004).setLabel(year)

        try:
            landscapeControl = self.getControl(4005)
        if landscapeControl is not None:
            self.getControl(4005).setImage(landscape)
        except:
              pass

        try:
            fanartControl = self.getControl(4007)
            if fanartControl is not None:
                fanartControl.setImage(fanartimage)
