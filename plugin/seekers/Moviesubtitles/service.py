# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import json
import difflib
import os
import re
import string
from six.moves import html_parser
from six.moves.urllib.request import FancyURLopener
from six.moves.urllib.parse import quote_plus, urlencode
import urllib.request
import urllib.parse
from urllib.parse import quote
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
from .MoviesubtitlesUtilities import get_language_info
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


HDR= {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.0',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
      'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
      'Upgrade-Insecure-Requests': '1',
      'Content-Type': 'application/x-www-form-urlencoded',
      'Host': 'moviesubtitles.com',
      'Referer': 'http://www.moviesubtitles.org',
      'Upgrade-Insecure-Requests': '1',
      'Connection': 'keep-alive',
      'Accept-Encoding':'gzip'}#, deflate'}
      
s = requests.Session()  
 

main_url = "http://www.moviesubtitles.org"
debug_pretext = "moviesubtitles.org"


moviesubtitles_languages = {
    'Chinese BG code': 'Chinese',
    'Brazillian Portuguese': 'Portuguese (Brazil)',
    'Serbian': 'SerbianLatin',
    'Ukranian': 'Ukrainian',
    'Farsi/Persian': 'Persian'
}

        
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
    
def getSearchTitle(title, year=None): 
    title = title.strip()
    year = str(year)
    url = "http://www.moviesubtitles.org/search.php"
    params = ({'q': title, 'submit': 'Search'})
    data = s.post(url,data=params,headers=HDR,verify=False,allow_redirects=True).text
    data = data.replace("\n","").replace("(","").replace(")","")
    blocks = data.split('class="left"')  
    #print(("xxxxxxx", blocks))    
    blocks.pop(0)
    list1 = []
    for blocks in blocks:
        try:
            regx = '''<a href="(.*?)">(.*?)</a>'''
            matches = re.findall(regx, blocks)
            name = matches[0][1]
            href = matches[0][0]
            print(("hrefxxx", href))
            print(("yearxx", year))
            if year is None:
               if "/movie-" in href:
                  href = 'http://www.moviesubtitles.org' + href
                  return href
            if year in blocks:
                regx = '.*<a href="(.*?)">'+title+' '+year+'</a>\s?'
                href = re.findall(regx, blocks, re.M|re.I)[0]
                print ("hrefi", href)
                if "/movie-" in href:
                   href = 'http://www.moviesubtitles.org' + href
                   return href
        except:
            break
    return 'http://www.moviesubtitles.org' + href
    
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
    get_subtitles_list(title, year, language_info2, language_info1, subtitles_list)
    return subtitles_list, "", msg #standard output

def download_subtitles (subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):  # standard input
    language = subtitles_list[pos]["language_name"]
    lang = subtitles_list[pos]["language_flag"]
    filename = subtitles_list[pos]["filename"]
    print(filename)
    id = subtitles_list[pos]["id"]
    id = id.replace("subtitle","download")
    downloadlink = 'http://www.moviesubtitles.org%s' % (id)
    #downloadlink_pattern = '<a id="download_'+lang+'" onclick=.+?href=\"(.+?)\" class="green-link">Download</a>'
    #print(downloadlink_pattern) 
    if downloadlink:
        log(__name__ , "%s Downloadlink: %s " % (debug_pretext, downloadlink))
        viewstate = 0
        previouspage = 0
        subtitleid = 0
        typeid = "zip"
        filmid = 0
        #postparams = { '__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '' , '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid}
        postparams = urllib3.request.urlencode({ '__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '' , '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid})
        #class MyOpener(urllib.FancyURLopener):
            #version = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.0'
        #my_urlopener = MyOpener()
        #my_urlopener.addheader('Referer', url)
        log(__name__ , "%s Fetching subtitles using url with referer header '%s' and post parameters '%s'" % (debug_pretext, downloadlink, postparams))
        #response = my_urlopener.open(downloadlink, postparams)
        response = s.get(downloadlink,data=postparams,headers=HDR,verify=False,allow_redirects=True) 
        print(response.content)
        local_tmp_file = zip_subs
        try:
            log(__name__ , "%s Saving subtitles to '%s'" % (debug_pretext, local_tmp_file))
            if not os.path.exists(tmp_sub_dir):
                os.makedirs(tmp_sub_dir)
            local_file_handle = open(local_tmp_file, 'wb')
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

def prepare_search_string(s):
    s = s.strip()
    s = re.sub(r'\(\d\d\d\d\)$', '', s)  # remove year from title
    s = quote_plus(s)
    return s
    
def get_subtitles_list(title, year, languageshort, languagelong, subtitles_list):
    #url = '%s/index.php?search=%s' % (main_url, quote(searchstring))
    dst = languageshort.lower()
    print ("dst", dst)
    title = title.strip()
    print ("title", title)
    search_string = prepare_search_string(title)
    print(("getSearchTitle", getSearchTitle))
    url = getSearchTitle(search_string, year)#.replace("%2B","-")
    print(("true url", url))
    content = s.get(url,headers=HDR,verify=False,allow_redirects=True).text
    #print(content)
    try:                                         
        log( __name__ ,"%s Getting '%s' subs ..." % (debug_pretext, languageshort))
        subtitles = re.compile('(<img src=.+?flags/'+dst+'.gif.+?</b>)').findall(content)
        print ("subtitles", subtitles)
    except:
        log( __name__ ,"%s Failed to get subtitles" % (debug_pretext))
        return
    for subtitle in subtitles:
        try:
            filename = re.compile('<a.+?><b>(.+?)</b>').findall(subtitle)[0]
            filename = filename.strip()
            print(filename)
            id = re.compile('href="(.+?)"').findall(subtitle)[0]
            print(id)
            try:
                downloads = re.compile('<a href="(.+?)"><b>').findall(subtitle)[0]
                print("downloads", downloads)
                downloads = re.sub("\D", "", downloads)
            except:
                pass
            try:
                rating = get_rating(downloads)
                print(rating)
            except:
                rating = 0
                pass
                
            if not (downloads == 'Εργαστήρι Υποτίτλων' or downloads == 'subs4series'):
                log( __name__ ,"%s Subtitles found: %s (id = %s)" % (debug_pretext, filename, id))
                subtitles_list.append({'rating': str(rating), 'no_files': 1, 'filename': filename, 'sync': False, 'id' : id, 'language_flag': languageshort, 'language_name': languagelong})

        except:
            pass
    return
