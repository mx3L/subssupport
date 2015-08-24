# -*- coding: utf-8 -*-

import HTMLParser
import difflib
import os, re, string, urllib, urllib2

from SubsceneUtilities import geturl, get_language_info

from ..utilities import log


main_url = "http://subscene.com/"
debug_pretext = ""


# Seasons as strings for searching
# Seasons as strings for searching
seasons = ["Specials", "First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]
seasons = seasons + ["Eleventh", "Twelfth", "Thirteenth", "Fourteenth", "Fifteenth", "Sixteenth", "Seventeenth",
                     "Eighteenth", "Nineteenth", "Twentieth"]
seasons = seasons + ["Twenty-first", "Twenty-second", "Twenty-third", "Twenty-fourth", "Twenty-fifth", "Twenty-sixth",
                     "Twenty-seventh", "Twenty-eighth", "Twenty-ninth"]

movie_season_pattern = ("<a href=\"(?P<link>/subtitles/[^\"]*)\">(?P<title>[^<]+)\((?P<year>\d{4})\)</a>\s+"
                        "</div>\s+<div class=\"subtle count\">\s+(?P<numsubtitles>\d+)")


def find_movie(content, title, year):
    url_found = None
    h = HTMLParser.HTMLParser()
    for matches in re.finditer(movie_season_pattern, content, re.IGNORECASE | re.DOTALL):
        found_title = matches.group('title')
        found_title = h.unescape(found_title)
        log(__name__, "Found movie on search page: %s (%s)" % (found_title, matches.group('year')))
        if string.find(string.lower(found_title), string.lower(title)) > -1:
            if matches.group('year') == year:
                log(__name__, "Matching movie found on search page: %s (%s)" % (found_title, matches.group('year')))
                url_found = matches.group('link')
                break
    return url_found


def find_tv_show_season(content, tvshow, season):
    url_found = None
    possible_matches = []
    all_tvshows = []

    h = HTMLParser.HTMLParser()
    for matches in re.finditer(movie_season_pattern, content, re.IGNORECASE | re.DOTALL):
        found_title = matches.group('title')
        found_title = h.unescape(found_title)

        log(__name__, "Found tv show season on search page: %s" % found_title)
        s = difflib.SequenceMatcher(None, string.lower(found_title + ' ' + matches.group('year')), string.lower(tvshow))
        all_tvshows.append(matches.groups() + (s.ratio() * int(matches.group('numsubtitles')),))
        if string.find(string.lower(found_title), string.lower(tvshow) + " ") > -1:
            if string.find(string.lower(found_title), string.lower(season)) > -1:
                log(__name__, "Matching tv show season found on search page: %s" % found_title)
                possible_matches.append(matches.groups())

    if len(possible_matches) > 0:
        possible_matches = sorted(possible_matches, key=lambda x:-int(x[3]))
        url_found = possible_matches[0][0]
        log(__name__, "Selecting matching tv show with most subtitles: %s (%s)" % (
            possible_matches[0][1], possible_matches[0][3]))
    else:
        if len(all_tvshows) > 0:
            all_tvshows = sorted(all_tvshows, key=lambda x:-int(x[4]))
            url_found = all_tvshows[0][0]
            log(__name__, "Selecting tv show with highest fuzzy string score: %s (score: %s subtitles: %s)" % (
                all_tvshows[0][1], all_tvshows[0][4], all_tvshows[0][3]))

    return url_found


def getallsubs(content, allowed_languages, filename="", search_string=""):
    subtitle_pattern = ("<a href=\"(?P<link>/subtitles/[^\"]+)\">\s+"
                        "<span class=\"[^\"]+ (?P<quality>\w+-icon)\">\s+(?P<language>[^\r\n\t]+)\s+</span>\s+"
                        "<span>\s+(?P<filename>[^\r\n\t]+)\s+</span>\s+"
                        "</a>\s+</td>\s+"
                        "<td class=\"[^\"]+\">\s+(?P<numfiles>[^\r\n\t]*)\s+</td>\s+"
                        "<td class=\"(?P<hiclass>[^\"]+)\">"
                        "(?P<rest>.*?)</tr>")
    comment_pattern = "<td class=\"a6\">\s+<div>\s+(?P<comment>[^\"]+)&nbsp;\s*</div>"

    subtitles = []
    h = HTMLParser.HTMLParser()

    for matches in re.finditer(subtitle_pattern, content, re.IGNORECASE | re.DOTALL):
        numfiles = 1
        if matches.group('numfiles') != "":
            numfiles = int(matches.group('numfiles'))
        languagefound = matches.group('language')
        language_info = get_language_info(languagefound)
        if language_info and language_info['name'] in allowed_languages:
            link = main_url + matches.group('link')
            subtitle_name = string.strip(matches.group('filename'))
            hearing_imp = (matches.group('hiclass') == "a41")
            rating = '0'
            comment = ''
            if matches.group('quality') == "bad-icon":
                continue
            if matches.group('quality') == "positive-icon":
                rating = '5'

            commentmatch = re.search(comment_pattern, matches.group('rest'), re.IGNORECASE | re.DOTALL);
            if commentmatch != None:
                comment = re.sub("[\r\n\t]+", " ", h.unescape(string.strip(commentmatch.group('comment'))))

            sync = False
            if filename != "" and string.lower(filename) == string.lower(subtitle_name):
                sync = True

            if search_string != "":
                if string.find(string.lower(subtitle_name), string.lower(search_string)) > -1:
                    subtitles.append({'rating': rating, 'filename': subtitle_name, 'sync': sync, 'link': link,
                                     'language_name':language_info['name'], 'lang': language_info, 'hearing_imp': hearing_imp, 'comment': comment})
                elif numfiles > 2:
                    subtitle_name = subtitle_name + ' ' + ("%d files" % int(matches.group('numfiles')))
                    subtitles.append({'rating': rating, 'filename': subtitle_name, 'sync': sync, 'link': link,
                                     'language_name':language_info['name'], 'lang': language_info, 'hearing_imp': hearing_imp, 'comment': comment})
            else:
                subtitles.append({'rating': rating, 'filename': subtitle_name, 'sync': sync, 'link': link,
                                 'language_name':language_info['name'], 'lang': language_info, 'hearing_imp': hearing_imp, 'comment': comment})

    subtitles.sort(key=lambda x: [not x['sync']])
    return subtitles

def prepare_search_string(s):
    s = string.strip(s)
    s = re.sub(r'\(\d\d\d\d\)$', '', s)  # remove year from title
    s = urllib.quote_plus(s)
    return s


def search_movie(title, year, languages, filename):
    title = string.strip(title)
    search_string = prepare_search_string(title)

    log(__name__, "Search movie = %s" % search_string)
    url = main_url + "/subtitles/title?q=" + urllib.quote_plus(search_string) + '&r=true'
    content, response_url = geturl(url)

    if content is not None:
        log(__name__, "Multiple movies found, searching for the right one ...")
        subspage_url = find_movie(content, title, year)
        if subspage_url is not None:
            log(__name__, "Movie found in list, getting subs ...")
            url = main_url + subspage_url
            content, response_url = geturl(url)
            if content is not None:
                return getallsubs(content, languages, filename)
        else:
            log(__name__, "Movie not found in list: %s" % title)
            if string.find(string.lower(title), "&") > -1:
                title = string.replace(title, "&", "and")
                log(__name__, "Trying searching with replacing '&' to 'and': %s" % title)
                subspage_url = find_movie(content, title, year)
                if subspage_url is not None:
                    log(__name__, "Movie found in list, getting subs ...")
                    url = main_url + subspage_url
                    content, response_url = geturl(url)
                    if content is not None:
                        return getallsubs(content, languages, filename)
                else:
                    log(__name__, "Movie not found in list: %s" % title)
                    

def search_tvshow(tvshow, season, episode, languages, filename):
    tvshow = string.strip(tvshow)
    search_string = prepare_search_string(tvshow)
    search_string += " - " + seasons[int(season)] + " Season"

    log(__name__, "Search tvshow = %s" % search_string)
    url = main_url + "/subtitles/title?q=" + urllib.quote_plus(search_string) + '&r=true'
    content, response_url = geturl(url)

    if content is not None:
        log(__name__, "Multiple tv show seasons found, searching for the right one ...")
        tv_show_seasonurl = find_tv_show_season(content, tvshow, seasons[int(season)])
        if tv_show_seasonurl is not None:
            log(__name__, "Tv show season found in list, getting subs ...")
            url = main_url + tv_show_seasonurl
            content, response_url = geturl(url)
            if content is not None:
                search_string = "s%#02de%#02d" % (int(season), int(episode))
                return getallsubs(content, languages, filename, search_string)


def search_manual(searchstr, languages, filename):
    search_string = prepare_search_string(searchstr)
    url = main_url + "/subtitles/release?q=" + search_string + '&r=true'
    content, response_url = geturl(url)

    if content is not None:
        return getallsubs(content, languages, filename)

def geturl(url):
    log(__name__ , "%s Getting url:%s" % (debug_pretext, url))
    try:
        response = urllib2.urlopen(url)
        content = response.read()
        # Fix non-unicode charachters in movie titles
        strip_unicode = re.compile("([^-_a-zA-Z0-9!@#%&=,/'\";:~`\$\^\*\(\)\+\[\]\.\{\}\|\?\<\>\\]+|[^\s]+)")
        content = strip_unicode.sub('', content)
        return_url = response.geturl()
    except:
        import traceback
        traceback.print_exc()
        log(__name__ , "%s Failed to get url:%s" % (debug_pretext, url))
        content = None
        return_url = None
    return(content, return_url)

def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):  # standard input
    log(__name__ , "%s Search_subtitles = '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'" % 
         (debug_pretext, file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack))
    if lang1 == 'Farsi':
        lang1 = 'Persian'
    if lang2 == 'Farsi':
        lang2 = 'Persian'
    if lang3 == 'Farsi':
        lang3 = 'Persian'
    if tvshow:
        sublist = search_tvshow(tvshow, season, episode, [lang1, lang2, lang3], file_original_path)
    elif title and year:
        sublist = search_movie(title, year, [lang1, lang2, lang3], file_original_path)
    else:
        sublist = search_manual(title, [lang1, lang2, lang3], file_original_path)
    return sublist, "", ""


def download_subtitles (subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):  # standard input
    url = subtitles_list[pos][ "link" ]
    language = subtitles_list[pos][ "language_name" ]
    content, response_url = geturl(url)
    downloadlink_pattern = "...<a href=\"(.+?)\" rel=\"nofollow\" onclick=\"DownloadSubtitle"
    match = re.compile(downloadlink_pattern).findall(content)
    if match:
        downloadlink = "http://subscene.com" + match[0]
        log(__name__ , "%s Downloadlink: %s " % (debug_pretext, downloadlink))
        viewstate = 0
        previouspage = 0
        subtitleid = 0
        typeid = "zip"
        filmid = 0
        postparams = urllib.urlencode({ '__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '' , '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid})
        class MyOpener(urllib.FancyURLopener):
            version = 'User-Agent=Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)'
        my_urlopener = MyOpener()
        my_urlopener.addheader('Referer', url)
        log(__name__ , "%s Fetching subtitles using url '%s' with referer header '%s' and post parameters '%s'" % (debug_pretext, downloadlink, url, postparams))
        response = my_urlopener.open(downloadlink, postparams)
        local_tmp_file = zip_subs
        try:
            log(__name__ , "%s Saving subtitles to '%s'" % (debug_pretext, local_tmp_file))
            if not os.path.exists(tmp_sub_dir):
                os.makedirs(tmp_sub_dir)
            local_file_handle = open(local_tmp_file, "w" + "b")
            local_file_handle.write(response.read())
            local_file_handle.close()
            # Check archive type (rar/zip/else) through the file header (rar=Rar!, zip=PK)
            myfile = open(local_tmp_file, "rb")
            myfile.seek(0)
            if (myfile.read(1) == 'R'):
                typeid = "rar"
                packed = True
                log(__name__ , "Discovered RAR Archive")
            else:
                myfile.seek(0)
                if (myfile.read(1) == 'P'):
                    typeid = "zip"
                    packed = True
                    log(__name__ , "Discovered ZIP Archive")
                else:
                    typeid = "srt"
                    packed = False
                    subs_file = local_tmp_file
                    log(__name__ , "Discovered a non-archive file")
            myfile.close()
            log(__name__ , "%s Saving to %s" % (debug_pretext, local_tmp_file))
        except:
            log(__name__ , "%s Failed to save subtitle to %s" % (debug_pretext, local_tmp_file))
        if packed:
            subs_file = typeid
        log(__name__ , "%s Subtitles saved to '%s'" % (debug_pretext, local_tmp_file))
        return packed, language, subs_file  # standard output
