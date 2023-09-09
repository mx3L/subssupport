'''
Created on Aug 2, 2014

@author: marko
'''
from __future__ import absolute_import
from __future__ import print_function

import sys
import json
import time
import traceback

stdout = None


class Messages(object):
    MESSAGE_CAPTCHA_CALLBACK = 1
    MESSAGE_UPDATE_CALLBACK = 2
    MESSAGE_DELAY_CALLBACK = 3
    MESSAGE_CANCELLED_SCRIPT = 4
    MESSAGE_FINISHED_SCRIPT = 5
    MESSAGE_ERROR_SCRIPT = 6
    MESSAGE_CHOOSE_FILE_CALLBACK = 7
    MESSAGE_OVERWRITE_CALLBACK = 8


def send(mtype, m):
    dump = json.dumps({'message': mtype, 'value': m})
    dump = "%07d%s" % (len(dump) + 7, dump)
    stdout.write(dump)
    stdout.flush()


def recieve():
    return json.loads(sys.stdin.read(int(sys.stdin.read(7))))


def delayCB(seconds):
    send(Messages.MESSAGE_DELAY_CALLBACK, seconds)
    recieve()


def captchaCB(image):
    send(Messages.MESSAGE_CAPTCHA_CALLBACK, image)
    return recieve()


def messageCB(text):
    print('messageCB:', text)


def updateCB(*args):
    send(Messages.MESSAGE_UPDATE_CALLBACK, args)


def chooseFileCB(*args):
    send(Messages.MESSAGE_CHOOSE_FILE_CALLBACK, args)
    return recieve()


def overwriteFileCB(*args):
    send(Messages.MESSAGE_OVERWRITE_CALLBACK, args)
    return recieve()


def scriptError(e):
    try:
        from .seekers.seeker import SubtitlesErrors, BaseSubtitlesError
    except (ValueError, ImportError):
        from seekers.seeker import SubtitlesErrors, BaseSubtitlesError
    if isinstance(e, BaseSubtitlesError):
        send(Messages.MESSAGE_ERROR_SCRIPT, {'error_code': e.code, 'provider': e.provider})
    else:
        send(Messages.MESSAGE_ERROR_SCRIPT, {'error_code': SubtitlesErrors.UNKNOWN_ERROR, 'provider': ''})


def scriptFinished(subtitlesDict):
    send(Messages.MESSAGE_FINISHED_SCRIPT, subtitlesDict)


def scriptCancelled(subtitlesDict):
    send(Messages.MESSAGE_CANCELLED_SCRIPT, subtitlesDict)


def searchSubtitles(seeker, options):
    seekers = options.get('providers')
    title = options.get('title')
    filepath = options.get('filepath')
    langs = options.get('langs')
    year = options.get('year')
    tvshow = options.get('tvshow')
    season = options.get('season')
    episode = options.get('episode')
    timeout = options.get('timeout', 10)
    return seeker.getSubtitles(seekers, updateCB, title, filepath, langs, year, tvshow, season, episode, timeout)


def downloadSubtitles(seeker, options):
    overwriteFileCBTmp = None
    if options.get('settings').get('ask_overwrite'):
        overwriteFileCBTmp = overwriteFileCB

    return seeker.downloadSubtitle(
        options.get("selected_subtitle"),
        options.get("subtitles_dict"),
        chooseFileCB,
        options.get("path"),
        options.get("filename"),
        overwriteFileCBTmp,
        options.get("settings"))


def main():
    global stdout
    stdout = sys.stdout
    sys.stdout = open('/tmp/subssupport.log', 'w')
    sys.stderr = sys.stdout
    options = recieve()
    print('recieved options: %r' % options)
    try:
        from .seek import SubsSeeker
    except (ValueError, ImportError):
        from seek import SubsSeeker
    seeker = SubsSeeker(options.get('download_path', '/tmp/'),
                        options.get('tmp_path', '/tmp/'),
                        captchaCB, delayCB, messageCB,
                        options.get('settings'))
    if options.get('search'):
        return searchSubtitles(seeker, options['search'])
    elif options.get('download'):
        return downloadSubtitles(seeker, options['download'])


if __name__ == '__main__':
    try:
        scriptFinished(main())
        stdout.close()
        sys.stdout.close()
        sys.exit(0)
    except KeyboardInterrupt:
        scriptCancelled({})
        stdout.close()
        sys.stdout.flush()
        sys.stdout.close()
        sys.exit(0)
    except Exception as e:
        traceback.print_exc()
        scriptError(e)
        stdout.close()
        sys.stdout.close()
        sys.exit(1)
