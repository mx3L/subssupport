from __future__ import absolute_import
import re
import traceback
from .baseparser import BaseParser, ParseError, HEX_COLORS


class MicroDVDParser(BaseParser):
    parsing = ('.sub', '.txt')
    format = "MicroDVD"

    def _removeTags(self, text):
        return re.sub('\{[^\}]*\}', '', text)

    #{0}{25}{c:$BBGGRR}Hello!
    def _getColor(self, text, color):
        newColor = color
        colorMatch = re.search('\{c\:([^\}]+)', text)
        if color:
            if colorMatch:
                colortext = colorMatch.group(1)
                colorbgrMatch = re.search("\$([0-9,a-f,A-F]{6})", colortext)
                if colorbgrMatch:
                    colorbgr = colorbgrMatch.group(1)
                    color = newColor = colorbgr[4:6] + colorbgr[2:4] + colorbgr[:2]
                else:
                    try:
                        color = newColor = HEX_COLORS[colortext.lower()][1:]
                    except KeyError:
                        pass
        else:
            if colorMatch:
                colortext = colorMatch.group(1)
                colorbgrMatch = re.search("\$([0-9,a-f,A-F]{6})", colortext)
                if colorbgrMatch:
                    colorbgr = colorbgrMatch.group(1)
                    color = colorbgr[4:6] + colorbgr[2:4] + colorbgr[:2]
                else:
                    try:
                        color = HEX_COLORS[colortext.lower()][1:]
                    except KeyError:
                        color = 'default'
            else:
                color = 'default'
        return color, newColor

    #{0}{25}{y:i}Hello!
    def _getStyle(self, text, style):
        newStyle = style
        styleMatch = re.search('\{y\:(?P<style>[ibus])\}', text)
        if style:
            if styleMatch:
                if styleMatch.group('style') == 'b':
                    style = newStyle = 'bold'
                elif styleMatch.group('style') == 'i':
                    style = newStyle = 'italic'
                elif styleMatch.group('style') == 'u':
                    style = newStyle = 'underline'
        else:
            if styleMatch:
                if styleMatch.group('style') == 'b':
                    style = 'bold'
                elif styleMatch.group('style') == 'i':
                    style = 'italic'
                elif styleMatch.group('style') == 'u':
                    style = 'underline'
                else:
                    style = 'regular'
            else:
                style = 'regular'
        return style, newStyle

    def _parse(self, text, fps):
        subs = []
        idx = 0
        if fps is None:
            raise ParseError("cannot parse, FPS not provided")

        for m in re.finditer("\{(\d+)\}\{(\d+)\}(.*)", text):
            try:
                startTime = float(int(m.group(1)) / float(fps)) * 1000
                endTime = float(int(m.group(2)) / float(fps)) * 1000
                text = '\n'.join(m.group(3).split('|'))
                subs.append(self.createSub(text, startTime, endTime))
            except Exception as e:
                traceback.print_exc()
                raise ParseError(str(e) + ', subtitle_index: %d' % idx)
        return subs


parserClass = MicroDVDParser
