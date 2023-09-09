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
from .ElsubtitleUtilities import get_language_info
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

HDR= {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:85.0) Gecko/20100101 Firefox/85.0',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
      'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
      'Content-Type':'application/x-www-form-urlencoded',
      #'Content-Type':'application/x-www-form-urlencoded; charset=utf-8',
      'Host': 'www.mimastech.com',
      'Referer': 'https://www.mimastech.com',
      'Upgrade-Insecure-Requests': '1',
      'Connection': 'keep-alive',
      'Accept-Encoding':'gzip, deflate'} 
      
HDS= {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.0',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
      'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
      'Upgrade-Insecure-Requests': '1',
      'Content-Type': 'application/x-www-form-urlencoded',
      'Host': 'www.elsubtitle.com',
      'Referer': 'https://www.elsubtitle.com',
      'Upgrade-Insecure-Requests': '1',
      'Connection': 'keep-alive',
      'Accept-Encoding':'gzip'}#, deflate'} 
                
s = requests.Session()  
 

main_url = "https://www.elsubtitle.com"
url1="https://www.mimastech.com/cs_download/subdownload_p1.php"
url2="https://www.mimastech.com/cs_download/subdownload_p2.php"

debug_pretext = "https://www.elsubtitle.com"


elsubtitle_languages = {
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

def getSearchTitle(title, searchstring, year=None): ## new Add  .replace("+","-")
    title = title.strip()
    hrf = searchstring.lower()       
    hrf = hrf.replace(":","+")
    print('hrf', hrf)
    url = 'https://www.elsubtitle.com/search-results/?search_name=%s' % hrf
    print(("url", url))
    data = s.get(url,headers=HDS,verify=False).content
    data = data.decode('utf-8')
    subtitles = re.compile('(<a href="/title/.+?src)').findall(data)
    subtitles = " ".join(subtitles)
    #print(("subtitles", subtitles))
    for subtitle in subtitles:
        #regx = '.*<a href="(.+?)"><img.+?alt="(.+?)"'
        regx = '<a href="(.+?)" title.+?>(.+?)</a>'
        try: 
            href = re.compile('.*<a href="(.+?)"><img.+?alt="'+title+'"\s+').findall(subtitles)[0]
            print(("href", href))
            href = 'https://www.elsubtitle.com' + href
            return href
            if year and year == '':
               matches = re.findall(regx, subtitles)
               name = matches[0][1]
               href = matches[0][0]
               print(("hrefxxx", href))
               print(("yearxx", year))            
               if "/title/" in href:
                  return href
            if not year:
              if "/title/" in href:
                  return href
            if year and str(year) in name:
                if "/title/" in href:
                   print(("href", href))
                   return href
        except:
            break                             
    return 'https://www.elsubtitle.com/search-results/?search_name=/' + hrf
    
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

def prepare_search_string(s):
    s = s.strip()
    s = re.sub(r'\(\d\d\d\d\)$', '', s)  # remove year from title    type="hidden" value="ar" /><input name="subtitle_id" type="hidden" value="SUL_360528" /><input name="imdb_id" t
    s = quote_plus(s)
    return s
    
def download_subtitles (subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):  # standard input
    language = subtitles_list[pos]["language_name"]   
    lang = subtitles_list[pos]["language_flag"]   
    id = subtitles_list[pos]["id"]
    imdb_id = id.split('/')[1]
    id = id.split('/')[0]
    print('language ', language)    
    print('lang ', lang)    
    check_data='site_language=en&subtitle_language='+lang+'&subtitle_id='+id+'&imdb_id='+imdb_id+''
    data=s.post(url1,headers=HDR,data=check_data,verify=False,allow_redirects=False).text
    #print(data)    
    regx='workid" type="hidden" value="(.*?)"'
    regx2='rawurlencode" type="hidden" value="(.*?)"'
    regx3='worktitle" type="hidden" value="(.*?)"'
    regx4='workyear" type="hidden" value="(.*?)"'
    try:workid=re.findall(regx, data, re.M|re.I)[0]
    except:pass                                                                                
    #print("workid:",workid)
    try:rawurlencode=re.findall(regx2, data, re.M|re.I)[0]
    except:pass                                                                                
    #print("rawurlencode:",rawurlencode)
    try:worktitle=re.findall(regx3, data, re.M|re.I)[0]
    except:pass                                                                                
    #print("worktitle:",worktitle)
    try:workyear=re.findall(regx4, data, re.M|re.I)[0]
    except:pass                                                                                
    #print("workyear:",workyear)
    check_data2='workid='+workid+'&rawurlencode='+rawurlencode+'&linkback=Back to&linkanother=Download another subtitle file&downloadtext=Download the subtitle file for&worktitle='+worktitle+'&workyear='+workyear+'&sublanguage=""&submit=Download The Subtitle File'
    post_data=s.post(url2,headers=HDR,data=check_data2,verify=False,allow_redirects=False).text
    #print(post_data)
    regx='<a href="(.*?)" download'
    link = re.findall(regx, post_data, re.M|re.I)[0]
    #print("link:",link)
    downloadlink = 'https://www.mimastech.com/cs_download/%s' % (link)
    #print("downloadlink:",downloadlink)
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
        HDS.update({'Referer': downloadlink})
        #class MyOpener(urllib.FancyURLopener):
            #version = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.0'
        #my_urlopener = MyOpener()
        #my_urlopener.addheader('Referer', url)
        log(__name__ , "%s Fetching subtitles using url '%s' with referer header and post parameters '%s'" % (debug_pretext, downloadlink, postparams))
        #response = my_urlopener.open(downloadlink, postparams) response.
        response = s.get(downloadlink,headers=HDR,params=postparams,verify=False,allow_redirects=False)
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
            if (myfile.read(1) == 'R'):
                typeid = "rar"
                packed = True
                log(__name__ , "Discovered RAR Archive")
            else:
                myfile.seek(0)
                if (myfile.read(1) == 'P'):
                    typeid = "zip"
                    packed = True
                    log(__name__ , "Discovered ZIP Archive")
                else:
                    typeid = "srt"
                    packed = True
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
    dst = languageshort
    dtt = languagelong
    title = title.strip()
    search_string = prepare_search_string(title)
    url = getSearchTitle(title, search_string, year)
    id_imdb = url.replace('https://www.elsubtitle.com/title/', '').replace('/', '')
    print('true url', url)
    print('id_imdb', id_imdb)
    try:
        log(__name__, "%s Getting url: %s" % (debug_pretext, url))
        content = s.get(url,headers=HDS,verify=False,allow_redirects=False).text
        content = content.replace('\n', '')
        print(("content", content))
    except:
        pass
        log(__name__, "%s Failed to get url:%s" % (debug_pretext, url))
        return                                                                      
    try:
        log( __name__ ,"%s Getting '%s' subs ..." % (debug_pretext, languageshort))
        subtitles = re.compile('(<tr><td.+?name="subtitle_language".+?value="'+dst+'".+?>'+dtt+'</span>)').findall(content)
        print(("subtitles", subtitles))
    except:
        log( __name__ ,"%s Failed to get subtitles" % (debug_pretext))
        return
    for subtitle in subtitles:   
        try:    
            filename = re.compile('.*>(.*?)</div><div').findall(subtitle)[0]
            filename = filename.strip()
            #print(filename) 
            id = re.compile('.*value="'+dst+'" /><input name="subtitle_id" type="hidden" value="(.*?)"').findall(subtitle)[0]
            #id = re.compile('name="subtitle_id" type="hidden" value="(.*?)"').findall(subtitle)[0]
            id= id+'/'+id_imdb
            #print(id)
            try:
                downloads = re.compile('action="(.+?)"').findall(subtitle)[0]
                downloads = re.sub("\D", "", downloads)
            except:
                pass
            try:
                rating = get_rating(downloads)
                #print(rating)
            except:
                rating = 0
                pass
                
            if not downloads == 0:
                log( __name__ ,"%s Subtitles found: %s (id = %s)" % (debug_pretext, filename, id))
                subtitles_list.append({'rating': str(rating), 'no_files': 1, 'filename': filename, 'sync': False, 'id' : id, 'language_flag': languageshort, 'language_name': languagelong})

        except:
            pass
    return
