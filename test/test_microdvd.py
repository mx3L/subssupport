import os
import sys
import unittest

test = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(test, '..', 'plugin'))

from parsers import SubRipParser, MicroDVDParser

PARSERS = [SubRipParser, MicroDVDParser]


class TestMicroDVDBlockParser (unittest.TestCase):
    def setUp(self):
      self.parser = MicroDVDParser()

    def test_italics(self):
      text = "{y:i}Jsme skupina Pinheads."
      style = self.parser.getStyle(text, None)
      self.assertTrue(style[0] == 'italic', "style == %s" % style[0])

    def test_bold(self):
        text = "{y:b}Jsme skupina Pinheads."
        style = self.parser.getStyle(text, None)
        self.assertTrue(style[0] == 'bold', "style == %s" % style[0])

    def test_color(self):
        text = "{c:$112233}Hello!"
        color = self.parser.getColor(text, None)
        self.assertTrue(color[0] == '332211', "color == %s" % color[0])

    def test_text_color(self):
        text = "{c:red}Hello!"
        color = self.parser.getColor(text, None)
        self.assertTrue(color[0] == 'FF0000', "color == %s" % color[0])

    def test_remove_tags(self):
        text = "{c:$0000ff}{y:b,u}{f:DeJaVuSans}{s:12}Hello!"
        cleaned = self.parser.removeTags(text)
        self.assertTrue(cleaned == 'Hello!', "text == %s" % cleaned)


class TestMicroDVDRowParser(unittest.TestCase):
    def setUp(self):
      self.parser = MicroDVDParser(True)
