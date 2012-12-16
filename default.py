# -*- coding: utf-8 -*-

"""
    Plugin for streaming media from Tou.tv
"""

__plugin__ = "Tou.tv"
__author__ = 'misil [michaelsillslavoie@gmail.com]'
__url__ = "http://xbmctoutv.blogspot.com/"
__credits__ = "PBS and CBS plugins"
__version__ = "0.1.5"

import xbmc
import xbmcgui
import xbmcplugin
import urllib2
import urllib
import re
import sys
import os
import traceback
import json

HEADER = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1'
BASE_CACHE_PATH = os.path.join( xbmc.translatePath( "special://profile/" ), "Thumbnails", "Video" )

TOU_TV_BASE_URL = 'http://www.tou.tv'
TOU_TV_REPERTOIRE_URL = '/repertoire'
TOU_TV_SEARCH_URL = '/recherche?q='

TOUTV_API_URL = 'http://api.radio-canada.ca/validationMedia/v1/Validation.html?output=json&appCode=thePlatform&deviceType=Android&connectionType=wifi&idMedia='

def unescape_callback(matches):
	html_entities = {
		'quot':'\"', 'amp':'&', 'apos':'\'', 'lt':'<', 'gt':'>', 'nbsp':' ', 'copy':'©', 'reg':'®',
		'Agrave':'À', 'Aacute':'Á', 'Acirc':'Â', 'Atilde':'Ã', 'Auml':'Ä', 'Aring':'Å', 'AElig':'Æ',
		'Ccedil':'Ç', 'Egrave':'È', 'Eacute':'É', 'Ecirc':'Ê', 'Euml':'Ë', 'Igrave':'Ì', 'Iacute':'Í',
		'Icirc':'Î', 'Iuml':'Ï', 'ETH':'Ð', 'Ntilde':'Ñ', 'Ograve':'Ò', 'Oacute':'Ó', 'Ocirc':'Ô',
		'Otilde':'Õ', 'Ouml':'Ö', 'Oslash':'Ø', 'Ugrave':'Ù', 'Uacute':'Ú', 'Ucirc':'Û', 'Uuml':'Ü',
		'Yacute':'Ý', 'agrave':'à', 'aacute':'á', 'acirc':'â', 'atilde':'ã', 'auml':'ä', 'aring':'å',
		'aelig':'æ', 'ccedil':'ç', 'egrave':'è', 'eacute':'é', 'ecirc':'ê', 'euml':'ë', 'igrave':'ì',
		'iacute':'í', 'icirc':'î', 'iuml':'ï', 'eth':'ð', 'ntilde':'ñ', 'ograve':'ò', 'oacute':'ó',
		'ocirc':'ô', 'otilde':'õ', 'ouml':'ö', 'oslash':'ø', 'ugrave':'ù', 'uacute':'ú', 'ucirc':'û',
		'uuml':'ü', 'yacute':'ý', 'yuml':'ÿ'
	}

	entity = matches.group(0)
	val = matches.group(1)

	try:
		if entity[:2] == '\u':
			return entity.decode('unicode-escape')
		elif entity[:3] == '&#x':
			return unichr(int(val, 16))
		elif entity[:2] == '&#':
			return unichr(int(val))
		else:
			return html_entities[val].decode('utf-8')

	except (ValueError, KeyError):
		pass

def HTMLUnescape(data):
	data = data.decode('utf-8')
	data = re.sub('&#?x?(\w+);|\\\\u\d{4}', unescape_callback, data)
	data = data.encode('utf-8')

	return data


"""
	Read all the text from the specified url
"""
def readUrl(url, params):
	req = urllib2.Request(url)
	req.add_header('User-Agent', HEADER)
	f = urllib2.urlopen(req, params)
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
	xbmcplugin.addDirectoryItem(handle,u + '?mode=2&name=repertoire',xbmcgui.ListItem('A à Z'),True)
	xbmcplugin.addDirectoryItem(handle,u + '?mode=0&name=genres',xbmcgui.ListItem('Genres'),True)
	xbmcplugin.addDirectoryItem(handle,u + '?mode=0&name=recherche',xbmcgui.ListItem('Recherche'),True)
	xbmcplugin.addDirectoryItem(handle,u + '?mode=0&name=country', xbmcgui.ListItem('Par pays'),True)
	xbmcplugin.addDirectoryItem(handle,u + '?mode=0&name=VignettesTouTVADecouvrir',xbmcgui.ListItem('À Découvrir'),True)
	xbmcplugin.addDirectoryItem(handle,u + '?mode=0&name=VignettesTouTVFavoris',xbmcgui.ListItem('Les Favoris Sur TOU.TV'),True)
	xbmcplugin.addDirectoryItem(handle,u + '?mode=0&name=VignettesTouTVRecents',xbmcgui.ListItem('Les Plus Récents'),True)

"""
    Show the category selected at the top level
"""
def showCategory(name):
	if name  == 'repertoire':
		showRepertoire(None, None)
	elif name == 'recherche':
		showSearch()
	elif name == 'country':
		showCountry()
	elif name == 'genres':
		showGenres()
	else:
		showSection(name)

def showSearch():
	kb = xbmc.Keyboard('', 'Recherche',False)
	kb.doModal()
	if kb.isConfirmed():
		params = urllib.urlencode({'query': kb.getText()})
		url_data = readUrl(TOU_TV_BASE_URL + TOU_TV_SEARCH_URL, params)
		showSearchResults(url_data)
	else:
		showRoot()

def showSearchResults(url_data):
	
	match = re.compile('<img src="(.+?)".+?>.+?<div class="recherche_episodeMetadata">\s+<a href="(.+?)".+?<h3>(.+?)<span.+?">(.+?)</span>.+?<p>(.+?)</p>', re.DOTALL).findall(url_data)

	for img, url, title, season, desc in match:
		url = TOU_TV_BASE_URL + url
		title = HTMLUnescape(title + ' (' + season + ')')
		desc = re.sub('</*span.+?>', '', HTMLUnescape(desc))
			
		thumb = get_thumbnail(img)
		
		li = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
		li.setInfo( type="Video", infoLabels={ "Title": title, "Plot" : desc } )
		u = sys.argv[0] + "?mode=4&name=" + urllib.quote_plus(title) + "&url=" + urllib.quote_plus(url) + "&thumb=" + urllib.quote_plus(thumb) + "&plot=" + urllib.quote_plus(desc)
		xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li)


"""
	Show the available genres from the repertoire page
"""
def showGenres():
	url_data = readUrl(TOU_TV_BASE_URL + TOU_TV_REPERTOIRE_URL, None)
	match = re.compile('var genres\s*=\s*[^;]+').findall(url_data)
	
	genres = re.compile('Title":"(.+?)",.+?"Id":(\d+)').findall(match[0])
	for title,id in genres:
		li = xbmcgui.ListItem(title)
		u = sys.argv[0] + "?mode=1&name=" + urllib.quote_plus(id)
		xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)

"""
	Show the available countries from the repertoire page
"""
def showCountry():
	url_data = readUrl(TOU_TV_BASE_URL + TOU_TV_REPERTOIRE_URL, None)
	match = re.compile('var countries\s*=\s*\[[^;]+').findall(url_data)

	countries = re.compile('"CountryKey":"(.+?)","CountryValue":"(.+?)"').findall(match[0])
	for country,name in countries:
		name = HTMLUnescape(name)

		li = xbmcgui.ListItem(name)
		u = sys.argv[0] + "?mode=5&name=" + urllib.quote_plus(country)
		xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)


"""
	show thumbnail items either from a complete genre page or from a section of the main page
"""
def showDisplayItems(data):
	info = re.compile('DetailsViewDescription":"(.+?)","DetailsViewSaison":"(.+?)".+?"DetailsViewImageUrlL":"(.+?)".+?"DetailsFullDescription":"(.+?)","DetailsViewUrl":"(.+?)"', re.DOTALL).findall(data)
	for title, season, img, desc, url in info:
		title = title + ' (' + season + ')'
		thumb = get_thumbnail(img)
		url = TOU_TV_BASE_URL + url

		li = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
		li.setInfo( type="Video", infoLabels={ "Title": title, "Plot": desc })
		u = sys.argv[0] + "?mode=4&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&thumb=" + urllib.quote_plus(thumb) + "&plot=" + urllib.quote_plus(desc)

		xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li)

def showSection(vignette):
	url_data = readUrl(TOU_TV_BASE_URL, None)
	
	match = re.compile('data-initialdata="(.+?)"').findall(url_data)
	data = HTMLUnescape(match[0])

	match = re.compile('\{"Id":"' + vignette + '"(.+?)(?:\{"Id"|$)').findall(data)

	showDisplayItems(match[0])


"""
	List all Tou.tv shows in the Tou.tv plugin root directory
"""
def showRepertoire(filter_genre, filter_country):
	url_data = readUrl(TOU_TV_BASE_URL + TOU_TV_REPERTOIRE_URL, None)
	match = re.compile('data-bind=".*displayGenre\(\'(\d*)\'\).*displayCountry\(\'(.*?)\'\)">\s*<div class="repertoire_groupeNivTitre">\s*<.*href="(.+?)">(.+?)</a>').findall(url_data)

	for genre, country, url, name in match:
		if (filter_genre is not None) and (filter_genre != genre):
			continue

		if (filter_country is not None) and (filter_country != country):
			continue

		url = TOU_TV_BASE_URL + url
		name = HTMLUnescape(name)

		li = xbmcgui.ListItem(name)
		u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url)
		xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)

"""
	List a specified show episodes
"""
def showList(url, name, season):
	url_data = readUrl(url, None)

	if 'VignettesTouTVEpisodes' in url_data:
		match = re.compile('data-initialdata="(.+?)"').findall(url_data)
		data = HTMLUnescape(match[0])

		season_list = re.compile('"SeasonList":\[(.+?)\]').findall(data)[0]
		season_list = season_list.split(',')

		if (season is None) and (len(season_list) > 1):
			info = re.compile('"SeasonList":\[(.+?)\]').findall(data)
			for season in season_list:
				li = xbmcgui.ListItem('Saison ' + season)
				u = sys.argv[0] + '?mode=3&name=' + urllib.quote_plus(name) + '&url=' + urllib.quote_plus(url) + '&season=' + season
				xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li,True)

		else:
			info = re.compile('"EmissionId":(\d+)').findall(data)
			emission_id = info[0]

			if (season is None):
				season = season_list[0]

			url_vignette = TOU_TV_BASE_URL + '/Emisode/GetVignetteSeason?emissionId=' + emission_id + '&season=' + str(season)
			data_vignette = HTMLUnescape(readUrl(url_vignette, None))

			info = re.compile('DetailsViewDescription":"(.+?)".+?"DetailsViewSaison":"(.+?)".+?"DetailsViewImageUrlL":"(.+?)".+?"DetailsFullDescription":"(.+?)".+?"DetailsViewUrl":"(.+?)".+?"DetailsIndexSeason":(.+?),', re.DOTALL).findall(data_vignette)
			for title, season_episode, img, desc, url, item_season in info:
				
				thumb = get_thumbnail(img)
				url = TOU_TV_BASE_URL + url

				title = title + ' (' + season_episode + ')'

				li = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
				li.setInfo( type="Video", infoLabels={ "Title": title, "Plot": desc })
				u = sys.argv[0] + "?mode=4&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&thumb=" + urllib.quote_plus(thumb) + "&plot=" + urllib.quote_plus(desc)

				xbmcplugin.addDirectoryItem(int(sys.argv[1]),u,li)


	else:
		title = HTMLUnescape(re.compile('<meta itemprop="name" content="(.+?)"').findall(url_data)[0])
		desc = HTMLUnescape(re.compile('<meta itemprop="description" content="(.+?)"').findall(url_data)[0])

		img = re.compile('<meta itemprop="image" content="(.+?)"').findall(url_data)[0]
		thumb = get_thumbnail(img)

		li = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
		li.setInfo( type="Video", infoLabels={ "Title": title, "Plot": desc })
		u = sys.argv[0] + "?mode=4&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&thumb=" + urllib.quote_plus(thumb) + "&plot=" + urllib.quote_plus(desc)

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
	url_data = readUrl(url, None)
	p = re.compile('"idMedia":"(.+?)"')
	pid = p.findall(url_data)					# Fetch the video id
	url = TOUTV_API_URL + pid[0]
	
	url_data = readUrl(url, None)				# Get video url
	jdata = json.loads(url_data)
	
	rtsp_url = jdata['url']
	rtsp_url = re.compile('(.+?)\\?').findall(rtsp_url)[0]	# Find the mp4 rtsp link
	rtsp_url = rtsp_url.replace('_800.', '_1200.');			# We want the best quality...

	item = xbmcgui.ListItem(label=name,iconImage="DefaultVideo.png",thumbnailImage=thumb)
	item.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot } )
	xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(rtsp_url, item)


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
	season = int(params["season"])
except:
	season = None
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
	showCategory(name)
elif mode == 1:
	showRepertoire(name, None)
elif mode == 2:
	showRepertoire(None, None)
elif mode == 3:
	showList(url, name, season)
elif mode == 4:
	playVideo(url, name, thumb, plot)
elif mode == 5:
	showRepertoire(None, name)

xbmcplugin.setPluginCategory(handle = int(sys.argv[1]), category = name )
xbmcplugin.addSortMethod( handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_NONE )
xbmcplugin.endOfDirectory(handle = int(sys.argv[1]))
