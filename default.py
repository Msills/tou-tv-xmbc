# coding=utf-8

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
TOU_TV_SEARCH_URL = '/recherche?q='
TOU_TV_MEDIA_FLAG = 'toutv.mediaData'

THEPLATFORM_CONTENT_URL = 'http://release.theplatform.com/content.select?pid='

DHARMA_RTMP_FIX = False

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
	List the home page
"""
def showRoot():
		# add the built in categories
		handle = int(sys.argv[1])
		u  =  sys.argv[0]
		url = urllib.quote_plus(TOU_TV_BASE_URL + TOU_TV_REPERTOIRE_URL)
		xbmcplugin.addDirectoryItem(handle,u + '?mode=2&name=repertoire&url=' + url,xbmcgui.ListItem('A à Z'),True)
		xbmcplugin.addDirectoryItem(handle,u + '?mode=0&name=genres',xbmcgui.ListItem('Genres'),True)
		xbmcplugin.addDirectoryItem(handle,u + '?mode=0&name=recherche',xbmcgui.ListItem('Recherche'),True)
		xbmcplugin.addDirectoryItem(handle,u + '?mode=0&name=nouveautes',xbmcgui.ListItem('À Découvrir'),True)
		xbmcplugin.addDirectoryItem(handle,u + '?mode=0&name=favoris',xbmcgui.ListItem('Les Favoris Sur TOU.TV'),True)
		xbmcplugin.addDirectoryItem(handle,u + '?mode=0&name=vedette',xbmcgui.ListItem('Les Plus Récents'),True)

"""
    Show the category selected at the top level
"""
def showCategory(name):
	if name  == 'repertoire':
		showRepertoire()
	elif name == 'recherche':
		showSearch()
	elif name == 'genres':
		showGenres()
	else:
		showSection(name)

def showSearch():
	kb = xbmc.Keyboard('', 'Recherche',False)
	kb.doModal()
	if kb.isConfirmed():
		url_data = readUrl(TOU_TV_BASE_URL + TOU_TV_SEARCH_URL + urllib.quote_plus(kb.getText()))
		showSearchResults(url_data)
	else:
		showRoot()

def showSearchResults(url_data):

	# sometimes we match an entire series

	series = '<p class="grandstitres resultats"><strong>(.+?)</strong><small>(.+?)</small></p>.+?[\n\s]+<img class="separateur".+?[\n\s]+<a href="(.+?)" id="MainContent_ctl00_ResultsEmissionsRepeater_LienImage.+?"><img src="(.+?)" id=.+?/></a>'

	match = re.compile(series).findall(url_data)

	for title1,title2,url,img in match:
		thumb = get_thumbnail(img)
		url = TOU_TV_BASE_URL + url
		li = xbmcgui.ListItem(title1 + ' - ' + title2,iconImage=thumb, thumbnailImage=thumb)
		u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(title1) + "&url=" + urllib.quote_plus(url) 
		xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)

	reg ='<div class="blocepisodeemission">[\s\n]+<div class="floatimg">[\s\n]+<a href="(.+?)" .+?class="vignettesgrandes">[\s\n]+<span class="play"></span>[\s\n]+<span class="duration">&nbsp;(.+?)</span>[\s\n]+<img src="(.+?)" id.+? />[\s\n]+</a>[\s\n]+</div>[\s\n]+<div class="floatinfos">[\s\n]+<a href=".+?" id=.+?class="infosEmission">[\s\n]+<strong>(.+?)</strong>[\s\n]+(.+?)[\s\n]+</a>' 

	match = re.compile(reg).findall(url_data)
	
	for url,duration,img,title1,title2 in match:
		thumb = get_thumbnail(img)
		url = TOU_TV_BASE_URL + url
		title2 = re.sub('<.+?>','',title2)
		li = xbmcgui.ListItem(title1, iconImage=thumb, thumbnailImage=thumb)
		li.setInfo( type="Video", infoLabels={ "Title": title1 + " - " + title2 + ' (' + duration + ')'} )
		u = sys.argv[0] + "?mode=4&plot=&name=" + urllib.quote_plus(title1) + "&url=" + urllib.quote_plus(url) + "&thumb=" + urllib.quote_plus(thumb)
		xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li)

"""
	Show the available genres from the main page
"""
def showGenres():
	url_data = readUrl(TOU_TV_BASE_URL)
	match = re.compile('<a id="GenresFooterRepeater.+?href="(.+?)">(.+?)</a></li>').findall(url_data)
	for url,name in match:
		url = TOU_TV_BASE_URL + url
		li = xbmcgui.ListItem(name)
		u = sys.argv[0] + "?mode=1&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url)
		xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)

"""
	show thumbnail items either from a complete genre page or from a section of the main page
"""
def showDisplayItems(data):
	regex = '<a href="(.+?)" id="MainContent.+?" class="vignettesgrandes".+?>[\n\s]+<span class="play"></span>[\n\s]+<span class="duration">&nbsp;(.+?)</span>[\n\s]+<img id=".+?" src="(.+?)".+?/>[\n\s]+</a>[\n\s]+<h3><a href=.+?>(.+?)</a></h3>[\n\s]+<a href=".+?>\s*(?:<small.+?>)?(.+?)<' 

	match = re.compile(regex).findall(data)
	
	for url,duration,img,title1,title2 in match:
		thumb = get_thumbnail(img)
		url = TOU_TV_BASE_URL + url
		li = xbmcgui.ListItem(title1, iconImage=thumb, thumbnailImage=thumb)
		li.setInfo( type="Video", infoLabels={ "Title": title1 + " - " + title2 + ' (' + duration + ')'} )
		u = sys.argv[0] + "?mode=4&plot=&name=" + urllib.quote_plus(title1) + "&url=" + urllib.quote_plus(url) + "&thumb=" + urllib.quote_plus(thumb)
		xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li)

def showSection(name):
	url_data = readUrl(TOU_TV_BASE_URL)
	ar = url_data.split('<h2>')
	d = {'nouveautes':1,'favoris':2,'vedette':3}
	showDisplayItems(ar[d[name]])

"""
	Show the main page for a given genre
"""
def showAccueil(data_url,genre):
	url_data = readUrl(data_url)
	# first, add the entry for all videos
	match = re.compile('<a id="MainContent_ctl00_LienRepertoireHaut" .+?href="(.+?)"></a>').search(url_data)
	
	if not match is None:
		li = xbmcgui.ListItem(genre + ' - A-Z' )
		url = urllib.quote_plus(TOU_TV_BASE_URL + match.group(1))
		u = sys.argv[0] + "?mode=2&name=" + urllib.quote_plus(genre) + "&url=" + url
		xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)
	
	showDisplayItems(url_data)

"""
	List all Tou.tv shows in the Tou.tv plugin root directory
"""
def showRepertoire(data_url, category):
		url_data = readUrl(data_url)
		match = re.compile('href="(.+?)">\s+<h1 class="titreemission">(.+?)</h1>').findall(url_data)
		for url, name in match:
			url = TOU_TV_BASE_URL + url
			li = xbmcgui.ListItem(name)
			u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url)
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
				u = sys.argv[0] + "?mode=4&name=" + urllib.quote_plus(title) + "&url=" + urllib.quote_plus(url) + "&thumb=" + urllib.quote_plus(thumb) + "&plot=" + urllib.quote_plus(desc)
				xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li)
		else:
			desc, season, title, img = re.compile('toutv.mediaData.+?"description":"(.+?)".+?"seasonNumber":(.+?),.+?"title":"(.+?)".+?toutv.imageA=\'(.+?)\'',re.IGNORECASE).findall(url_data)[0]
			thumb = get_thumbnail(img)
			li = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
			season = "Saison " + season
			li.setInfo( type="Video", infoLabels={ "Title": season + " - " + title, "Plot": desc, "Season": season} )
			u = sys.argv[0] + "?mode=4&name=" + urllib.quote_plus(title) + "&url=" + urllib.quote_plus(url) + "&thumb=" + urllib.quote_plus(thumb) + "&plot=" + urllib.quote_plus(desc)
			xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li)

"""
	Get a thumbnail and cache it
"""
def get_thumbnail(thumbnail_url):
	try:
		print thumbnail_url
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
	if DHARMA_RTMP_FIX:
		item.setProperty("PlayPath", playpath)
	else:
		rtmp_url += " playpath=" + playpath
	
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

print mode,url,name,int(sys.argv[1])

if mode == None:
	name = ''
	showRoot()
elif mode == 0:
	showCategory(name)
elif mode == 1:
	showAccueil(url,name)
elif mode == 2:
	showRepertoire(url, name)
elif mode == 3:
	showList(url, name)
elif mode == 4:
	playVideo(url, name, thumb, plot)

xbmcplugin.setPluginCategory(handle = int(sys.argv[1]), category = name )
xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
xbmcplugin.endOfDirectory(handle = int(sys.argv[1]))
