# -*- coding: utf-8 -*-
import os
import urllib
import urllib2
import xbmcplugin
import xbmcgui
import xbmcaddon
import json
from datetime import datetime
from client import GraphQLClient

_apiurl = 'https://api.televizeseznam.cz/graphql'
_useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'

_addon = xbmcaddon.Addon('plugin.video.televizeseznam.cz')
_lang = _addon.getLocalizedString

MODE_LIST_SHOWS = 1
MODE_LIST_CHANNELS = 2
MODE_LIST_CATEGORIES = 3
MODE_LIST_EPISODES = 4
MODE_LIST_EPISODES_LATEST = 5
MODE_VIDEOLINK = 10

def log(msg, level=xbmc.LOGDEBUG):
    if type(msg).__name__ == 'unicode':
        msg = msg.encode('utf-8')
    xbmc.log("[%s] %s" % (_addon.getAddonInfo('name'), msg.__str__()), level)

def logDbg(msg):
    log(msg,level=xbmc.LOGDEBUG)

def logErr(msg):
    log(msg,level=xbmc.LOGERROR)

def listContent():
    addDir(_lang(30002), 'ListLatest', MODE_LIST_EPISODES_LATEST, '')
    addDir(_lang(30003), 'ListShowLatest', MODE_LIST_SHOWS, '')
    addDir(_lang(30004), 'listCategories', MODE_LIST_CATEGORIES, '')

def listCategories():    
    client = GraphQLClient(_apiurl)
    params = { "limit": 20 }

    data = client.execute('''query LoadTags($limit : Int){ tags(inGuide: true, limit: $limit){ ...NavigationCategoryFragmentOnTag  } tagsCount(inGuide: true) }
		fragment NavigationCategoryFragmentOnTag on Tag {
			id,
			name,
			category,
			urlName
		}
	''', params)
        
    for item in data[u'data'][u'tags']:
        link = item[u'id']
        name = item[u'name']
        addDir(name, link, MODE_LIST_CHANNELS, '')
        
def listShows():    
    client = GraphQLClient(_apiurl)
    params = { "limit": 500 }

    data = client.execute('''query LoadTags($limit : Int){ tags(listing: navigation, limit: $limit){ ...NavigationFragmentOnTag  } tagsCount(listing: navigation) }
		fragment NavigationFragmentOnTag on Tag {
			id,
			name,
			images {
				...DefaultFragmentOnImage
			},
			category,
			urlName,
			originTag {
				...DefaultOriginTagFragmentOnTag
			}
		}
	
		fragment DefaultFragmentOnImage on Image {
			usage,
			url
		}
	
		fragment DefaultOriginTagFragmentOnTag on Tag {
			id,
			dotId,
			name,
			urlName,
			category,
			images {
				...DefaultFragmentOnImage
			}
		}
	''', params)

    for item in data[u'data'][u'tags']:
        name = item[u'name']
        for images in item[u'images']:
            image = 'https:'+images[u'url'] 
        if item[u'category'] == 'service':
            addDir(name, item[u'id'], MODE_LIST_CHANNELS, image)
        else:
            addDir(name, item[u'urlName'], MODE_LIST_EPISODES, image)

def listChannels(url):
    client = GraphQLClient(_apiurl)
    params = { "id": url, "childTagsConnectionFirst": 500, "childTagsConnectionCategories": ["show","tag"] }

    data = client.execute('''query LoadChildTags($id : ID, $childTagsConnectionFirst : Int, $childTagsConnectionCategories : [Category]){ tag(id: $id){ childTagsConnection(categories: $childTagsConnectionCategories,first : $childTagsConnectionFirst) { ...TagCardsFragmentOnTagConnection  } } }
		fragment TagCardsFragmentOnTagConnection on TagConnection {
			totalCount
			pageInfo {
				endCursor
				hasNextPage
			}
			edges {
				node {
					...TagCardFragmentOnTag
				}
			}
		}
	
		fragment TagCardFragmentOnTag on Tag {
			id,
			dotId,
			name,
			category,
			perex,
			urlName,
			images {
				...DefaultFragmentOnImage
			},
			originTag {
				...DefaultOriginTagFragmentOnTag
			}
		}
	
		fragment DefaultFragmentOnImage on Image {
			usage,
			url
		}
	
		fragment DefaultOriginTagFragmentOnTag on Tag {
			id,
			dotId,
			name,
			urlName,
			category,
			images {
				...DefaultFragmentOnImage
			}
		}
	''', params)
    
        
    for item in data[u'data'][u'tag'][u'childTagsConnection'][u'edges']:
        link = item['node'][u'urlName']
        for images in item[u'node'][u'images']:
            image = 'https:'+images[u'url'] 
        name = item[u'node'][u'name']
        addDir(name, link, MODE_LIST_EPISODES, image) 

def listEpisodes(url):
    client = GraphQLClient(_apiurl)
    params = { "urlName": url, "episodesConnectionFirst": 20 }

    data = client.execute('''query LoadTag($urlName : String, $episodesConnectionFirst : Int){ tagData:tag(urlName: $urlName, category: show){ ...ShowDetailFragmentOnTag episodesConnection(first : $episodesConnectionFirst) { ...SeasonEpisodeCardsFragmentOnEpisodeItemConnection } } }
		fragment ShowDetailFragmentOnTag on Tag {
			id
			dotId
			name
			category
			urlName
			favouritesCount
			perex
			images {
				...DefaultFragmentOnImage
			}
			bannerAdvert {
				...DefaultFragmentOnBannerAdvert
			},
			originServiceTag {
				...OriginServiceTagFragmentOnTag
			}
		}	
	
		fragment SeasonEpisodeCardsFragmentOnEpisodeItemConnection on EpisodeItemConnection {
			totalCount
			pageInfo {
				endCursor
				hasNextPage
			}
			edges {
				node {
					...SeasonEpisodeCardFragmentOnEpisode
				}
			}
		}
	
		fragment DefaultFragmentOnImage on Image {
			usage,
			url
		}
	
		fragment DefaultFragmentOnBannerAdvert on BannerAdvert {
			section
		}
	
		fragment OriginServiceTagFragmentOnTag on Tag {
			id,
			dotId,
			name,
			urlName,
			category,
			invisible,
			images {
				...DefaultFragmentOnImage
			}
		}
	
		fragment SeasonEpisodeCardFragmentOnEpisode on Episode {
			id
			dotId
			name
			namePrefix
			duration
			images {
				...DefaultFragmentOnImage
			}
			urlName
			originTag {
				...DefaultOriginTagFragmentOnTag
			}
			publish
			views
		}
	
		fragment DefaultOriginTagFragmentOnTag on Tag {
			id,
			dotId,
			name,
			urlName,
			category,
			images {
				...DefaultFragmentOnImage
			}
		}
        ''', params)
        
    for item in data[u'data'][u'tagData'][u'episodesConnection'][u'edges']:
        link = item[u'node'][u'urlName']
        image = 'https:'+item[u'node'][u'images'][0][u'url']
        name = item[u'node'][u'name']
        date = datetime.utcfromtimestamp(item[u'node'][u'publish']).strftime("%Y-%m-%d")
        info={'duration':item[u'node'][u'duration'],'date':date}
        addResolvedLink(name, link, image, name, info=info)

        
def listEpisodesLatest(url):
    client = GraphQLClient(_apiurl)
    params = { "episodesConnectionAfter": "1~MTU2ODg4MzYwMA~NjM5NzMzODE", "episodesConnectionFirst": 100, "id": "VGFnOjEyNDM2OTc" }

    data = client.execute('''query LoadTag($id : ID, $episodesConnectionAfter : String, $episodesConnectionFirst : Int){ tagData:tag(id: $id){ episodesConnection(after: $episodesConnectionAfter,first : $episodesConnectionFirst) { ...EpisodeCardsFragmentOnEpisodeItemConnection } } }
		fragment EpisodeCardsFragmentOnEpisodeItemConnection on EpisodeItemConnection {
			totalCount
			pageInfo {
				endCursor
				hasNextPage
			}
			edges {
				node {
					...EpisodeCardFragmentOnEpisode
				}
			}
		}
	
		fragment EpisodeCardFragmentOnEpisode on Episode {
			id
			dotId
			name
			duration
			images {
				...DefaultFragmentOnImage
			}
			urlName
			originTag {
				...DefaultOriginTagFragmentOnTag
			}
			publish
			views
		}
	
		fragment DefaultFragmentOnImage on Image {
			usage,
			url
		}
	
		fragment DefaultOriginTagFragmentOnTag on Tag {
			id,
			dotId,
			name,
			urlName,
			category,
			images {
				...DefaultFragmentOnImage
			}
		}
	''', params)
        
    
    for item in data[u'data'][u'tagData'][u'episodesConnection'][u'edges']:
        link = item[u'node'][u'urlName']
        tag = item[u'node'][u'originTag'][u'name']
        name = item[u'node'][u'name']
        if tag:
            name = tag + ' | ' + name
        image = 'https:'+item[u'node'][u'images'][0][u'url']
        date = datetime.utcfromtimestamp(item[u'node'][u'publish']).strftime("%Y-%m-%d")
        logDbg(date)
        info={'duration':item[u'node'][u'duration'],'date':date}
        addResolvedLink(name, link, image, name, info=info)

def getVideoLink(url):
    req = urllib2.Request(url, None, {'Content-type': 'application/json', 'Accept': 'application/json', 'User-Agent': _useragent})
    resp = urllib2.urlopen(req)
    return json.loads(resp.read().decode('utf-8'))
    
def videoLink(url):
    client = GraphQLClient(_apiurl)
    params = { "urlName": url }

    data = client.execute('''query LoadEpisode($urlName : String){ episode(urlName: $urlName){ ...VideoDetailFragmentOnEpisode } }
		fragment VideoDetailFragmentOnEpisode on Episode {
			id
			dotId
			dotOriginalService
			originalId
			name
			perex
			duration
			images {
				...DefaultFragmentOnImage
			}
			spl
			commentsDisabled
			productPlacement
			urlName
			originUrl
			originTag {
				...OriginTagInfoFragmentOnTag
			}
			advertEnabled
			adverts {
				...DefaultFragmentOnAdvert
			}
			bannerAdvert {
				...DefaultFragmentOnBannerAdvert
			}
			views
			publish
			links {
				...DefaultFragmentOnLinks
			}
			recommendedAbVariant
			sklikRetargeting
		}
	
		fragment DefaultFragmentOnImage on Image {
			usage,
			url
		}
	
		fragment OriginTagInfoFragmentOnTag on Tag {
			id,
			dotId,
			name,
			urlName,
			category,
			invisible,
			images {
				...DefaultFragmentOnImage
			}
		}
	
		fragment DefaultFragmentOnAdvert on Advert {
			zoneId
			section
			collocation
			position
			rollType
		}
	
		fragment DefaultFragmentOnBannerAdvert on BannerAdvert {
			section
		}
	
		fragment DefaultFragmentOnLinks on Link {
			label,
			url
		}
	''', params)
    
    name = data[u'data'][u'episode'][u'name']
    image = 'https:'+data[u'data'][u'episode'][u'images'][0][u'url']
    perex = data[u'data'][u'episode'][u'perex']
    link = data[u'data'][u'episode'][u'spl'].split('/')
    
    url=getVideoLink(data[u'data'][u'episode'][u'spl']+'spl2,3')

    if 'Location' in url:
        link = url['Location'].split('/')
        url = getVideoLink(url['Location'])
    
    for quality in sorted(url[u'data'][u"mp4"], key=lambda kv: kv[1], reverse=True):
        stream_quality=quality
        video_url = url[u'data'][u"mp4"][stream_quality][u"url"][3:]

    stream_url = '/'.join(link[0:5])+'/'+video_url

    liz = xbmcgui.ListItem()
    liz = xbmcgui.ListItem(path=stream_url)  
    liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": perex})
    liz.setProperty('isPlayable', 'true')
    xbmcplugin.setResolvedUrl(handle=addonHandle, succeeded=True, listitem=liz)

def getParams():
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

def composePluginUrl(url, mode, name):
    return sys.argv[0]+"?url="+urllib.quote_plus(url.encode('utf-8'))+"&mode="+str(mode)+"&name="+urllib.quote_plus(name.encode('utf-8'))

def addItem(name, url, mode, iconimage, desc, isfolder, islatest=False, info={}):
    u = composePluginUrl(url, mode, name)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, 'plot': desc})
    liz.setProperty("Fanart_Image", iconimage)
    if u'duration' in info:
            liz.setInfo('video', {'duration': info[u'duration']})
    if u'date' in info:
            liz.setInfo('video', {'premiered': info[u'date']})
    liz.setInfo('video', {'mediatype': 'episode', 'title': name, 'plot': desc})
    if not isfolder:
        liz.setProperty("isPlayable", "true")
    ok=xbmcplugin.addDirectoryItem(handle=addonHandle,url=u,listitem=liz,isFolder=isfolder)
    return ok

def addDir(name, url, mode, iconimage, plot='', info={}):
    logDbg("addDir(): '"+name+"' url='"+url+"' icon='"+iconimage+"' mode='"+str(mode)+"'")
    return addItem(name, url, mode, iconimage, plot, True)
    
def addResolvedLink(name, url, iconimage, plot='', islatest=False, info={}):
    xbmcplugin.setContent(addonHandle, 'episodes')
    mode = MODE_VIDEOLINK
    logDbg("addUnresolvedLink(): '"+name+"' url='"+url+"' icon='"+iconimage+"' mode='"+str(mode)+"'")
    return addItem(name, url, mode, iconimage, plot, False, islatest, info)

addonHandle=int(sys.argv[1])
params=getParams()
url = None
name = None
thumb = None
mode = None

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

logDbg("Mode: "+str(mode))
logDbg("URL: "+str(url))
logDbg("Name: "+str(name))

if mode==None or url==None or len(url)<1:
    logDbg('listContent()')
    listContent()

elif mode==MODE_LIST_SHOWS:
    logDbg('listShows()')
    listShows()
    
elif mode==MODE_LIST_CATEGORIES:
    logDbg('listCategories()')
    listCategories()

elif mode==MODE_LIST_CHANNELS:
    logDbg('listChannels()')
    listChannels(url)  
    
elif mode==MODE_LIST_EPISODES:
    logDbg('listEpisodes()')
    listEpisodes(url)
       
elif mode==MODE_LIST_EPISODES_LATEST:
    logDbg('listEpisodesLatest()')
    listEpisodesLatest(url)

elif mode==MODE_VIDEOLINK:
    logDbg('videoLink() with url ' + str(url))
    videoLink(url)
    
xbmcplugin.endOfDirectory(addonHandle)