# -*- coding: utf-8 -*-
import urllib, urllib2, json
#import urlresolver
import os, re

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


urlMain = "http://www.filme-streamz.com"
print "requesting "+urlMain

# -- regexes --
rCategories = r'href="([^"]+)" class="rightsidemenu cat">([^<]+)<'
rMovies = r'"imgborder" style="">(.?)<a href="([^"]+)" title="([^"]+)">(.*?)<img src="([^"]+)"' # multiline dotall
rStreams = r'<a href="((http://)([^/]+)(/)([^"]+))" target="videoPlayer" class="sinactive server" style="text-align: center; width: 20%;">'

httpData = getUrlData(urlMain)
cats = re.findall(rCategories,httpData)
for c in cats:
	print c

print "-----------------"
urlCat = urlMain+cats[0][0]
print "requesting "+urlCat
httpData = getUrlData(urlCat)
rM = re.compile(rMovies, re.MULTILINE|re.DOTALL)
movs = rM.findall(httpData)
for m in movs:
	print m[1]+" / "+m[2].replace(" stream - film stream","")+" / "+m[4]

print "------------------"
urlMovie = urlMain+movs[0][1]
print "requesting "+urlMovie
httpData = getUrlData(urlMovie)
rS = re.compile(rStreams, re.DOTALL)
streams = rS.findall(httpData)
for s in streams:
	streamer = s[2].split(".")
	streamName = streamer[len(streamer)-2]
	print streamName+" - "+s[0]

raw_input("Press Enter to continue...")