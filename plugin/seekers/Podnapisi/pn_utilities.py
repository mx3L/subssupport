# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
import os
import zlib
from xml.dom import minidom

from ..seeker import SubtitlesDownloadError, SubtitlesErrors
from ..utilities import log, getFileSize, hashFile
import subprocess
import six
from six.moves import urllib
from six.moves import xmlrpc_client
import requests , json, re,random,string,time,warnings
from six.moves import xmlrpc_client
LINKFILE='/tmp/link'
LINKFILE2='/tmp/link2'
LINKFILE0='/tmp/link0'

try:
    # Python 2.6 +
    from hashlib import md5 as md5
    from hashlib import sha256
except ImportError:
    # Python 2.5 and earlier
    from md5 import md5
    from .sha256 import sha256

__scriptid__ = 'podnapisi'
__scriptname__ = 'XBMC Subtitles'
__version__ = '3.9.18'

USER_AGENT = "%s_v%s" % (__scriptname__.replace(" ", "_"), __version__)
SEARCH_URL = "http://www.podnapisi.net/ppodnapisi/search?tbsl=1&sK=%s&sJ=%s&sY=%s&sTS=%s&sTE=%s&sXML=1&lang=0"
SEARCH_URL_HASH = "http://www.podnapisi.net/ppodnapisi/search?tbsl=1&sK=%s&sJ=%s&sY=%s&sTS=%s&sTE=%s&sMH=%s&sXML=1&lang=0"

DOWNLOAD_URL = "http://www.podnapisi.net/subtitles/%s/download"


def OpensubtitlesHash(item):
    try:
        return hashFile(item["file_original_path"], item["rar"])[1]
    except Exception as e:
        log(__name__, "[OpensubtitlesHash] error: %s" % str(e))
        return "000000000000"


def dec2hex(n, l=0):
    # return the hexadecimal string representation of integer n
    s = "%X" % n
    if (l > 0):
        while len(s) < l:
            s = "0" + s
    return s


def invert(_basestring):
    asal = [_basestring[i:i + 2]
            for i in range(0, len(_basestring), 2)]
    asal.reverse()
    return ''.join(asal)


def calculateSublightHash(filename):

    DATA_SIZE = 128 * 1024

    if not os.path.exists(filename):
        return "000000000000"

    filesize = getFileSize(filename)

    if filesize < DATA_SIZE:
        return "000000000000"
    fileToHash = open(filename, 'r')

    sum = 0
    hash = ""

    number = 2
    sum = sum + number
    hash = hash + dec2hex(number, 2)

    sum = sum + (filesize & 0xff) + ((filesize & 0xff00) >> 8) + ((filesize & 0xff0000) >> 16) + ((filesize & 0xff000000) >> 24)
    hash = hash + dec2hex(filesize, 12)

    buffer = fileToHash.read(DATA_SIZE)
    begining = zlib.adler32(buffer) & 0xffffffff
    sum = sum + (begining & 0xff) + ((begining & 0xff00) >> 8) + ((begining & 0xff0000) >> 16) + ((begining & 0xff000000) >> 24)
    hash = hash + invert(dec2hex(begining, 8))

    fileToHash.seek(filesize / 2, 0)
    buffer = fileToHash.read(DATA_SIZE)
    middle = zlib.adler32(buffer) & 0xffffffff
    sum = sum + (middle & 0xff) + ((middle & 0xff00) >> 8) + ((middle & 0xff0000) >> 16) + ((middle & 0xff000000) >> 24)
    hash = hash + invert(dec2hex(middle, 8))

    fileToHash.seek(filesize - DATA_SIZE, 0)
    buffer = fileToHash.read(DATA_SIZE)
    end = zlib.adler32(buffer) & 0xffffffff
    sum = sum + (end & 0xff) + ((end & 0xff00) >> 8) + ((end & 0xff0000) >> 16) + ((end & 0xff000000) >> 24)
    hash = hash + invert(dec2hex(end, 8))

    fileToHash.close()
    hash = hash + dec2hex(sum % 256, 2)

    return hash.lower()


class PNServer:
    def Create(self):
        self.subtitles_list = []
        self.connected = False

    def Login(self):
        self.podserver = xmlrpc_client.Server('http://ssp.podnapisi.net:8000')
        init = self.podserver.initiate(USER_AGENT)
        hash = md5()
        hash.update(settings_provider.getSetting("PNpass"))
        self.password = sha256(str(hash.hexdigest()) + str(init['nonce'])).hexdigest()
        self.user = settings_provider.getSetting("PNuser")
        if init['status'] == 200:
            self.pod_session = init['session']
            auth = self.podserver.authenticate(self.pod_session, self.user, self.password)
            if auth['status'] == 300:
                log(__name__, "Authenticate [%s]" % "InvalidCredentials")
                raise SubtitlesDownloadError(SubtitlesErrors.INVALID_CREDENTIALS_ERROR, "provided invalid credentials")
                self.connected = False
            else:
                log(__scriptid__, "Connected to Podnapisi server")
                self.connected = True
        else:
            self.connected = False

    def SearchSubtitlesWeb(self, item):
        if len(item['tvshow']) > 1:
            item['title'] = item['tvshow']

        if (settings_provider.getSetting("PNmatch") == 'true'):
            url = SEARCH_URL_HASH % (item['title'].replace(" ", "+"),
                                     ','.join(item['3et_language']),
                                     str(item['year']),
                                     str(item['season']),
                                     str(item['episode']),
                                     '%s,sublight:%s,sublight:%s' % (item['OShash'], item['SLhash'], md5(item['SLhash']).hexdigest())
                                     )
        else:
            url = SEARCH_URL % (item['title'].replace(" ", "+"),
                                 ','.join(item['3et_language']),
                                 str(item['year']),
                                 str(item['season']),
                                 str(item['episode'])
                                )

        log(__scriptid__, "Search URL - %s" % (url))

        subtitles = self.fetch(url)

        if subtitles:
            for subtitle in subtitles:
                filename = self.get_element(subtitle, "release")
                if len(filename):
                    filename = filename.split()[0]

                if filename == "":
                    filename = self.get_element(subtitle, "title")

                hashMatch = False
                if (item['OShash'] in self.get_element(subtitle, "exactHashes") or
                   item['SLhash'] in self.get_element(subtitle, "exactHashes")):
                    hashMatch = True

                self.subtitles_list.append({'filename': filename,
                                            'link': self.get_element(subtitle, "pid"),
                                            'movie_id': self.get_element(subtitle, "movieId"),
                                            'season': self.get_element(subtitle, "tvSeason"),
                                            'episode': self.get_element(subtitle, "tvEpisode"),
                                            'language_name': self.get_element(subtitle, "languageName"),
                                            'language_flag': self.get_element(subtitle, "language"),
                                            'rating': str(int(float(self.get_element(subtitle, "rating"))) * 2),
                                            'sync': hashMatch,
                                            'hearing_imp': "n" in self.get_element(subtitle, "flags"),
                                            'hash': item['OShash'],
                                            })
            self.mergesubtitles()
        return self.subtitles_list

    def Download(self, params):
        print(params)
        subtitle_ids = []
        if (settings_provider.getSetting("PNmatch") == 'true' and params["hash"] != "000000000000"):
            self.Login()
            if params["match"] == "True":
                subtitle_ids.append(str(params["link"]))

            log(__scriptid__, "Sending match to Podnapisi server")
            result = self.podserver.match(self.pod_session, params["hash"], params["movie_id"], int(params["season"]), int(params["episode"]), subtitle_ids)
            if result['status'] == 200:
                log(__scriptid__, "Match successfuly sent")

        return DOWNLOAD_URL % str(params["link"])

    def get_element(self, element, tag):
        if element.getElementsByTagName(tag)[0].firstChild:
            return element.getElementsByTagName(tag)[0].firstChild.data
        else:
            return ""

    def fetch(self, url):
        subprocess.check_output(['wget', '-O', '/tmp/link', url])    
        with open(LINKFILE, 'r') as f:
            result = f.read()
            xmldoc = minidom.parseString(result)
            return xmldoc.getElementsByTagName("subtitle")

    def compare_columns(self, b, a):
        return cmp(b["language_name"], a["language_name"]) or cmp(a["sync"], b["sync"])

    def mergesubtitles(self):
        if(len(self.subtitles_list) > 0):      
            #self.subtitles_list.sort(key=lambda x: [not x['sync'], x['lang_index']])
            self.subtitles_list = sorted(self.subtitles_list, key=lambda x: [x['sync'], x['language_name']])

