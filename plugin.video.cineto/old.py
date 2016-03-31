# -*- coding: utf-8 -*-
import urllib, urllib2, json
#import urlresolver
import os, re


#SEP = os.sep
#thisPlugin = int(sys.argv[1])
#dialog = xbmcgui.Dialog()
#addonInfo = xbmcaddon.Addon()
#hosterList = xbmcplugin.getSetting(thisPlugin,"hosterlist").lower()
#serienOrdner = xbmcplugin.getSetting(thisPlugin, 'seriespath')
#thumbUrl = addonInfo.getAddonInfo('path')+SEP+"resources"+SEP+"img"+SEP
#dataUrl = xbmc.translatePath(addonInfo.getAddonInfo('profile'))

def getJSON(url, postData):
	try:
		req = urllib2.Request(url,postData)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		dr = response.read()
		print "-response-"
		print dr
		print response.geturl()
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

siteUrl = "https://cine.to"
print "requesting "+siteUrl

search = {'kind':'all',
			'genre':'0',
			'rating':'5',
			'year[]':['2000','2015'],
			'term':'',
			'page':'1',
			'count':'50'
			}
			
# kind all, cinema, retail
# genreList = { 'All','Action','Adventure','Animation','Biography','Comedy','Crime','Documentary','Drama','Family','Fantasy','FilmNoirt','History','Horror','Music','Musical','Mystery','Romance','SciFi','Sport','Thriller','War','Western'}
siteUrl = "https://cine.to/request/search"
pd = "kind=all&genre=0&rating=5&year%5B%5D=2010&year%5B%5D=2016&term=&page=3&count=24"
do = getJSON(siteUrl,pd)
#print do
n = 0
jsonContent = json.loads(do)
for entry in jsonContent['entries']:
	print str(n)+" - "+entry['title'] +" "+ entry['quality']
	n = n+1
	checked = entry
print "--"
movieUrl = "http://cine.to/request/entry"
pd = "ID="+checked['imdb']
dm = getJSON(movieUrl,pd);
movieData = json.loads(dm)
print movieData
print "--"

movieUrl = "http://cine.to/request/links"
pd = "ID="+checked['imdb']+"&lang=en"
dm = getJSON(movieUrl,pd);
linkData = json.loads(dm)
print linkData
print "--"

for streamName, data in linkData['links'].iteritems():
	print "stream: '"+streamName+"'"
	print data
	if streamName=="vivo":
		streamID = data[1]
		print "found"
		streamUrl = "http://cine.to/out/"+str(streamID)
		finalstreamUrl = getStreamUrl(streamUrl);
		print finalstreamUrl

raw_input("Press Enter to continue...")