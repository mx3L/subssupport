# -*- coding: utf-8 -*-
import re
import struct
import unicodedata

try:
    from hashlib import md5
except:
    from md5 import new as md5

import os
import urllib2

SUPRESS_LOG = True

def log(module,msg):
    if SUPRESS_LOG:
        return
    if isinstance(msg, unicode):
        print module, msg.encode('utf-8')
    else:
        print module, msg

LANGUAGES      = (

    # Full Language name[0]     podnapisi[1]  ISO 639-1[2]   ISO 639-1 Code[3]   Script Setting Language[4]   localized name id number[5]

    ("Albanian", "29",       "sq",            "alb",                 "0",                     30201),
    ("Arabic", "12",       "ar",            "ara",                 "1",                     30202),
    ("Belarusian", "0",       "hy",            "arm",                 "2",                     30203),
    ("Bosnian", "10",       "bs",            "bos",                 "3",                     30204),
    ("Bulgarian", "33",       "bg",            "bul",                 "4",                     30205),
    ("Catalan", "53",       "ca",            "cat",                 "5",                     30206),
    ("Chinese", "17",       "zh",            "chi",                 "6",                     30207),
    ("Croatian", "38",       "hr",            "hrv",                 "7",                     30208),
    ("Czech", "7",        "cs",            "cze",                 "8",                     30209),
    ("Danish", "24",       "da",            "dan",                 "9",                     30210),
    ("Dutch", "23",       "nl",            "dut",                 "10",                    30211),
    ("English", "2",        "en",            "eng",                 "11",                    30212),
    ("Estonian", "20",       "et",            "est",                 "12",                    30213),
    ("Persian", "52",       "fa",            "per",                 "13",                    30247),
    ("Finnish", "31",       "fi",            "fin",                 "14",                    30214),
    ("French", "8",        "fr",            "fre",                 "15",                    30215),
    ("German", "5",        "de",            "ger",                 "16",                    30216),
    ("Greek", "16",       "el",            "ell",                 "17",                    30217),
    ("Hebrew", "22",       "he",            "heb",                 "18",                    30218),
    ("Hindi", "42",       "hi",            "hin",                 "19",                    30219),
    ("Hungarian", "15",       "hu",            "hun",                 "20",                    30220),
    ("Icelandic", "6",        "is",            "ice",                 "21",                    30221),
    ("Indonesian", "0",        "id",            "ind",                 "22",                    30222),
    ("Italian", "9",        "it",            "ita",                 "23",                    30224),
    ("Japanese", "11",       "ja",            "jpn",                 "24",                    30225),
    ("Korean", "4",        "ko",            "kor",                 "25",                    30226),
    ("Latvian", "21",       "lv",            "lav",                 "26",                    30227),
    ("Lithuanian", "0",        "lt",            "lit",                 "27",                    30228),
    ("Macedonian", "35",       "mk",            "mac",                 "28",                    30229),
    ("Malay", "0",        "ms",            "may",                 "29",                    30248),
    ("Norwegian", "3",        "no",            "nor",                 "30",                    30230),
    ("Polish", "26",       "pl",            "pol",                 "31",                    30232),
    ("Portuguese", "32",       "pt",            "por",                 "32",                    30233),
    ("PortugueseBrazil", "48",       "pb",            "pob",                 "33",                    30234),
    ("Romanian", "13",       "ro",            "rum",                 "34",                    30235),
    ("Russian", "27",       "ru",            "rus",                 "35",                    30236),
    ("Serbian", "36",       "sr",            "scc",                 "36",                    30237),
    ("Slovak", "37",       "sk",            "slo",                 "37",                    30238),
    ("Slovenian", "1",        "sl",            "slv",                 "38",                    30239),
    ("Spanish", "28",       "es",            "spa",                 "39",                    30240),
    ("Swedish", "25",       "sv",            "swe",                 "40",                    30242),
    ("Thai", "0",        "th",            "tha",                 "41",                    30243),
    ("Turkish", "30",       "tr",            "tur",                 "42",                    30244),
    ("Ukrainian", "46",       "uk",            "ukr",                 "43",                    30245),
    ("Vietnamese", "51",       "vi",            "vie",                 "44",                    30246),
    ("BosnianLatin", "10",       "bs",            "bos",                 "100",                   30204),
    ("Farsi", "52",       "fa",            "per",                 "13",                    30247),
   # ("English (US)"               , "2",        "en",            "eng",                 "100",                   30212  ),
   # ("English (UK)"               , "2",        "en",            "eng",                 "100",                   30212  ),
    ("Portuguese (Brazilian)", "48",       "pt-br",         "pob",                 "100",                   30234),
    ("Portuguese (Brazil)", "48",       "pb",            "pob",                 "33",                    30234),
    ("Portuguese-BR", "48",       "pb",            "pob",                 "33",                    30234),
    ("Brazilian", "48",       "pb",            "pob",                 "33",                    30234),
    ("Español (Latinoamérica)", "28",       "es",            "spa",                 "100",                   30240),
    ("Español (España)", "28",       "es",            "spa",                 "100",                   30240),
    ("Spanish (Latin America)", "28",       "es",            "spa",                 "100",                   30240),
    ("Español", "28",       "es",            "spa",                 "100",                   30240),
    ("SerbianLatin", "36",       "sr",            "scc",                 "100",                   30237),
    ("Spanish (Spain)", "28",       "es",            "spa",                 "100",                   30240),
    ("Chinese (Traditional)", "17",       "zh",            "chi",                 "100",                   30207),
    ("Chinese (Simplified)", "17",       "zh",            "chi",                 "100",                   30207))

REGEX_EXPRESSIONS = ['[Ss]([0-9]+)[][._-]*[Ee]([0-9]+)([^\\\\/]*)$',
                      '[\._ \-]([0-9]+)x([0-9]+)([^\\/]*)',  # foo.1x09
                      '[\._ \-]([0-9]+)([0-9][0-9])([\._ \-][^\\/]*)',  # foo.109
                      '([0-9]+)([0-9][0-9])([\._ \-][^\\/]*)',
                      '[\\\\/\\._ -]([0-9]+)([0-9][0-9])[^\\/]*',
                      'Season ([0-9]+) - Episode ([0-9]+)[^\\/]*',  # Season 01 - Episode 02
                      'Season ([0-9]+) Episode ([0-9]+)[^\\/]*',  # Season 01 Episode 02
                      '[\\\\/\\._ -][0]*([0-9]+)x[0]*([0-9]+)[^\\/]*',
                      '[[Ss]([0-9]+)\]_\[[Ee]([0-9]+)([^\\/]*)',  # foo_[s01]_[e01]
                      '[\._ \-][Ss]([0-9]+)[\.\-]?[Ee]([0-9]+)([^\\/]*)',  # foo, s01e01, foo.s01.e01, foo.s01-e01
                      's([0-9]+)ep([0-9]+)[^\\/]*',  # foo - s01ep03, foo - s1ep03
                      '[Ss]([0-9]+)[][ ._-]*[Ee]([0-9]+)([^\\\\/]*)$',
                      '[\\\\/\\._ \\[\\(-]([0-9]+)x([0-9]+)([^\\\\/]*)$'
                     ]

LANG_COUNTRY = {"ar":"AE",
                "bg":"BG",
                "ca":"AD",
                "cs":"CZ",
                "da":"DK",
                "de":"DE",
                "el":"GR",
                "en":"GB",
                "es":"ES",
                "et":"EE",
                "fa":"IR",
                "fi":"FI",
                "fr":"FR",
                "fy":"NL",
                "he":"IL",
                "hr":"HR",
                "hu":"HU",
                "is":"IS",
                "it":"IT",
                "ku":"KU",
                "lt":"LT",
                "lv":"LV",
                "nl":"NL",
                "nb":"NO",
                "no":"NO",
                "pl":"PL",
                "pt":"PT",
                "pt":"BR",
                "ro":"RO",
                "ru":"RU",
                "sk":"SK",
                "sl":"SI",
                "sr":"RS",
                "sv":"SE",
                "th":"TH",
                "tr":"TR",
                "uk":"UA"}

LANGNAME_ISO6391 = dict(map(lambda lang:(lang[0], lang[2]),LANGUAGES))
LANGNAME_ISO6392 = dict(map(lambda lang:(lang[0], lang[3]),LANGUAGES))
ISO6391_LANGNAME = dict(map(lambda lang:(lang[2], lang[0]),LANGUAGES))
ISO6392_LANGNAME = dict(map(lambda lang:(lang[3], lang[0]),LANGUAGES))

def languageTranslate(lang, lang_from, lang_to):
    if lang_from == 0 and lang_to == 2:
        if lang in LANGNAME_ISO6391:
            return LANGNAME_ISO6391[lang]
    elif lang_from == 0 and lang_to == 3:
        if lang in LANGNAME_ISO6392:
            return LANGNAME_ISO6392[lang]
    if lang_from == 2 and lang_to == 0:
        if lang in ISO6391_LANGNAME:
            return ISO6391_LANGNAME[lang]
    elif lang_from == 3 and lang_to == 0:
        if lang in ISO6392_LANGNAME:
            return ISO6392_LANGNAME[lang]
    else:
        for x in LANGUAGES:
            if lang == x[lang_from]:
                return x[lang_to]

def regex_movie(title):
    # from periscope
    movie_regexes =['(?P<movie>.*)[\.|\[|\(| ]{1}(?P<year>(?:(?:19|20)[0-9]{2}))(?P<teams>.*)']
    for regex in movie_regexes:
        match = re.search(regex,title, re.IGNORECASE)
        if match:
            return match.group('movie'), match.group('year')
    return '',''

def regex_tvshow(compare, file, sub=""):
    sub_info = ""
    tvshow = 0

    for regex in REGEX_EXPRESSIONS:
        response_file = re.findall(regex, file)
        if len(response_file) > 0:
            log(__name__, "Regex File Se: %s, Ep: %s," % (str(response_file[0][0]), str(response_file[0][1]),))
            tvshow = 1
            if not compare:
                title = re.split(regex, file)[0]
                for char in ['[', ']', '_', '(', ')', '.', '-']:
                    title = title.replace(char, ' ')
                if title.endswith(" "):
                    title = title[:-1]
                return title, response_file[0][0], response_file[0][1]
            else:
                break

    if (tvshow == 1):
        for regex in REGEX_EXPRESSIONS:
            response_sub = re.findall(regex, sub)
            if len(response_sub) > 0:
                try:
                    sub_info = "Regex Subtitle Ep: %s," % (str(response_sub[0][1]),)
                    if (int(response_sub[0][1]) == int(response_file[0][1])):
                        return True
                except:
                    pass
        return False
    if compare:
        return True
    else:
        return "", "", ""


def hashFile(file_path, rar):
    if rar:
        return OpensubtitlesHashRar(file_path)

    log(__name__,"Hash Standard file")
    longlongformat = 'q'  # long long
    bytesize = struct.calcsize(longlongformat)
    f = open(file_path,'r')

    filesize = getFileSize(file_path)
    hash = filesize

    if filesize < 65536 * 2:
        return "SizeError"

    buffer = f.read(65536)
    f.seek(max(0,filesize-65536),0)
    buffer += f.read(65536)
    f.close()
    for x in range((65536/bytesize)*2):
        size = x*bytesize
        (l_value,)= struct.unpack(longlongformat, buffer[size:size+bytesize])
        hash += l_value
        hash = hash & 0xFFFFFFFFFFFFFFFF

    returnHash = "%016x" % hash
    return filesize,returnHash


def normalizeString(str):
    return unicodedata.normalize(
           'NFKD', unicode(unicode(str, 'utf-8'))
           ).encode('ascii','ignore')


def OpensubtitlesHashRar(firsrarfile):
    log(__name__,"Hash Rar file")
    f = open(firsrarfile,'r')
    a=f.read(4)
    if a!='Rar!':
        raise Exception('ERROR: This is not rar file.')
    seek=0
    for i in range(4):
        f.seek(max(0,seek),0)
        a=f.read(100)
        type,flag,size=struct.unpack('<BHH', a[2:2+5])
        if 0x74==type:
            if 0x30!=struct.unpack('<B', a[25:25+1])[0]:
                raise Exception('Bad compression method! Work only for "store".')
            s_partiizebodystart=seek+size
            s_partiizebody,s_unpacksize=struct.unpack('<II', a[7:7+2*4])
            if (flag & 0x0100):
                s_unpacksize=(struct.unpack('<I', a[36:36+4])[0] <<32)+s_unpacksize
                log(__name__, 'Hash untested for files biger that 2gb. May work or may generate bad hash.')
            lastrarfile=getlastsplit(firsrarfile,(s_unpacksize-1)/s_partiizebody)
            hash=addfilehash(firsrarfile,s_unpacksize,s_partiizebodystart)
            hash=addfilehash(lastrarfile,hash,(s_unpacksize%s_partiizebody)+s_partiizebodystart-65536)
            f.close()
            return (s_unpacksize,"%016x" % hash)
        seek+=size
    raise Exception('ERROR: Not Body part in rar file.')

def getlastsplit(firsrarfile,x):
    if firsrarfile[-3:]=='001':
        return firsrarfile[:-3]+('%03d' %(x+1))
    if firsrarfile[-11:-6]=='.part':
        return firsrarfile[0:-6]+('%02d' % (x+1))+firsrarfile[-4:]
    if firsrarfile[-10:-5]=='.part':
        return firsrarfile[0:-5]+('%1d' % (x+1))+firsrarfile[-4:]
    return firsrarfile[0:-2]+('%02d' %(x-1))

def addfilehash(name,hash,seek):
    f = open(name,'r')
    f.seek(max(0,seek),0)
    for i in range(8192):
        hash+=struct.unpack('<q', f.read(8))[0]
        hash =hash & 0xffffffffffffffff
    f.close()
    return hash

def hashFileMD5(file_path, buff_size=1048576):
    # calculate MD5 key from file
    f = open(file_path,'r')
    if f.size() < buff_size:
        return None
    f.seek(0,0)
    buff = f.read(buff_size)    # size=1M
    f.close()
    # calculate MD5 key from file
    m = md5()
    m.update(buff)
    return m.hexdigest()

def langToCountry(lang):
    if lang in LANG_COUNTRY:
        return LANG_COUNTRY[lang]
    return 'UNK'

class HeadRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"

def getFileSize(filepath):
    try:
        if os.path.isfile(filepath):
            return os.path.getsize(filepath)
    except Exception:
        return None
    if filepath.startswith('http://'):
        try:
            resp = urllib2.urlopen(HeadRequest(filepath))
            return  long(resp.info().get('Content-Length'))
        except Exception:
            return None
        finally:
            if 'resp' in locals():
                locals()['resp'].close()
    return None

# http://www.garykessler.net/library/file_sigs.html
def getCompressedFileType(filepath):
    signature_dict = {
                         "\x50\x4b\x03\x04":"zip",
                         "\x52\x61\x72\x21\x1A":"rar"
    }
    max_len = max(len(x) for x in signature_dict)
    with open(filepath) as f:
        file_start = f.read(max_len)
    for signature, filetype in signature_dict.items():
        if file_start.startswith(signature):
            return filetype
    return None

def detectSearchParams(title):
    print '[detectSearchParams] detecting parameters for - title: %s'%title
    season=episode=tvshow=""
    titlemovie, year = regex_movie(title)
    if titlemovie:
        title = titlemovie.strip()
    year = year.strip()
    # from xbmc-subtitles
    if year == "":                                            # If we have a year, assume no tv show
        if str(year) == "":                                          # Still no year: *could* be a tvshow
            title_tvshow, season, episode = regex_tvshow(False, title)
            if title_tvshow != "" and season != "" and episode != "":
                season = str(int(season)).strip()
                episode = str(int(episode)).strip()
                tvshow = title_tvshow.strip()
                title = ""
            else:
                season = ""                                              # Reset variables: could contain garbage from tvshow regex above
                episode = ""
                tvshow = ""
        else:
            year = ""
    print '[detectSearchParams] detected -  title: %s, year: %s, tvshow: %s, season: %s, episode: %s' %(title, year, tvshow, season, episode)
    return title, year, tvshow, season, episode

class SimpleLogger(object):

    LOG_FORMAT = "[{0}]{1}"
    LOG_NONE, LOG_ERROR, LOG_INFO, LOG_DEBUG = range(4)

    def __init__(self, prefix_name, log_level=LOG_INFO):
        self.prefix_name = prefix_name
        self.log_level = log_level

    def set_log_level(self, level):
        self.log_level = level

    def error(self, text, *args):
        if self.log_level >= self.LOG_ERROR:
            text = self._eval_message(text, args)
            text = "[error] {0}".format(toString(text))
            out = self._format_output(text)
            self._out_fnc(out)

    def info(self, text, *args):
        if self.log_level >= self.LOG_INFO:
            text = self._eval_message(text, args)
            text = "[info] {0}".format(toString(text))
            out = self._format_output(text)
            self._out_fnc(out)

    def debug(self, text, *args):
        if self.log_level == self.LOG_DEBUG:
            text = self._eval_message(text, args)
            text = "[debug] {0}".format(toString(text))
            out = self._format_output(text)
            self._out_fnc(out)

    def _eval_message(self, text, *args):
        if len(args) == 1 and isinstance(args[0], tuple):
            text = text % toString(args[0])
        elif len(args) >=1:
            text = text % tuple([toString(a) for a in args])
        return text

    def _format_output(self, text):
        return self.LOG_FORMAT.format(self.prefix_name, text)

    def _out_fnc(self, text):
        print text

def toString(text):
    if isinstance(text,basestring):
        if isinstance(text, unicode):
            return text.encode('utf-8')
    return text
