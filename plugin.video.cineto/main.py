# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
import sys, os, json, zlib
import urllib, urllib2, cookielib
import re, base64
import urlresolver

SEP = os.sep
thisPlugin = int(sys.argv[1])
dialog = xbmcgui.Dialog()
addonInfo = xbmcaddon.Addon()
thumbUrl = addonInfo.getAddonInfo('path')+SEP+"resources"+SEP+"img"+SEP
dataUrl = xbmc.translatePath(addonInfo.getAddonInfo('profile'))

# -- main urls --
urlMain = "https://cine.to"
urlSearch = "https://cine.to/request/search"
urlMeta = "https://cine.to/request/entry"
urlLinks = "https://cine.to/request/links"
urlPics = "https://s.cine.to/cover/"
urlStream = "https://cine.to/out/"

# -- get Values from config settings
yearStart = xbmcplugin.getSetting(thisPlugin,'start_year')
yearEnd = xbmcplugin.getSetting(thisPlugin,'end_year')
imdbRating = xbmcplugin.getSetting(thisPlugin,'imdb_rating')
langSelect = xbmcplugin.getSetting(thisPlugin,'lang_select')
print "langSetting "+langSelect
# -- searchquery --
sQ = ""

# --------------
# main functions
# --------------
def q(genre=0, page=1):
	global yearStart,yearEnd,imdbRating, sQ
	# decided to limit the query
	return "kind=all&genre="+str(genre)+"&rating="+imdbRating+"&year%5B%5D="+yearStart+"&year%5B%5D="+yearEnd+"&term="+str(sQ)+"&page="+str(page)+"&count=24"

def mainContent(genre=0, genreName="",page=1):
	global thisPlugin, urlSearch
	print "[cineto][mainSite] started"
	query = q(genre,page)
	#print "[cineto] query"
	#print query
	data = getData(urlSearch,query)
	#print "[cineto] data"
	#print data
	jsonContent = json.loads(data)
	addDirectoryItem(".Genre. ("+str(genreName)+")", {"selector":"1"})
	addDirectoryItem(".Search.", {"selector":"4"})
	addDirectoryItem("next page.."+str(int(page)+1), {"pageData":int(page)+1, "genreData":genreData, "genreName":genreName})
	for entry in jsonContent['entries']:
		#print entry
		languages = entry['language'].split(',')
		qual = entry['quality']
		lang = []
		for ll in languages:
			lang.append(ll[0:2])
		lang.sort()
		l = ",".join(lang)
		title = entry['title']+" ("+l+" "+qual+")"
		picture = "http:"+entry['cover']
		#print picture
		if langSelect[0:2] == "al":
			addDirectoryItem(title.encode('utf-8'), {"selector":2, "name": entry['title'].encode('utf-8'), "imdb":entry['imdb'].encode('utf-8'),"lang":l.encode('utf-8')},picture)
		else:
			if langSelect[0:2] in l:
				addDirectoryItem(title.encode('utf-8'), {"selector":2, "name": entry['title'].encode('utf-8'), "imdb":entry['imdb'].encode('utf-8'),"lang":l.encode('utf-8')},picture)
	xbmcplugin.endOfDirectory(thisPlugin)

def changeGenre():
	global thisPlugin, urlMain
	print "[cineto][changeGenre] started"
	addDirectoryItem(".all.", {"genreData":0})
	httpData = getData(urlMain+"/#","")
	print httpData
	reCategories = r'data-id="[0-9]+" href="#" class="list-group-item">([^<]+)<small>([^<]?)</small>'
	cats = re.findall(reCategories,httpData)
	print cats
	d = 0
	for c in cats:
		print c
		cat = c[0]+" ("+c[1]+")"
		d = d+1
		addDirectoryItem(cat.encode('utf-8'), {"genreData":d,"genreName":c[0].encode('utf-8')})
	xbmcplugin.endOfDirectory(thisPlugin)

def showMovie(title, imdb, lang):
	global thisPlugin, urlLinks, urlMeta, urlPics
	print "[cineto][showMovie] started"
	picture = urlPics + imdb + ".jpg"
	addDirectoryItem("."+title.encode('utf-8')+".",{},picture)
	for l in lang.split(","):
		print "'"+l+"' imdb " + str(imdb) 
		pd = "ID="+str(imdb)+"&lang="+str(l)
		linkData = getData(urlLinks,pd)
		print linkData
		linkDataJSON = json.loads(linkData)
		links = linkDataJSON['links']
		for link in links.iteritems():
			host = link[0]
			qual = link[1][0]
			if len(link[1])>2:
				del link[1][0]
				count = 1
				for li in link[1]:
					addDirectoryItem(l.encode('utf-8')+" "+host.encode('utf-8')+"("+str(count)+") "+qual.encode('utf-8'), {"selector":"3","imdb":imdb,"streamId":str(li),"title":title.encode('utf-8')},picture)
					count +=1
			else:
				id = link[1][1]
				addDirectoryItem(l.encode('utf-8')+" "+host.encode('utf-8')+" "+qual.encode('utf-8'), {"selector":"3","imdb":imdb,"streamId":str(id),"title":title.encode('utf-8')},picture)
	xbmcplugin.endOfDirectory(thisPlugin)

def playStream(streamId,imdb,title):
	print "[cineto][playStream] started"
	global thisPlugin, urlStream
	icon = urlPics + imdb + ".jpg"
	streamUrl = urlStream+str(streamId)
	finalstreamUrl = getStreamUrl(streamUrl)
	videoLink = urlresolver.resolve(finalstreamUrl)
	print videoLink
	if videoLink:
		print "[cineto][playStream] playing: "+videoLink
		li = xbmcgui.ListItem(label=title.encode('utf-8'), iconImage=icon, thumbnailImage=icon, path=videoLink)
		li.setInfo(type='Video', infoLabels={ "Title": title.encode('utf-8') })
		li.setProperty('IsPlayable', 'true')
		xbmc.Player().play(item=videoLink, listitem=li)
	else:
		addDirectoryItem("ERROR. Video deleted or urlResolver cant handle Host", {"urlV": "/"})
		xbmcplugin.endOfDirectory(thisPlugin)

def search():
	global thisPlugin, urlSearch, sQ
	print "[cineto][search] started"
	keyboard = xbmc.Keyboard(sQ, 'Suche Serie')
	keyboard.doModal()
	if keyboard.isConfirmed():
		sQ = keyboard.getText().replace(' ','+')  # sometimes you need to replace spaces with + or %20
		if sQ == None:
			addDirectoryItem("! no input !", {"selector":"0"})
			sQ = ""
			xbmcplugin.endOfDirectory(thisPlugin)
		else:
			ok = mainContent()

# ------
# helper
# ------
def getData(url, postData):
	try:
		req = urllib2.Request(url,postData)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		dr = response.read()
		response.close()
		return dr
	except:
		return False

def getStreamUrl(url):
	try:
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		res = response.read()
		resp = response.geturl()
		response.close()
		return resp
	except:
		return False

def addDirectoryItem(name, parameters={},pic=""):
	global addonInfo
	iconpic = pic
	if pic == "":
		iconpic = "DefaultFolder.png"
	li = xbmcgui.ListItem(name,iconImage=iconpic, thumbnailImage=pic)
	li.setProperty('fanart_image', addonInfo.getAddonInfo('fanart'))
	#li.setInfo()
	u = sys.argv[0] + '?' + urllib.urlencode(parameters)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=li, isFolder=True)

def addPlayableItem(name, parameters={},pic=""):
	global addonInfo
	iconpic = pic
	if pic == "":
		iconpic = "DefaultFolder.png"
	li = xbmcgui.ListItem(name,iconImage=iconpic, thumbnailImage=pic)
	li.setProperty('fanart_image', addonInfo.getAddonInfo('fanart'))
	li.setProperty("IsPlayable","true")
	u = sys.argv[0] + '?' + urllib.urlencode(parameters)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=li, isFolder=False)

def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


# ----------------
# ----- main -----
# ----------------

params = parameters_string_to_dict(sys.argv[2])

selector = str(params.get("selector",""))
genreData = str(params.get("genreData",""))
genreName = str(params.get("genreName",""))
searchData = str(params.get("searchData", ""))
pageData = str(params.get("pageData", ""))
title = str(params.get("name", ""))
imdb = str(params.get("imdb", ""))
lang = str(params.get("lang", ""))
streamId = str(params.get("streamId", ""))

print "[cineto][main] show params"
print params

if not params.has_key('selector'):	# -- init start --
	selector = "0"
if not params.has_key('genreData'):
	genreData = "0"
if not params.has_key('genreName'):
	genreName = "All"
if not params.has_key('pageData'):
	pageData = "1"

if selector=="0":						# -- show Main --
	pageData = urllib.unquote(pageData)
	genreData = urllib.unquote(genreData)
	genreName = urllib.unquote(genreName)
	ok = mainContent(genreData,genreName,pageData)
if selector=="1":						# -- show Genre --
	ok = changeGenre()
if selector=="2":						# -- show Meta and Links --
	title = urllib.unquote(title)
	imdb = urllib.unquote(imdb)
	lang = urllib.unquote(lang)
	ok = showMovie(title,imdb,lang)
if selector=="3":						# -- get link and play
	imdb = urllib.unquote(imdb)
	title = urllib.unquote(title)
	streamId = urllib.unquote(streamId)
	ok = playStream(streamId,imdb, title)
if selector=="4":						# -- search --
	ok = search()