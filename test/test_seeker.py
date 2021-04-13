import os
import sys
import socket
import time
import urllib2
import unittest
import shutil

test = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join (test, '..', 'plugin'))

from seekers.seeker import BaseSeeker, SubtitlesSearchError, SubtitlesDownloadError, SubtitlesErrors
from seek import SubsSeeker

def remove_files_in_dir(dirpath):
    for f in os.listdir(dirpath):
        fpath = os.path.join(dirpath, f)
        if os.path.isfile(fpath):
            os.remove(fpath)

def captcha_cb(self, url):
        print '[captcha_cb] visit url:"%s"\nre-type captcha:' % url
        print '[captcha_cb] not visiting just returning empty string'
        return ""

def message_cb(self, text):
    print '[message_cb] %s' % text

def delay_cb(self, seconds):
    print '[delay_cb] waiting for %d seconds' % seconds
    for i in xrange(seconds):
        print '[delay_cb] %d second'
        time.sleep(1)

def choosefile_cb(files):
    print '[choosefile_cb]'
    print '\n'.join(("%d. ) %s" % (idx, os.path.basename(file)) for idx, file in enumerate(files)))
    print '[choosefile_cb] selecting [0] - %s' % (os.path.basename(files[0]))
    return files[0]


class TimeoutSeeker(BaseSeeker):
    id = 'timeout'
    provider_name = 'timeoutSeeker'
    supported_langs = []

    def _search(self, title, filepath, langs, season, episode, tvshow, year):
        raise socket.timeout()

class URLErrorSeeker(BaseSeeker):
    id = 'URLError'
    provider_name = 'urlErrorSeeker'
    supported_langs = []

    def _search(self, title, filepath, langs, season, episode, tvshow, year):
        raise urllib2.URLError("test")


class StandardErrorSeeker(BaseSeeker):
    id = 'standarderror'
    provider_name = 'standardErrorSeeker'
    supported_langs = []

    def _search(self, title, filepath, langs, season, episode, tvshow, year):
        raise SubtitlesSearchError(SubtitlesErrors.UNKNOWN_ERROR, "unknown")


class ArchiveDownloadSeeker(BaseSeeker):

    id = 'archivedownload'
    provider_name = 'archiveDownloadSeeker'
    supported_langs = []
    default_settings = {}
    subpath = os.path.join(test, 'subtmp', 'tpath', 'rarfile')

    def __init__(self, tmp_path, download_path, settings=None, settings_provider=None, captcha_cb=None, delay_cb=None, message_cb=None):
        BaseSeeker.__init__(self, tmp_path, download_path, settings, settings_provider)

    def _download(self, subtitles, selected_subtitle, path):
        return True, 'English', self.subpath


class NotArchiveDownloadSeeker(BaseSeeker):
    id = 'notarchivedownload'
    provider_name = 'notArchiveDownloadSeeker'
    supported_langs = []
    default_settings = {}
    subpath = os.path.join(test, 'subtmp', 'tpath', 'test_microdvd.txt')

    def __init__(self, tmp_path, download_path, settings=None, settings_provider=None, captcha_cb=None, delay_cb=None, message_cb=None):
        BaseSeeker.__init__(self, tmp_path, download_path, settings, settings_provider)

    def _download(self, subtitles, selected_subtitle, path):
        return False, 'Czech', self.subpath


class TestErrorSeeker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.timeout_seeker = TimeoutSeeker("", "")
        cls.serror_seeker = StandardErrorSeeker("", "")
        cls.urlerror_seeker = URLErrorSeeker("", "")

    def test_search_timeout_error(self):
        self.assertRaises(SubtitlesSearchError, self.timeout_seeker.search, "test")
        try:
            self.timeout_seeker.search("test")
        except SubtitlesSearchError as e:
            self.assertEqual(e.code, SubtitlesErrors.TIMEOUT_ERROR, "invalid error code: %d" % e.code)

    def test_search_standard_error(self):
        self.assertRaises(SubtitlesSearchError, self.serror_seeker.search, "test")
        try:
            self.serror_seeker.search("test")
        except SubtitlesSearchError as e:
            self.assertEqual(e.code, SubtitlesErrors.UNKNOWN_ERROR, "invalid error code")

    def test_search_url_error(self):
        self.assertRaises(SubtitlesSearchError, self.urlerror_seeker.search, "test")
        try:
            self.urlerror_seeker.search("test")
        except SubtitlesSearchError as e:
            self.assertEqual(e.code, SubtitlesErrors.UNKNOWN_ERROR, "invalid error code")



class TestSeekerDownload(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.download_path = os.path.join(test, 'subtmp', 'dpath')
        cls.custom_path = os.path.join(test, 'subtmp', 'cpath')
        cls.video_path = os.path.join(test, 'subtmp', 'vpath')
        cls.temp_path = os.path.join(test, 'subtmp', 'tpath')
        shutil.rmtree(cls.download_path, True)
        shutil.rmtree(cls.custom_path, True)
        shutil.rmtree(cls.video_path, True)
        shutil.rmtree(cls.temp_path, True)
        os.makedirs(cls.download_path)
        os.makedirs(cls.custom_path)
        os.makedirs(cls.video_path)
        os.makedirs(cls.temp_path)

    def setUp(self):
        remove_files_in_dir(self.download_path)
        remove_files_in_dir(self.custom_path)
        remove_files_in_dir(self.temp_path)
        remove_files_in_dir(self.video_path)
        try:
            shutil.copyfile(os.path.join(test, 'utilsfiles', 'rarfile'), ArchiveDownloadSeeker.subpath)
        except:
            pass
        try:
            shutil.copyfile(os.path.join(test, 'subfiles', 'test_microdvd.txt'), NotArchiveDownloadSeeker.subpath)
        except:
            pass
        providers = [ArchiveDownloadSeeker, NotArchiveDownloadSeeker]
        self.seeker = SubsSeeker(self.download_path, self.temp_path, captcha_cb, delay_cb, message_cb, debug=True, providers=providers)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.download_path, True)
        shutil.rmtree(cls.custom_path, True)
        shutil.rmtree(cls.video_path, True)
        shutil.rmtree(cls.temp_path, True)

    def _test_download(self, expected_output, output):
        self.assertTrue(output == expected_output, '"%s"!="%s"'%(expected_output, output))
        self.assertTrue(os.path.isfile(output))

    def test_choose_file(self):
        expected_output = os.path.join(self.download_path, 'subfile1.srt')
        provider = ArchiveDownloadSeeker
        selected_subtitle = {'filename':'subfile.srt'}
        subtitles_dict = {provider.id:{'list':[selected_subtitle], 'params':{'filepath':os.path.join(self.video_path, 'vsubfile.avi')}}}
        settings = {'save_as':'default', 'lang_to_filename':False}
        output = self.seeker.downloadSubtitle(selected_subtitle, subtitles_dict, choosefile_cb, settings=settings)
        self._test_download(expected_output, output)

    def test_save_as_version(self):
        expected_output = os.path.join(self.download_path, 'subfile.srt')
        provider = NotArchiveDownloadSeeker
        selected_subtitle = {'filename':'subfile.srt'}
        subtitles_dict = {provider.id:{'list':[selected_subtitle], 'params':{'filepath':os.path.join(self.video_path, 'vsubfile.avi')}}}
        settings = {'save_as':'version', 'lang_to_filename':False}
        output = self.seeker.downloadSubtitle(selected_subtitle, subtitles_dict, choosefile_cb, settings=settings)
        self._test_download(expected_output, output)

    def test_save_as_video(self):
        expected_output = os.path.join(self.download_path, 'vsubfile.srt')
        provider = NotArchiveDownloadSeeker
        selected_subtitle = {'filename':'subfile.srt'}
        subtitles_dict = {provider.id:{'list':[selected_subtitle], 'params':{'filepath':os.path.join(self.video_path, 'vsubfile.avi')}}}
        settings = {'save_as':'video', 'lang_to_filename':False}
        output = self.seeker.downloadSubtitle(selected_subtitle, subtitles_dict, choosefile_cb, settings=settings)
        self._test_download(expected_output, output)

    def test_lang_to_filename(self):
        expected_output = os.path.join(self.download_path, 'subfile.cs.srt')
        provider = NotArchiveDownloadSeeker
        selected_subtitle = {'filename':'subfile.srt'}
        subtitles_dict = {provider.id:{'list':[selected_subtitle], 'params':{'filepath':os.path.join(self.video_path, 'vsubfile.avi')}}}
        settings = {'save_as':'version', 'lang_to_filename':True}
        output = self.seeker.downloadSubtitle(selected_subtitle, subtitles_dict, choosefile_cb, settings=settings)
        self._test_download(expected_output, output)

    def test_save_to_custom_dir(self):
        expected_output = os.path.join(self.custom_path, 'subfile.srt')
        provider = NotArchiveDownloadSeeker
        selected_subtitle = {'filename':'subfile.srt'}
        subtitles_dict = {provider.id:{'list':[selected_subtitle], 'params':{'filepath':os.path.join(self.video_path, 'vsubfile.avi')}}}
        settings = {'save_as':'version', 'lang_to_filename':False}
        output = self.seeker.downloadSubtitle(selected_subtitle, subtitles_dict, choosefile_cb, settings=settings, path=self.custom_path)
        self._test_download(expected_output, output)
        
    def test_save_custom_fname(self):
        expected_output = os.path.join(self.download_path, 'custom.srt')
        provider = NotArchiveDownloadSeeker
        selected_subtitle = {'filename':'subfile.srt'}
        subtitles_dict = {provider.id:{'list':[selected_subtitle], 'params':{'filepath':os.path.join(self.video_path, 'vsubfile.avi')}}}
        output = self.seeker.downloadSubtitle(selected_subtitle, subtitles_dict, choosefile_cb, fname="custom")
        self._test_download(expected_output, output)

    def test_allow_overwrite(self):
        expected_output = os.path.join(self.download_path, 'subfile.srt')
        provider = NotArchiveDownloadSeeker
        open(expected_output, 'w').close()
        selected_subtitle = {'filename':'subfile.srt'}
        subtitles_dict = {provider.id:{'list':[selected_subtitle], 'params':{'filepath':os.path.join(self.video_path, 'vsubfile.avi')}}}
        settings = {'save_as':'version', 'lang_to_filename':False}
        original_size = os.path.getsize(provider.subpath)
        output = self.seeker.downloadSubtitle(selected_subtitle, subtitles_dict, choosefile_cb, settings=settings, overwrite_cb=lambda x:True)
        downloaded_size = os.path.getsize(expected_output)
        self.assertTrue(original_size == downloaded_size, 'original size != downloaded size: "%d != %d"' % (original_size, downloaded_size))
        self._test_download(expected_output, output)

    def test_not_allow_overwrite(self):
        provider = NotArchiveDownloadSeeker
        expected_output = provider.subpath
        overwrite_path = os.path.join(self.download_path, 'subfile.srt')
        open(overwrite_path, 'w').close()
        selected_subtitle = {'filename':'subfile.srt'}
        subtitles_dict = {provider.id:{'list':[selected_subtitle], 'params':{'filepath':os.path.join(self.video_path, 'vsubfile.avi')}}}
        settings = {'save_as':'version', 'lang_to_filename':False}
        output = self.seeker.downloadSubtitle(selected_subtitle, subtitles_dict, choosefile_cb, settings=settings, overwrite_cb=lambda x:False)
        self.assertTrue(os.path.getsize(overwrite_path) == 0)
        self._test_download(expected_output, output)

    def test_cancel_overwrite(self):
        provider = NotArchiveDownloadSeeker
        expected_output = provider.subpath
        overwrite_path = os.path.join(self.download_path, 'subfile.srt')
        open(overwrite_path, 'w').close()
        selected_subtitle = {'filename':'subfile.srt'}
        subtitles_dict = {provider.id:{'list':[selected_subtitle], 'params':{'filepath':os.path.join(self.video_path, 'vsubfile.avi')}}}
        settings = {'save_as':'version', 'lang_to_filename':False}
        output = self.seeker.downloadSubtitle(selected_subtitle, subtitles_dict, choosefile_cb, settings=settings, overwrite_cb=lambda x:None)
        self.assertTrue(os.path.getsize(overwrite_path) == 0)
        self._test_download(expected_output, output)

class TestSeeker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = {}
        cls.tmp_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'subtmp')
        cls.download_path = cls.tmp_path
        cls.provider_class = None

    def setUp(self):
        download_path = tmp_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'subtmp')
        settings = {'Titulky.com':{'Titulkypass':'', 'Titulkyuser':''}}
        self.seeker = SubsSeeker(download_path, tmp_path, captcha_cb, delay_cb, message_cb, settings=settings, debug=True)

    def test_get_tvshow_providers(self):
        providers = self.seeker.getProviders(None, movie=False, tvshow=True)
        for provider in providers:
            self.assertTrue(provider.tvshow_search, "%s is not tvshow subtitles provider" % provider)

    def test_get_movie_providers(self):
        providers = self.seeker.getProviders(None, movie=True, tvshow=False)
        for provider in providers:
            self.assertTrue(provider.movie_search, "%s is not movie subtitles provider" % provider)

    def test_single_thread_search(self):
        subtitles = self.seeker.getSubtitles(providers=['titulky.com'], title='True Detective', langs=['cs', 'sk'], tvshow='True Detective', season=1, episode=1)
        self.assertIsNotNone(subtitles)
        self.assertTrue('titulky.com' in subtitles)
        self.assertTrue(len(subtitles['titulky.com']['list']) > 0, 'there should be at least one subtitle found')

    def test_search_simple(self):
        langs = ['cs', 'sk']
        subtitles = self.seeker.getSubtitlesSimple(title='True Detective S01 E01', langs=langs)
        providers = self.seeker.getProviders(langs)
        self.assertIsNotNone(subtitles)
        self.assertTrue(len(self.seeker.getSubtitlesList(subtitles)) > 0, 'there should be at least one subtitle found')

    def test_download_simple(self):
        subtitles = self.seeker.getSubtitlesSimple(title='True Detective', langs=['cs', 'sk', 'en'])
        subtitle = self.seeker.getSubtitlesList(subtitles)[-1]
        self.assertTrue(len(self.seeker.downloadSubtitle(subtitle, subtitles, choosefile_cb)) > 0)

    def test_download_with_choosefile(self):
        subtitles = self.seeker.getSubtitles(['edna.cz'], langs=['cs', 'sk', 'en'], tvshow='Homeland', season='2', episode='6')
        subtitle = self.seeker.getSubtitlesList(subtitles)[0]
        subtitlePath = self.seeker.downloadSubtitle(subtitle, subtitles, choosefile_cb)
        self.assertIsNotNone(subtitlePath)
        self.assertTrue(subtitlePath)

if __name__ == "__main__":
    unittest.main()
