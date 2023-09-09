# -*- coding: UTF-8 -*-
from __future__ import absolute_import
import os
import re

from ..seeker import SubtitlesDownloadError, SubtitlesErrors
from six.moves import http_cookiejar
from six.moves import urllib

from ..utilities import log


main_url = "http://www.italiansubs.net/"

#====================================================================================================================
# Regular expression patterns
#====================================================================================================================

#<input type="hidden" name="return" value="aHR0cDovL3d3dy5pdGFsaWFuc3Vicy5uZXQv" /><input type="hidden" name="c10b48443ee5730c9b5a0927736bd09f" value="1" />
unique_pattern = '<input type="hidden" name="return" value="([^\n\r\t ]+?)" /><input type="hidden" name="([^\n\r\t ]+?)" value="([^\n\r\t ]+?)" />'
#<a href="http://www.italiansubs.net/index.php?option=com_remository&amp;Itemid=6&amp;func=select&amp;id=1170"> Castle</a>
show_pattern = '<a href="http://www\.italiansubs\.net/(index.php\?option=com_remository&amp;Itemid=\d+&amp;func=select&amp;id=[^\n\r\t ]+?)"> %s</a>'
#href="http://www.italiansubs.net/index.php?option=com_remository&amp;Itemid=6&amp;func=select&amp;id=1171"> Stagione 1</a>
season_pattern = '<a href="http://www\.italiansubs\.net/(index.php\?option=com_remository&amp;Itemid=\d+?&amp;func=select&amp;id=[^\n\r\t ]+?)"> Stagione %s</a>'
#<img src='http://www.italiansubs.net/components/com_remository/images/folder_icons/category.gif' width=20 height=20><a name="1172"><a href="http://www.italiansubs.net/index.php?option=com_remository&amp;Itemid=6&amp;func=select&amp;id=1172"> 720p</a>
category_pattern = '<img src=\'http://www\.italiansubs\.net/components/com_remository/images/folder_icons/category\.gif\' width=20 height=20><a name="[^\n\r\t ]+?"><a href="http://www\.italiansubs\.net/(index.php\?option=com_remository&amp;Itemid=\d+?&amp;func=select&amp;id=[^\n\r\t ]+?)"> ([^\n\r\t]+?)</a>'
#<a href="http://www.italiansubs.net/index.php?option=com_remository&amp;Itemid=6&amp;func=fileinfo&amp;id=7348">Dexter 3x02</a>
subtitle_pattern = '<a href="http://www\.italiansubs\.net/(index.php\?option=com_remository&amp;Itemid=\d+?&amp;func=fileinfo&amp;id=([^\n\r\t ]+?))">(%s %sx%02d.*?)</a>'
#<a href='http://www.italiansubs.net/index.php?option=com_remository&amp;Itemid=6&amp;func=download&amp;id=7228&amp;chk=5635630f675375afbdd6eec317d8d688&amp;no_html=1'>
subtitle_download_pattern = '<a href=\'http://www\.italiansubs\.net/(index\.php\?option=com_remository&amp;Itemid=\d+?&amp;func=download&amp;id=%s&amp;chk=[^\n\r\t ]+?&amp;no_html=1\')>'


#====================================================================================================================
# Functions
#====================================================================================================================

def geturl(url):
    log(__name__, " Getting url: %s" % (url))
    try:
        response = urllib.request.urlopen(url)
        content = response.read()
    except:
        log(__name__, " Failed to get url:%s" % (url))
        content = None
    return(content)


def login(username, password):
    log(__name__, " Logging in with username '%s' ..." % (username))
    content = geturl(main_url + 'index.php')
    if content is not None:
        match = re.search('logouticon.png', content, re.IGNORECASE | re.DOTALL)
        if match:
            return 1
        else:
            match = re.search(unique_pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return_value = match.group(1)
                unique_name = match.group(2)
                unique_value = match.group(3)
                login_postdata = urllib.parse.urlencode({'username': username, 'passwd': password, 'remember': 'yes', 'Submit': 'Login', 'remember': 'yes', 'option': 'com_user', 'task': 'login', 'silent': 'true', 'return': return_value, unique_name: unique_value})
                cj = http_cookiejar.CookieJar()
                my_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
                my_opener.addheaders = [('Referer', main_url)]
                urllib.request.install_opener(my_opener)
                request = urllib.request.Request(main_url + 'index.php', login_postdata)
                response = urllib.request.urlopen(request).read()
                match = re.search('logouticon.png', response, re.IGNORECASE | re.DOTALL)
                if match:
                    return 1
                else:
                    return 0
    else:
        return 0


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack): #standard input
    subtitles_list = []
    msg = ""
    if len(tvshow) > 0:
        italian = 0
        content = geturl(main_url + 'index.php?option=com_remository&Itemid=6')
        if content is not None:
            match = re.search(show_pattern % tvshow, content, re.IGNORECASE | re.DOTALL)
            if match is None and tvshow[-1] == ")":
                log(__name__, " Year Bug? '%s'" % tvshow)
                tvshow = tvshow[:-7]
                match = re.search(show_pattern % tvshow, content, re.IGNORECASE | re.DOTALL)
            if match:
                log(__name__, " Tv show '%s' found" % tvshow)
                content = geturl(main_url + match.group(1))
                if content is not None:
                    match = re.search(season_pattern % season, content, re.IGNORECASE | re.DOTALL)
                    if match:
                        log(__name__, " Season %s of tv show '%s' found" % (season, tvshow))
                        category = 'normal'
                        categorypage = match.group(1)
                        content = geturl(main_url + categorypage)
                        if content is not None:
                            for matches in re.finditer(subtitle_pattern % (tvshow, int(season), int(episode)), content, re.IGNORECASE | re.DOTALL):
                                filename = matches.group(3)
                                id = matches.group(2)
                                log(__name__, " Adding '%s' to list of subtitles" % filename)
                                subtitles_list.append({'rating': '0', 'no_files': 1, 'filename': filename, 'sync': False, 'id': id, 'link': categorypage, 'language_flag': 'flags/it.gif', 'language_name': 'Italian'})
                            for matches in re.finditer(category_pattern, content, re.IGNORECASE | re.DOTALL):
                                categorypage = matches.group(1)
                                category = matches.group(2)
                                log(__name__, " Page for category '%s' found" % category)
                                content = geturl(main_url + categorypage)
                                if content is not None:
                                    for matches in re.finditer(subtitle_pattern % (tvshow, int(season), int(episode)), content, re.IGNORECASE | re.DOTALL):
                                        id = matches.group(2)
                                        filename = matches.group(3)
                                        log(__name__, " Adding '%s (%s)' to list of subtitles" % (filename, category))
                                        subtitles_list.append({'rating': '0', 'no_files': 1, 'filename': "%s (%s)" % (filename, category), 'sync': False, 'id': id, 'link': categorypage, 'language_flag': 'flags/it.gif', 'language_name': 'Italian'})
                    else:
                        log(__name__, " Season %s of tv show '%s' not found" % (season, tvshow))
                        msg = "Season %s of tv show '%s' not found" % (season, tvshow)
            else:
                log(__name__, " Tv show '%s' not found." % tvshow)
                msg = "Tv show '%s' not found" % tvshow
    else:
        msg = "Won't work, Itasa is only for tv shows."
    return subtitles_list, "", msg #standard output


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id): #standard input
    username = settings_provider.getSetting("ITuser")
    password = settings_provider.getSetting("ITpass")
    if username == "" or password == "":
        raise SubtitlesDownloadError(SubtitlesErrors.NO_CREDENTIALS_ERROR, "not provided credentials")
    if login(username, password):
        log(__name__, " Login successful")
        id = subtitles_list[pos]["id"]
        link = subtitles_list[pos]["link"]
        content = geturl(main_url + link)
        match = re.search(subtitle_download_pattern % id, content, re.IGNORECASE | re.DOTALL)
        if match:
            language = subtitles_list[pos]["language_name"]
            log(__name__, " Fetching subtitles using url %s" % (main_url + match.group(1)))
            content = geturl(main_url + match.group(1))
            if content is not None:
                header = content[:4]
                if header == 'Rar!':
                    local_tmp_file = os.path.join(tmp_sub_dir, "undertexter.rar")
                    packed = True
                elif header == 'PK':
                    local_tmp_file = os.path.join(tmp_sub_dir, "undertexter.zip")
                    packed = True
                else: # never found/downloaded an unpacked subtitles file, but just to be sure ...
                    local_tmp_file = os.path.join(tmp_sub_dir, "undertexter.srt") # assume unpacked subtitels file is an '.srt'
                    packed = False
                subs_file = local_tmp_file
                log(__name__, " Saving subtitles to '%s'" % (local_tmp_file))
                try:
                    local_file_handle = open(local_tmp_file, "wb")
                    local_file_handle.write(content)
                    local_file_handle.close()
                except:
                    log(__name__, " Failed to save subtitles to '%s'" % (local_tmp_file))
                return packed, language, subs_file #standard output
    log(__name__, " Login to Itasa failed. Check your username/password at the addon configuration.")
    raise SubtitlesDownloadError(SubtitlesErrors.INVALID_CREDENTIALS_ERROR, "provided invalid credentials")
