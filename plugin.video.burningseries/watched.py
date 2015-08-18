# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs

addonInfo = xbmcaddon.Addon()
watchedFile = addonInfo.getAddonInfo('path')+"/watched.data"

# since 1.3.0
def writeWatchedData(n):
	global watchedFile
	name = n.decode('utf-8')
	f = xbmcvfs.File(watchedFile)
	d = f.read()
	f.close()
	f = xbmcvfs.File(watchedFile, 'w')
	b = d+name.encode('utf-8')+"\n"
	result = f.write(b)
	print "[bs][writeWatchedData] write "+watchedFile+" -> "+ name.encode('utf-8')
	f.close()
	return result
	
def readWatchedData(n):
	global watchedFile
	name = n.decode('utf-8')
	f = xbmcvfs.File(watchedFile)
	b = f.read()
	f.close()
	watchedData = b.splitlines()
	for m in watchedData:
		if name == m:
			print "[bs][readWatchedData] found "+name.encode('utf-8')+" in watched.data"
			return True
	print "[bs][readWatchedData] "+name.encode('utf-8')+" not found in watched.data"
	return False

def changeToWatched(watchedString):
	# -- rewrite listentry
	return "[I]"+watchedString.encode('utf-8')+"[/I] (watched)"

def markParentEntry(urlData):
	if not readWatchedData(urlData):
		writeWatchedData(urlData)
