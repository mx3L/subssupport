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

import os
import shutil
import socket
import threading
import time
import traceback
import zipfile

from seekers import SubtitlesDownloadError, SubtitlesSearchError, \
    SubtitlesErrors, TitulkyComSeeker, EdnaSeeker, SerialZoneSeeker, \
    OpenSubtitlesSeeker, PodnapisiSeeker, SubsceneSeeker, SubtitlesGRSeeker, \
    ItasaSeeker, TitloviSeeker
from seekers.seeker import BaseSeeker
from seekers.utilities import languageTranslate, langToCountry, \
    getCompressedFileType, detectSearchParams
from utils import SimpleLogger, toString



SUBTITLES_SEEKERS = []
SUBTITLES_SEEKERS.append(TitulkyComSeeker)
SUBTITLES_SEEKERS.append(EdnaSeeker)
SUBTITLES_SEEKERS.append(SerialZoneSeeker)
SUBTITLES_SEEKERS.append(OpenSubtitlesSeeker)
SUBTITLES_SEEKERS.append(PodnapisiSeeker)
SUBTITLES_SEEKERS.append(SubsceneSeeker)
SUBTITLES_SEEKERS.append(SubtitlesGRSeeker)
SUBTITLES_SEEKERS.append(ItasaSeeker)
SUBTITLES_SEEKERS.append(TitloviSeeker)


class ErrorSeeker(BaseSeeker):
    def __init__(self, wseeker_cls, *args, **kwargs):
        self.id = wseeker_cls.id
        self.error = wseeker_cls.error
        self.provider_name = wseeker_cls.provider_name
        self.supported_langs = wseeker_cls.supported_langs
        self.description = getattr(wseeker_cls, 'description', "")
        self.tvshow_search = getattr(wseeker_cls, 'tvshow_search', True)
        self.movie_search = getattr(wseeker_cls, 'movie_search', True)
        self.default_settings = getattr(wseeker_cls, 'default_settings', dict())
        BaseSeeker.__init__(self, *args, **kwargs)
        
    def close(self):
        pass


class SubsSeeker(object):
    SUBTILES_EXTENSIONS = ['.srt', '.sub']

    def __init__(self, download_path, tmp_path, captcha_cb, delay_cb, message_cb, settings=None, settings_provider_cls=None, settings_provider_args=None, debug=False, providers=None):
        self.log = SimpleLogger(self.__class__.__name__, log_level=debug and SimpleLogger.LOG_DEBUG or SimpleLogger.LOG_INFO)
        self.download_path = toString(download_path)
        self.tmp_path = toString(tmp_path)
        self.seekers = []
        providers = providers or SUBTITLES_SEEKERS
        for seeker in providers:
            provider_id = seeker.id
            default_settings = seeker.default_settings
            default_settings['enabled'] = {'type':'yesno', 'default':True, 'label':'Enabled', 'pos':-1}
            if settings_provider_cls is not None:
                settings = None
                settings_provider = settings_provider_cls(provider_id, default_settings, settings_provider_args)
                if hasattr(seeker, 'error') and seeker.error is not None:
                    settings_provider.setSetting('enabled', False)
                    self.seekers.append(ErrorSeeker(seeker, tmp_path, download_path, settings, settings_provider, captcha_cb, delay_cb, message_cb))
                else:
                    self.seekers.append(seeker(tmp_path, download_path, settings, settings_provider, captcha_cb, delay_cb, message_cb))
            elif settings is not None and provider_id in settings:
                settings_provider = None
                if hasattr(seeker, 'error') and seeker.error is not None:
                    self.seekers.append(ErrorSeeker(seeker, tmp_path, download_path, settings, settings_provider, captcha_cb, delay_cb, message_cb))
                else:
                    self.seekers.append(seeker(tmp_path, download_path, settings[provider_id], settings_provider, captcha_cb, delay_cb, message_cb))
            else:
                settings = None
                settings_provider = None
                if hasattr(seeker, 'error') and seeker.error is not None:
                    self.seekers.append(ErrorSeeker(seeker, tmp_path, download_path, settings, settings_provider, captcha_cb, delay_cb, message_cb))
                else:
                    self.seekers.append(seeker(tmp_path, download_path, settings, settings_provider, captcha_cb, delay_cb, message_cb))

    def getSubtitlesSimple(self, updateCB=None, title=None, filepath=None, langs=None):
        title, year, tvshow, season, episode = detectSearchParams(title or filepath)
        seekers = self.getProviders(langs)
        return self.getSubtitles(seekers, updateCB, title, filepath, langs, year, tvshow, season, episode)

    def getSubtitles(self, providers, updateCB=None, title=None, filepath=None, langs=None, year=None, tvshow=None, season=None, episode=None, timeout=10):
        self.log.info('getting subtitles list - title: %s, filepath: %s, year: %s, tvshow: %s, season: %s, episode: %s' % (
            toString(title), toString(filepath), toString(year), toString(tvshow), toString(season), toString(episode)))
        subtitlesDict = {}
        threads = []
        socket.setdefaulttimeout(timeout)
        lock = threading.Lock()
        if len(providers) == 1:
            provider = providers[0]
            if isinstance(provider, basestring):
                provider = self.getProvider(providers[0])
            if provider.error is not None:
                self.log.debug("provider '%s' has 'error' flag set, skipping...", provider)
                return subtitlesDict
            else:
                self._searchSubtitles(lock, subtitlesDict, updateCB, provider, title, filepath, langs, season, episode, tvshow, year)
        else:
            for provider in providers:
                if isinstance(provider, basestring):
                    provider = self.getProvider(provider)
                if provider.error is not None:
                    self.log.debug("provider '%s' has 'error' flag set, skipping...", provider)
                else:
                    threads.append(threading.Thread(target=self._searchSubtitles, args=(lock, subtitlesDict, updateCB, provider, title, filepath, langs, season, episode, tvshow, year)))
            for t in threads:
                t.setDaemon(True)
                t.start()
            working = True
            while working:
                working = False
                time.sleep(0.5)
                for t in threads:
                    working = working or t.is_alive()
        socket.setdefaulttimeout(socket.getdefaulttimeout())
        return subtitlesDict

    def getSubtitlesList(self, subtitles_dict, provider=None, langs=None, synced=False, nonsynced=False):
        subtitles_list = []
        if provider and provider in subtitles_dict:
            subtitles_list = subtitles_dict[provider]['list']
            for sub in subtitles_list:
                if 'provider' not in sub:
                    sub['provider'] = provider
                if 'country' not in sub:
                    sub['country'] = langToCountry(languageTranslate(sub['language_name'], 0, 2))
        else:
            for provider in subtitles_dict:
                provider_list = subtitles_dict[provider]['list']
                subtitles_list += provider_list
                for sub in provider_list:
                    if 'provider' not in sub:
                        sub['provider'] = provider
                    if 'country' not in sub:
                        sub['country'] = langToCountry(languageTranslate(sub['language_name'], 0, 2))
        if synced:
            subtitles_list = filter(lambda x:x['sync'], subtitles_list)
        elif nonsynced:
            subtitles_list = filter(lambda x:not x['sync'], subtitles_list)
        if langs:
            subtitles_list = filter(lambda x:x['language_name'] in [languageTranslate(lang, 0, 2) for lang in langs])
        return subtitles_list

    def sortSubtitlesList(self, subtitles_list, langs=None, sort_langs=False, sort_rank=False, sort_sync=False, sort_provider=False):
        def sortLangs(x):
            for idx, lang in enumerate(langs):
                if languageTranslate(x['language_name'], 0, 2) == lang:
                    return idx
            return len(langs)
        if langs and sort_langs:
            return sorted(subtitles_list, key=sortLangs)
        if sort_provider:
            return sorted(subtitles_list, key=lambda x:x['provider'])
        if sort_rank:
            return subtitles_list
        if sort_sync:
            return sorted(subtitles_list, key=lambda x:x['sync'], reverse=True)
        return subtitles_list

    def downloadSubtitle(self, selected_subtitle, subtitles_dict, choosefile_cb, path=None, fname=None, overwrite_cb=None, settings=None):
        self.log.info('downloading subtitle "%s" with settings "%s"' % (selected_subtitle['filename'], toString(settings) or {}))
        if settings is None:
            settings = {}
        seeker = None
        for provider_id in subtitles_dict.keys():
            if selected_subtitle in subtitles_dict[provider_id]['list']:
                seeker = self.getProvider(provider_id)
                break
        if seeker is None:
            self.log.error('provider for "%s" subtitle was not found', selected_subtitle['filename'])
        lang, filepath = seeker.download(subtitles_dict[provider_id], selected_subtitle)[1:3]
        compressed = getCompressedFileType(filepath)
        if compressed:
            subfiles = self._unpack_subtitles(filepath, self.tmp_path)
        else:
            subfiles = [filepath]
        subfiles = [toString(s) for s in subfiles]
        if len(subfiles) == 0:
            self.log.error("no subtitles were downloaded!")
            raise SubtitlesDownloadError(msg="[error] no subtitles were downloaded")
        elif len(subfiles) == 1:
            self.log.debug('found one subtitle: "%s"', str(subfiles))
            subfile = subfiles[0]
        else:
            self.log.debug('found more subtitles: "%s"', str(subfiles))
            subfile = choosefile_cb(subfiles)
            if subfile is None:
                self.log.debug('no subtitles file choosed!')
                return
            self.log.debug('selected subtitle: "%s"', subfile)
        ext = os.path.splitext(subfile)[1]
        if ext not in self.SUBTILES_EXTENSIONS:
            ext = os.path.splitext(toString(selected_subtitle['filename']))[1]
            if ext not in self.SUBTILES_EXTENSIONS:
                ext = '.srt'
        if fname is None:
            filename = os.path.basename(subfile)
            save_as = settings.get('save_as', 'default')
            if save_as == 'version':
                self.log.debug('filename creating by "version" setting')
                filename = toString(selected_subtitle['filename'])
                if os.path.splitext(filename)[1] not in self.SUBTILES_EXTENSIONS:
                    filename = os.path.splitext(filename)[0] + ext
            elif save_as == 'video':
                self.log.debug('filename creating by "video" setting')
                videopath = toString(subtitles_dict[seeker.id]['params'].get('filepath'))
                filename = os.path.splitext(os.path.basename(videopath))[0] + ext
    
            if settings.get('lang_to_filename', False):
                lang_iso639_1_2 = toString(languageTranslate(lang, 0, 2))
                self.log.debug('appending language "%s" to filename', lang_iso639_1_2)
                filename, ext = os.path.splitext(filename)
                filename = "%s.%s%s" % (filename, lang_iso639_1_2, ext)
        else:
            self.log.debug('using provided filename')
            filename = toString(fname) + ext
        self.log.debug('filename: "%s"', filename)
        download_path = os.path.join(toString(self.download_path), filename)
        if path is not None:
            self.log.debug('using custom download path: "%s"', path)
            download_path = os.path.join(toString(path), filename)
        self.log.debug('download path: "%s"', download_path)
        if os.path.isfile(download_path) and overwrite_cb is not None:
            ret = overwrite_cb(download_path)
            if ret is None:
                self.log.debug('overwrite cancelled, returning temp path')
                return subfile
            elif not ret:
                self.log.debug('not overwriting, returning temp path')
                return subfile
            elif ret:
                self.log.debug('overwriting')
                try:
                    shutil.move(subfile, download_path)
                    return download_path
                except Exception as e:
                    self.log.error('moving "%s" to "%s" - %s' % (
                        os.path.split(subfile)[-2:], 
                        os.path.split(download_path)[-2:]), str(e))
                    return subfile
        try:
            shutil.move(subfile, download_path)
        except Exception as e:
            self.log.error('moving "%s" to "%s" - %s', (
                os.path.split(subfile)[-2:],
                os.path.split(download_path)[-2:]), str(e))
            return subfile
        return download_path

    def getProvider(self, provider_id):
        for s in self.seekers:
            if s.id == provider_id:
                return s

    def getProviders(self, langs=None, movie=True, tvshow=True):
        def check_langs(provider):
            for lang in provider.supported_langs:
                        if lang in langs:
                            return True
            return False

        providers = set()
        for provider in self.seekers:
            if provider.settings_provider.getSetting('enabled'):
                if langs:
                    if check_langs(provider):
                        if movie and provider.movie_search:
                            providers.add(provider)
                        if tvshow and provider.tvshow_search:
                            providers.add(provider)
                else:
                    if movie and provider.movie_search:
                        providers.add(provider)
                    if tvshow and provider.tvshow_search:
                        providers.add(provider)
        return list(providers)

    def _searchSubtitles(self, lock, subtitlesDict, updateCB, seeker, title, filepath, langs, season, episode, tvshow, year):
        try:
            subtitles = seeker.search(title, filepath, langs, season, episode, tvshow, year)
        except Exception as e:
            traceback.print_exc()
            with lock:
                subtitlesDict[seeker.id] = {'message':str(e), 'status':False, 'list':[]}
                if updateCB is not None:
                    updateCB(seeker.id, False, e)
        else:
            with lock:
                subtitles['status'] = True
                subtitlesDict[seeker.id] = subtitles
                if updateCB is not None:
                    updateCB(seeker.id, True, subtitles)

    def _unpack_subtitles(self, filepath, dest_dir, max_recursion=3):
        compressed = getCompressedFileType(filepath)
        if compressed == 'zip':
            self.log.debug('found "zip" archive, unpacking...')
            subfiles = self._unpack_zipsub(filepath, dest_dir)
        elif compressed == 'rar':
            self.log.debug('found "rar" archive, unpacking...')
            subfiles = self._unpack_rarsub(filepath, dest_dir)
        else:
            self.log.error('unsupported archive - %s', compressed)
            raise Exception(_("unsupported archive %s", compressed))
        for s in subfiles:
            if os.path.splitext(s)[1] in ('.rar', '.zip') and max_recursion > 0:
                subfiles.extend(self._unpack_subtitles(s, dest_dir, max_recursion - 1))
        subfiles = filter(lambda x:os.path.splitext(x)[1] in self.SUBTILES_EXTENSIONS, subfiles)
        return subfiles

    def _unpack_zipsub(self, zip_path, dest_dir):
        zf = zipfile.ZipFile(zip_path)
        namelist = zf.namelist()
        subsfiles = []
        for subsfn in namelist:
            if os.path.splitext(subsfn)[1] in self.SUBTILES_EXTENSIONS + ['.rar', '.zip']:
                filename = os.path.basename(subsfn)
                outfile = open(os.path.join(dest_dir, filename) , 'wb')
                outfile.write(zf.read(subsfn))
                outfile.flush()
                outfile.close()
                subsfiles.append(os.path.join(dest_dir, filename))
        return subsfiles

    def _unpack_rarsub(self, rar_path, dest_dir):
        try:
            import rarfile
        except ImportError:
            self.log.error('rarfile lib not available -  pip install rarfile')
            raise
        rf = rarfile.RarFile(rar_path)
        namelist = rf.namelist()
        subsfiles = []
        for subsfn in namelist:
            if os.path.splitext(subsfn)[1] in self.SUBTILES_EXTENSIONS + ['.rar', '.zip']:
                filename = os.path.basename(subsfn)
                outfile = open(os.path.join(dest_dir, filename) , 'wb')
                outfile.write(rf.read(subsfn))
                outfile.flush()
                outfile.close()
                subsfiles.append(os.path.join(dest_dir, filename))
        return subsfiles


