# -*- coding: UTF-8 -*-
###### EDit By mino60 ######################   Titulky.com #################################

from __future__ import absolute_import

import os, os.path
from six.moves.urllib.request import HTTPCookieProcessor, build_opener, install_opener, Request, urlopen
from six.moves.urllib.parse import urlencode
from six.moves import http_cookiejar

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


LINKFILE='/tmp/code'

timestamp = str(calendar.timegm(time.gmtime()))

def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack ): #standard input
    # need to filter titles like <Localized movie name> (<Movie name>)
    br_index = title.find('(')
    if br_index > -1:
        title = title[:br_index]
    title = title.strip()
    session_id = "0"
    client = TitulkyClient()
    subtitles_list = client.search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, 'Czech', 'Slovak', 'EN')
    return subtitles_list, session_id, ""  #standard output


def download_subtitles (subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id): #standard input

    subtitle_id =  subtitles_list[pos][ 'ID' ]
    client = TitulkyClient()
    username = settings_provider.getSetting("Titulkyuser")
    password = settings_provider.getSetting("Titulkypass")
    if password == '' or username == '':
        log(__name__,'Credentials to Titulky.com not provided')
    else:
        if client.login(username,password) == False:
            log(__name__,'Login to Titulky.com failed. Check your username/password at the addon configuration')
            raise SubtitlesDownloadError(SubtitlesErrors.INVALID_CREDENTIALS_ERROR,
                                          "Login to Titulky.com failed. Check your username/password at the addon configuration")
            return True,subtitles_list[pos]['language_name'], ""
        log(__name__,'Login successfull')
    log(__name__,'Get page with subtitle (id=%s)'%(subtitle_id))
    
    content = client.get_subtitle_page(subtitle_id)
    control_img = client.get_control_image(content)
    
    if not control_img == None:
        log(__name__, 'Found control image :(, asking user for input')
        # subtitle limit was reached .. we need to ask user to rewrite image code :(
        log(__name__, 'Download control image')
        img = client.get_file(control_img)
        img_file = open(os.path.join(tmp_sub_dir, 'image.png'), 'wb')
        img_file.write(img)
        img_file.flush()
        img_file.close()
        
        solution = captcha_cb(os.path.join(tmp_sub_dir, 'image.png'))
        if os.path.exists(LINKFILE):
           f = open(LINKFILE, 'r')
           for line in f.readlines():
               id = line.strip('\n')
               try:code = "{0}".format(id)
               except:pass 
        #s.headers.update({'downkod': code})       
        content = client.get_subtitle_page2(content,code,subtitle_id)
        control_img2 = client.get_control_image(content)
        print(code)
        if solution == None: 
        #if solution:
            log(__name__,'Solution provided: %s' %solution)
            #content = client.get_subtitle_page2(content,solution,subtitle_id)
            #control_img2 = client.get_control_image(content)
            if not control_img2 == None:
                log(__name__,'Invalid control text')
                raise SubtitlesDownloadError(SubtitlesErrors.CAPTCHA_RETYPE_ERROR, "Invalid control text")
                #xbmc.executebuiltin("XBMC.Notification(%s,%s,1000,%s)" % (__scriptname__,"Invalid control text",os.path.join(__cwd__,'icon.png')))
                return True,subtitles_list[pos]['language_name'], ""
        else:
            log(__name__,'Dialog was canceled')
            log(__name__,'Control text not confirmed, returning in error')
            return True,subtitles_list[pos]['language_name'], ""

    wait_time = client.get_waittime(content)
    cannot_download = client.get_cannot_download_error(content)
    if not None == cannot_download:
        log(__name__,'Subtitles cannot be downloaded, user needs to login')
        raise SubtitlesDownloadError(SubtitlesErrors.NO_CREDENTIALS_ERROR, "Subtitles cannot be downloaded, user needs to login")
        return True,subtitles_list[pos]['language_name'], ""
    link = client.get_link(content)
    
    log(__name__,'Got the link, wait %i seconds before download' % (wait_time))
    delay = wait_time
    if 'delay_cb' in globals():
        delay_cb(wait_time+2)
    else:
        for i in range(wait_time+1):
            line2 = 'Download will start in %i seconds' % (delay,)
            #xbmc.executebuiltin("XBMC.Notification(%s,%s,1000,%s)" % (__scriptname__,line2,os.path.join(__cwd__,'icon.png')))
            delay -= 1
            time.sleep(1)

    log(__name__,'Downloading subtitle zip')
    data = client.get_file2(link)
    log(__name__,'Saving to file %s' % zip_subs)
    zip_file = open(zip_subs,'wb')
    zip_file.write(data)
    zip_file.close()
    return True,subtitles_list[pos]['language_name'], "zip" #standard output

def lang_titulky2xbmclang(lang):
    if lang == 'CZ': return 'Czech'
    if lang == 'SK': return 'Slovak'
    return 'English'

def lang_xbmclang2titulky(lang):
    if lang == 'Czech': return 'CZ'
    if lang == 'Slovak': return 'SK'
    return 'EN'

def get_episode_season(episode,season):
    return 'S%sE%s' % (get2DigitStr(int(season)),get2DigitStr(int(episode)))
def get2DigitStr(number):
    if number>9:
        return str(number)
    else:
        return '0'+str(number)

def lang2_opensubtitles(lang):
    lang = lang_titulky2xbmclang(lang)
    return languageTranslate(lang,0,2)

class TitulkyClient(object):

    def __init__(self):
        self.cookies = {}
        self.server_url = 'https://www.titulky.com'
        opener = urllib.request.build_opener(HTTPCookieProcessor(http_cookiejar.LWPCookieJar()))
        opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
        install_opener(opener)

    def login(self, username, password):
            log(__name__, 'Logging in to Titulky.com')
            login_postdata = ({'Login': username, 'Password': password, 'foreverlog': '1', 'Detail2': ''})
            data = urllib.parse.urlencode(login_postdata).encode("utf-8")
            req = urllib.request.Request(self.server_url + '/index.php')
            with urllib.request.urlopen(req,data=data) as f:
                response = f.read().decode('utf-8')
                print(response)
            #request = Request(self.server_url + '/index.php', login_postdata)
            #response = urlopen(request)
            log(__name__, 'Got response')
            if response.find('BadLogin') > -1:
                return False

            log(__name__, 'Storing Cookies')
            #self.cookies = {}
            #self.cookies['CRC'] = re.search('CRC=(\S+);', response.headers.get('Set-Cookie'), re.IGNORECASE | re.DOTALL).group(1)
            #self.cookies['LogonLogin'] = re.search('LogonLogin=(\S+);', response.headers.get('Set-Cookie'), re.IGNORECASE | re.DOTALL).group(1)
            #self.cookies['LogonId'] = re.search('LogonId=(\S+);', response.headers.get('Set-Cookie'), re.IGNORECASE | re.DOTALL).group(1)

            #return True

    def search_subtitles(self, file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3 ):
        br_index = title.find('(')
        if br_index > -1:
            title = title[:br_index]
        title = title.strip()
        session_id = "0"
        url = self.server_url + '/index.php?' + urllib3.request.urlencode({'Fulltext': title, 'FindUser': ''})
        print(("url", url))
        if not (tvshow == None or tvshow == ''):
            title2 = tvshow + ' ' + get_episode_season(episode, season)
            url = self.server_url + '/index.php?' + urllib3.request.urlencode({'Fulltext': title2, 'FindUser': ''})
        try:
            size = getFileSize(file_original_path)
            file_size = '%.2f' % (float(size) / (1024 * 1024))
        except:
            file_size = '-1'
        log(__name__, 'Opening %s' % (url))
        #response = urlopen(req)
        #content = response.read().decode('utf-8')
        #response.close()
        log(__name__,'Done')
        http = urllib3.PoolManager()
        r = http.request('GET', url)
        content = r.data.decode('utf-8')
        
        subtitles_list = []
        max_downloads = 1
        log(__name__, 'Searching for subtitles')
        for row in re.finditer('<tr class=\"r(.+?)</tr>', content, re.IGNORECASE | re.DOTALL):
            item = {}
            log(__name__, 'New subtitle found')
            try:
                item['ID'] = re.search('[^<]+<td[^<]+<a href=\"[\w-]+-(?P<data>\d+).htm\"', row.group(1), re.IGNORECASE | re.DOTALL).group('data')
                item['title'] = re.search('[^<]+<td[^<]+<a[^>]+>(<div[^>]+>)?(?P<data>[^<]+)', row.group(1), re.IGNORECASE | re.DOTALL).group('data')
                item['sync'] = ''
                sync_found = re.search('((.+?)</td>)[^>]+>[^<]*<a(.+?)title=\"(?P<data>[^\"]+)', row.group(1), re.IGNORECASE | re.DOTALL)
                if sync_found:
                    item['sync'] = sync_found.group('data')
                item['tvshow'] = re.search('((.+?)</td>){2}[^>]+>(?P<data>[^<]+)', row.group(1), re.IGNORECASE | re.DOTALL).group('data')
                item['year'] = re.search('((.+?)</td>){3}[^>]+>(?P<data>[^<]+)', row.group(1), re.IGNORECASE | re.DOTALL).group('data')
                item['downloads'] = re.search('((.+?)</td>){4}[^>]+>(?P<data>[^<]+)', row.group(1), re.IGNORECASE | re.DOTALL).group('data')
                item['lang'] = re.search('((.+?)</td>){5}[^>]+><img alt=\"(?P<data>\w{2})\"', row.group(1), re.IGNORECASE | re.DOTALL).group('data')
                item['numberOfDiscs'] = re.search('((.+?)</td>){6}[^>]+>(?P<data>[^<]+)', row.group(1), re.IGNORECASE | re.DOTALL).group('data')
                #item['size'] = re.search('((.+?)</td>){7}[^>]+>(?P<data>[\d\.]+)', row.group(1), re.IGNORECASE | re.DOTALL).group('data')
            except:
                log(__name__, 'Exception when parsing subtitle, all I got is  %s' % str(item))
                continue
            if item['sync'] == '': # if no sync info is found, just use title instead of None
                item['filename'] = item['title']
            else:
                item['filename'] = item['sync']
                item['language_flag'] = "flags/%s.gif" % (lang2_opensubtitles(item['lang']))
                sync = False
                
            if not item['sync'] == '': 
                log(__name__, 'found sync : filename match')
                sync = True
  
            #if file_size == item['size']:
                #log(__name__, 'found sync : size match')
                #sync = True
                #item['sync'] = sync

            try:
               downloads = int(item['downloads'])
               if downloads > max_downloads:
                    max_downloads = downloads
            except:
                  downloads = 0
             
                  item['downloads'] = downloads

            if year:
                if not item['year'] == year:
                 log(__name__, 'year does not match, ignoring %s' % str(item))
                 continue
            lang = lang_titulky2xbmclang(item['lang'])

            item['language_name'] = lang
            item['mediaType'] = 'mediaType'
            item['rating'] = '0'

            if lang in [lang1, lang2, lang3]:
                subtitles_list.append(item)

            else:
                log(__name__, 'language does not match, ignoring %s' % str(item))
        # computing ratings is based on downloads
        for subtitle in subtitles_list:
            subtitle['rating'] = str((int(subtitle['downloads']) * 10 / max_downloads))
        return subtitles_list

    def get_cannot_download_error(self, content):
        if content.find('CHYBA') > -1:
            return True

    def get_waittime(self, content):
        for matches in re.finditer('CountDown\((\d+)\)', content, re.IGNORECASE | re.DOTALL):
            return int(matches.group(1))

    def get_link(self, content):
        for matches in re.finditer('<a.+id=\"downlink\" href="([^\"]+)\"', content, re.IGNORECASE | re.DOTALL):
            return str(matches.group(1))

    def get_control_image(self, content):
        for matches in re.finditer('\.\/(captcha\/captcha\.php)', content, re.IGNORECASE | re.DOTALL):
            return '/' + str(matches.group(1))
        return None

    def get_file(self, link):
        url = self.server_url + link
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
        log(__name__, 'Done')
        response.close()
        return content

    def get_file2(self, link):
        url = self.server_url + link
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
        log(__name__, 'Done')
        response.close()
        return content
                       
    def get_subtitle_page2(self, content, code, id):
        url = 'https://www.titulky.com/idown.php'
        post_data = ({ 'downkod': code, 'titulky': id, 'zip': 'z', 'securedown': '2', 'histstamp': '', 'T': '2.01-%s'%timestamp })
        data = urllib.parse.urlencode(post_data).encode("utf-8")
        req = request.Request(url,data)
        req = self.add_cookies_into_header(req)
        log(__name__,'Opening %s POST:%s' % (url,str(post_data)))
        response = request.urlopen(req) 
        content = response.read().decode('utf-8')
        #print(content)
        log(__name__, 'Done')
        #response.close()
        return content                                                                            

    def get_subtitle_page(self, id):                                                                                               
        url = self.server_url + '/idown.php?' + urlencode({'R': timestamp, 'titulky': id, 'zip': 'z', 'histstamp': '', 'T': '2.01-%s'%timestamp})
        #print(url)
        log(__name__, 'Opening %s' % (url))
        req = Request(url)
        req = self.add_cookies_into_header(req)
        response = urlopen(req)
        content = response.read().decode('utf-8')
        log(__name__, 'Done')
        response.close()
        return content

    def add_cookies_into_header(self, request):
        cookies_string = ""
        try:
            cookies_string = "LogonLogin=" + self.cookies['LogonLogin'] + "; "
            cookies_string += "LogonId=" + self.cookies['LogonId'] + "; "
            cookies_string += "CRC=" + self.cookies['CRC']
        except KeyError:
            pass
        if 'PHPSESSID' in self.cookies:
            cookies_string += "; PHPSESSID=" + self.cookies['PHPSESSID']
        request.add_header('Cookie', cookies_string)
        return request
