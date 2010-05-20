"""
    Plugin for streaming media from Tou.tv
"""

__plugin__ = "Tou.tv"
__author__ = 'misil [michaelsillslavoie@gmail.com]'
__url__ = "http://xbmctoutv.blogspot.com/"
__credits__ = "PBS and CBS plugins"
__version__ = "0.0.8"

import xbmc, xbmcgui, xbmcplugin, urllib2, urllib, re, sys, os, traceback

HEADER = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1'
BASE_CACHE_PATH = os.path.join( xbmc.translatePath( "special://profile/" ), "Thumbnails", "Video" )

TOU_TV_BASE_URL = 'http://www.tou.tv'
TOU_TV_REPERTOIRE_URL = '/repertoire'
TOU_TV_MEDIA_FLAG = 'toutv.mediaData'

THEPLATFORM_CONTENT_URL = 'http://release.theplatform.com/content.select?pid='

"""
	Read all the text from the specified url
"""
def readUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', HEADER)
	f = urllib2.urlopen(req)
	url_data = f.read()
	f.close()
	return url_data

"""
	List Tou.tv shows in the Tou.tv plugin root directory
"""
def showRoot():
		url_data = readUrl(TOU_TV_BASE_URL + TOU_TV_REPERTOIRE_URL)
		match = re.compile('href="(.+?)">\s+<h1 class="titreemission">(.+?)</h1>').findall(url_data)
		for url, name in match:
			url = TOU_TV_BASE_URL + url
			li = xbmcgui.ListItem(name)
			u = sys.argv[0] + "?mode=0&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url)
			xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)

"""
	List a specified show episodes
"""
def showList(url, name):
		url_data = readUrl(url)

		if TOU_TV_MEDIA_FLAG not in url_data:
			info = re.compile('<img id=".+?" src="(.+?)".+?class="saison">(.+?)</p>.+?class="episode".+?href="(.+?)".+?<b>(.+?)(&nbsp;)*?</b>.+?<p>(.+?)</p>', re.DOTALL).findall(url_data)
			for img, saison, url, title, trash, desc in info:
				thumb = get_thumbnail(img)
				url = TOU_TV_BASE_URL + url
				li = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
				li.setInfo( type="Video", infoLabels={ "Title": saison + " - " + title, "Plot": desc, "Season": saison } )
				u = sys.argv[0] + "?mode=1&name=" + urllib.quote_plus(title) + "&url=" + urllib.quote_plus(url) + "&thumb=" + urllib.quote_plus(thumb) + "&plot=" + urllib.quote_plus(desc)
				xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li)
		else:
			desc, season, title, img = re.compile('toutv.mediaData.+?"description":"(.+?)".+?"seasonNumber":(.+?),.+?"title":"(.+?)".+?toutv.imageA=\'(.+?)\'').findall(url_data)[0]
			thumb = get_thumbnail(img)
			li = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
			season = "Saison " + season
			li.setInfo( type="Video", infoLabels={ "Title": season + " - " + title, "Plot": desc, "Season": season} )
			u = sys.argv[0] + "?mode=1&name=" + urllib.quote_plus(title) + "&url=" + urllib.quote_plus(url) + "&thumb=" + urllib.quote_plus(thumb) + "&plot=" + urllib.quote_plus(desc)
			xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li)

"""
	Get a thumbnail and cache it
"""
def get_thumbnail(thumbnail_url):
	try:
		filename = xbmc.getCacheThumbName( thumbnail_url )
		filepath = xbmc.translatePath( os.path.join( BASE_CACHE_PATH, filename[ 0 ], filename ) )
		if not os.path.isfile( filepath ):
			info = urllib.urlretrieve( thumbnail_url, filepath )
			urllib.urlcleanup()
		return filepath
	except:
		print "Error: get_thumbnail()"
		return thumbnail_url

"""
	Play an episode
"""
def playVideo(url, name, thumb, plot):
	url_data = readUrl(url)
	p = re.compile("toutv.releaseUrl='(.+?)'")
	pid = p.findall(url_data)
	url = THEPLATFORM_CONTENT_URL + pid[0] + '&format=SMIL'
	url_data = readUrl(url)
	rtmp_url = re.compile('<meta base="rtmp:(.+?)"').findall(url_data)[0]
	playpath = re.compile('<ref src="mp4:(.+?)"').findall(url_data)[0]
	playpath = "mp4:" + playpath
	rtmp_url = "rtmp:" + rtmp_url
	item = xbmcgui.ListItem(label=name,iconImage="DefaultVideo.png",thumbnailImage=thumb)
	item.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot } )
	item.setProperty("PlayPath", playpath)
	xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(rtmp_url, item)

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

params = get_params()
mode = None
name = None
url = None
page = 1
try:
	url = urllib.unquote_plus(params["url"])
except:
	pass
try:
	name = urllib.unquote_plus(params["name"])
except:
	pass
try:
	mode = int(params["mode"])
except:
	pass
try:
	page = int(params["page"])
except:
	pass
try:
	thumb = urllib.unquote_plus(params["thumb"])
except:
	pass
try:
	plot = urllib.unquote_plus(params["plot"])
except:
	pass

if mode == None:
	name = ''
	showRoot()
elif mode == 0:
	showList(url, name)
elif mode == 1:
	playVideo(url, name, thumb, plot)

xbmcplugin.setPluginCategory(handle = int(sys.argv[1]), category = name )
xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
xbmcplugin.endOfDirectory(handle = int(sys.argv[1]))
