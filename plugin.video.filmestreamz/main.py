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
urlMain = "http://www.filme-streamz.com"

# -- regexes --
rCategories = r'href="([^"]+)" class="rightsidemenu cat">([^<]+)<'
rMovies = r'"imgborder" style="">(.*?)<a href="([^"]+)" title="([^"]+)">(.*?)<img src="([^"]+)"' # multiline dotall
rNew = r'"imgborder" style="[^"]+">(.?)<a href="([^"]+)" title="([^"]+)">(.*?)<img src="([^"]+)"'
rStreams = r'<a href="((http://)([^/]+)(/)([^"]+))" target="videoPlayer" class="sinactive server" style="text-align: center; width: 20%;">'
rPages = r'-p[0-9]{1,2}.html'

# -- searchquery --
sQ = ""

# --------------
# main functions
# --------------
def mainContent(genreUrl="", genreName="",page=1):
	global thisPlugin, urlMain, rMovies, sQ
	print "[filmestreamz][mainContent] started"
	nextPageUrl = re.sub(rPages,"",genreUrl)+"-p"+str(int(page)+1)+".html"
	print "[filmestreamz][mainContent] url "+nextPageUrl
	print "[filmestreamz][mainContent] genreName "+genreName
	
	addDirectoryItem(".Neues.", {"selector":"0", "pageData":int(page), "genreUrl":"/categorie/7/Neuerscheinungen-stream-p1.html", "genreName":"NEU"})
	addDirectoryItem(".Genre. ("+str(genreName)+")", {"selector":"1"})
	addDirectoryItem(".Suche.", {"genreName":"FUND"})
	addDirectoryItem(".next..("+str(int(page)+1)+")", {"pageData":int(page)+1, "genreUrl":nextPageUrl, "genreName":genreName})
	
	if genreName=="FUND":
		print "[filestreamz][search] started"
		keyboard = xbmc.Keyboard(sQ, 'Suche Serie')
		keyboard.doModal()
		if keyboard.isConfirmed():
			sQ = keyboard.getText()
		genreUrl = "/s/"+sQ+"-stream-deutch-online-anschauen-p1.html"
		
	if (page>1) and (genreUrl==""):
		urlMain = urlMain+"/page/"+str(page)+".html"
		data = getUrlData(urlMain)
		rM = re.compile(rMovies, re.MULTILINE|re.DOTALL)
		movs = rM.findall(data)
	
	if (genreUrl is not ""):
		urlGenre = urlMain+genreUrl
		print "[filmestreamz][mainContent] genreUrl is "+str(urlGenre)
		data = getUrlData(urlGenre)
		rM = re.compile(rMovies, re.MULTILINE|re.DOTALL)
		if genreName=="NEU":
			rM = re.compile(rNew, re.MULTILINE|re.DOTALL)
		if genreName=="FUND":
			rM = re.compile(rMovies, re.MULTILINE|re.DOTALL)
		movs = rM.findall(data)
	
	for m in movs:
		streamLink = m[1]
		title = m[2].replace(" stream - film stream","").decode('utf-8')
		picture = m[4].replace(" ","%20")
		addDirectoryItem(title.encode('utf-8'), {"selector":2, "name": title.encode('utf-8'),"streamData":streamLink, "picture":picture},picture)
	
	xbmcplugin.endOfDirectory(thisPlugin)

def changeGenre():
	global thisPlugin, urlMain, rCategories
	print "[filmeStreamz][changeGenre] started"
	addDirectoryItem(".all.", {"genreUrl":""})
	httpData = getUrlData(urlMain,"")
	cats = re.findall(rCategories,httpData)
	print cats
	for c in cats:
		print c
		cUrl = c[0].decode('utf-8')
		cName = c[1].decode('utf-8')
		addDirectoryItem(cName.encode('utf-8'), {"genreUrl":c[0],"genreName":cName.encode('utf-8')})
	xbmcplugin.endOfDirectory(thisPlugin)

def showMovie(title, streamData, picture):
	global thisPlugin, urlMain
	print "[filmeStreamz][showMovie] started"
	addDirectoryItem("."+title.decode('utf-8').encode('utf-8')+".",{},picture)
	print "link "+str(streamData)
	urlMovie = urlMain+streamData
	httpData = getUrlData(urlMovie)
	rS = re.compile(rStreams, re.DOTALL)
	streams = rS.findall(httpData)
	for s in streams:
		streamer = s[2].split(".")
		streamName = ("HOSTER: "+streamer[len(streamer)-2]+"."+streamer[len(streamer)-1]).decode('utf-8')
		addDirectoryItem(streamName.encode('utf-8'), {"selector":"3","streamUrl":s[0],"title":title.decode('utf-8').encode('utf-8')},picture)
	xbmcplugin.endOfDirectory(thisPlugin)

def playStream(streamLink,title,picture):
	print "[filmeStreamz][playStream] started"
	global thisPlugin
	print "streamLink A "+str(streamLink)
	streamLink = urllib2.unquote(streamLink)
	print "streamLink B "+str(streamLink)
	videoLink = urlresolver.resolve(streamLink)
	print videoLink
	if videoLink:
		print "[filmeStreamz][playStream] playing: "+videoLink
		li = xbmcgui.ListItem(label=title.encode('utf-8'), iconImage=picture, thumbnailImage=picture, path=videoLink)
		li.setInfo(type='Video', infoLabels={ "Title": title.encode('utf-8') })
		li.setProperty('IsPlayable', 'true')
		xbmc.Player().play(item=videoLink, listitem=li)
	else:
		addDirectoryItem("ERROR. Video deleted or urlResolver cant handle Host", {"urlV": "/"})
		xbmcplugin.endOfDirectory(thisPlugin)

def search():
	global thisPlugin, urlSearch, sQ
	print "[filmeStreamz][search] started"
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
def getUrlData(url, postData=""):
	try:
		req = urllib2.Request(url,postData)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		dr = response.read()
		print response.geturl()
		response.close()
		return dr
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
genreUrl = str(params.get("genreUrl",""))
genreName = str(params.get("genreName",""))
searchData = str(params.get("searchData", ""))
pageData = str(params.get("pageData", ""))
title = str(params.get("name", ""))
picture = str(params.get("picture", ""))
streamUrl = str(params.get("streamUrl", ""))
streamData = str(params.get("streamData", ""))
link = str(params.get("link", ""))

print "[filmeStreamz][main] show params"
print params

if not params.has_key('selector'):	# -- init start --
	selector = "0"
if not params.has_key('genreUrl'):
	genreUrl = ""
if not params.has_key('genreName'):
	genreName = "All"
if not params.has_key('pageData'):
	pageData = "1"

if selector=="0":						# -- show Main/Genre/Search --
	pageData = urllib.unquote(pageData)
	genreUrl = urllib.unquote(genreUrl)
	genreName = urllib.unquote(genreName)
	ok = mainContent(genreUrl,genreName,pageData)
if selector=="1":						# -- change Genre --
	ok = changeGenre()
if selector=="2":						# -- show Hoster Links --
	title = urllib.unquote(title)
	streamData = urllib.unquote(streamData)
	picture = urllib.unquote(picture)
	ok = showMovie(title,streamData,picture)
if selector=="3":						# -- get link and play
	streamUrl = urllib.unquote(streamUrl)
	title = urllib.unquote(title)
	picture = urllib.unquote(picture)
	ok = playStream(streamUrl,title,picture)
