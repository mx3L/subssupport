# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
from ..utilities import log, hashFile
from .os_utilities import OSDBServer
import six


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):  # standard input
    hash_search = False
    enabled = settings_provider.getSetting("enabled")
    user_agent = settings_provider.getSetting("user_agent")
    if len(tvshow) > 0:  # TvShow
        OS_search_string = ("%s S%.2dE%.2d" % (tvshow,
                                               int(season),
                                               int(episode),)
                                              ).replace(" ", "+")
    else:  # Movie or not in Library
        if str(year) == "":  # Not in Library
            title, year = title, ""  # xbmc.getCleanMovieTitle( title )
        else:  # Movie in Library
            year = year
            title = title
        OS_search_string = title.replace(" ", "+")
    log(__name__, "Search String [ %s ]" % (OS_search_string,))

    if set_temp:
        hash_search = False
        file_size = "000000000"
        SubHash = "000000000000"
    else:
        try:
            file_size, SubHash = hashFile(file_original_path, rar)
            log(__name__, "xbmc module hash and size")
            hash_search = True
        except:
            file_size = ""
            SubHash = ""
            hash_search = False

    if file_size != "" and SubHash != "":
        log(__name__, "File Size [%s]" % file_size)
        log(__name__, "File Hash [%s]" % SubHash)

    log(__name__, "Search by hash and name %s" % (os.path.basename(file_original_path),))
    subtitles_list, msg = OSDBServer(user_agent).searchsubtitles(OS_search_string, lang1, lang2, lang3, hash_search, SubHash, file_size)

    return subtitles_list, "", msg  # standard output


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):  # standard input
    user_agent = settings_provider.getSetting("user_agent")
    destination = os.path.join(six.ensure_str(tmp_sub_dir), "%s.srt" % subtitles_list[pos]["ID"])
    result = OSDBServer(user_agent).download(subtitles_list[pos]["ID"], destination, session_id)
    if not result:
        import urllib
        urllib.urlretrieve(subtitles_list[pos]["link"], zip_subs)

    language = subtitles_list[pos]["language_name"]
    return not result, language, destination  # standard output
