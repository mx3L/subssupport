# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from six.moves import html_parser
from six.moves.urllib.request import FancyURLopener
from six.moves.urllib.parse import quote_plus, urlencode
import urllib.request
import urllib.parse
from ..utilities import log
import html
import urllib3
import requests, re
import requests , json, re,random,string,time,warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from six.moves import html_parser
warnings.simplefilter('ignore',InsecureRequestWarning)
import os, os.path
from six.moves.urllib.request import HTTPCookieProcessor, build_opener, install_opener, Request, urlopen
from six.moves.urllib.parse import urlencode
from six.moves import http_cookiejar
from .SubsytsUtilities import get_language_info
from ..utilities import languageTranslate, log, getFileSize
from ..utilities import log
import urllib3
from urllib import request, parse
from urllib.parse import urlencode
import urllib.request
import urllib.parse
import six
from six.moves import urllib
from six.moves import xmlrpc_client

import time
import calendar
import re
from six.moves import html_parser
from ..seeker import SubtitlesDownloadError, SubtitlesErrors
HDR= {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
      'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
      'Upgrade-Insecure-Requests': '1',
      'Content-Type': 'application/x-www-form-urlencoded',
      'Referer': 'https://www.titulky.com',
      'Connection': 'keep-alive',
      'Accept-Encoding':'gzip, deflate'}
      
HDT= {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.0',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
      'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
      'Upgrade-Insecure-Requests': '1',
      'nel': '{"success_fraction":0,"report_to":"cf-nel","max_age":604800}',
      'Content-Type':'text/html; charset=utf-8',
      'Origin': 'https://yifysubtitles.ch',
      'Host': 'yifysubtitles.ch',
      'Referer': 'https://yifysubtitles.ch/',
      'Connection': 'keep-alive',
      'TE': 'trailers',
      'Upgrade-Insecure-Requests': '1',
      'Accept-Encoding':'gzip, deflate, br'}
      
s = requests.Session()  
 

main_url = "https://yts-subs.com"
main_url2 = "https://yifysubtitles.ch"
debug_pretext = "yts-subs.com"


subsyts_languages = {
    'Chinese BG code': 'Chinese',
    'Brazillian Portuguese': 'Portuguese (Brazil)',
    'Serbian': 'SerbianLatin',
    'Ukranian': 'Ukrainian',
    'Farsi/Persian': 'Persian'
}

def get_file2(downloadlink):
    def __init__(self):
        url = '%s%s' % (main_url2, downloadlink) 
        print(url) 
        log(__name__, 'Downloading file %s' % (url))
        req = Request(url)
        req = self.add_cookies_into_header(req)
        response = urlopen(req)
        if response.headers.get('Set-Cookie'):
            phpsessid = re.search('PHPSESSID=(\S+);', response.headers.get('Set-Cookie'), re.IGNORECASE | re.DOTALL)
            if phpsessid:
                log(__name__, "Storing PHPSessionID")
                self.cookies['PHPSESSID'] = phpsessid.group(1)
        content = response.read()
        print(content) 
        log(__name__, 'Done')
        response.close()
        return content
    
def find_movie(content, title, year):
    d = content
    print(d)
    url_found = None
    h = html_parser.HTMLParser()
    for matches in re.finditer(movie_season_pattern, content, re.IGNORECASE | re.DOTALL):
        print((tuple(matches.groups())))
        found_title = matches.group('title')
        found_title = html.unescape(found_title) 
        print(("found_title", found_title))  
        log(__name__, "Found movie on search page: %s (%s)" % (found_title, matches.group('year')))
        if found_title.lower().find(title.lower()) > -1:
            if matches.group('year') == year:
                log(__name__, "Matching movie found on search page: %s (%s)" % (found_title, matches.group('year')))
                url_found = matches.group('link')
                break
    return url_found
        
def get_url(url, referer=None):
    if referer is None:
        headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
    else:
        headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0', 'Referer': referer}
    req = urllib.request.Request(url, None, headers)
    response = urllib.request.urlopen(req)
    content = response.read().decode('utf-8') 
    response.close()
    content = content.replace('\n', '')
    return content


def get_rating(downloads):
    rating = int(downloads)
    if (rating < 50):
        rating = 1
    elif (rating >= 50 and rating < 100):
        rating = 2
    elif (rating >= 100 and rating < 150):
        rating = 3
    elif (rating >= 150 and rating < 200):
        rating = 4
    elif (rating >= 200 and rating < 250):
        rating = 5
    elif (rating >= 250 and rating < 300):
        rating = 6
    elif (rating >= 300 and rating < 350):
        rating = 7
    elif (rating >= 350 and rating < 400):
        rating = 8
    elif (rating >= 400 and rating < 450):
        rating = 9
    elif (rating >= 450):
        rating = 10
    return rating                           


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack): #standard input
    languagefound = lang1
    language_info = get_language_info(languagefound)
    language_info1 = language_info['name']
    language_info2 = language_info['2et']
    language_info3 = language_info['3et']

    subtitles_list = []
    msg = ""   

    if len(tvshow) == 0 and year: # Movie
        searchstring = "%s (%s)" % (title, year)
    elif len(tvshow) > 0 and title == tvshow: # Movie not in Library
        searchstring = "%s (%#02d%#02d)" % (tvshow, int(season), int(episode))
    elif len(tvshow) > 0: # TVShow
        searchstring = "%s S%#02dE%#02d" % (tvshow, int(season), int(episode))
    else:
        searchstring = title
    log(__name__, "%s Search string = %s" % (debug_pretext, searchstring))
    get_subtitles_list(searchstring, title, year, language_info2, language_info1, subtitles_list)
    return subtitles_list, "", msg #standard output

def download_subtitles (subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):  # standard input
    language = subtitles_list[pos]["language_name"]
    lang = subtitles_list[pos]["language_flag"]   
    id = subtitles_list[pos]["id"]
    downloadlink = '%s%s.zip' % (main_url2, id)
    if downloadlink:    
        log(__name__ , "%s Downloadlink: %s " % (debug_pretext, downloadlink))
        viewstate = 0
        previouspage = 0
        subtitleid = 0
        typeid = "zip"
        filmid = 0
        #postparams = { '__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '' , '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid}
        #postparams = urllib3.request.urlencode({ '__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '' , '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid})
        postparams = urlencode({'__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '', '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid})

        #class MyOpener(urllib.FancyURLopener):
            #version = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.0'
        #my_urlopener = MyOpener()
        #my_urlopener.addheader('Referer', url)
        log(__name__ , "%s Fetching subtitles using url '%s' with referer header and post parameters '%s'" % (debug_pretext, downloadlink, postparams))
        #response = my_urlopener.open(downloadlink, postparams)
        response = s.get(downloadlink,headers=HDT,params=postparams,verify=False,allow_redirects=True) 
        #r = requests.get(downloadlink, stream=True)
        print(response.content)
        #s = response.decode('latin1')
        local_tmp_file = zip_subs
        try:
            log(__name__ , "%s Saving subtitles to '%s'" % (debug_pretext, local_tmp_file))
            if not os.path.exists(tmp_sub_dir):
                os.makedirs(tmp_sub_dir)
   
            local_file_handle = open(local_tmp_file, 'wb')
            #local_file_handle.write(s.content) #(response.content)  StringIO.StringIO(r.content)
            local_file_handle.write(response.content)
            local_file_handle.close()
            # Check archive type (rar/zip/else) through the file header (rar=Rar!, zip=PK) urllib3.request.urlencode
            myfile = open(local_tmp_file, "rb")
            myfile.seek(0)
            if (myfile.read(1).decode('utf-8') == 'R'):
                typeid = "rar"
                packed = True
                log(__name__ , "Discovered RAR Archive")
            else:
                myfile.seek(0)
                if (myfile.read(1).decode('utf-8') == 'P'):
                    typeid = "zip"
                    packed = True
                    log(__name__ , "Discovered ZIP Archive")
                else:
                    typeid = "srt"
                    packed = False
                    subs_file = local_tmp_file
                    log(__name__ , "Discovered a non-archive file")
            myfile.close()
            log(__name__ , "%s Saving to %s" % (debug_pretext, local_tmp_file))
        except:
            log(__name__ , "%s Failed to save subtitle to %s" % (debug_pretext, local_tmp_file))
        if packed:
            subs_file = typeid
        log(__name__ , "%s Subtitles saved to '%s'" % (debug_pretext, local_tmp_file))
        return packed, language, subs_file  # standard output

       
def get_subtitles_list(searchstring, title, year, languageshort, languagelong, subtitles_list):
    s = languagelong.strip()
    title = title.strip()
    #search_string = prepare_search_string(title)
    #print(("getSearchTitle", getSearchTitle))
    #print(s)
    #print(title)
    url = '%s/search/%s' % (main_url, urllib.parse.quote_plus(searchstring))
    print(url)
    try:
        log(__name__, "%s Getting url: %s" % (debug_pretext, url))
        content = get_url(url,referer=main_url)
        #print(content)        
    except:
        pass
        log(__name__, "%s Failed to get url:%s" % (debug_pretext, url))
        return
    try:
        log( __name__ ,"%s Getting '%s' subs ..." % (debug_pretext, languageshort))
        #print(data) 
        subtitles = re.compile('(<a href="/movie-imdb/.+?</h3>)').findall(content)
        #print(subtitles)
        subtitles = " ".join(subtitles)
        regx = 'alt="'+title+'".+?href="(.+?)">' 
        downloadlink=re.findall(regx,subtitles, re.M|re.I)[0]
        #print(downloadlink)
        link = '%s%s' % (main_url, downloadlink)
        #print(link)
        content = get_url(link,referer=main_url)                   
        #print(content)
        subtitles = re.compile('(<span class="sub-lang">'+s+'</span>.+?download</a>)').findall(content)
        #print(subtitles)
    except:
        log( __name__ ,"%s Failed to get subtitles" % (debug_pretext))
        return
    for subtitle in subtitles:
        try:
            filename = re.compile('subtitle</span> (.+?)</a>').findall(subtitle)[0].replace("<br />","\n")
            filename = filename.strip()
            #print(filename)
            id = re.compile('href="(.+?)"').findall(subtitle)[0].replace("subtitles","subtitle")
            #print(id)
            try:
                downloads = re.compile('<a href="(.+?)">.+?<span').findall(subtitle)[0]
                print(downloads)
                downloads = re.sub("\D", "", downloads)
            except:
                pass
            try:
                rating = get_rating(downloads)
                #print(rating)
            except:
                rating = 0
                pass
                
            if not (downloads == 'Εργαστήρι Υποτίτλων' or downloads == 'subs4series'):
                log( __name__ ,"%s Subtitles found: %s (id = %s)" % (debug_pretext, filename, id))
                subtitles_list.append({'rating': str(rating), 'no_files': 1, 'filename': str(filename), 'id': id, 'sync': False, 'language_flag': languageshort, 'language_name': languagelong})

        except:
            pass
    return
