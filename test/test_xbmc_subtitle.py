'''
Created on Feb 6, 2014

@author: marko
'''
import os
import sys
import time
import unittest
import ConfigParser

test = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(test, '..','plugin'))

MOVIE_PATH = os.path.join(test,'moviefiles')

from seekers import SubtitlesDownloadError, SubtitlesSearchError, \
    SubtitlesErrors
    
import seekers.utilities as u
u.SUPRESS_LOG = False


class TestXBMCSubtitleProvider(object):

    @classmethod
    def setUpClass(cls):
        cls.settings = {}
        cls.tmp_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'subtmp')
        if not os.path.isdir(cls.tmp_path):
            os.mkdir(cls.tmp_path)
        cls.download_path = cls.tmp_path

    def captcha_cb(self, url):
        print '[captcha_cb] visit url:"%s"\nre-type captcha:'%url
        print '[captcha_cb] not visiting just returning empty string'
        return ""

    def message_cb(self, text):
        print '[message_cb] %s'%text

    def delay_cb(self, seconds):
        print '[delay_cb] waiting for %d seconds'%seconds
        for i in xrange(seconds):
            print '[delay_cb] %d second'
            time.sleep(1)

    def setUp(self):
        self.search_list = []
        self.movie_list = []
        self.tvshow_list = []
        self.hash_list = []
        self.download_movie_list = []
        self.download_tvshow_list = []

    def test_search_simple(self):
        for title in self.search_list:
            result = self.provider.search(title)
            self.assertTrue(len(result['list']) > 0, 'There should be at least 1 subtitle found')

    def test_search_tvshow(self):
        for title, season, episode in self.tvshow_list:
            result = self.provider.search(tvshow=title, season=season, episode=episode)
            self.assertTrue(len(result['list']) > 0, 'There should be at least 1 subtitle found')

    def test_search_movie(self):
        for movie in self.movie_list:
            if len(movie) == 1:
                title, year, langs = movie[0], '',''
            elif len(movie) == 2:
                title, year, langs = movie[0], movie[1], ''
            elif len(movie) == 3:
                title, year, langs = movie[0], movie[1], movie[2]
            result = self.provider.search(title=title, year=year, langs=langs)
            self.assertTrue(len(result['list']) > 0, 'There should be at least 1 subtitle found')
        
    def test_hash_search(self):
        for h in self.hash_list:
            if len(h) == 1:
                path, langs =  h[0], ''
            elif len(h) == 2:
                path,langs = h[0],h[1]
            else:
                continue
            if os.path.isfile(path):
                result = self.provider.search(filepath=path, langs=langs)
                self.assertTrue(len(result['list']) > 0, 'There should be at least 1 subtitle found')

    def test_download(self):
        for title, year  in self.download_movie_list:
            subtitles = self.provider.search(title=title, year=year)
            self.assertTrue(len(subtitles['list']) > 0, 'There should be at least 1 subtitle found')
            self._test_download(self.provider.download(subtitles, subtitles['list'][0]))
        for title, season, episode in self.download_tvshow_list:
            subtitles = self.provider.search(tvshow=title, season=season, episode=episode)
            self.assertTrue(len(subtitles['list']) > 0, 'There should be at least 1 subtitle found')
            self._test_download(self.provider.download(subtitles, subtitles['list'][0]))

    def _test_download(self, result):
        self.assertIsNotNone(result)
        self.assertTrue(isinstance(result, tuple))
        self.assertTrue(os.path.isfile(result[2]))

class TestXBMCSubtitleProviderWithCredentials(TestXBMCSubtitleProvider):

    @classmethod
    def get_credentials(cls, filename):
        config = ConfigParser.RawConfigParser()
        cfgpath = os.path.join(os.path.dirname(__file__),filename)
        try:
            config.read(cfgpath)
            config.get('Credentials','username')
        except:
            print 'Cannot read config file '+ filename
            config.add_section('Credentials')
            config.set('Credentials', 'username', 'name_')
            config.set('Credentials', 'password', 'pass_')
            with open(cfgpath, 'wb') as configfile:
                config.write(configfile)
            print 'Wrote default values to config file'
        return config.get('Credentials','username'), config.get('Credentials','password')

    def test_download(self):
        pass

    def test_download_without_credentials(self):
        assert self.login_setting_key != ""
        assert self.password_setting_key != ""
        self.provider.settings_provider.setSetting(self.login_setting_key, "")
        self.provider.settings_provider.setSetting(self.password_setting_key, "")
        try:
            TestXBMCSubtitleProvider.test_download(self)
        except SubtitlesDownloadError as e:
            self.assertEqual(e.code, SubtitlesErrors.NO_CREDENTIALS_ERROR)
        except:
            self.fail("invalid error code")
        else:
            self.fail("no error code, maybe no credentials necessary?")

    def test_download_with_credentials(self):
        assert self.login != ""
        assert self.password != ""
        assert self.login_setting_key != ""
        assert self.password_setting_key != ""
        self.provider.settings_provider.setSetting(self.login_setting_key, self.login)
        self.provider.settings_provider.setSetting(self.password_setting_key, self.password)
        TestXBMCSubtitleProvider.test_download(self)


from seekers.xbmc_subtitles import TitulkyComSeeker
class TestTitulkycom(TestXBMCSubtitleProviderWithCredentials, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestTitulkycom,cls).setUpClass()
        cls.login, cls.password = cls.get_credentials('titulkycom.cfg')

    def setUp(self):
        self.search_list = ['Alias']
        self.tvshow_list = []
        self.movie_list = []
        self.hash_list = []
        self.download_movie_list = []
        self.download_tvshow_list = [] #[('Frasier','1','1')]
        self.login_setting_key = 'Titulkyuser'
        self.password_setting_key = 'Titulkypass'
        self.provider= TitulkyComSeeker(self.tmp_path,
                                                                        self.download_path,
                                                                        None,
                                                                        None,
                                                                        self.captcha_cb,
                                                                        self.delay_cb,
                                                                        self.message_cb)

from seekers.xbmc_subtitles import EdnaSeeker
class TestEdna(TestXBMCSubtitleProvider, unittest.TestCase):
    def setUp(self):
        self.settings = {}
        self.search_list = []
        self.tvshow_list = [('True Detective','1','1')]
        self.movie_list = []
        self.hash_list = []
        self.download_movie_list = []
        self.download_tvshow_list = []
        self.provider= EdnaSeeker(self.tmp_path,
                                                                        self.download_path,
                                                                        self.settings,
                                                                        None,
                                                                        self.captcha_cb,
                                                                        self.delay_cb,
                                                                        self.message_cb)

from seekers.xbmc_subtitles import SerialZoneSeeker
class TestSerialZone(TestXBMCSubtitleProvider, unittest.TestCase):
    def setUp(self):
        self.search_list = []
        self.tvshow_list = [('True Detective','1','1')]
        self.movie_list = []
        self.hash_list = []
        self.download_movie_list = []
        self.download_tvshow_list = []
        self.provider= SerialZoneSeeker(self.tmp_path,
                                                                        self.download_path,
                                                                        self.settings,
                                                                        None,
                                                                        self.captcha_cb,
                                                                        self.delay_cb,
                                                                        self.message_cb)

from seekers.xbmc_subtitles import OpenSubtitlesSeeker
class TestOpenSubtitles(TestXBMCSubtitleProvider, unittest.TestCase):
    def setUp(self):
        self.settings = {}
        self.search_list = ['Dark Knight']
        self.tvshow_list = [('True Detective','1','1')]
        self.movie_list = []
        self.hash_list = []
        self.download_movie_list = []
        self.download_tvshow_list = [('True Detective','1','1')]
        self.provider= OpenSubtitlesSeeker(self.tmp_path,
                                                                        self.download_path,
                                                                        self.settings,
                                                                        None,
                                                                        self.captcha_cb,
                                                                        self.delay_cb,
                                                                        self.message_cb)

from seekers.xbmc_subtitles import PodnapisiSeeker
class TestPodnapisi(TestXBMCSubtitleProviderWithCredentials, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestPodnapisi,cls).setUpClass()
        cls.login, cls.password = cls.get_credentials('podnapisi.cfg')

    def setUp(self):
        self.search_list = ['Dark Knight']
        self.tvshow_list = []
        self.movie_list = [('The Hobbit','2012')]
        self.hash_list = []
        self.download_movie_list = [('The Hobbit','2012')]
        self.download_tvshow_list = []
        self.login_setting_key = 'PNuser'
        self.password_setting_key = 'PNpass'
        self.provider= PodnapisiSeeker(self.tmp_path,
                                                                        self.download_path,
                                                                        None,
                                                                        None,
                                                                        self.captcha_cb,
                                                                        self.delay_cb,
                                                                        self.message_cb)
        
    def test_hash_search(self):
        self.provider.settings_provider.setSetting('PNmatch', 'true')
        TestXBMCSubtitleProviderWithCredentials.test_hash_search(self)

from seekers.xbmc_subtitles import SubsceneSeeker
class TestSubscene(TestXBMCSubtitleProvider, unittest.TestCase):
    def setUp(self):
        self.settings = {}
        self.search_list = []
        self.tvshow_list = []
        self.movie_list = [('The Hobbit','2012'), ('Bad boys','',['fa'])]
        self.hash_list = []
        self.download_movie_list = [('The Hobbit','2012')]
        self.download_tvshow_list = []
        self.provider= SubsceneSeeker(self.tmp_path,
                                                                        self.download_path,
                                                                        self.settings,
                                                                        None,
                                                                        self.captcha_cb,
                                                                        self.delay_cb,
                                                                        self.message_cb)

from seekers.xbmc_subtitles import SubtitlesGRSeeker
class TestSubtitlesGR(TestXBMCSubtitleProvider, unittest.TestCase):
    def setUp(self):
        self.settings = {}
        self.search_list = []
        self.tvshow_list = [('True Detective','1','1')]
        self.movie_list = [('The Hobbit','2012')]
        self.hash_list = []
        self.download_movie_list = [('The Hobbit','2012')]
        self.download_tvshow_list = []
        self.provider= SubtitlesGRSeeker(self.tmp_path,
                                                                        self.download_path,
                                                                        self.settings,
                                                                        None,
                                                                        self.captcha_cb,
                                                                        self.delay_cb,
                                                                        self.message_cb)

from seekers.xbmc_subtitles import ItasaSeeker
class TestItasa(TestXBMCSubtitleProviderWithCredentials, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestItasa,cls).setUpClass()
        cls.login, cls.password = cls.get_credentials('itasa.cfg')

    def setUp(self):
        self.search_list = []
        self.movie_list = []
        self.tvshow_list = [('True Detective','1','1')]
        self.hash_list = []
        self.download_tvshow_list = [('True Detective','1','1')]
        self.download_movie_list = []
        self.login_setting_key = 'ITuser'
        self.password_setting_key = 'ITpass'
        self.provider= ItasaSeeker(self.tmp_path,
                                                                        self.download_path,
                                                                        None,
                                                                        None,
                                                                        self.captcha_cb,
                                                                        self.delay_cb,
                                                                        self.message_cb)

from seekers.xbmc_subtitles import TitloviSeeker
class TestTitlovi(TestXBMCSubtitleProvider, unittest.TestCase):
    def setUp(self):
        self.settings = {}
        self.search_list = []
        self.tvshow_list = [('True Detective','1','1')]
        self.movie_list = [('The Hobbit','2012')]
        self.hash_list = []
        self.download_movie_list = [('The Hobbit','2012')]
        self.download_tvshow_list = []
        self.provider= TitloviSeeker(self.tmp_path,
                                                                        self.download_path,
                                                                        self.settings,
                                                                        None,
                                                                        self.captcha_cb,
                                                                        self.delay_cb,
                                                                        self.message_cb)

if __name__ == "__main__":
    unittest.main()
