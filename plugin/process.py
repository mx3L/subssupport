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

from __future__ import absolute_import, division
import os
import traceback

from .parsers.baseparser import ParseError, NoSubtitlesParseError
from .seekers.utilities import getFileSize, SimpleLogger
from .utils import load, decode, toString

from six.moves.urllib.error import URLError, HTTPError


SUBTITLES_FILE_MAX_SIZE = 400 * 1024  # 400KB


class ParserNotFoundError(Exception):
    pass


class DecodeError(Exception):
    pass


class LoadError(Exception):
    pass


class SubsLoader(object):
    def __init__(self, parsers_cls, encodings=None):
        self._parsers = [parser_cls() for parser_cls in parsers_cls]
        self._encodings = ['utf-8']
        if encodings:
            self._encodings = encodings
        self._row_parsing = False
        self.log = SimpleLogger('SubsLoader',)

    def toggle_row_parsing(self):
        if self._row_parsing:
            self.set_row_parsing(False)
        else:
            self.set_row_parsing(True)

    def set_row_parsing(self, val):
        for parser in self._parsers:
            parser.rowParse = val
        if val:
            self.log.info("setting row parsing for Parsers")
            self._row_parsing = True
        else:
            self.log.info("setting block parsing for Parsers")
            self._row_parsing = False

    def change_encodings(self, encodings):
        self.log.info("changing encoding group to: %s" % str(encodings))
        self._encodings = encodings

    def change_encoding(self, text, current_encoding):
        try:
            decoded_text, encoding = decode(text, self._encodings, current_encoding)
        except Exception:
            traceback.print_exc()
            self.log.error("cannot decode subtitles'")
            raise DecodeError()

        return decoded_text, encoding

    def load(self, subfile, current_encoding=None, fps=None):
        filename = os.path.basename(subfile)
        self.log.info("<%s> loading ...", filename)
        while True:
            decoded_text, encoding = self._process_path(subfile, current_encoding)
            try:
                sublist = self._parse(decoded_text, os.path.splitext(subfile)[1], fps)
            except NoSubtitlesParseError:
                # this could mean that subtitles file was decoded but
                # with not right encoding, we try to use other encodings
                if current_encoding == self._encodings[-1]:
                    raise
                self.log.info("<%s> no subtitles parsed, will try different encoding", filename)
                current_encoding = encoding
                continue
            self.log.info("<%s> successfully loaded", filename)
            return sublist, encoding

    def _process_path(self, subfile, current_encoding=None):
        filename = os.path.basename(subfile)
        size = getFileSize(subfile)
        if size and size > SUBTITLES_FILE_MAX_SIZE:
            self.log.error("<%s> not supported subtitles size ({%d}KB > {%d}KB)!", filename, size // 1024, SUBTITLES_FILE_MAX_SIZE // 1024)
            raise LoadError('"%s" - not supported subtitles size: "%dKB"' % (toString(os.path.basename(subfile)), size // 1024))
        try:
            text = load(subfile)
        except (URLError, HTTPError, IOError) as e:
            self.log.error("<%s> %s", filename, str(e))
            raise LoadError(subfile)
        try:
            decoded_text, encoding = decode(text, self._encodings, current_encoding)
        except Exception as e:
            self.log.error("<%s> %s", filename, "cannot decode")
            raise DecodeError(subfile)
        return decoded_text, encoding

    def _parse(self, text, ext=None, fps=None, strict=False):
        self.log.info("looking for '%s' parser", str(ext))
        for parser in self._parsers:
            if not ext:
                self.log.info("extension is not set, parsing without it ...")
                break
            if parser.canParse(ext):
                self.log.info("found <%s> parser", parser)
                self.log.info("<%s> parsing...", parser)
                try:
                    return parser.parse(text, fps)
                except ParseError as e:
                    self.log.error("<%s>: %s", parser, str(e))
                    if strict:
                        raise
        for parser in self._parsers:
            self.log.info("trying parsing with <%s>", parser)
            try:
                return parser.parse(text, fps)
            except NoSubtitlesParseError as e:
                if parser == self._parsers[-1]:
                    raise
                continue
            except ParseError as e:
                self.log.error("<%s>: %s", parser, str(e))
                continue
        raise ParserNotFoundError(str(ext))
