from __future__ import print_function
import os

import six
from six.moves import urllib


def load(subpath):
    if subpath.startswith('http'):
        req = urllib.request.Request(subpath)
        try:
            response = urllib.request.urlopen(req)
            text = response.read()
        except Exception:
            raise
        finally:
            if 'response' in locals():
                response.close()
        return text
    else:
        try:
            with open(subpath, 'rb') as f:
                return f.read()
        except Exception:
            return ""


def toString(text):
    if isinstance(text, str):
        if isinstance(text, six.text_type):
            return six.ensure_str(text)
    return text


def toUnicode(text):
    if isinstance(text, str):
        if isinstance(text, str):
            return six.ensure_text(text, errors='ignore')
    return text


def decode(text, encodings, current_encoding=None, decode_from_start=False):
    utext = None
    used_encoding = None
    current_encoding_idx = -1
    current_idx = 0

    if decode_from_start:
        current_encoding = None

    if current_encoding is not None:
        current_encoding_idx = encodings.index(current_encoding)
        current_idx = current_encoding_idx + 1
        if current_idx >= len(encodings):
            current_idx = 0

    while current_idx != current_encoding_idx:
        enc = encodings[current_idx]
        try:
            print('[decode] trying encoding', enc, '...')
            utext = text.decode(enc)
            print('[decode] decoded with', enc, 'encoding')
            used_encoding = enc
            return utext, used_encoding
        except Exception:
            if enc == encodings[-1] and current_encoding_idx == -1:
                print('[decode] cannot decode with provided encodings')
                raise Exception("decode error")
            elif enc == encodings[-1] and current_encoding_idx != -1:
                current_idx = 0
                continue
            else:
                current_idx += 1
                continue


class HeadRequest(urllib.request.Request):
    def get_method(self):
        return "HEAD"


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


class SimpleLogger(object):

    LOG_FORMAT = "[{0}]{1}"
    LOG_NONE, LOG_ERROR, LOG_INFO, LOG_DEBUG = list(range(4))

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
        elif len(args) >= 1:
            text = text % tuple([toString(a) for a in args])
        return text

    def _format_output(self, text):
            return self.LOG_FORMAT.format(self.prefix_name, text)

    def _out_fnc(self, text):
        print(text)
