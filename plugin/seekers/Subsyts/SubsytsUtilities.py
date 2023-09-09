# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
import requests
import re
from ..utilities import log as _log

from six.moves import urllib
import six


ses = requests.Session()

LANGUAGES = (
    ("Albanian", "29", "sq", "alb", "0", 30201),
    ("Arabic", "12", "ar", "ara", "1", 30202),
    ("Belarusian", "0", "hy", "arm", "2", 30203),
    ("Bosnian", "10", "bs", "bos", "3", 30204),
    ("Bulgarian", "33", "bg", "bul", "4", 30205),
    ("Catalan", "53", "ca", "cat", "5", 30206),
    ("Chinese", "17", "zh", "chi", "6", 30207),
    ("Croatian", "38", "hr", "hrv", "7", 30208),
    ("Czech", "7", "cs", "cze", "8", 30209),
    ("Danish", "24", "da", "dan", "9", 30210),
    ("Dutch", "23", "nl", "dut", "10", 30211),
    ("English", "2", "en", "eng", "11", 30212),
    ("Estonian", "20", "et", "est", "12", 30213),
    ("Persian", "52", "fa", "per", "13", 30247),
    ("Finnish", "31", "fi", "fin", "14", 30214),
    ("French", "8", "fr", "fre", "15", 30215),
    ("German", "5", "de", "ger", "16", 30216),
    ("Greek", "16", "el", "ell", "17", 30217),
    ("Hebrew", "22", "he", "heb", "18", 30218),
    ("Hindi", "42", "hi", "hin", "19", 30219),
    ("Hungarian", "15", "hu", "hun", "20", 30220),
    ("Icelandic", "6", "is", "ice", "21", 30221),
    ("Indonesian", "0", "id", "ind", "22", 30222),
    ("Italian", "9", "it", "ita", "23", 30224),
    ("Japanese", "11", "ja", "jpn", "24", 30225),
    ("Korean", "4", "ko", "kor", "25", 30226),
    ("Latvian", "21", "lv", "lav", "26", 30227),
    ("Lithuanian", "0", "lt", "lit", "27", 30228),
    ("Macedonian", "35", "mk", "mac", "28", 30229),
    ("Malay", "0", "ms", "may", "29", 30248),
    ("Norwegian", "3", "no", "nor", "30", 30230),
    ("Polish", "26", "pl", "pol", "31", 30232),
    ("Portuguese", "32", "pt", "por", "32", 30233),
    ("PortugueseBrazil", "48", "pb", "pob", "33", 30234),
    ("Romanian", "13", "ro", "rum", "34", 30235),
    ("Russian", "27", "ru", "rus", "35", 30236),
    ("Serbian", "36", "sr", "scc", "36", 30237),
    ("Slovak", "37", "sk", "slo", "37", 30238),
    ("Slovenian", "1", "sl", "slv", "38", 30239),
    ("Spanish", "28", "es", "spa", "39", 30240),
    ("Swedish", "25", "sv", "swe", "40", 30242),
    ("Thai", "0", "th", "tha", "41", 30243),
    ("Turkish", "30", "tr", "tur", "42", 30244),
    ("Ukrainian", "46", "uk", "ukr", "43", 30245),
    ("Vietnamese", "51", "vi", "vie", "44", 30246),
    ("BosnianLatin", "10", "bs", "bos", "100", 30204),
    ("Farsi", "52", "fa", "per", "13", 30247),
    ("English (US)", "2", "en", "eng", "100", 30212),
    ("English (UK)", "2", "en", "eng", "100", 30212),
    ("Portuguese (Brazilian)", "48", "pt-br", "pob", "100", 30234),
    ("Portuguese (Brazil)", "48", "pb", "pob", "33", 30234),
    ("Portuguese-BR", "48", "pb", "pob", "33", 30234),
    ("Brazilian", "48", "pb", "pob", "33", 30234),
    ("Español (Latinoamérica)", "28", "es", "spa", "100", 30240),
    ("Español (España)", "28", "es", "spa", "100", 30240),
    ("Spanish (Latin America)", "28", "es", "spa", "100", 30240),
    ("Español", "28", "es", "spa", "100", 30240),
    ("SerbianLatin", "36", "sr", "scc", "100", 30237),
    ("Spanish (Spain)", "28", "es", "spa", "100", 30240),
    ("Chinese (Traditional)", "17", "zh", "chi", "100", 30207),
    ("Chinese (Simplified)", "17", "zh", "chi", "100", 30207))

subsyts_languages = {
    'Chinese BG code': 'Chinese',
    'Brazillian Portuguese': 'Portuguese (Brazil)',
    'Serbian': 'SerbianLatin',
    'Ukranian': 'Ukrainian',
    'Farsi/Persian': 'Persian'
}


def get_language_info(language):
    if language in subsyts_languages:
        language = subsyts_languages[language]

    for lang in LANGUAGES:
        if lang[0] == language:
            return {'name': lang[0], '2et': lang[2], '3et': lang[3]}


def log(module, msg):
    _log(module, msg.encode('utf-8'))


def geturl(url1, headers=None, params=None):
    try:
        res = ses.get(url1, headers=headers, verify=False, timeout=5)
        print('res.status_code', res.status_code)
        if res.status_code == 200:
            return six.ensure_str(res.content)
        e = res.raise_for_status()
        print(('Download error', e))
        return ''
    except requests.exceptions.RequestException as e:
        print(('Download error', str(e)))
        return ''
