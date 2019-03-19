# -*- coding: utf-8 -*-
################################################################################
#				zdfmobile.py - Part of Plex-Plugin-ARDMediathek2016
#							mobile Version der ZDF Mediathek
################################################################################
# 	dieses Modul nutzt nicht die Webseiten der Mediathek ab https://www.zdf.de/,
#	sondern die Seiten ab https://zdf-cdn.live.cellular.de/mediathekV2 - diese
#	Seiten werden im json-Format ausgeliefert

import  json		
import os, sys
import urllib, urllib2
import ssl
import ctypes
import datetime, time
import re				# u.a. Reguläre Ausdrücke

import xbmc, xbmcgui, xbmcaddon, xbmcplugin

import resources.lib.util as util
PLog=util.PLog;  home=util.home;  Dict=util.Dict;  name=util.name; 
UtfToStr=util.UtfToStr;   get_page=util.get_page;					# addDir=util.addDir; 
img_urlScheme=util.img_urlScheme;  R=util.R;  RLoad=util.RLoad;  RSave=util.RSave; 
GetAttribute=util.GetAttribute; CalculateDuration=util.CalculateDuration;  
teilstring=util.teilstring; repl_dop=util.repl_dop;  repl_char=util.repl_char;  mystrip=util.mystrip; 
DirectoryNavigator=util.DirectoryNavigator; stringextract=util.stringextract;  blockextract=util.blockextract; 
teilstring=util.teilstring;  repl_dop=util.repl_dop; cleanhtml=util.cleanhtml;  decode_url=util.decode_url;  
unescape=util.unescape;  mystrip=util.mystrip; make_filenames=util.make_filenames;  transl_umlaute=util.transl_umlaute;  
humanbytes=util.humanbytes;  time_translate=util.time_translate; get_keyboard_input=util.get_keyboard_input; 
transl_wtag=util.transl_wtag;

# Globals
KODI_VERSION = xbmc.getInfoLabel('System.BuildVersion')
ADDON_ID      	= 'plugin.video.ardundzdf'
SETTINGS 		= xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    	= SETTINGS.getAddonInfo('name')
SETTINGS_LOC  	= SETTINGS.getAddonInfo('profile')
ADDON_PATH    	= SETTINGS.getAddonInfo('path').decode('utf-8')	# Basis-Pfad Addon
ADDON_VERSION 	= SETTINGS.getAddonInfo('version')
PLUGIN_URL 		= sys.argv[0]				# plugin://plugin.video.ardundzdf/
HANDLE			= int(sys.argv[1])

DEBUG			= SETTINGS.getSetting('pref_info_debug')

FANART = xbmc.translatePath('special://home/addons/' + ADDON_ID + '/fanart.jpg')
ICON = xbmc.translatePath('special://home/addons/' + ADDON_ID + '/icon.png')
DICTSTORE 		= os.path.join("%s/resources/data/Dict") % ADDON_PATH

ICON 					= 'icon.png'		# ARD + ZDF
ICON_MAIN_ZDFMOBILE		= 'zdf-mobile.png'			
ICON_DIR_FOLDER			= "Dir-folder.png"
ICON_SPEAKER 			= "icon-speaker.png"
imgWidth		= 840			# max. Breite Teaserbild
imgWidthLive	= 1280			# breiter für Videoobjekt
NAME			= 'ARD und ZDF'
ZDFNAME			= "ZDFmobile"

def Main_ZDFmobile():
	PLog('zdfmobile_Main_ZDF:')
	
	li = xbmcgui.ListItem()
	li = home(li, ID='ARD und ZDF')		# Home-Button
	
	# Suche bleibt abgeschaltet - bisher keine Suchfunktion bei zdf-cdn.live.cellular.de gefunden.
	# Web-Player: folgendes DirectoryObject ist Deko für das nicht sichtbare InputDirectoryObject dahinter:
	#fparams="&fparams={'name': '%s'}" % name
	#addDir(li=li, label='Suche: im Suchfeld eingeben', action="dirList", dirID="Main_ZDFmobile", 
	#	fanart=R(ICON_SEARCH), thumb=R(ICON_SEARCH), fparams=fparams)
		
	title = 'Startseite'
	fparams="&fparams={'ID': '%s'}" % title
	addDir(li=li, label=title, action="dirList", dirID="resources.lib.zdfmobile.Hub", fanart=R(ICON_MAIN_ZDFMOBILE), 
		thumb=R(ICON_DIR_FOLDER), fparams=fparams)

	fparams="&fparams={'ID': 'Kategorien'}"
	addDir(li=li, label="Kategorien", action="dirList", dirID="resources.lib.zdfmobile.Hub", fanart=R(ICON_MAIN_ZDFMOBILE), 
		thumb=R(ICON_DIR_FOLDER), fparams=fparams)

	fparams="&fparams={'ID': 'Sendungen A-Z'}"
	addDir(li=li, label="Sendungen A-Z", action="dirList", dirID="resources.lib.zdfmobile.Hub", fanart=R(ICON_MAIN_ZDFMOBILE), 
		thumb=R(ICON_DIR_FOLDER), fparams=fparams)

	fparams="&fparams={'ID': 'Sendung verpasst'}"
	addDir(li=li, label="Sendung verpasst", action="dirList", dirID="resources.lib.zdfmobile.Hub", fanart=R(ICON_MAIN_ZDFMOBILE), 
		thumb=R(ICON_DIR_FOLDER), fparams=fparams)

	fparams="&fparams={'ID': 'Live TV'}"
	addDir(li=li, label='Live TV', action="dirList", dirID="resources.lib.zdfmobile.Hub", fanart=R(ICON_MAIN_ZDFMOBILE), 
	thumb=R(ICON_DIR_FOLDER), fparams=fparams, summary='nur in Deutschland zu empfangen!')

	xbmcplugin.endOfDirectory(HANDLE)
		
# ----------------------------------------------------------------------			
# ID = Dict-Parameter und title2 für ObjectContainer 
def Hub(ID):
	PLog('Hub, ID: %s' % ID)
	li = xbmcgui.ListItem()
	li = home(li, ID=ZDFNAME)				# Home-Button
	
	if ID=='Startseite':
		# lokale Testdatei:
		# path = '/daten/entwicklung/Plex/Codestuecke/ZDF_JSON/ZDF_start-page.json'
		# page = Resource.Load(path)
		path = 'https://zdf-cdn.live.cellular.de/mediathekV2/start-page'
	
	if ID=='Kategorien':
		path = 'https://zdf-cdn.live.cellular.de/mediathekV2/categories'
		
	if ID=='Sendungen A-Z':
		path = 'https://zdf-cdn.live.cellular.de/mediathekV2/brands-alphabetical'
		
	if ID=='Sendung verpasst':
		li = Verpasst(DictID='Verpasst')	
		return li		# raus - jsonObject wird in Verpasst_load geladen	

	if ID=='Live TV':
		now 	= datetime.datetime.now()
		datum 	= now.strftime("%Y-%m-%d")	
		path = 'https://zdf-cdn.live.cellular.de/mediathekV2/live-tv/%s' % datum	

	page = loadPage(path)		
	PLog(len(page))
	if page.startswith('Fehler') or page == '':
		xbmcgui.Dialog().ok(ADDON_NAME, 'Fehler beim Abruf von:', path, '')
		xbmcplugin.endOfDirectory(HANDLE)
		
	jsonObject = json.loads(page)		
	if ID=='Startseite':
		v = 'Startpage' 		# speichern
		vars()[v] = jsonObject
		Dict('store', v, vars()[v])
		li = videoObjects=PageMenu(li,jsonObject,DictID='Startpage')		
	if ID=='Kategorien':
		v = 'Kategorien'
		vars()['Kategorien'] = jsonObject
		Dict("store", v, vars()[v])
		li = videoObjects=PageMenu(li,jsonObject,DictID='Kategorien')		
	if ID=='Sendungen A-Z':
		v = 'A_Z'
		vars()['A_Z'] = jsonObject
		Dict("store", v, vars()[v])
		li = videoObjects=PageMenu(li,jsonObject,DictID='A_Z')		
	if ID=='Live TV':
		v = 'Live'
		vars()['Live'] = jsonObject
		Dict("store", v, vars()[v])
		li = videoObjects=PageMenu(li,jsonObject,DictID='Live')	

	return li

# ----------------------------------------------------------------------
def Verpasst(DictID):					# Wochenliste
	PLog('Verpasst')
	
	li = xbmcgui.ListItem()
	# li = home(li, ID=ZDFNAME)				# Home-Button - s. Hub
		
	wlist = range(0,7)
	now = datetime.datetime.now()

	for nr in wlist:
		rdate = now - datetime.timedelta(days = nr)
		iDate = rdate.strftime("%Y-%m-%d")		# ZDF-Format 	
		display_date = rdate.strftime("%d-%m-%Y") 	# Formate s. man strftime(3)
		iWeekday =  rdate.strftime("%A")
		if nr == 0:
			iWeekday = 'Heute'	
		if nr == 1:
			iWeekday = 'Gestern'	
		iWeekday = transl_wtag(iWeekday)		# -> ARD Mediathek
		path = 'https://zdf-cdn.live.cellular.de/mediathekV2/broadcast-missed/%s' % iDate
		title =	"%s | %s" % (display_date, iWeekday)
		PLog(title); PLog(path);
		fparams="&fparams={'path': '%s', 'datum': '%s'}" % (path, display_date)
		addDir(li=li, label=title, action="dirList", dirID="resources.lib.zdfmobile.Verpasst_load", fanart=R(ICON_MAIN_ZDFMOBILE), 
			thumb=R(ICON_DIR_FOLDER), fparams=fparams)
	xbmcplugin.endOfDirectory(HANDLE)
# ----------------------------------------------------------------------
# lädt json-Datei für gewählten Wochtentag:
def Verpasst_load(path, datum):		# 5 Tages-Abschnitte in 1 Datei, path -> DictID 
	PLog('Verpasst_load:' + path)
	li = xbmcgui.ListItem()
	
	page = loadPage(path)		
	if page.startswith('Fehler') or page == '':
		xbmcgui.Dialog().ok(ADDON_NAME, 'Fehler beim Abruf von:', path, '')
		xbmcplugin.endOfDirectory(HANDLE)
	PLog(len(page))
	
	jsonObject = json.loads(page)
	path = path.split('/')[-1]			# Pfadende -> Dict-ID
	v = path
	vars()[path] = jsonObject
	Dict("store", v, vars()[v])
	li = PageMenu(li,jsonObject,DictID=path)
	xbmcplugin.endOfDirectory(HANDLE)
				
# ----------------------------------------------------------------------
# Bisher nicht genutzt
def ZDFmSearch(query, title='Suche', offset=0):
	PLog('ZDFmSearch')
	PLog('query: %s' % query)
	li = xbmcgui.ListItem()	
	return oc		
# ----------------------------------------------------------------------			
def PageMenu(li,jsonObject,DictID):										# Start- + Folgeseiten
	PLog('PageMenu, DictID: ' + DictID)
		
	mediatype=''													# Kennz. Videos im Listing
	if SETTINGS.getSetting('pref_video_direct') == 'true':
		if SETTINGS.getSetting('pref_show_resolution') == 'false':
			mediatype='video'
	PLog('mediatype: ' + mediatype); 
			
	if("stage" in jsonObject):
		i=0
		for stageObject in jsonObject["stage"]:
			if(stageObject["type"]=="video"):							# Videos am Seitenkopf
				title,subTitle,descr,img,date,dauer = Get_content(stageObject,imgWidth) 

				if subTitle:
					title = '%s | %s' % (title,subTitle)

				if date:
					title = '%s | %s' % (title,date)

				if dauer:
					title = '%s |  %s' % (title, dauer)

				date = '%s |  Laenge: %s' % (date, dauer)
				path = 'stage|%d' % i
				PLog(path)
				fparams="&fparams={'path': '%s', 'DictID': '%s'}" % (path, DictID)	
				addDir(li=li, label=title, action="dirList", dirID="resources.lib.zdfmobile.ShowVideo", fanart=img, thumb=img, 
					fparams=fparams, summary=descr, tagline=date, mediatype=mediatype)
						
			i=i+1							
	if("cluster" in jsonObject):
		for counter, clusterObject in enumerate(jsonObject["cluster"]):	# Bsp. "name":"Neu in der Mediathek"
			if "teaser" in clusterObject and "name" in clusterObject:
				path = "cluster|%d|teaser" % counter
				title = clusterObject["name"]
				if title == '':
					title = 'ohne Titel'
				title = title.encode("utf-8")
				path = path.encode("utf-8")
				PLog('Mark1')
				fparams="&fparams={'path': '%s', 'title': '%s', 'DictID': '%s'}"  % (path, title, DictID)
				PLog(title); PLog(path);  PLog(fparams); 
				addDir(li=li, label=title, action="dirList", dirID="resources.lib.zdfmobile.SingleRubrik", 				
					fanart=R(ICON_MAIN_ZDFMOBILE), thumb=R(ICON_DIR_FOLDER), fparams=fparams)
								
	if("broadcastCluster" in jsonObject):								# 
		for counter, clusterObject in enumerate(jsonObject["broadcastCluster"]):
			if clusterObject["type"].startswith("teaser") and "name" in clusterObject:
				path = "broadcastCluster|%d|teaser" % counter
				title = clusterObject["name"]
				title = title.encode("utf-8")
				path = path.encode("utf-8")
				fparams="&fparams={'path': '%s', 'title': '%s', 'DictID': '%s'}" % (path, title, DictID)
				addDir(li=li, label=title, action="dirList", dirID="resources.lib.zdfmobile.SingleRubrik", 
				fanart=R(ICON_MAIN_ZDFMOBILE), thumb=R(ICON_DIR_FOLDER), fparams=fparams)
								
	if("epgCluster" in jsonObject):
		for counter, epgObject in enumerate(jsonObject["epgCluster"]):	# Livestreams
			if("liveStream" in epgObject and len(epgObject["liveStream"]) >= 0):
				path = "epgCluster|%d|liveStream" % counter
				title = epgObject["name"] + ' Live'
				title = title.encode("utf-8")
				path = path.encode("utf-8")
				fparams="&fparams={'path': '%s', 'DictID': '%s'}" % (urllib2.quote(path), DictID)	
				addDir(li=li, label=title, action="dirList", dirID="resources.lib.zdfmobile.ShowVideo", 
					fanart=R(ICON_MAIN_ZDFMOBILE), thumb=R(ICON_DIR_FOLDER), fparams=fparams, mediatype=mediatype)
					
	xbmcplugin.endOfDirectory(HANDLE)				
				
# ----------------------------------------------------------------------	
def Get_content(stageObject, maxWidth):
	PLog('Get_content:')
	# PLog(str(stageObject))
	
	title=stageObject["headline"]
	subTitle=stageObject["titel"]

	if(len(title)==0):
		title = subTitle
		subTitle = ""
	descr=''	
	if("beschreibung" in stageObject):
		descr = stageObject["beschreibung"]

	dauer=''
	if("length" in stageObject):
		sec = stageObject["length"]
		if sec:
			dauer = time.strftime('%H:%M:%S', time.gmtime(sec))	
		
	img="";
	if("teaserBild" in stageObject):
		for width,imageObject in stageObject["teaserBild"].iteritems():
			if int(width) <= maxWidth:
				img=imageObject["url"];

	if("visibleFrom" in stageObject):
		date = stageObject["visibleFrom"]
	else:
		date = stageObject["date"]
		#now = datetime.datetime.now()
		#date = now.strftime("%d.%m.%Y %H:%M")
		
	descr=descr.replace('"', '') 		# json-komp. für func_pars in router()
	descr=descr.replace('&', 'und') 	# json-komp. für func_pars in router()
	title=title.replace('"', '') 		# json-komp. für func_pars in router()
	title=title.replace('&', 'und') 	# json-komp. für func_pars in router()
	
	title=UtfToStr(title); subTitle=UtfToStr(subTitle); descr=UtfToStr(descr); 
	img=UtfToStr(img);	date=UtfToStr(date); dauer=UtfToStr(dauer);
	PLog('Get_content: %s |%s | %s | %s | %s | %s' % (title,subTitle,descr,img,date,dauer) )		
	return title,subTitle,descr,img,date,dauer
# ----------------------------------------------------------------------			
# einzelne Rubrik mit Videobeiträgen, alles andere wird ausgefiltert	
def SingleRubrik(path, title, DictID):		
	PLog('SingleRubrik: %s' % path)
	
	path_org = path
	
	jsonObject = Dict("load", DictID)
	jsonObject = GetJsonByPath(path, jsonObject)
	PLog('jsonObjects: ' + str(len(jsonObject)))	
	li = xbmcgui.ListItem()
	li = home(li, ID=ZDFNAME)				# Home-Button

	i=0
	for entry in jsonObject:
		path = path_org + '|%d' % i
		date=''; title=''; descr=''; img=''
		PLog('entry-type: %s' % entry["type"])
		# PLog(entry)
		mediatype=''
		if entry["type"] == 'video':		# Kennz. Video nur bei Sofortstart in ShowVideo
			if SETTINGS.getSetting('pref_video_direct') == 'true':
				if SETTINGS.getSetting('pref_show_resolution') == 'false':
					mediatype='video'
		
		# alle anderen entry-types werden übersprungen, da sie keine 
		# verwendbaren Videos enthalten - Bsp.:
		#	category, brandsAlphabetical, externalUrl, broadcastMissed
		# Bei "brand" nehmen wir in Kauf, dass Infoseiten leere Videos
		#	zurückliefern - Bsp. Heute-Journal
					
		if entry["type"] == "video" or entry["type"] == "brand":
			title,subTitle,descr,img,date,dauer = Get_content(entry,imgWidth)
			if subTitle: 
				# title = '%s | %s' % (title,subTitle)
				title = '%s | %s' % (subTitle, title ) 	# subTitle = Sendungstitel
			if date:
				title = '%s | %s' % (title,date)
			if dauer:
				title = '%s |  %s' % (title, dauer)
				date = '%s |  Laenge: %s' % (date, dauer)
			# PLog('video-content: %s |  %s |  %s |  %s | ' % (title,subTitle,descr,img))	
			fparams="&fparams={'path': '%s', 'DictID': '%s'}" % (path, DictID)
			PLog("fparams: " + fparams)	
			addDir(li=li, label=title, action="dirList", dirID="resources.lib.zdfmobile.ShowVideo", fanart=img, 
				thumb=img, fparams=fparams, summary=descr, tagline=date, mediatype=mediatype)
		i=i+1
		# break		# Test Einzelsatz
	xbmcplugin.endOfDirectory(HANDLE)

# ----------------------------------------------------------------------
# iteriert durch das Objekt	und liefert Restobjekt ab path
def GetJsonByPath(path, jsonObject):		
	PLog('GetJsonByPath: '+ path)
	path = path.split('|')
	i = 0
	while(i < len(path)):
		if(isinstance(jsonObject,list)):
			index = int(path.pop(0))
		else:
			index = path.pop(0)
		PLog('i=%s, index=%s' % (i,index))
		jsonObject = jsonObject[index]	
	# PLog(jsonObject)
	return jsonObject	
# ----------------------------------------------------------------------			
def ShowVideo(path, DictID):
	PLog('ShowVideo:'); PLog(path); PLog(DictID)
	
	jsonObject = Dict("load", DictID)
	videoObject = GetJsonByPath(path,jsonObject)
	title,subTitle,descr,img,date,dauer = Get_content(videoObject,imgWidthLive)
	title = UtfToStr(title); subTitle = UtfToStr(subTitle); descr = UtfToStr(descr);

	if subTitle:
		title = '%s | %s' % (title,subTitle)
	if date:
		if DictID <> 'Live':				# kein Datum bei Livestreams 
			title = '%s | %s' % (title,date)
	if dauer:
		title = '%s |  %s' % (title, dauer)
	title_org = UtfToStr(title)	
	PLog(title_org)	
		
	li = xbmcgui.ListItem()
	li = home(li, ID=ZDFNAME)				# Home-Button
		
	if("formitaeten" in videoObject):
		PLog('formitaeten in videoObject')				# OK - hat Videoquellen
		formitaeten = get_formitaeten(videoObject)	
		PLog(len(formitaeten))					
	else:
		PLog('formitaeten fehlen, lade videoObject-url')
		formitaeten=[]; detail=[]
		url = videoObject["url"]
		# url=url.replace('https', 'http')
		page = loadPage(url)
		PLog(len(page))		
		jsonObject = json.loads(page)

		if "formitaeten" in jsonObject["document"]:
			PLog('formitaeten nachgeladen')					# Videoquellen nachgeladen
			# PLog(jsonObject["document"]["formitaeten"])
			formitaeten = get_formitaeten(jsonObject["document"])
		else:
			url = url.encode("utf-8")
			PLog('url: ' + url)							# Bsp. ../document/ambra-parfum-100
			DictID = url.split('/')[-1]					# letztes Pfadelement -> DictID
			PLog('DictID: ' + DictID)	
			vars()[DictID] = jsonObject					# speichern
			Dict("store", DictID, vars()[DictID])
			li = videoObjects=PageMenu(li,jsonObject,DictID=DictID)	# Rubrik o.ä.	
			return li

	i=0
	for detail in formitaeten:	
		PLog("Mark4")
		i = i + 1
		quality = detail[0]				# Bsp. auto [m3u8]
		# hd = 'HD: ' + str(detail[1])	# falsch bei mp4-Dateien (False trotz high)
		url = detail[2]
		url = url.replace('https', 'http')
		typ = detail[3]
		if url.endswith('mp4'):
			try:
				bandbreite = url.split('_')[-2]		# Bsp. ../4/170703_despot1_inf_1496k_p13v13.mp4
			except:
				bandbreite = ''
				
		title_org=UtfToStr(title_org);
		title_org=unescape(title_org); 	
		title_org=title_org.replace('"', '') 		# json-komp. für func_pars in router()
		title_org=title_org.replace('&', 'und') 	# json-komp. für func_pars in router()
		descr=descr.replace('"', '') 				# dto.
					
		PLog("url: " + url)	
	
		if url.find('master.m3u8') > 0:		# 
			if 'auto' in quality:			# speichern für ShowSingleBandwidth
				if SETTINGS.getSetting('pref_video_direct') == 'true':	     # Sofortstart
					if SETTINGS.getSetting('pref_show_resolution') == 'false':
						PLog('Sofortstart: ZDF Mobile (ShowVideo)')
						PlayVideo(url=url, title=title_org, thumb=img, Plot=descr, direkt=True)
						return
				url_auto = url
			title=str(i) + '. ' + quality + ' [m3u8]'
			PLog("title: " + title)
			tagline = 'Qualitaet: ' + quality + ' | Typ: ' + typ + ' [m3u8-Streaming]'
			tagline = UtfToStr(tagline);
			fparams="&fparams={'url': '%s', 'title': '%s', 'thumb': '%s', 'Plot': '%s'}" % (urllib2.quote(url), 
				urllib2.quote(title_org), urllib.quote_plus(img), urllib.quote_plus(descr))	
			addDir(li=li, label=title, action="dirList", dirID="resources.lib.zdfmobile.PlayVideo", fanart=img, 
				thumb=img, fparams=fparams, summary=descr, tagline=tagline, mediatype='video')	
		else:
			title=str(i) + '. %s [%s]'  % (quality, typ)
			PLog("title: " + title)
			tagline = 'Qualitaet: ' + quality + ' | Typ: ' + typ
			if bandbreite:
				tagline = '%s | %s'	% (tagline, bandbreite)		
			tagline = UtfToStr(tagline);
			fparams="&fparams={'url': '%s', 'title': '%s', 'thumb': '%s', 'Plot': '%s'}" % (urllib2.quote(url), 
				urllib2.quote(title_org), urllib.quote_plus(img), urllib.quote_plus(descr))	
			addDir(li=li, label=title, action="dirList", dirID="resources.lib.zdfmobile.PlayVideo", fanart=img, 
				thumb=img, fparams=fparams, summary=descr, tagline=tagline, mediatype='video')	
	
	'''
	# einzelne Auflösungen anbieten:	# bei zdfMobile überflüssig - Varianten von low - veryhigh vorh.
	title = 'einzelne Bandbreiten/Aufloesungen zu auto [m3u8]'
	fparams="&fparams={'title': '%s', 'url_m3u8': '%s', 'thumb': '%s', 'descr': '%s'}" % (urllib2.quote(title_org), 
		urllib2.quote(url_auto), urllib2.quote(img), urllib.quote_plus(descr))
	addDir(li=li, label=title, action="dirList", dirID="resources.lib.zdfmobile.ShowSingleBandwidth", fanart=img, 
		thumb=img, fparams=fparams, summary=descr, mediatype='')
	'''
	xbmcplugin.endOfDirectory(HANDLE)
				
# ----------------------------------------------------------------------
def get_formitaeten(jsonObject):
	PLog('get_formitaeten')
	forms=[]
	for formitaet in jsonObject["formitaeten"]:
		detail=[]
		url = formitaet["url"];
		quality = formitaet["quality"]
		hd = formitaet["hd"]
		typ = formitaet["type"]
		PLog("quality:%s hd:%s url:%s" % (quality,hd,url))
		detail.append(quality); detail.append(hd); 
		detail.append(url); detail.append(typ)
		forms.append(detail)
	# PLog('forms: ' + str(forms))
	return forms		

# ----------------------------------------------------------------------
def ShowSingleBandwidth(title,url_m3u8,thumb, descr):	# .m3u8 -> einzelne Auflösungen
	PLog('ShowSingleBandwidth:')
	
	playlist = loadPage(url_m3u8)
	if playlist.startswith('Fehler'):
		xbmcgui.Dialog().ok(ADDON_NAME, playlist, url_m3u8, '')
		
	li = xbmcgui.ListItem()
	li =  Parseplaylist(li, playlist=playlist, title=title, thumb=thumb, descr=descr)		
	
	xbmcplugin.endOfDirectory(HANDLE)

####################################################################################################
#									Hilfsfunktionen
####################################################################################################
def Parseplaylist(li, playlist, title, thumb, descr):	# playlist (m3u8, ZDF-Format) -> einzelne Auflösungen
	PLog ('Parseplaylist:')
	PLog(title)
	title = UtfToStr(title)
	title_org = title
  
	lines = playlist.splitlines()
	# PLog(lines)
	lines.pop(0)		# 1. Zeile entfernen (#EXTM3U)
	
	line_inf=[]; line_url=[]
	for i in xrange(0, len(lines),2):
		line_inf.append(lines[i])
		line_url.append(lines[i+1])
	# PLog(line_inf); PLog(line_url); 	
	
	i=0; Bandwith_old = ''
	for inf in line_inf:
		PLog(inf)
		url = line_url[i]
		i=i+1		
		Bandwith=''; Resolution=''; Codecs=''; 
		Bandwith = re.search('BANDWIDTH=(\d+)', inf).group(1)
		if 'RESOLUTION=' in inf:		# fehlt ev.
			Resolution = re.search('RESOLUTION=(\S+),CODECS', inf).group(1)
		Codecs = re.search(r'"(.*)"', inf).group(1)	# Zeichen zw. Hochkommata
		
		summ= 'Bandbreite: %s' % Bandwith 
		if Resolution:
			summ= 'Bandbreite %s | Auflösung: %s' % (Bandwith, Resolution)
		if Codecs:
			summ= '%s | Codecs: %s' % (descr, Codecs)
		summ = summ.replace('"', '')	# Bereinigung Codecs
			
		PLog(Bandwith); PLog(Resolution); PLog(Codecs); 
		tagline='m3u8-Streaming'
		title = '%s. %s' 	% (str(i), title_org)
		if 	Bandwith_old == Bandwith:
			title = '%s. %s | 2. Alternative' 	% (str(i), title_org)
		Bandwith_old = Bandwith
		if int(Bandwith) <=  100000: 		# Audio - PMS-Transcoder: Stream map '0:V:0' matches no streams 
			tagline = '%s | nur Audio'	% tagline
			thumb=R(ICON_SPEAKER)
		
		descr = UtfToStr(descr)		
		fparams="&fparams={'url': '%s', 'title': '%s', 'thumb': '%s', 'Plot': '%s'}" % (urllib.quote_plus(url), 
			urllib.quote_plus(title_org), urllib.quote_plus(thumb), urllib.quote_plus(descr))			
		addDir(li=li, label=title, action="dirList", dirID="resources.lib.zdfmobile.PlayVideo", fanart=thumb, 
			thumb=thumb, fparams=fparams, summary=summ, tagline=tagline, mediatype='video')	

	return li
	
	
#----------------------------------------------------------------  			
def loadPage(url, maxTimeout = None):
	try:
		safe_url = url.replace( " ", "%20" ).replace("&amp;","&")
		PLog("loadPage: " + safe_url)

		req = urllib2.Request(safe_url)
		gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 5.1; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11')
		req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
		req.add_header('Accept-Language', 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3')
		req.add_header('Accept-Charset', 'utf-8')

		if maxTimeout == None:
			maxTimeout = 60;
		r = urllib2.urlopen(req, timeout=maxTimeout, context=gcontext)
		doc = r.read()	
		doc = doc.encode('utf-8')
		return doc
		
	except Exception as exception:
		msg = 'Fehler: ' + str(exception)
		msg = msg + '\r\n' + safe_url			 			 	 
		msg =  msg
		PLog(msg)
		return msg
#----------------------------------------------------------------  
# Kopie von ardundzdf.py - für Sofortstart erforderlich (Showvideo))
# Details s. PlayVideo im Hauptprg 
# sub_path hier nicht unterstützt
def PlayVideo(url, title, thumb, Plot, direkt=False):	
	PLog('zdfMobile_PlayVideo:'); PLog(url); PLog(title); PLog(Plot); PLog(direkt);
	# Plot=transl_doubleUTF8(Plot)				# hier n.b.
		
	# # SSL-Problem bei Kodi V17.6:  ERROR: CCurlFile::Stat - Failed: SSL connect error(35)
	url = url.replace('https', 'http')  
	
	li = xbmcgui.ListItem(path=url)		
	li.setArt({'thumb': thumb, 'icon': thumb})
	ilabels = ({'Title': title})
	
	Plot=Plot.replace('||', '\n')				# || Code für LF (\n scheitert in router)
	ilabels.update({'Plot': '%s' % Plot})
	li.setInfo(type="video", infoLabels=ilabels)
	# li.setContentLookup(False)				# Kodi V17: ückfall in Listing kurz nach Videostart
	
		
	# xbmc.Player().play(url, li, False)					# direkter Aufruf verhindert Resume-Funktion
	# Kodi V17 startet PlayMedia kurz und öffnet wieder akt. Listing
	# Kodi V17: setResolvedUrl verwenden, für V18 PlayMedia + return OK:
	kodi_version = re.search('(\d+)', KODI_VERSION).group(0) # Major-Version reicht hier	
	if int(kodi_version) >= 18: 
		xbmc.executebuiltin('PlayMedia(%s)' % url)
		return
	else:
		# Kodi V17: xbmc.executebuiltin bietet zwar Kontextmenü, springt aber bei "fortsetzen" ins Listing -
		#	dies wird durch endOfDirectory unterdrückt, das Video kann starten
		#	Kontextmenü-Probleme:
		#		Nach Videoende wird das Kontextmenü (fortsetzen/(Anfang) erneut gezeigt, lässt sich aber 
		#		wegklicken (Aufruf Merkliste)
		#		Aufruf Listing: Kontextmenü kann nacheinander zwei Startzeiten anzeigen, wenn das Video 
		#			aus der Merkliste aufgerufen wurde.
		#	gelegentliche Abstürze bei den Tests.
		xbmc.executebuiltin('PlayMedia(%s)' % url)	# Merkliste OK, aber script Listing nach kurz. Videostart
		# xbmc.Player().play(url, li, False)		# verhindert Resume-Funktion
		# return
		xbmcplugin.setResolvedUrl(HANDLE, True, li)		# indirekt
		xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False) # verhindert Rücksprung ins Listing beim Videostart

#----------------------------------------------------------------  
# addDir hier zeitweise zusätzl. wg. Test Resumefunktion 
def addDir(li, label, action, dirID, fanart, thumb, fparams, summary='', tagline='', mediatype='', cmenu=True):
	PLog('addDir:')
	PLog('addDir - label: %s, action: %s, dirID: %s' % (label, action, dirID))
	PLog('addDir - summary: %s, tagline: %s, mediatype: %s, cmenu: %s' % (summary, tagline, mediatype, cmenu))
	
	label=UtfToStr(label); thumb=UtfToStr(thumb); fanart=UtfToStr(fanart); 
	summary=UtfToStr(summary); tagline=UtfToStr(tagline); 
	fparams=UtfToStr(fparams);

	li.setLabel(label)			# Kodi Benutzeroberfläche: Arial-basiert für arabic-Font erf.
	if mediatype == 'video': 	# s.o.
		li.setInfo('video', {'title': label, 'mediatype': 'video'})
		isFolder = False		# nicht bei direktem Player-Aufruf - OK mit setResolvedUrl
		li.setProperty('IsPlayable', 'true')					
	else:
		li.setProperty('IsPlayable', 'false')
		isFolder = True	
	
	li.setArt({'thumb':thumb, 'icon':thumb, 'fanart':fanart})
	xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
	PLog('PLUGIN_URL: ' + PLUGIN_URL)
	PLog('HANDLE: ' + str(HANDLE))
	url = PLUGIN_URL+"?action="+action+"&dirID="+dirID+"&fanart="+fanart+"&thumb="+thumb+urllib.quote_plus(fparams)
	PLog("addDir_url: " + urllib.unquote_plus(url))
		
	# PLog('summary, tagline: %s, %s' % (summary, tagline))
	ilabels = {'Plot': ''}								# ilabels (Plot: long, Plotoutline: short)	
	if tagline:								
		ilabels['Plot'] = tagline
	if summary:									
		ilabels['Plot'] = "%s\n\n%s" % (ilabels['Plot'], summary)
	if mediatype:							# "video", "music" setzen: List- statt Dir-Symbol
		ilabels.update({'mediatype': '%s' % mediatype})
		
	PLog('ilabels: ' + str(ilabels))
	li.setInfo(type="video", infoLabels=ilabels)						
	
	if SETTINGS.getSetting('pref_watchlist') ==  'true':	# Merkliste verwenden 
		if cmenu:											# Kontextmenüs Merkliste hinzufügen	
			Plot = ilabels['Plot']
			Plot = Plot.replace('\n', '||')		# || Code für LF (\n scheitert in router)
			# PLog('Plot: ' + Plot)
			fparams_add = "&fparams={'action': 'add', 'name': '%s', 'thumb': '%s', 'Plot': '%s', 'url': '%s'}" \
				%   (label, thumb,  urllib.quote_plus(Plot), urllib.quote_plus(url))
				# %   (label, thumb,  base64.b64encode(url))#möglich: 'Incorrect padding' error 
			fparams_add = urllib.quote_plus(fparams_add)

			fparams_del = "&fparams={'action': 'del', 'name': '%s'}" \
				%   (label)									# name reicht für del
				# %   (label, thumb,  base64.b64encode(url))
			fparams_del = urllib.quote_plus(fparams_del)	

			li.addContextMenuItems([('Zur Merkliste hinzufügen', 'RunAddon(%s, ?action=dirList&dirID=Watch%s)' \
				% (ADDON_ID, fparams_add)), ('Aus Merkliste entfernen', 'RunAddon(%s, ?action=dirList&dirID=Watch%s)' \
				% (ADDON_ID, fparams_del))])
		else:
			pass											# Kontextmenü entfernen klappt so nicht
			#li.addContextMenuItems([('Zur Merkliste hinzufügen', 'RunAddon(%s, ?action=dirList&dirID=dummy)' \
			#	% (ADDON_ID))], replaceItems=True)

		
	xbmcplugin.addDirectoryItem(handle=HANDLE,url=url,listitem=li,isFolder=isFolder)
	
	PLog('addDir_End')		
	return	

#---------------------------------------------------------------- 



