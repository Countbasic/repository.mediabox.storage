# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
import sys, os, random, json, zlib
import urllib, urllib2, cookielib
import re, base64
from watched import *
from array import *
from htmlentitydefs import name2codepoint as n2cp
import htmlentitydefs
# new since v0.95
import urlresolver
# new since 1.3.0
from player import bsPlayer

thisPlugin = int(sys.argv[1])
dialog = xbmcgui.Dialog()
addonInfo = xbmcaddon.Addon()
hosterList = xbmcplugin.getSetting(thisPlugin,"hosterlist").lower()
serienOrdner = xbmcplugin.getSetting(thisPlugin, 'seriespath')
thumbUrl = addonInfo.getAddonInfo('path')+"/resources/img/"

urlHost = "http://bs.to/api/"
urlPics = "http://s.bs.to/img/cover/"

# --------------
# main functions
# --------------

def showContent(sortType):
	global thisPlugin
	print "[bs][showContent] started"
	seriesList = {}
	serie =[]
	picture = ""
	try:
		if sortType[0] == "A":
			data = getUrl(urlHost+"series")
		if sortType[0] == "G":
			data = getUrl(urlHost+"series:genre")
	except Exception:
		addDirectoryItem("! a problem with website or network !", {"kindOf":0, "sortType": "A"})
		return
	print "[bs][showContent] -- some init data"
	print "[bs][showContent] len(data): "+str(len(data))
	print "[bs][showContent] sortType: "+sortType
	if sortType[0] == "A":
		# -- alphabetical order --
		jsonContent = json.loads(data)
		for d in jsonContent:
			serie = ["[B]"+d['series'].strip()+"[/B]",d['series'],d['id']]
			helper = ord(d['series'][0])
			if helper>90:
				helper = helper-32
			if (helper>64) and (helper<91):
				lKey = chr(helper).upper()
			else:
				lKey = "0"
			if lKey in seriesList:
				seriesList[lKey].append(serie)
			else:
				seriesList[lKey] = []
				seriesList[lKey].append(serie)
			
	if sortType[0] == "G":
		# -- sort by genre --
		jsonContent = json.loads(data)
		for d,dv in jsonContent.iteritems():
			if sortType[0] == "G":
				for ks in dv['series']:
					#print ks['name'].encode('utf-8')
					serie = [d+" : [B]"+ks['name'].strip()+"[/B]",ks['name'],ks['id']]
					lKey = d
					if lKey in seriesList:
						seriesList[lKey].append(serie)
					else:
						seriesList[lKey] = []
						seriesList[lKey].append(serie)
	
	if len(sortType)==1:
		# -- if only A or G show list of series --
		addDirectoryItem(".sort by Alphabet", {"kindOf":0, "sortType": "A"})
		addDirectoryItem(".sort by Genre", {"kindOf":0, "sortType": "G"})
		addDirectoryItem("", {"kindOf":0, "sortType": "A"})
		for key in sorted(seriesList):
			picture = thumbUrl+key+".jpg"
			skey = key
			if key =="0":
				skey = "0-9 etc"
			addDirectoryItem("[B]"+skey.encode('utf-8')+"[/B] (%d)" % len(seriesList[key]), {"kindOf":0, "sortType": sortType+key.encode('utf-8')},picture)
	else:
		# -- show subset for A or G --
		# -- example AD shows all series with D
		# -- example GAnimation shows all Series in Animation
		sortType = sortType.decode('utf-8')		
		sKey = sortType[1:]
		for s in sorted(seriesList[sKey], key=lambda f:f[0]):
			seriesName = s[0]
			picture = urlPics+str(s[2])+'.jpg|encoding=gzip'
			print picture
			# check if watched
			if readWatchedData(s[1].encode('utf-8')):
				seriesName = changeToWatched(seriesName)
			addDirectoryItem(seriesName, {"kindOf":1, "name": s[1].encode('utf-8'), "id":s[2],"doFav":"0"},picture)
	print "[bs][showContent] --- ok"	
	xbmcplugin.endOfDirectory(thisPlugin)

def showSeasons(n, id):
	global thisPlugin
	cover = urlPics+str(id)+'.jpg|encoding=gzip'
	name = n.decode('utf-8')
	print "[bs][showSeasons] started"
	addDirectoryItem("[B]. "+name.encode('utf-8')+"[/B]", {},cover)
	addDirectoryItem("[B]* add to Library[/B]", {"kindOf":"add2lib",'name': name.encode('utf-8'), 'id': str(id)},cover)
	season = 0
	seasonWatched = 0
	while True:
		season+=1
		data = json.loads(getUrl(urlHost+"series/"+str(id)+"/"+str(season)))
		print "[bs][showSeasons] reading seasons"
		if data.has_key('error'):
			season-=1
			break
		seasonName = "[B] Staffel"+str(season)+"[/B]"
		if readWatchedData((name+"/"+str(season)).encode('utf-8')):
			seasonWatched += 1
			seasonName = changeToWatched(seasonName.encode('utf-8'))
		if data.has_key('series'):
			addDirectoryItem(seasonName, {"kindOf":2, "name":data['series']['series'].encode('utf-8'), "id":id, "season":season},cover)
	if seasonWatched == season:
		markParentEntry(name.encode('utf-8'))
	print "[bs][showSeasons] --- ok"	
	xbmcplugin.endOfDirectory(thisPlugin)

def showEpisodes(n,id,season):
	global thisPlugin
	name = n.decode('utf-8')	
	episodesWatched = 0
	cover = urlPics+str(id)+'.jpg|encoding=gzip'
	addDirectoryItem("[B]. "+name.encode('utf-8')+" Staffel "+str(season)+"[/B]", {},cover)
	print "[bs][showEpisodes] started with "+name.encode('utf-8')
	data = json.loads(getUrl(urlHost+"series/"+str(id)+"/"+str(season)))
	for d in data['epi']:
		episodeName = "#"+str(d['epi'])
		if 'german' in d:
			episodeName += " "+d['german']
		if 'english' in d:
			if not d['english']=='':
				episodeName += " ("+d['english']+")"
		print episodeName.encode('utf-8')
		episodeName_watched = episodeName
		if readWatchedData((name+"/"+str(season)+"/"+str(d['epi'])).encode('utf-8')):
			episodesWatched += 1
			episodeName_watched = changeToWatched(episodeName)
		addDirectoryItem(episodeName_watched, {"kindOf": 3, "name":data['series']['series'].encode('utf-8'), "id":id, "season":season, "episode":d['epi'],"episodename":episodeName.encode('utf-8')},cover)
	# if watched all episodes, mark Season
	if episodesWatched == len(data['epi']):
		markParentEntry(name.encode('utf-8')+"/"+str(season))
	print "[bs][showEpisodes] ok"	
	xbmcplugin.endOfDirectory(thisPlugin)

def showHosts(n, id, season,episode,episodeName):
	global thisPlugin
	n = name.decode('utf-8')
	matchCover = ""
	cover = urlPics+str(id)+'.jpg|encoding=gzip'
	addDirectoryItem("[B]."+name+" Staffel "+str(season)+" "+str(episode)+"[/B]", {},cover)
	addDirectoryItem("[B]."+episodeName+"[/B]", {},cover)
	data = json.loads(getUrl(urlHost+"series/"+str(id)+"/"+str(season)+"/"+str(episode)))
	for d in data['links']:
		if d['hoster'].lower() in hosterList:
			showVideo(d['id'],data['series'].encode('utf8'),season,episode)
			break
		addDirectoryItem("Host: "+d['hoster'], {"kindOf":4, "vid":d['id'], "name": data['series'].encode("utf-8"),"season": season, "episode":episode},matchCover)
	print "[bs][showHosts] ok"	
	xbmcplugin.endOfDirectory(thisPlugin)
	
def showVideo(vid, n,season,episode):
	global thisPlugin
	name = n.decode('utf-8')
	print "[bs][showVideo] started on "+name.encode('utf8')+"/"+season+"/"+episode+" - "+str(vid)
	data = json.loads(getUrl(urlHost+"watch/"+str(vid)))
	videoLink = urlresolver.resolve(data['fullurl']);
	print "[bs][showVideo] urlResolver returns - "
	print videoLink
	if videoLink:
		item = xbmcgui.ListItem(path=videoLink)
		bsPlayer().playStream(videoLink, name.encode('utf-8'),season,episode)
	else:
		addDirectoryItem("ERROR. Video deleted or urlResolver cant handle Host", {"urlV": "/"})
		xbmcplugin.endOfDirectory(thisPlugin)

def straightPlay(id,season,episode):
	global thisPlugin
	thisUrl = urlHost+"series/"+str(id)+"/"+str(season)+"/"+str(episode)
	print "[bs][straightPlay] thisUrl: "+thisUrl
	episodeData = getUrl(thisUrl)
	print episodeData
	episodeJSON = json.loads(episodeData)
	series = episodeJSON['series']
	allHoster = []
	for d in episodeJSON['links']:
		hoster = d['hoster']
		hEntry = {"hoster":hoster,"id":str(d['id'])}
		if hoster.lower() in hosterList:
			hEntry['hoster'] = "-"+hEntry['hoster']
			allHoster.append(hEntry)
		else:
			allHoster.append(hEntry)
	sortedHoster = sorted(allHoster,key=lambda k: k['hoster'])
	
	print "[bs][straightPlay] sortedHoster: ",sortedHoster
	for sortedH in sortedHoster:	
		streamData = getUrl(urlHost+"watch/"+str(sortedH['id']))
		streamJSON = json.loads(streamData)
		fullurl = streamJSON['fullurl']
		print "[bs][straightPlay] fullurl: "+fullurl
		videoLink = urlresolver.resolve(fullurl)
		if videoLink:
			print "[bs][straightPlay] playing: "+videoLink
			li = xbmcgui.ListItem (series.encode('utf-8'), path=videoLink)
			xbmcplugin.setResolvedUrl(thisPlugin, True, li)
			break
		else:
			print "[bs][straightPlay] escaping: "+sortedH['hoster']+" - video url null"

# --------------------
# -- add to library -- hints from movieserver.addon - jin - thx
# --------------------
def add2Library(n,id):
	global thisPlugin
	print "[bs][add2Lib] creating Data for "+n
	newName = simplifyName(n)
	print type(newName),newName
	print serienOrdner
	folder = os.path.join(serienOrdner,newName)
	print "[bs][add2Lib] Folder "+folder
	season = 0
	while True:
		season += 1
		seasonData = getUrl(urlHost+"series/"+str(id)+"/"+str(season))
		seasonJSON = json.loads(seasonData)
		if 'error' in seasonJSON:
			break
		seasonName = "[B]Staffel"+str(season)+"[/B]"
		if seasonJSON.has_key('series'):
			episodeUrl = urlHost+"series/"+str(id)+"/"+str(season)
			episodeData = getUrl(episodeUrl)
			episodeJSON = json.loads(episodeData)
			for d in episodeJSON['epi']:
				episode = d['epi']
				newFile = newName+"_s"+str(season)+"e"+str(episode)+".strm"
				print "[bs][add2Lib] creating: "+newFile
				try:
					parameters = {"kindOf": "straightPlay", "id":id, "season":season, "episode":episode}
					pluginCall = sys.argv[0] + '?' + urllib.urlencode(parameters)
					strmFile = os.path.join(serienOrdner,newName,newFile)
					create_strm_file(strmFile,str(pluginCall))
				except Exception:
					continue
	print "[bs][add2Lib] ended"
	
def create_strm_file(strm,strmentry):
    if not xbmcvfs.exists(os.path.dirname(strm)):
        try: 
            xbmcvfs.mkdirs(os.path.dirname(strm))
        except:
            xbmc.executebuiltin('[bs][libEntry] Notification(Info: Konnte keinen Ordner erstellen!,)')
            return
    old_strmentry = ''
    try:
        f = xbmcvfs.File(strm, 'r')
        old_strmentry = f.read()
        f.close()
    except:
        pass
    if strmentry != old_strmentry:
        try:
            file_desc = xbmcvfs.File(strm, 'w')
            file_desc.write(strmentry)
            file_desc.close()
        except:
            xbmc.executebuiltin('[bs][libENtry] Notification(Info: Konnte keine Datei erstellen!,)')		

def simplifyName(s):
	# because mostly used by german rewrite umlaut
	s = s.replace("ä","ae")
	s = s.replace("ö","oe")
	s = s.replace("ü","ue")
	s = s.replace("ß","ss")
	s = s.replace(" ","_")
	astr = s.decode('utf-8').encode("ascii",'ignore')
	astr = astr.replace("/","_")
	astr = astr.replace("\\","_")
	astr = astr.replace(".","_")
	astr = astr.replace("*","_")
	astr = astr.replace("?","_")
	astr = astr.replace(":","_")
	return astr

# --------------
# --- helper ---
# --------------

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def baseN(num,b,numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
	return ((num == 0) and numerals[0]) or (baseN(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])

def getUrl(url):
	try:
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		req.add_header('Accept-encoding', 'gzip')
		response = urllib2.urlopen(req)
		if response.info().get('Content-Encoding') == 'gzip':
			d = zlib.decompressobj(16+zlib.MAX_WBITS)
			return d.decompress(response.read())
		else:
			return response.read()
		response.close()
	except:
		return False

def addDirectoryItem(name, parameters={},pic=""):
	iconpic = pic
	if pic == "":
		iconpic = "DefaultFolder.png"
	li = xbmcgui.ListItem(name,iconImage=iconpic, thumbnailImage=pic)
	u = sys.argv[0] + '?' + urllib.urlencode(parameters)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=li, isFolder=True)

def addPlayableItem(name, parameters={},pic=""):
	iconpic = pic
	if pic == "":
		iconpic = "DefaultFolder.png"
	li = xbmcgui.ListItem(name,iconImage=iconpic, thumbnailImage=pic)
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

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, unicode(text, "UTF-8"), re.UNICODE)
	

# ----------------
# ----- main -----
# ----------------

params = parameters_string_to_dict(sys.argv[2])

#showFavs = str(params.get("showFavs",""))
kindOf = str(params.get("kindOf",""))
sortType = str(params.get("sortType", ""))
name = str(params.get("name", ""))
id = str(params.get("id", ""))
season = str(params.get("season", ""))
episode = str(params.get("episode", ""))
episodename = str(params.get("episodename", ""))
vid = str(params.get("vid", ""))

print "[bs][init] show params"
print params

if not params.has_key('kindOf'):	# -- init start --
	kindOf = "0"
	sortType = "A"

if kindOf=="0":						# -- show Series --
	sortType = urllib.unquote(sortType)
	ok = showContent(sortType)
if kindOf=="1": 					# -- showSeasons --
	name = urllib.unquote(name)
	id = urllib.unquote(id)
	ok = showSeasons(name, id)
if kindOf=="2":						# -- showEpisodes --
	name = urllib.unquote(name)
	id = urllib.unquote(id)
	season = urllib.unquote(season)
	ok = showEpisodes(name, id, season)
if kindOf=="3":						# -- showHosts --
	name = urllib.unquote(name)
	id = urllib.unquote(id)
	season = urllib.unquote(season)
	episode = urllib.unquote(episode)
	episodename = urllib.unquote(episodename)
	ok = showHosts(name, id, season, episode, episodename)
if kindOf=="4":						# -- showVideo --
	vid = urllib.unquote(vid)
	name = urllib.unquote(name)
	season = urllib.unquote(season)
	episode = urllib.unquote(episode)
	ok = showVideo(vid,name,season,episode)
if kindOf == "add2lib":
	name = urllib.unquote(name)
	id = urllib.unquote(id)
	ok = add2Library(name, id)
	ok = dialog.notification("add 2 Library", name+" finished.", xbmcgui.NOTIFICATION_INFO,4000)
	ok = showSeasons(name,id)
if kindOf == "straightPlay":
	id = urllib.unquote(id)
	season = urllib.unquote(season)
	episode = urllib.unquote(episode)
	ok = straightPlay(id,season,episode)
