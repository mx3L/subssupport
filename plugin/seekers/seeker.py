# -*- coding: UTF-8 -*-
#################################################################################
#
#    This module is part of SubsSupport plugin
#    Coded by mx3L (c) 2014
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the  
#    GNU General Public License for more details.
#
#################################################################################
from __future__ import absolute_import
import socket
import sys
import time
import traceback

from .utilities import langToCountry, languageTranslate, SimpleLogger, toString


import six


class SubtitlesErrors:
    UNKNOWN_ERROR = 0
    INVALID_CREDENTIALS_ERROR = 1
    NO_CREDENTIALS_ERROR = 2
    CAPTCHA_RETYPE_ERROR = 3
    TIMEOUT_ERROR = 4


class BaseSubtitlesError(Exception):
    def __init__(self, code=None, msg=""):
        self.code = code
        self.msg = msg
        self.provider = None

    def __str__(self):
        if self.provider:
            return "{0} - {1}".format(self.provider, self.msg)
        return "{0}".format(self.msg)


class SubtitlesSearchError(BaseSubtitlesError):
    """Raised when subtitles search error occurs"""


class SubtitlesDownloadError(BaseSubtitlesError):
    """Raised when subtitles download error occurs"""


class SettingsProvider(object):
    def __init__(self, default_settings, settings=None, *args, **kwargs):
        self.settings = default_settings
        if settings:
            self.settings.update(settings)

    def getSetting(self, key):
        if isinstance(self.settings[key], dict):
            if not 'value' in self.settings[key]:
                if not 'default' in self.settings[key]:
                    raise Exception("Invalid settings provided, missing 'value/default' entry")
                return self.settings[key]['default']
            return self.settings[key]['value']
        return self.settings[key]

    def setSetting(self, key, value):
        if not isinstance(self.settings[key], dict):
            self.settings[key] = {}
        self.settings[key]['value'] = value


class BaseSeeker(object):

    def __init__(self, tmp_path, download_path, settings=None, settings_provider=None, logo=None, *args, **kwargs):
        self.log = SimpleLogger(self.__class__.__name__, log_level=SimpleLogger.LOG_INFO)
        assert hasattr(self, 'id') and isinstance(self.id, six.string_types), 'you have to provide class variable: "id" with provider id'
        assert hasattr(self, 'provider_name') and isinstance(self.provider_name, six.string_types), 'you have to provide class variable: "provider_name" with provider name'
        assert hasattr(self, 'supported_langs') and isinstance(self.supported_langs, list), 'you have to provide class variable: "supported_langs" with list of supported langs'
        if not hasattr(self, 'description'):
            self.description = ""
        if not hasattr(self, 'tvshow_search'):
            self.tvshow_search = True
        if not hasattr(self, 'movie_search'):
            self.movie_search = True
        if not hasattr(self, 'default_settings'):
            self.default_settings = {}
        self.tmp_path = tmp_path
        self.download_path = download_path
        if settings_provider is not None:
            self.log.debug('using custom settings_provider - %s' % settings_provider)
            self.settings_provider = settings_provider
        elif settings is not None:
            self.log.debug('using default settings_provider with custom settings')
            self.settings_provider = SettingsProvider(self.default_settings, settings)
        else:
            self.log.debug('using default settings_provider with default settings')
            self.settings_provider = SettingsProvider(self.default_settings)
        self.logo = logo
        # if seeker is not going to work(i.e. missing python libs), you can assign to error
        # Exception which caused this issue, when tuple is used
        # then you can use it like  (Exception, error_msg)
        # when error is not None then seeker is not working and cannot be used
        if not hasattr(self, 'error'):
            self.error = None

    def __str__(self):
        return "[" + self.id + "]"

    def search(self, title=None, filepath=None, langs=None, season=None, episode=None, tvshow=None, year=None):
        """
        returns found subtitles dict
        {'list': [{'filename':str,'language_name':str,'sync':bool},{..},..], 'provider':provider instance}

        raises SubtitlesSearchError
        """
        assert title is not None or filepath is not None or tvshow is not None, 'title or filepath needs to be provided'
        self.log.info("search -  title: %s, filepath: %s, langs: %s, season: %s, episode: %s, tvshow: %s, year: %s" % (
                    str(title), str(filepath), str(langs), str(season), str(episode), str(tvshow), str(year)))
        start_time = time.time()
        if langs is None:
            langs = []
        valid_langs = langs[:]
        for l in langs:
            if l not in self.supported_langs:
                valid_langs.remove(l)
                self.log.info('this language is not supported by this provider - "%s"!' % languageTranslate(l, 2, 0))
        try:
            subtitles = self._search(title, filepath, valid_langs, season, episode, tvshow, year)
        except socket.timeout as e:
            self.log.error("timeout error occured: %s" % (str(e)))
            e = SubtitlesSearchError(SubtitlesErrors.TIMEOUT_ERROR, "timeout!")
            e.provider = self.id
            raise
        except SubtitlesSearchError as e:
            self.log.error("search error occured: %s" % str(e))
            e.provider = self.id
            raise e
        except Exception as e:
            self.log.error("unknown search error occured: %s" % str(e))
            err = SubtitlesSearchError(SubtitlesErrors.UNKNOWN_ERROR, str(e))
            err.provider = self.id
            err.wrapped_error = e
            raise err
        subtitles['id'] = self.id
        subtitles['time'] = time.time() - start_time
        subtitles['params'] = {
                'title': title,
                'filepath': filepath,
                'langs': langs,
                'year': year,
                'tvshow': tvshow,
                'season': season,
                'episode': episode}
        subtitles.setdefault('list', [])
        self.log.info("search finished, found %d subtitles in %.2fs" % (len(subtitles['list']), subtitles['time']))
        return subtitles

    def _search(self, title, filepath, langs, season, episode, tvshow, year):
        """
        implement your search logic
        """
        return {'list': [{'filename': '', 'language_name': '', 'size': '', 'sync': ''}, ]}

    def download(self, subtitles, selected_subtitle, path=None):
        """
        downloads and returns path to subtitles file(can be compressed)

        @param subtitles: subtitles list returned by search function
        @param selected_subtitle: subtitle from subtitles list which will be downloaded
        @param path: if provided then this path will be used as download path instead
                                      of default download path

        raises SubtitlesDownloadError
        """
        self.log.info("download - selected_subtitle: %s, path: %s" % (toString(selected_subtitle['filename']), toString(path)))
        try:
            compressed, lang, filepath = self._download(subtitles, selected_subtitle, toString(path))
        except SubtitlesDownloadError as e:
            self.log.error("download error occured: %s" % str(e))
            e.provider = self.id
            raise e
        except Exception:
            exc_value, exc_traceback = sys.exc_info()[1:]
            self.log.error("unknown download error occured: %s" % str(exc_value))
            self.log.error("traceback: \n%s" % "".join(traceback.format_tb(exc_traceback)))
            err = SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, str(exc_value))
            err.provider = self.id
            err.wrapped_error = exc_value
            raise err

        self.log.info("download finished, compressed: %s, lang: %s, filepath:%s" % (toString(compressed), toString(lang), toString(filepath)))
        return compressed, lang, filepath

    def _download(self, subtitles, selected_subtitle, path):
        """
        implement your download logic
        """
        return False, "", ""
