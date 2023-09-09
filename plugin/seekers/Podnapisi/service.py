# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os

from .pn_utilities import PNServer, OpensubtitlesHash, \
    calculateSublightHash, __scriptid__
from . import pn_utilities

from ..utilities import log, languageTranslate, normalizeString

from six.moves import urllib
import os, os.path
import subprocess
import requests , json, re,random,string,time,warnings
LINKFILE='/tmp/link'
LINKFILE2='/tmp/link2'



def Search(item):
    pn_server = PNServer()
    pn_server.Create()
    if item['temp']:
        item['OShash'] = "000000000000"
        item['SLhash'] = "000000000000"
    else:
        item['OShash'] = OpensubtitlesHash(item)
        item['SLhash'] = calculateSublightHash(item['file_original_path'])
        log(__scriptid__, "xbmc module OShash: %s, SLhash:%s" % (item['OShash'], item['SLhash']))

    log(__scriptid__, "Search for [%s] by name" % (os.path.basename(item['file_original_path']),))
    subtitles_list = pn_server.SearchSubtitlesWeb(item)
    return subtitles_list


def Download(params):
    pn_server = PNServer()
    pn_server.Create()
    url = pn_server.Download(params)
    return url


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):  # standard input
    pn_utilities.settings_provider = settings_provider
    item = {}
    item['temp'] = False
    item['rar'] = False
    item['year'] = year
    item['season'] = str(season)
    item['episode'] = str(episode)
    item['tvshow'] = tvshow
    item['title'] = title
    item['file_original_path'] = file_original_path
    item['3et_language'] = [languageTranslate(lang1, 0, 1), languageTranslate(lang2, 0, 1), languageTranslate(lang3, 0, 1)]

    if not item['title']:
        log(__scriptid__, "VideoPlayer.OriginalTitle not found")
        item['title'] = normalizeString(os.path.basename(item['file_original_path']))

    if item['episode'] and item['episode'].lower().find("s") > -1:  # Check if season is "Special"
        item['season'] = "0"  #
        item['episode'] = item['episode'][-1:]

    if (item['file_original_path'].find("http") > -1):
        item['temp'] = True

    elif (item['file_original_path'].find("rar://") > -1):
        item['rar'] = True
        item['file_original_path'] = os.path.dirname(item['file_original_path'][6:])

    elif (item['file_original_path'].find("stack://") > -1):
        stackPath = item['file_original_path'].split(" , ")
        item['file_original_path'] = stackPath[0][8:]

    return Search(item), "", ""


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):  # standard input
    pn_utilities.settings_provider = settings_provider
    params = subtitles_list[pos]
    # params["hash"] = params['OShash']
    params['match'] = params['sync']
    url = Download(params)
    if url != None:
        local_file = open(zip_subs, "w" + "b")
        #f = urllib.request.urlopen(url)
        subprocess.check_output(['wget', '-O', '/tmp/link2', url])    
        with open(LINKFILE2, 'rb') as f:
            local_file.write(f.read())
            local_file.close()
    language = params['language_name']
    return True, language, ""  # standard output
