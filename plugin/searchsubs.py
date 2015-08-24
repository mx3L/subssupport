'''
Created on Aug 2, 2014

@author: marko
'''

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

def send(mtype, m):
    dump = json.dumps({'message':mtype, 'value':m})
    dump = "%07d%s" % (len(dump)+7, dump)
    stdout.write(dump)
    stdout.flush()

def recieve():
    return  json.loads(sys.stdin.read(int(sys.stdin.read(7))))

def delayCB(seconds):
    send(Messages.MESSAGE_DELAY_CALLBACK, seconds)
    time.sleep(seconds)

def captchaCB(image):
    send(Messages.MESSAGE_CAPTCHA_CALLBACK, image)
    return recieve()

def messageCB(text):
    print 'messageCB:', text

def updateCB(*args):
    send(Messages.MESSAGE_UPDATE_CALLBACK, args)

def scriptError(exc):
    send(Messages.MESSAGE_ERROR_SCRIPT, exc)

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

def main():
    global stdout
    stdout = sys.stdout
    stderr = sys.stderr
    sys.stdout = open('/tmp/subssupport.log','w')
    sys.stderr = sys.stdout
    options = recieve()
    print 'recieved options: %r'%options
    from seek import SubsSeeker
    seeker = SubsSeeker(options.get('download_path','/tmp/'),
                        options.get('tmp_path','/tmp/'),
                        captchaCB, delayCB, messageCB,
                        options.get('settings'))
    return searchSubtitles(seeker, options['search'])

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
