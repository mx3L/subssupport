# -*- coding: UTF-8 -*-
#################################################################################
#
#    SubsSupport 1.2.0 for Enigma2
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

from __future__ import absolute_import
from __future__ import print_function

from Plugins.Plugin import PluginDescriptor
from datetime import datetime
import json
import os
import re
import sys
from threading import Thread
import traceback
from twisted.internet.defer import Deferred
from twisted.web import client
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, loadPNG, RT_WRAP, eConsoleAppContainer, eServiceCenter, eServiceReference, getDesktop, loadPic, loadJPG, RT_VALIGN_CENTER, gPixmapPtr, ePicLoad, eTimer
from ServiceReference import ServiceReference
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.ConfigList import ConfigListScreen
from Components.GUIComponent import GUIComponent
from Components.Harddisk import harddiskmanager
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, \
    MultiContentEntryPixmapAlphaTest
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.Boolean import Boolean
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.config import ConfigSubsection, ConfigSelection, ConfigYesNo, \
    configfile, getConfigListEntry, config, ConfigText, ConfigDirectory, ConfigOnOff, \
    ConfigNothing, ConfigInteger, NoSave, KEY_DELETE, KEY_BACKSPACE, \
    KEY_TIMEOUT, KEY_ASCII
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarNotifications
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools import Notifications
from Tools.Directories import SCOPE_CURRENT_SKIN, SCOPE_SKIN, SCOPE_PLUGINS, resolveFilename, pathExists, \
    fileExists
from Tools.ISO639 import LanguageCodes
from Tools.LoadPixmap import LoadPixmap
from six.moves import reload_module
from .compat import eConnectCallback, FileList
from .e2_utils import messageCB, E2SettingsProvider, MyLanguageSelection, unrar, \
    ConfigFinalText, Captcha, DelayMessageBox, MyConfigList, getFps, fps_float, \
    getFonts, BaseMenuScreen, isFullHD, isHD, getDesktopSize
from enigma import eTimer, eConsoleAppContainer, ePythonMessagePump, eSize, ePoint, RT_HALIGN_LEFT, \
    RT_HALIGN_RIGHT, RT_VALIGN_CENTER, eListboxPythonMultiContent, \
    getDesktop, eServiceCenter, eServiceReference, \
    iPlayableService, gFont, \
    gRGB, loadPNG, eLabel, eEnv
from .parsers import SubRipParser, MicroDVDParser
from .process import SubsLoader, DecodeError, ParseError, ParserNotFoundError, \
    LoadError
from .searchsubs import Messages
from .seek import SubsSeeker, SubtitlesDownloadError, SubtitlesErrors
from .seekers.utilities import detectSearchParams, languageTranslate
from skin import parseColor, parsePosition, parseFont
from .utils import toString, SimpleLogger, toUnicode

from . import _, __author__, __version__, __email__

import six
from six.moves.queue import Queue
from six.moves import range
from six.moves import urllib
from six.moves.urllib.parse import quote

try:
    from xml.etree.cElementTree import parse as parse_xml
except ImportError:
    from xml.etree.ElementTree import parse as parse_xml


try:
    from Screens.AudioSelection import QuickSubtitlesConfigMenu
except ImportError:
    QuickSubtitlesConfigMenu = None

if six.PY3:
    long = int

# localization function

def warningMessage(session, text):
    session.open(MessageBox, text, type=MessageBox.TYPE_WARNING, timeout=5)


def debug(text, *args):
    if DEBUG:
        if len(args) == 1 and isinstance(args[0], tuple):
            text = text % args[0]
        else:
            text = text % (args)
        print("[SubsSupport]", toString('utf-8'))


# set the name of plugin in which this library belongs
# PLUGIN_NAME = 'mediaplayer2'

# set debug mode
DEBUG = False

# set supported encodings, you have to make sure, that you have corresponding python
# libraries in %PYTHON_PATH%/encodings/ (ie. iso-8859-2 requires iso_8859_2.searchsubs library)

# to choose encodings for region you want, visit:
# http://docs.python.org/release/2.4.4/lib/standard-encodings.html

# Common encodings for all languages
ALL_LANGUAGES_ENCODINGS = ['utf-8', 'utf-16']

# other encodings, sorted according usage
CENTRAL_EASTERN_EUROPE_ENCODINGS = ['windows-1250', 'iso-8859-2', 'maclatin2', 'IBM852']
WESTERN_EUROPE_ENCODINGS = ['windows-1252', 'iso-8859-15', 'macroman', 'ibm1140', 'IBM850']
RUSSIAN_ENCODINGS = ['windows-1251', 'cyrillic', 'maccyrillic', 'koi8_r', 'IBM866']
ARABIC_ENCODINGS = ['windows-1256', 'iso-8859-6', 'IBM864']
TURKISH_ENCODINGS = ['windows-1254', 'iso-8859-9', 'latin5', 'macturkish', 'ibm1026', 'IBM857']
GREEK_ENCODINGS = ['windows-1253', 'iso-8859-7', 'macgreek']
HEBREW_ENCODINGS = ['windows-1255', 'iso-8859-8', 'IBM862']

ENCODINGS = {("Central and Eastern Europe"): CENTRAL_EASTERN_EUROPE_ENCODINGS,
            ("Western Europe"): WESTERN_EUROPE_ENCODINGS,
            ("Russia"): RUSSIAN_ENCODINGS,
            ("Arabic"): ARABIC_ENCODINGS,
            ("Turkish"): TURKISH_ENCODINGS,
            ("Greek"): GREEK_ENCODINGS,
            ("Hebrew"): HEBREW_ENCODINGS}

# initializing parsers
PARSERS = [SubRipParser, MicroDVDParser]


def getDefaultFont(fontType):
    ubuntu = None
    openpli = None
    for f in getFonts():
        if fontType == "regular":
            if f == "Subs":
                openpli = f
            elif f == "Ubuntu-M":
                ubuntu = f
        elif fontType == "italic":
            if f == "Subsi":
                openpli = f
            elif f == "Ubuntu-MI":
                ubuntu = f
        elif fontType == "bold":
            if f == "Subsb":
                openpli = f
            elif f == "Ubuntu-B":
                ubuntu = f
    if ubuntu:
        return ubuntu
    if openpli:
        return openpli
    return "Regular"


def getEmbeddedFontSizeCfg(defaultFontSizeCfg):
    CONFIG_SUBTITLES_OPENPLI = "subtitles"
    CONFIG_FONTSIZE_OPENPLI = "subtitle_fontsize"
    CONFIG_SUBTITLES_VTI = "subtitle"
    CONFIG_FONTSIZE_VTI = "subtitlefontsize"

    try:
        subtitles_pli_cfg = getattr(config, CONFIG_SUBTITLES_OPENPLI)
    except KeyError:
        subtitles_pli_cfg = None
    if subtitles_pli_cfg is not None:
        try:
            return getattr(subtitles_pli_cfg, CONFIG_FONTSIZE_OPENPLI)
        except KeyError:
            pass
    try:
        subtitles_vti_cfg = getattr(config, CONFIG_SUBTITLES_VTI)
    except KeyError:
        subtitles_vti_cfg = None
    if subtitles_vti_cfg is not None:
        try:
            return getattr(subtitles_vti_cfg, CONFIG_FONTSIZE_VTI)
        except KeyError:
            pass
    return defaultFontSizeCfg


GLOBAL_CONFIG_INIT = False

fontChoiceList = [f for f in getFonts()]
fontSizeChoiceList = [("%d" % i, "%d px" % i) for i in range(10, 60, 1)]
positionChoiceList = [("0", _("top"))]
positionChoiceList.extend([("%d" % i, "%d %%" % i) for i in range(1, 100, 1)])
positionChoiceList.append(("100", _("bottom")))
shadowSizeChoiceList = [("%d" % i, "%d px" % i) for i in range(1, 8, 1)]
shadowOffsetChoiceList = [("%d" % i, "%d px" % i) for i in range(-8, -1, 1)]
backgroundOffsetChoiceList = [("%d" % i, "%d px" % i) for i in range(5, 100, 1)]
colorChoiceList = []
colorChoiceList.append(("ff0000", _("red")))
colorChoiceList.append(("DCDCDC", _("grey")))
colorChoiceList.append(("00ff00", _("green")))
colorChoiceList.append(("ff00ff", _("purple")))
colorChoiceList.append(("ffff00", _("yellow")))
colorChoiceList.append(("ffffff", _("white")))
colorChoiceList.append(("00ffff", _("blue")))
colorChoiceList.append(("000000", _("black")))
COLORFILE = os.path.join(os.path.dirname(__file__), 'colors.txt')
print('[SubsSupport] looking for custom colors in', COLORFILE)
try:
    with open(COLORFILE, 'r') as f:
        for line in f:
            color = re.search('^(\w+)\s+([0-9A-Fa-f]{6})$', line)
            if color is not None:
                alias = color.group(1)
                hex_color = color.group(2)
                print('[SubsSupport] adding custom color', alias)
                colorChoiceList.append((hex_color, alias))
except IOError as e:
    print('[SubsSupport] error while loading custom colors', str(e))

alphaChoiceList = [("00", _("opaque"))]
alphaChoiceList.extend([("%02x" % val, "%d %%" % (int(percent * 100 / float(32)))) for percent, val in enumerate(range(0, 256, 8)) if val != 0])
alphaChoiceList.append(("ff", _("transparent")))


def initGeneralSettings(configsubsection):
    configsubsection.pauseVideoOnSubtitlesMenu = ConfigYesNo(default=True)
    configsubsection.encodingsGroup = ConfigSelection(default="Central and Eastern Europe", choices=[(e, _(e)) for e in ENCODINGS.keys()])


def initExternalSettings(configsubsection):
    configsubsection.position = ConfigSelection(default="94", choices=positionChoiceList)
    configsubsection.font = ConfigSubsection()
    configsubsection.font.regular = ConfigSubsection()
    configsubsection.font.regular.type = ConfigSelection(default=getDefaultFont("regular"), choices=fontChoiceList)
    configsubsection.font.regular.alpha = ConfigSelection(default="00", choices=alphaChoiceList)
    configsubsection.font.regular.color = ConfigSelection(default="ffffff", choices=colorChoiceList)
    configsubsection.font.italic = ConfigSubsection()
    configsubsection.font.italic.type = ConfigSelection(default=getDefaultFont("italic"), choices=fontChoiceList)
    configsubsection.font.italic.alpha = ConfigSelection(default="00", choices=alphaChoiceList)
    configsubsection.font.italic.color = ConfigSelection(default="ffffff", choices=colorChoiceList)
    configsubsection.font.bold = ConfigSubsection()
    configsubsection.font.bold.type = ConfigSelection(default=getDefaultFont("bold"), choices=fontChoiceList)
    configsubsection.font.bold.alpha = ConfigSelection(default="00", choices=alphaChoiceList)
    configsubsection.font.bold.color = ConfigSelection(default="ffffff", choices=colorChoiceList)
    configsubsection.font.size = ConfigSelection(default="43", choices=fontSizeChoiceList)
    configsubsection.shadow = ConfigSubsection()
    configsubsection.shadow.enabled = ConfigOnOff(default=True)
    configsubsection.shadow.type = ConfigSelection(default="border", choices=[("offset", _("offset")), ("border", _('border'))])
    configsubsection.shadow.color = ConfigSelection(default="000000", choices=colorChoiceList)
    configsubsection.shadow.size = ConfigSelection(default="2", choices=shadowSizeChoiceList)
    configsubsection.shadow.xOffset = ConfigSelection(default="-3", choices=shadowOffsetChoiceList)
    configsubsection.shadow.yOffset = ConfigSelection(default="-3", choices=shadowOffsetChoiceList)
    configsubsection.background = ConfigSubsection()
    configsubsection.background.enabled = ConfigOnOff(default=True)
    configsubsection.background.type = ConfigSelection(default="dynamic", choices=[("dynamic", _("dynamic")), ("static", _("static"))])
    configsubsection.background.xOffset = ConfigSelection(default="10", choices=backgroundOffsetChoiceList)
    configsubsection.background.yOffset = ConfigSelection(default="10", choices=backgroundOffsetChoiceList)
    configsubsection.background.color = ConfigSelection(default="000000", choices=colorChoiceList)
    configsubsection.background.alpha = ConfigSelection(default="80", choices=alphaChoiceList)


def initEmbeddedSettings(configsubsection):
    configsubsection.position = ConfigSelection(default="94", choices=positionChoiceList)
    configsubsection.font = ConfigSubsection()
    configsubsection.font.regular = ConfigSubsection()
    configsubsection.font.regular.type = ConfigSelection(default=getDefaultFont("regular"), choices=fontChoiceList)
    configsubsection.font.italic = ConfigSubsection()
    configsubsection.font.italic.type = ConfigSelection(default=getDefaultFont("italic"), choices=fontChoiceList)
    configsubsection.font.bold = ConfigSubsection()
    configsubsection.font.bold.type = ConfigSelection(default=getDefaultFont("bold"), choices=fontChoiceList)
    configsubsection.font.size = ConfigSelection(default="34", choices=fontSizeChoiceList)
    configsubsection.color = ConfigSelection(default="ffffff", choices=colorChoiceList)
    configsubsection.shadow = ConfigSubsection()
    configsubsection.shadow.size = ConfigSelection(default="3", choices=shadowSizeChoiceList)
    configsubsection.shadow.color = ConfigSelection(default="000000", choices=colorChoiceList)
    configsubsection.shadow.xOffset = ConfigSelection(default="-3", choices=shadowOffsetChoiceList)
    configsubsection.shadow.yOffset = ConfigSelection(default="-3", choices=shadowOffsetChoiceList)


def initEngineSettings(configsubsection):
    configsubsection.expert = ConfigSubsection()
    configsubsection.expert.show = NoSave(ConfigYesNo(default=False))
    configsubsection.expert.playerDelay = ConfigSelection(default="0", choices=[("%d" % i, "%d ms" % i) for i in range(-20000, 20000, 200)])
    configsubsection.expert.startDelay = ConfigSelection(default="1200", choices=[("%d" % i, "%d ms" % i) for i in range(0, 1500, 100)])
    configsubsection.expert.hideDelay = ConfigSelection(default="200", choices=[("%d" % i, "%d ms" % i) for i in range(0, 1000, 50)])
    configsubsection.expert.ptsDelayCheck = ConfigSelection(default="200", choices=[("%d" % i, "%d ms" % i) for i in range(100, 1000, 100)])
    configsubsection.expert.syncDelay = ConfigSelection(default="300", choices=[("%d" % i, "%d ms" % i) for i in range(100, 1000, 100)])
    configsubsection.expert.refreshDelay = ConfigSelection(default="1000", choices=[("%d" % i, "%d ms" % i) for i in range(200, 3000, 200)])


def initSearchSettings(configsubsection):
    configsubsection.downloadHistory = ConfigSubsection()
    configsubsection.downloadHistory.enabled = ConfigYesNo(default=True)
    configsubsection.downloadHistory.limit = ConfigInteger(default=50, limits=(2, 200))
    configsubsection.downloadHistory.path = ConfigDirectory(default=eEnv.resolve("$localstatedir/lib/subssupport"), visible_width=30)
    configsubsection.downloadHistory.removeAction = ConfigSelection(default='list', choices=[('list', _("List")), ('file', _("List + File"))])
    configsubsection.downloadHistory.removeActionAsk = ConfigYesNo(default=True)
    configsubsection.downloadPath = ConfigDirectory(default="/tmp/")
    configsubsection.tmpPath = ConfigDirectory(default="/tmp/")
    configsubsection.lang1 = ConfigFinalText(default=language.getLanguage()[:2])
    configsubsection.lang2 = ConfigFinalText(default=language.getLanguage()[:2])
    configsubsection.lang3 = ConfigFinalText(default=language.getLanguage()[:2])
    configsubsection.timeout = ConfigSelection(default="10", choices=[(("%d" % i, "%d s" % i)) for i in range(5, 20)])
    configsubsection.history = ConfigText(default="")
    configsubsection.movieProvider = ConfigSelection(default="all", choices=[("all", _("All")), ])
    configsubsection.tvshowProvider = ConfigSelection(default="all", choices=[("all", _("All")), ])
    configsubsection.manualSearch = ConfigYesNo(default=False)
    configsubsection.defaultSort = ConfigSelection(default='lang', choices=[('lang', _("Language")), ('provider', _("Provider"))])
    configsubsection.saveAs = ConfigSelection(default='version', choices=[('default', _("Default")), ('version', _("Release")), ('video', _("Video filename"))])
    configsubsection.saveAsFallback = ConfigSelection(default='version', choices=[('default', _("Default")), ('version', _("Release"))])
    configsubsection.saveTo = ConfigSelection(default='custom', choices=[('custom', _('User defined')), ('video', _('Next to video'))])
    configsubsection.addLangToSubsFilename = ConfigYesNo(default=False)
    configsubsection.askOverwriteExistingSubs = ConfigYesNo(default=True)
    configsubsection.loadSubtitlesAfterDownload = ConfigYesNo(default=True)
    configsubsection.openParamsDialogOnSearch = ConfigYesNo(default=True)
    configsubsection.showProvidersErrorMessage = ConfigYesNo(default=True)
    # session settings
    configsubsection.title = ConfigTextWithSuggestionsAndHistory(configsubsection.history, default="", fixed_size=False)
    configsubsection.type = ConfigSelection(default="movie", choices=[("tv_show", _("TV show")), ("movie", _("Movie"))])
    configsubsection.year = ConfigInteger(default=0, limits=(0, 2100))
    configsubsection.season = ConfigInteger(default=0, limits=(0, 100))
    configsubsection.episode = ConfigInteger(default=0, limits=(0, 100))
    configsubsection.provider = ConfigSelection(default="all", choices=[("all", _("All")), ])
    configsubsection.useFilePath = ConfigYesNo(default=True)


def initSubsSettings(configSubsection=None):
    global GLOBAL_CONFIG_INIT
    if configSubsection:
        print('[SubsSupport] using provided ConfigSubsection to store config')
        subtitles_settings = configSubsection
    elif 'PLUGIN_NAME' in globals():
        print('[SubsSupport] using config.plugins.%s.%s to store config' % (PLUGIN_NAME, 'subtitles'))
        plugin_settings = getattr(config.plugins, PLUGIN_NAME)
        setattr(plugin_settings, 'subtitles', ConfigSubsection())
        subtitles_settings = getattr(plugin_settings, 'subtitles')
    elif GLOBAL_CONFIG_INIT:
        print("[SubsSupport] using global config (already initialized)")
        return config.plugins.subtitlesSupport
    else:
        print("[SubsSupport] using global config")
        config.plugins.subtitlesSupport = ConfigSubsection()
        subtitles_settings = config.plugins.subtitlesSupport
        GLOBAL_CONFIG_INIT = True

    initGeneralSettings(subtitles_settings)
    subtitles_settings.external = ConfigSubsection()
    initExternalSettings(subtitles_settings.external)
    subtitles_settings.embedded = ConfigSubsection()
    initEmbeddedSettings(subtitles_settings.embedded)
    subtitles_settings.engine = ConfigSubsection()
    initEngineSettings(subtitles_settings.engine)
    subtitles_settings.search = ConfigSubsection()
    initSearchSettings(subtitles_settings.search)
    return subtitles_settings


class SubsStatusScreen(Screen, HelpableScreen):

    def __init__(self, session, setSubsDelay, getSubsDelay, subscribeDelay, unsubscribeDelay, toNextSub, toPrevSub, setSubsFps, getSubsFps, subsDelayStepInMs=200, showDelayInMs=False):

        ratio = 1.5 if isFullHD() else 1
        desktopSize = getDesktopSize()
        windowSize = (0.9 * desktopSize[0], 0.15 * desktopSize[1])
        fontSize = 22 * ratio
        delaySize = (0.45 * windowSize[0], windowSize[1])
        fpsSize = (0.45 * windowSize[0], windowSize[1])

        windowPos = (0.05 * desktopSize[0], 0.05 * desktopSize[0])
        delayPos = (0, 0)
        fpsPos = (0.55 * windowSize[0], 0)

        self.skin = """
        <screen position="%d,%d" size="%d,%d" zPosition="5" backgroundColor="transparent" flags="wfNoBorder">
            <widget source="delay" render="Label" position="%d,%d" size="%d,%d" valign="top" halign="left" font="Regular;%d" transparent="1" foregroundColor="#ffffff" shadowColor="#40101010" shadowOffset="2,2" />
            <widget source="fps" render="Label" position="%d,%d" size="%d,%d" valign="top" halign="right" font="Regular;%d" transparent="1" foregroundColor="#6F9EF5" shadowColor="#40101010" shadowOffset="2,2" />
        </screen>""" % (
                windowPos[0], windowPos[1], windowSize[0], windowSize[1],
                delayPos[0], delayPos[1], delaySize[0], delaySize[1], fontSize,
                fpsPos[0], fpsPos[1], fpsSize[0], fpsSize[1], fontSize
                )

        Screen.__init__(self, session)
        HelpableScreen.__init__(self)
        self.setSubsDelay = setSubsDelay
        self.getSubsDelay = getSubsDelay
        self.subscribeDelay = subscribeDelay
        self.unsubscribeDelay = unsubscribeDelay
        self.toNextSub = toNextSub
        self.toPrevSub = toPrevSub
        self.setSubsFps = setSubsFps
        self.getSubsFps = getSubsFps
        self.subsDelayStep = subsDelayStepInMs
        self.showDelayInMs = showDelayInMs
        self.fpsChoices = ["23.976", "23.980", "24.000", "25.000", "29.970", "30.000"]
        self['fps'] = StaticText()
        self['delay'] = StaticText()
        self['SubsArrowActions'] = HelpableActionMap(self, "DirectionActions",
        {
            'right': (self.nextSubDelay, _("jump to next subtitle")),
            'left': (self.prevSubDelay, _("jump to previous subtitle")),
            'up': (self.incSubDelay, _("increase subtitles delay")),
            'down': (self.decSubDelay, _("decrease subtitles delay")),
        })
        self['SubsColorActions'] = HelpableActionMap(self, "ColorActions",
        {
            'red': (self.reset, _("reset subtitles delay/fps")),
            'blue': (self.changeFps, _("change subtitles fps")),
        })
        self['OkCancelActions'] = HelpableActionMap(self, "OkCancelActions",
        {
            'ok': (self.showHelp, _("displays this menu")),
            'cancel': (self.close, _("exit"))
        })
        self._subsDelay = None
        self.onLayoutFinish.append(self._subscribeDelay)
        self.onLayoutFinish.append(self.updateSubsFps)
        self.onLayoutFinish.append(self.updateSubsDelay)
        self.onClose.append(self._unsubscribeDelay)

    def _subscribeDelay(self):
        self.subscribeDelay(self._setSubsDelayAndUpdate)

    def _unsubscribeDelay(self):
        self.unsubscribeDelay(self._setSubsDelayAndUpdate)

    def _setSubsDelayAndUpdate(self, delay):
        self._subsDelay = delay
        self.updateSubsDelay()

    def _getSubsDelay(self):
        if self._subsDelay is None:
            self._subsDelay = self.getSubsDelay()
        return self._subsDelay

    def updateSubsFps(self):
        subsFps = self.getSubsFps()
        videoFps = getFps(self.session, True)
        if subsFps is None or videoFps is None:
            self['fps'].text = "%s: %s" % (_("Subtitles FPS"), _("unknown"))
            return
        if subsFps == videoFps:
            self['fps'].text = "%s: %s" % (_("Subtitles FPS"), _("original"))
        else:
            self['fps'].text = "%s: %s" % (_("Subtitles FPS"), str(subsFps))

    def updateSubsDelay(self):
        subsDelay = self._getSubsDelay()
        if self.showDelayInMs:
            if subsDelay > 0:
                self["delay"].text = "%s: +%dms" % (_("Subtitles Delay"), subsDelay)
            else:
                self["delay"].text = "%s: %dms" % (_("Subtitles Delay"), subsDelay)
        else:
            if subsDelay > 0:
                self["delay"].text = "%s: +%.2fs" % (_("Subtitles Delay"), subsDelay / float(1000))
            else:
                self["delay"].text = "%s: %.2fs" % (_("Subtitles Delay"), subsDelay / float(1000))

    def nextSubDelay(self):
        self.toNextSub()

    def prevSubDelay(self):
        self.toPrevSub()

    def incSubDelay(self):
        self.setSubsDelay(self._getSubsDelay() + self.subsDelayStep)

    def decSubDelay(self):
        self.setSubsDelay(self._getSubsDelay() - self.subsDelayStep)

    def changeFps(self):
        subsFps = self.getSubsFps()
        if subsFps is None:
            return
        currIdx = self.fpsChoices.index(str(subsFps))
        if currIdx == len(self.fpsChoices) - 1:
            nextIdx = 0
        else:
            nextIdx = currIdx + 1
        self.setSubsFps(fps_float(self.fpsChoices[nextIdx]))
        self.updateSubsFps()

    def reset(self):
        self.setSubsFps(getFps(self.session, True))
        self.setSubsDelay(0)
        self.updateSubsFps()


class SubsSupportStatus(object):
    def __init__(self, delayStepInMs=200, showDelayInMs=False, statusScreen=None):
        assert isinstance(self, SubsSupport), "not derived from SubsSupport!"
        self.__delayStepInMs = delayStepInMs
        self.__showDelayInMs = showDelayInMs
        self.__statusScreen = statusScreen
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
            iPlayableService.evStart: self.__serviceChanged,
            iPlayableService.evEnd: self.__serviceChanged,
        })
        self["SubsStatusActions"] = HelpableActionMap(self, "SubtitlesActions",
        {
            "subtitlesStatus": (self.subsStatus, _("change external subtitles status")),
        }, -5)
        self.onClose.append(self.__closeSubsStatusScreen)

    def __serviceChanged(self):
        self.__closeSubsStatusScreen()

    def __closeSubsStatusScreen(self):
        try:
            self.__subsStatusScreen.close()
        except Exception:
            pass

    def subsStatus(self):
        setDelay = self.setSubsDelay
        getDelay = self.getSubsDelay
        subscribe = self.subscribeOnSubsDelayChanged
        unsubscribe = self.unsubscribeOnSubsDelayChanged
        toNextSub = self.setSubsDelayToNextSubtitle
        toPrevSub = self.setSubsDelayToPrevSubtitle
        getFps = self.getSubsFps
        setFps = self.setSubsFps
        if self.isSubsLoaded():
            self.__subsStatusScreen = self.session.open(SubsStatusScreen,
                setDelay, getDelay, subscribe, unsubscribe, toNextSub, toPrevSub, setFps, getFps,
                self.__delayStepInMs, self.__showDelayInMs)
        else:
            if self.__statusScreen is not None:
                self.__statusScreen.setStatus(_("No external subtitles are loaded"))
            elif isinstance(self, InfoBarNotifications):
                Notifications.AddNotification(MessageBox, _("No external subtitles are loaded"), type=MessageBox.TYPE_INFO, timeout=2)


class SubsSupportEmbedded(object):

    def __init__(self, embeddedSupport, preferEmbedded):
        self.embeddedSupport = embeddedSupport
        self.preferEmbedded = preferEmbedded
        self.__subStyles = {}
        self.selected_subtitle = None
        self.subtitle_window = self.session.instantiateDialog(SubsEmbeddedScreen, self.subsSettings.embedded)
        self.subtitle_window.hide()
        if isinstance(self, Screen):
            self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
                    iPlayableService.evStart: self.__serviceChanged,
                    iPlayableService.evEnd: self.__serviceChanged,
                    # iPlayableService.evUpdatedInfo: self.__updatedInfo
                })
            self.onClose.append(self.exitEmbeddedSubs)

    def __isEmbeddedEnabled(self):
        return self.subtitle_window.shown

    embeddedEnabled = property(__isEmbeddedEnabled)

    def getCurrentServiceSubtitle(self):
        service = self.session.nav.getCurrentService()
        return service and service.subtitle()
        
    def __serviceChanged(self):
        if self.selected_subtitle:
            self.selected_subtitle = None
            self.subtitle_window.hide()

    def __updatedInfo(self):
        if not self.selected_subtitle:
            subtitle = self.getCurrentServiceSubtitle()
            cachedsubtitle = subtitle.getCachedSubtitle()
            if cachedsubtitle:
                self.enableSubtitle(cachedsubtitle)

    def enableSubtitle(self, selectedSubtitle):
        print('[SubsSupportEmbedded] enableSubtitle', selectedSubtitle)
        subtitle = self.getCurrentServiceSubtitle()
        self.selected_subtitle = selectedSubtitle
        if subtitle and self.selected_subtitle:
            self.resetEmbeddedSubs()
            subtitle.enableSubtitles(self.subtitle_window.instance, self.selected_subtitle)
            self.subtitle_window.show()
            print('[SubsSupportEmbedded] enable embedded subtitles')
        else:
            print('[SubsSupportEmbedded] disable embedded subtitles')
            if subtitle:
                subtitle.disableSubtitles(self.subtitle_window.instance)
            self.subtitle_window.hide()

    def restartSubtitle(self):
        if self.selected_subtitle:
            print('[SubsSupportEmbedded] restart embedded subtitles')
            self.enableSubtitle(self.selected_subtitle)

    def resetEmbeddedSubs(self, reloadScreen=False):
        if QuickSubtitlesConfigMenu:
            return
        print('[SubsSupportEmbedded] updating  embedded screen')
        from enigma import eWidget, eSubtitleWidget
        scale = ((1, 1), (1, 1))
        embeddedSettings = self.subsSettings.embedded
        fontSize = embeddedSettings.font.size.value
        fontTypeR = embeddedSettings.font.regular.type.value
        fontTypeI = embeddedSettings.font.italic.type.value
        fontTypeB = embeddedSettings.font.bold.type.value
        foregroundColor = "#" + embeddedSettings.color.value
        foregroundColor = parseColor(foregroundColor)
        borderColor = "#" + embeddedSettings.shadow.color.value
        borderColor = parseColor(borderColor)
        borderWidth = int(embeddedSettings.shadow.size.value)
        offset = "%s,%s" % (embeddedSettings.shadow.xOffset.value,
                          embeddedSettings.shadow.yOffset.value)
        shadowOffset = parsePosition(offset, scale)
        fontRegular = parseFont("%s;%s" % (fontTypeR, fontSize), scale)
        fontItalic = parseFont("%s;%s" % (fontTypeI, fontSize), scale)
        fontBold = parseFont("%s;%s" % (fontTypeB, fontSize), scale)
        self._loadEmbeddedStyle({"Subtitle_Regular": (fontRegular, 1, foregroundColor, borderColor, borderWidth, borderColor, shadowOffset),
                                "Subtitle_Italic": (fontItalic, 1, foregroundColor, borderColor, borderWidth, borderColor, shadowOffset),
                                "Subtitle_Bold": (fontBold, 1, foregroundColor, borderColor, borderWidth, borderColor, shadowOffset)})
        if reloadScreen:
            print('[SubsSupportEmbedded] reloading embedded screen')
            subtitle = self.getCurrentServiceSubtitle()
            if subtitle:
                subtitle.disableSubtitles(self.subtitle_window.instance)
            self.session.deleteDialog(self.subtitle_window)
            self.subtitle_window = None
            self.subtitle_window = self.session.instantiateDialog(SubsEmbeddedScreen, self.subsSettings.embedded)
            self.subtitle_window.hide()
            self.restartSubtitle()

    def _parseEmbeddedStyles(self, filename):
        if filename in self.__subStyles:
            return self.defaultStyles[filename]
        skin = parse_xml(filename).getroot()
        for c in skin.findall("subtitles"):
            scale = ((1, 1), (1, 1))
            substyles = {}
            for substyle in c.findall("sub"):
                get_attr = substyle.attrib.get
                font = parseFont(get_attr("font"), scale)
                col = get_attr("foregroundColor")
                if col:
                    foregroundColor = parseColor(col)
                    haveColor = 1
                else:
                    foregroundColor = gRGB(0xFFFFFF)
                    haveColor = 0
                col = get_attr("borderColor")
                if col:
                    borderColor = parseColor(col)
                else:
                    borderColor = gRGB(0)
                borderwidth = get_attr("borderWidth")
                if borderwidth is None:
                    # default: use a subtitle border
                    borderWidth = 3
                else:
                    borderWidth = int(borderwidth)
                col = get_attr("shadowColor")
                if col:
                        shadowColor = parseColor(col)
                else:
                        shadowColor = gRGB(0)
                col = get_attr("shadowOffset")
                if col:
                    shadowOffset = get_attr("shadowOffset")
                else:
                    shadowOffset = "-3,-3"
                shadowOffset = parsePosition(shadowOffset, scale)
                substyles[get_attr("name")] = (font, haveColor, foregroundColor, borderColor, borderWidth, shadowColor, shadowOffset)
                self.__subStyles[filename] = substyle
            return substyles

    def _loadEmbeddedStyle(self, substyles):
        from enigma import eWidget, eSubtitleWidget
        for faceName in substyles.keys():
            s = substyles[faceName]
            face = eSubtitleWidget.__dict__[faceName]
            font, haveColor, foregroundColor, borderColor, borderWidth, shadowColor, shadowOffset = s[0], s[1], s[2], s[3], s[4], s[5], s[6]
            try:
                eSubtitleWidget.setFontStyle(face, font, haveColor, foregroundColor, borderColor, borderWidth)
            except TypeError:
                eSubtitleWidget.setFontStyle(face, font, haveColor, foregroundColor, shadowColor, shadowOffset)

    def resetEmbeddedDefaults(self):
        userSkin = resolveFilename(SCOPE_SKIN, 'skin_user.xml')
        defaultSkin = resolveFilename(SCOPE_SKIN, 'skin_default.xml')
        skinSubtitles = resolveFilename(SCOPE_SKIN, 'skin_subtitles.xml')
        skinPaths = [userSkin, skinSubtitles, defaultSkin]
        for skinPath in skinPaths:
            if fileExists(skinPath):
                styles = self._parseEmbeddedStyles(skinPath)
                if styles:
                    print("[SubsEmbeddedSupport] reseting defaults from", skinPath)
                    self._loadEmbeddedStyle(styles)
                    break

    def exitEmbeddedSubs(self):
        if self.subtitle_window is not None:
            self.session.deleteDialog(self.subtitle_window)
            self.subtitle_window = None
        if not QuickSubtitlesConfigMenu:
            self.resetEmbeddedDefaults()


class SubsSupport(SubsSupportEmbedded):
    """Client class for subtitles

        If this class is not subclass of Screen  you should  use public function of this class to
        to connect your media player (resume,pause,exit,after seeking, subtitles setup)
        functions with subtitles

    @param session: set active session
    @param subsPath: set path for subtitles to load
    @param defaultPath: set default path when choosing external subtitles
    @param forceDefaultPath: always use default path when choosing external subtitles
    @param autoLoad: tries to auto load  subtitles according to name of played file
    @param embeddedSupport: added support for embedded subtitles
    """

    def __init__(self, session=None, subsPath=None, defaultPath=None, forceDefaultPath=False, autoLoad=True,
                 showGUIInfoMessages=True, embeddedSupport=False, preferEmbedded=False, searchSupport=False, configEntry=None):
        if session is not None:
            self.session = session
        self.searchSupport = searchSupport
        self.subsSettings = initSubsSettings(configEntry)
        SubsSupportEmbedded.__init__(self, embeddedSupport, preferEmbedded)
        self.__subsScreen = self.session.instantiateDialog(SubsScreen, self.subsSettings.external)
        self.__subsScreen.hide()
        self.__subsEngine = SubsEngine(self.session, self.subsSettings.engine, self.__subsScreen)
        self.__subsLoader = SubsLoader(PARSERS, ALL_LANGUAGES_ENCODINGS + ENCODINGS[self.subsSettings.encodingsGroup.getValue()])
        self.__subsLoader.set_row_parsing(False)
        self.__loaded = False
        self.__working = False
        self.__firstStart = True
        self.__autoLoad = autoLoad
        self.__subsPath = None
        self.__subsDir = None
        self.__subsEnc = None
        self.__playerDelay = 0
        self.__startDelay = int(self.subsSettings.engine.expert.startDelay.value)
        self.__defaultPath = None
        self.__isServiceSet = False
        self.__subclassOfScreen = isinstance(self, Screen)
        self.__forceDefaultPath = forceDefaultPath
        self.__showGUIInfoMessages = showGUIInfoMessages
        self.__checkTimer = eTimer()
        self.__checkTimer_conn = None
        self.__starTimer = eTimer()
        self.__startTimer_conn = eConnectCallback(self.__starTimer.timeout, self.__updateSubs)
        try:
            from Screens.InfoBar import InfoBar
            InfoBar.instance.subtitle_window.hide()
        except Exception:
            pass

        if self.__subclassOfScreen:
            self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
                iPlayableService.evStart: self.__serviceStarted,
                iPlayableService.evEnd: self.__serviceStopped,
                iPlayableService.evSeekableStatusChanged: self.__seekableStatusChanged,
            })
            self["SubsActions"] = HelpableActionMap(self, "SubtitlesActions",
                {
                "subtitles": (self.subsMenu, _("show subtitles menu")),
                }, -5)

            self.onClose.append(self.exitSubs)

        if defaultPath is not None and os.path.isdir(toString(defaultPath)):
            self.__defaultPath = toString(defaultPath)
            self.__subsDir = toString(defaultPath)

        if subsPath is not None and self.__autoLoad:
            self.loadSubs(subsPath)

    def loadSubs(self, subsPath, newService=True):
        """loads subtitles from subsPath
        @param subsPath: path to subtitles (http url supported)
        @param newService: set False if service remains the same
        @return: True if subtitles was successfully loaded
        @return: False if subtitles wasnt successfully loaded
        """
        self.__working = True
        self.__subsPath = None
        if self.__defaultPath is not None:
            self.__subsDir = self.__defaultPath
        else:
            self.__subsDir = None

        if subsPath is not None:
            subsPath = toString(subsPath)
            if not subsPath.startswith('http'):
                if self.__defaultPath is not None and self.__forceDefaultPath:
                    self.__subsDir = self.__defaultPath
                else:
                    if os.path.isdir(os.path.dirname(subsPath)):
                        self.__subsDir = os.path.dirname(subsPath)
                    else:
                        self.__subsDir = self.__defaultPath
                if not os.path.isfile(subsPath):
                    print('[Subtitles] trying to load not existing path:', subsPath)
                    subsPath = None

            if subsPath is not None:
                subsList, self.__subsEnc = self.__processSubs(subsPath, self.__subsEnc)
                if subsList is not None:
                    self.__subsPath = subsPath
                    if newService:
                        self.__subsEngine.reset()
                    self.__subsEngine.pause()
                    self.__subsEngine.setPlayerDelay(self.__playerDelay)
                    self.__subsEngine.setSubsList(subsList)
                    self.__loaded = True
                    self.__working = False
                    return True
                else:
                    self.__subsEnc = None
                    self.__subsPath = None
        self.__working = False
        return False

    def startSubs(self, time):
        """If subtitles are loaded then start to play them after time set in ms"""
        def wrapped():
            self.__startTimer.start(time, True)

        if self.__working or self.__loaded:
            self.__afterWork(wrapped)

    def isSubsLoaded(self):
        return self.__loaded

    def getSubsFileFromSref(self):
        ref = self.session.nav.getCurrentlyPlayingServiceReference()
        path = ref and ref.getPath()
        if path and os.path.isdir(os.path.dirname(path)):
            self.__subsDir = os.path.dirname(path)
            for parser in PARSERS:
                for ext in parser.parsing:
                    subsPath = os.path.splitext(path)[0] + ext
                    if os.path.isfile(subsPath):
                        return subsPath
        return None

    def resumeSubs(self):
        if self.__loaded:
            print('[Subtitles] resuming subtitles')
            self.showSubsDialog()
            self.__subsEngine.resume()

    def pauseSubs(self):
        if self.__loaded:
            print('[Subtitles] pausing subtitles')
            self.__subsEngine.pause()

    def playAfterSeek(self):
        if self.__loaded:
            self.showSubsDialog()
            self.__subsEngine.sync()

    def showSubsDialog(self):
        if self.__loaded:
            print('[Subtitles] show dialog')
            self.__subsScreen.show()

    def hideSubsDialog(self):
        if self.__loaded:
            print('[Subtitles] hide dialog')
            if self.__subsScreen:
                self.__subsScreen.hide()

    def setPlayerDelay(self, delayInMs):
        self.__playerDelay = delayInMs

    def subscribeOnSubsDelayChanged(self, fnc):
        if fnc not in self.__subsEngine.onSubsDelayChanged:
            self.__subsEngine.onSubsDelayChanged.append(fnc)

    def unsubscribeOnSubsDelayChanged(self, fnc):
        if fnc in self.__subsEngine.onSubsDelayChanged:
            self.__subsEngine.onSubsDelayChanged.remove(fnc)

    def setSubsDelay(self, delayInMs):
        if self.__loaded:
            self.__subsEngine.setSubsDelay(delayInMs)

    def setSubsDelayToNextSubtitle(self):
        if self.__loaded:
            self.__subsEngine.setSubsDelayToNextSubtitle()

    def setSubsDelayToPrevSubtitle(self):
        if self.__loaded:
            self.__subsEngine.setSubsDelayToPrevSubtitle()

    def getSubsDelay(self):
        if self.__loaded:
            return self.__subsEngine.getSubsDelay()

    def subscribeOnSubsFpsChanged(self, fnc):
        if fnc not in self.__subsEngine.onFpsChanged:
            self.__subsEngine.onFpsChanged.append(fnc)

    def unsubscribeOnSubsFpsChanged(self, fnc):
        if fnc in self.__subsEngine.onFpsChanged:
            self.__subsEngine.onFpsChanged.remove(fnc)

    def setSubsFps(self, fps):
        if self.__loaded:
            return self.__subsEngine.setSubsFps(fps)

    def getSubsFps(self):
        if self.__loaded:
            return self.__subsEngine.getSubsFps()

    def getSubsPath(self):
        return self.__subsPath

    def subsMenu(self):
        if not self.__working and not (self.__subclassOfScreen and not self.__isServiceSet):
            self.__alreadyPausedVideo = False
            if self.subsSettings.pauseVideoOnSubtitlesMenu.value:
                print('[SubsSupport] stopVideoOnSubtitlesMenu: True')
                if isinstance(self, InfoBarSeek):
                    if self.seekstate == InfoBarSeek.SEEK_STATE_PLAY:
                        print('[SubsSupport] pausing video')
                        self.setSeekState(InfoBarSeek.SEEK_STATE_PAUSE)
                    else:
                        print('[SubsSupport] video is already paused')
                        self.__alreadyPausedVideo = True
                else:
                    print('[SubsSupport] not subclass of InfobarSeek')
            self.session.openWithCallback(self.__subsMenuCB, SubsMenu, self,
                                          self.__subsPath, self.__subsDir, self.__subsEnc, self.embeddedSupport, self.embeddedEnabled, self.searchSupport)

    def resetSubs(self, resetEnc=True, resetEngine=True, newSubsScreen=False, newService=True):
        """
        Resets subtitle state -> stops engine, reload encodings, reset paths..
        @param resetEnc : start trying encodings from beginning of  current encodings-group list
        @param resetEngine: clean active subtitle, subtitle list, reset engine vars
        @param newSubsSCreen: recreates subtitles screen
        @param newService: set to True if new servicereference is in use
        """
        # start trying encodings from beginning of encodings_group list
        if resetEnc:
            self.__subsEnc = None
        self.__subsLoader.change_encodings(ALL_LANGUAGES_ENCODINGS + ENCODINGS[self.subsSettings.encodingsGroup.getValue()])
        self.__subsEngine.pause()
        # stop subtitles, clean active subtitle,  subtitles list, reset delay
        # if new service -> remove service
        if resetEngine:
            self.__subsEngine.setSubsDelay(0)
            self.__subsEngine.reset()
            if newService:
                self.__firstStart = False
        # hide subtitles, reload screen with new settings
        # if  newSubsScreen, remove current subscreen and create new one
        self.__resetSubsScreen(newSubsScreen)
        self.__subsPath = None
        self.__loaded = False

    def __resetSubsScreen(self, newSubsScreen=False):
        self.__subsScreen.hide()
        if newSubsScreen:
            self.__subsEngine.setRenderer(None)
            self.session.deleteDialog(self.__subsScreen)
            self.__subsScreen = self.session.instantiateDialog(self._getSubsScreenCls(), self.subsSettings.external)
            self.__subsEngine.setRenderer(self.__subsScreen)
        else:
            self.__subsScreen.reloadSettings()
        self.__subsScreen.show()

    def exitSubs(self):
        """This method should be called at the end of usage of this class"""
        self.hideSubsDialog()

        if self.__subsEngine:
            self.__subsEngine.exit()
            self.__subsEngine = None

        if self.__subsScreen:
            self.session.deleteDialog(self.__subsScreen)
            self.__subsScreen = None

        self.__starTimer.stop()
        del self.__startTimer_conn
        del self.__starTimer

        self.__checkTimer.stop()
        del self.__checkTimer_conn
        del self.__checkTimer

        print('[SubsSupport] closing subtitleDisplay')

    def __subsMenuCB(self, subsPath, subsEmbedded, settingsChanged, changeEncoding,
                     changedEncodingGroup, changedShadowType, reloadEmbeddedScreen, turnOff, forceReload=False):
        if self.embeddedEnabled and self.embeddedSupport and not subsEmbedded and not turnOff and not subsPath:
            print("embedded settings changed")
            self.resetEmbeddedSubs(reloadEmbeddedScreen)
        elif turnOff:
            print('[SubsSupport] turn off')
            if self.embeddedSupport and self.embeddedEnabled:
                self.enableSubtitle(None)
            if self.__loaded:
                self.resetSubs(newService=False)
        elif self.embeddedSupport and subsEmbedded:
            print('[SubsSupport] loading embedded subtitles')
            if self.__loaded:
                self.resetSubs()
            self.__subsScreen.hide()
            self.enableSubtitle(subsEmbedded)
        elif subsPath is not None:
            if self.embeddedEnabled:
                self.enableSubtitle(None)
            newScreen = changedShadowType
            self.__subsScreen.show()
            if self.__subsPath == subsPath:
                if not settingsChanged and not ((changeEncoding or changedEncodingGroup) or newScreen or forceReload):
                    print('[SubsSupport] no changes made')
                elif settingsChanged and not (newScreen or changedEncodingGroup or forceReload):
                    print('[SubSupport] reloading SubScreen')
                    self.__subsEngine.pause()
                    self.__resetSubsScreen()
                    self.__subsEngine.resume()
                else:
                    self.__subsEngine.pause()
                    if changedEncodingGroup or (changedShadowType and not changeEncoding) or forceReload:
                        self.__subsEnc = None
                    if changedEncodingGroup:
                        self.__subsLoader.change_encodings(ALL_LANGUAGES_ENCODINGS + ENCODINGS[self.subsSettings.encodingsGroup.getValue()])
                    if newScreen:
                        self.__resetSubsScreen(newSubsScreen=True)
                    self.__subsEngine.reset(position=False)
                    if self.loadSubs(subsPath, newService=False):
                        self.__subsEngine.refresh()
            else:
                self.pauseSubs()
                self.__subsEnc = None
                if changedEncodingGroup:
                        self.__subsLoader.change_encodings(ALL_LANGUAGES_ENCODINGS + ENCODINGS[self.subsSettings.encodingsGroup.getValue()])
                if newScreen:
                    self.__resetSubsScreen(newSubsScreen=True)
                self.__subsEngine.reset()
                if self.__loaded:
                    if self.loadSubs(subsPath, newService=False):
                        self.__subsEngine.refresh()
                else:
                    if self.loadSubs(subsPath, newService=False):
                        self.__subsEngine.resume()
        if not self.__alreadyPausedVideo and isinstance(self, InfoBarSeek):
            print('[SubsSupport] unpausing video')
            del self.__alreadyPausedVideo
            self.setSeekState(InfoBarSeek.SEEK_STATE_PLAY)

    def __processSubs(self, subsPath, subsEnc):
        showMessages = self.__showGUIInfoMessages and not (self.__firstStart and self.__subclassOfScreen)
        try:
            return self.__subsLoader.load(subsPath, subsEnc, getFps(self.session))
        except LoadError:
            if showMessages:
                warningMessage(self.session, _("Cannot load subtitles. Invalid path"))
            return None, None
        except DecodeError:
            if showMessages:
                warningMessage(self.session, _("Cannot decode subtitles. Try another encoding group"))
            return None, None
        except ParserNotFoundError:
            if showMessages:
                warningMessage(self.session, _("Cannot parse subtitles. Not supported subtitles format"))
            return None, None
        except ParseError:
            if showMessages:
                warningMessage(self.session, _("Cannot parse subtitles. Invalid subtitles format"))
            return None, None
        finally:
            self.__firstStart = False

    def __updateSubs(self):
        if self.__loaded:
            self.resumeSubs()
            return

        subsPath = self.getSubsFileFromSref()
        if subsPath is not None:
            if self.loadSubs(subsPath):
                self.resumeSubs()
        self.__working = False

    def __afterWork(self, fnc):
        def checkWorking():
            if self.__working:
                print('check working..')
                self.__checkTimer.start(200, True)
            else:
                self.__checkTimer.stop()
                fnc()

        self.__checkTimer.stop()
        self.__starTimer.stop()

        if self.__working:
            del self.__checkTimer_conn
            self.__checkTimer_conn = eConnectCallback(self.__checkTimer.timeout, checkWorking)
            self.__checkTimer.start(200, True)
        else:
            fnc()


############ Methods triggered by videoEvents when SubsSupport is subclass of Screen ################


    def __serviceStarted(self):
        print('[SubsSupport] Service Started')

        def startSubs():
            self.__starTimer.start(self.__startDelay, True)

        self.__isServiceSet = True
        # subtitles are loading or already loaded
        if self.__working or self.__loaded:
            self.__afterWork(startSubs)
        else:
            self.resetSubs(True)
            if self.__subsPath is None and self.__autoLoad:
                startSubs()

    def __serviceStopped(self):
        print('[SubsSupport] Service Stopped')
        self.__starTimer.stop()
        self.resetSubs(True)
        self.__isServiceSet = False

    def __seekableStatusChanged(self):
        if not hasattr(self, 'seekstate'):
            return
        if self.seekstate == self.SEEK_STATE_PLAY:
            self.pauseSubs()
        elif self.seekstate == self.SEEK_STATE_PAUSE:
            self.resumeSubs()
        elif self.seekstate == self.SEEK_STATE_EOF:
            self.resetSubs(True)

########### Methods which extends InfobarSeek seek methods

    def doSeekRelative(self, pts):
        if self.__loaded:
            # self.__subsEngine.preSeek(pts)
            super(SubsSupport, self).doSeekRelative(pts)
            self.playAfterSeek()
        else:
            super(SubsSupport, self).doSeekRelative(pts)

    def doSeek(self, pts):
        if self.__loaded:
            super(SubsSupport, self).doSeek(pts)
            self.playAfterSeek()
        else:
            super(SubsSupport, self).doSeek(pts)

############################################################


class SubsEmbeddedScreen(Screen):

    """
    Pli defaults
    <fonts>
        <font filename="nmsbd.ttf" name="Subs" scale="100" />
    </fonts>
    <subtitles>
        <sub name="Subtitle_TTX" font="Subs;34" borderColor="#000000" borderWidth="3" />
        <sub name="Subtitle_Regular" font="Subs;34" foregroundColor="#ffffff" borderColor="#000000" borderWidth="3" />
        <sub name="Subtitle_Bold" font="Subs;34" foregroundColor="#ffffff" borderColor="#000000" borderWidth="3" />
        <sub name="Subtitle_Italic" font="Subs;34" foregroundColor="#ffffff" borderColor="#000000" borderWidth="3" />
    </subtitles>
    """

    def __init__(self, session, embeddedSettings):
        desktop = getDesktop(0)
        size = desktop.size()
        vSizeOrig = size.height()
        hSizeOrig = size.width()
        if QuickSubtitlesConfigMenu:
            vPosition = 0
            vSize = vSizeOrig
        else:
            vPositionPercent = int(embeddedSettings.position.value)
            fontSize = int(getEmbeddedFontSizeCfg(embeddedSettings.font.size).value)
            vSize = fontSize * 4 + 10
            vPosition = int(vPositionPercent * float((vSizeOrig - vSize) / 100))
            vPosition = vPosition if vPosition > 0 else 0
            vSize = vSizeOrig - vPosition
        self.skin = """<screen position="0,%s" size="%s,%s" zPosition="-1" backgroundColor="transparent" flags="wfNoBorder" />""" % (vPosition, hSizeOrig, vSize)
        Screen.__init__(self, session)


class SubtitlesWidget(GUIComponent):
    STATE_NO_BACKGROUND, STATE_BACKGROUND = range(2)

    def __init__(self, boundDynamic=True, boundXOffset=10, boundYOffset=10, boundSize=None, fontSize=25, positionPercent=94):
        GUIComponent.__init__(self)
        self.state = self.STATE_BACKGROUND
        self.boundDynamic = boundDynamic
        self.boundXOffset = boundXOffset
        self.boundYOffset = boundYOffset
        self.font = (gFont("Regular", fontSize), fontSize)
        self.positionPercent = positionPercent
        desktopSize = getDesktop(0).size()
        self.desktopSize = (desktopSize.width(), desktopSize.height())
        self.boundSize = boundSize or (self.desktopSize[0], self.calcWidgetHeight())

    def GUIcreate(self, parent):
        self.instance = eLabel(parent)
        self.instance2 = eLabel(parent)
        self.postWidgetCreate()

    def GUIdelete(self):
        self.preWidgetRemove()
        self.instance = None
        self.instance2 = None

    def postWidgetCreate(self):
        self.instance2.hide()
        self.update()

    def preWidgetRemove(self):
        pass

    def calcWidgetYPosition(self):
        return int((self.desktopSize[1] - self.calcWidgetHeight() - self.boundYOffset) / float(100) * self.positionPercent)

    def calcWidgetHeight(self):
        return int(4 * self.font[1] + 15)

    def update(self):
        ds = self.desktopSize
        bs = self.boundSize = (self.desktopSize[0], self.calcWidgetHeight())
        self.instance2.resize(eSize(int(ds[0]), int(bs[1])))
        self.instance2.move(ePoint(int(0), int(self.calcWidgetYPosition())))
        self.instance2.setHAlign(self.instance2.alignCenter)
        self.instance2.setVAlign(self.instance2.alignCenter)
        self.instance2.setFont(self.font[0])
        self.instance2.setTransparent(True)
        if not self.boundDynamic:
            self.instance.resize(eSize(int(bs[0]), int(bs[1])))
            self.instance.move(ePoint(int(ds[0] / 2 - bs[0] / 2), int(self.calcWidgetYPosition())))
        self.instance.setFont(self.font[0])
        self.instance.setHAlign(self.instance.alignCenter)
        self.instance.setVAlign(self.instance.alignCenter)

    def setText(self, text):
        if self.instance and self.instance2:
            if self.state == self.STATE_NO_BACKGROUND:
                self.instance.hide()
                self.instance2.setText(text)
                self.instance2.show()
            elif self.state == self.STATE_BACKGROUND:
                self.instance2.hide()
                if not text:
                    self.instance.hide()
                    return
                if self.boundDynamic:
                    # hack so empty spaces are part of calculateSize calculation
                    self.instance2.setText(text.replace(' ', '.'))
                    ds = self.desktopSize
                    bs = self.boundSize
                    ws = self.instance2.calculateSize()
                    ws = (ws.width() + self.boundXOffset * 2, ws.height() + self.boundYOffset * 2)
                    wp = self.instance2.position()
                    wp = (wp.x(), wp.y())
                    wpy = wp[1] + (bs[1] - ws[1]) / 2
                    wpx = ds[0] / 2 - ws[0] / 2
                    self.instance.resize(eSize(int(ws[0]), int(ws[1])))
                    self.instance.move(ePoint(int(wpx), int(wpy)))
                else:
                    bs = self.boundSize
                    ds = self.desktopSize
                    self.instance.resize(eSize(int(bs[0]), int(bs[1])))
                    self.instance.move(ePoint(int(ds[0] / 2 - bs[0] / 2), int(self.calcWidgetYPosition())))
                self.instance.setHAlign(self.instance.alignCenter)
                self.instance.setVAlign(self.instance.alignCenter)
                self.instance.setText(text)
                self.instance.show()

    def setPosition(self, percent):
        self.positionPercent = percent
        self.update()

    def setBoundDynamic(self, value):
        self.boundDynamic = value
        self.update()

    def setBoundOffset(self, offsetX, offsetY):
        self.boundXOffset = int(offsetX)
        self.boundYOffset = int(offsetY)
        self.update()

    def setForegroundColor(self, color):
        self.instance.setForegroundColor(parseColor(color))
        self.instance2.setForegroundColor(parseColor(color))

    def setBackgroundColor(self, color):
        if color[1:3] == "ff":
            self.state = self.STATE_NO_BACKGROUND
        else:
            self.state = self.STATE_BACKGROUND
            self.instance.setBackgroundColor(parseColor(color))

    def setBorderColor(self, color):
        self.instance.setBorderColor(parseColor(color))
        self.instance2.setBorderColor(parseColor(color))

    def setBorderWidth(self, width):
        self.instance.setBorderWidth(int(width))
        self.instance2.setBorderWidth(int(width))

    def setShadowColor(self, color):
        self.instance.setShadowColor(parseColor(color))
        self.instance2.setShadowColor(parseColor(color))

    def setShadowOffset(self, offset, scale):
        self.instance.setShadowOffset(parsePosition(offset, scale))
        self.instance2.setShadowOffset(parsePosition(offset, scale))

    def setFont(self, font):
        if self.font[1] == font[1]:
            self.font = font
            self.instance.setFont(font[0])
            self.instance2.setFont(font[0])
        else:
            self.font = font
            self.update()


class SubsScreen(Screen):
    def __init__(self, session, externalSettings):
        self.subShown = False
        self.__shadowType = 'border'
        self.__eLabelHasBorderParams = False
        self.externalSettings = externalSettings
        fontSize = int(externalSettings.font.size.getValue())
        self.font = {
            "regular": {
                'gfont': (gFont(externalSettings.font.regular.type.value, fontSize), fontSize),
                'color': externalSettings.font.regular.alpha.value + externalSettings.font.regular.color.value
            },
            "italic": {
                'gfont': (gFont(externalSettings.font.italic.type.value, fontSize), fontSize),
                'color': externalSettings.font.italic.alpha.value + externalSettings.font.italic.color.value
            },
            "bold": {
                'gfont': (gFont(externalSettings.font.bold.type.value, fontSize), fontSize),
                'color': externalSettings.font.bold.alpha.value + externalSettings.font.bold.type.value
            }
        }
        self.selectedFont = "regular"
        self.currentColor = externalSettings.font.regular.color.value
        self.skin = """
            <screen position="0,0" size="%d,%d" zPosition="-1" backgroundColor="transparent" flags="wfNoBorder">
                    <widget name="subtitles" />
            </screen>""" % (getDesktop(0).size().width(), getDesktop(0).size().height())

        Screen.__init__(self, session)
        self.stand_alone = True
        self["subtitles"] = SubtitlesWidget()
        self.onLayoutFinish.append(self.__checkElabelCaps)
        self.onLayoutFinish.append(self.reloadSettings)

    def __checkElabelCaps(self):
        if hasattr(self["subtitles"].instance, 'setBorderWidth') and hasattr(self["subtitles"].instance, 'setBorderColor'):
            self.__eLabelHasBorderParams = True
        elif self.__shadowType == 'border':
            self.__shadowType = 'offset'

    def setShadowType(self, type):
        if type == 'border' and self.__eLabelHasBorderParams:
            self.__shadowType = 'border'
        else:
            self.__shadowType = 'offset'

    def setShadow(self, type, color, size=None, xOffset=None, yOffset=None):
        self.setShadowType(type)
        if self.__shadowType == 'border':
            self["subtitles"].setBorderColor("#" + color)
        elif self.__shadowType == 'offset':
            self["subtitles"].setShadowColor("#" + color)
        if self.__shadowType == 'border' and size is not None:
            self["subtitles"].setBorderWidth(size)
        elif self.__shadowType == 'offset' and (xOffset is not None and yOffset is not None):
            self["subtitles"].setShadowOffset(str(-xOffset) + ',' + str(-yOffset), self.scale)

    def setBackground(self, type, alpha, color, xOffset=None, yOffset=None):
        if type == 'dynamic':
            self["subtitles"].setBoundDynamic(True)
            self["subtitles"].setBoundOffset(xOffset, yOffset)
        else:
            self["subtitles"].setBoundDynamic(False)
        color = "#" + alpha + color
        self["subtitles"].setBackgroundColor(color)

    def setColor(self, color):
        self.currentColor = color
        color = "#" + color
        self["subtitles"].setForegroundColor(color)

    def setPosition(self, position):
        self["subtitles"].setPosition(position)

    def setFonts(self, font):
        self.font = font
        self['subtitles'].setFont(self.font['regular']['gfont'])

    def reloadSettings(self):
        shadowType = self.externalSettings.shadow.type.getValue()
        shadowColor = self.externalSettings.shadow.color.getValue()
        shadowSize = int(self.externalSettings.shadow.size.getValue())
        shadowXOffset = int(self.externalSettings.shadow.xOffset.getValue())
        shadowYOffset = int(self.externalSettings.shadow.yOffset.getValue())
        shadowEnabled = int(self.externalSettings.shadow.enabled.getValue())
        if not shadowEnabled:
            shadowXOffset = shadowYOffset = shadowSize = 0
        backgroundType = self.externalSettings.background.type.getValue()
        backgroundAlpha = self.externalSettings.background.alpha.getValue()
        backgroundColor = self.externalSettings.background.color.getValue()
        backgroundXOffset = self.externalSettings.background.xOffset.getValue()
        backgroundYOffset = self.externalSettings.background.yOffset.getValue()
        backgroundEnabled = self.externalSettings.background.enabled.getValue()
        if not backgroundEnabled:
            backgroundAlpha = "ff"
            backgroundColor = "ffffff"
        fontSize = int(self.externalSettings.font.size.getValue())
        position = int(self.externalSettings.position.getValue())

        self.setPosition(position)
        self.setShadow(shadowType, shadowColor, shadowSize, shadowXOffset, shadowYOffset)
        self.setBackground(backgroundType, backgroundAlpha, backgroundColor, backgroundXOffset, backgroundYOffset)
        externalSettings = self.externalSettings
        self.setFonts({
            "regular": {
                'gfont': (gFont(externalSettings.font.regular.type.value, fontSize), fontSize),
                'color': externalSettings.font.regular.alpha.value + externalSettings.font.regular.color.value
            },
            "italic": {
                'gfont': (gFont(externalSettings.font.italic.type.value, fontSize), fontSize),
                'color': externalSettings.font.italic.alpha.value + externalSettings.font.italic.color.value
            },
            "bold": {
                'gfont': (gFont(externalSettings.font.bold.type.value, fontSize), fontSize),
                'color': externalSettings.font.bold.alpha.value + externalSettings.font.bold.color.value
            }
        })

    def setSubtitle(self, sub):
        if sub['style'] != self.selectedFont:
            self.selectedFont = sub['style']
            self['subtitles'].setFont(self.font[sub['style']]['gfont'])
        color = sub['color']
        if color == "default":
            color = self.font[sub['style']]['color']
        self.setColor(color)
        self["subtitles"].setText(toString(sub['text']))
        self.subShown = True

    def hideSubtitle(self):
        if self.subShown:
            self["subtitles"].setText("")
            self.subShown = False


class SubsEngine(object):
    def __init__(self, session, engineSettings, renderer):
        self.session = session
        self.engineSettings = engineSettings
        self.renderer = renderer
        self.subsList = None
        self.position = 0
        self.sub = None
        self.subsFpsRatio = 1
        self.onSubsFpsChanged = []
        self.subsDelay = 0
        self.onSubsDelayChanged = []
        self.playerDelay = 0
        self.syncDelay = 300
        self.hideInterval = 200 * 90
        self.__seek = None
        self.__pts = None
        self.__ptsDelay = None
        self.__callbackPts = None
        self.preDoPlay = [self.updateSubPosition]
        self.refreshTimer = eTimer()
        self.refreshTimer_conn = eConnectCallback(self.refreshTimer.timeout, self.play)
        self.refreshTimerDelay = 1000
        self.hideTimer = eTimer()
        self.hideTimer_conn_array = []
        self.hideTimer_conn_array.append(eConnectCallback(self.hideTimer.timeout, self.checkHideSub))
        self.hideTimer_conn_array.append(eConnectCallback(self.hideTimer.timeout, self.incSubPosition))
        self.hideTimer_conn_array.append(eConnectCallback(self.hideTimer.timeout, self.doPlay))
        self.getPlayPtsTimer = eTimer()
        self.getPlayPtsTimer_conn_array = []
        self.getPlayPtsTimer_conn_array.append(eConnectCallback(self.getPlayPtsTimer.timeout, self.getPts))
        self.getPlayPtsTimer_conn_array.append(eConnectCallback(self.getPlayPtsTimer.timeout, self.validPts))
        self.getPlayPtsTimer_conn_array.append(eConnectCallback(self.getPlayPtsTimer.timeout, self.callbackPts))
        self.getPlayPtsTimerDelay = 200
        self.resume = self.play
        self.addNotifiers()

    def addNotifiers(self):
        def hideInterval(configElement):
            self.hideInterval = int(configElement.value) * 90

        def playerDelay(configElement):
            self.playerDelay = int(configElement.value) * 90

        def syncDelay(configElement):
            self.syncDelay = int(configElement.value)

        def getPlayPtsTimerDelay(configElement):
            self.getPlayPtsTimerDelay = int(configElement.value)

        def refreshTimerDelay(configElement):
            self.refreshTimerDelay = int(configElement.value)

        self.engineSettings.expert.hideDelay.addNotifier(hideInterval)
        self.engineSettings.expert.playerDelay.addNotifier(playerDelay)
        self.engineSettings.expert.syncDelay.addNotifier(syncDelay)
        self.engineSettings.expert.ptsDelayCheck.addNotifier(getPlayPtsTimerDelay)
        self.engineSettings.expert.refreshDelay.addNotifier(refreshTimerDelay)

    def removeNotifiers(self):
        del self.engineSettings.expert.hideDelay.notifiers[:]
        del self.engineSettings.expert.playerDelay.notifiers[:]
        del self.engineSettings.expert.syncDelay.notifiers[:]
        del self.engineSettings.expert.ptsDelayCheck.notifiers[:]
        del self.engineSettings.expert.refreshDelay.notifiers[:]

    def getPlayPts(self, callback, delay=None):
        self.getPlayPtsTimer.stop()
        self.__callbackPts = callback
        self.__ptsDelay = delay
        self.__pts = None
        if delay is None:
            delay = 1
        self.getPlayPtsTimer.start(int(delay), True)

    def getPts(self):
        try:
            if not self.__seek:
                service = self.session.nav.getCurrentService()
                self.__seek = service.seek()
        except Exception:
            return
        r = self.__seek.getPlayPosition()
        if r[0]:
            self.__pts = None
        else:
            self.__pts = long(r[1]) + self.playerDelay

    def validPts(self):
        pass

    def callbackPts(self):
        if self.__pts is not None:
            self.getPlayPtsTimer.stop()
            self.__callbackPts()
        else:
            delay = self.getPlayPtsTimerDelay
            if self.__ptsDelay is not None:
                delay = self.__ptsDelay
            self.getPlayPtsTimer.start(int(delay))

    def setSubsList(self, subslist):
        self.subsList = subslist

    def setRenderer(self, renderer):
        self.renderer = renderer

    def setPlayerDelay(self, playerDelay):
        self.pause()
        self.playerDelay = playerDelay * 90
        self.resume()

    def setSubsFps(self, subsFps):
        print("[SubsEngine] setSubsFps - setting fps to %s" % str(subsFps))
        videoFps = getFps(self.session, True)
        if videoFps is None:
            print("[SubsEngine] setSubsFps - cannot get video fps!")
        else:
            self.pause()
            self.subsFpsRatio = subsFps / float(videoFps)
            for f in self.onSubsFpsChanged:
                f(self.getSubsFps())
            self.resume()

    def getSubsFps(self):
        videoFps = getFps(self.session, True)
        if videoFps is None:
            return None
        return fps_float(self.subsFpsRatio * videoFps)

    def setSubsDelay(self, delayInMs):
        print("[SubsEngine] setSubsDelay - setting delay to %sms" % str(delayInMs))
        self.pause()
        self.subsDelay = int(delayInMs) * 90
        for f in self.onSubsDelayChanged:
            f(self.getSubsDelay())
        self.resume()

    def getSubsDelay(self):
        return self.subsDelay / 90

    def getSubsPosition(self):
        return self.position

    def setSubsDelayToNextSubtitle(self):
        def setDelay():
            if not self.renderer.subShown:
                print('[SubsEngine] setDelayToNextSubtitle - next pos: %d of %d' % (self.position, len(self.subsList)))
                toSub = self.subsList[self.position]
                # position is incremented right after subtitle is hidden so we don't do anything
            elif self.renderer.subShown and self.position != len(self.subsList) - 1:
                print('[SubsEngine] setDelayToNextSubtitle - next pos: %d of %d' % (self.position + 1, len(self.subsList)))
                toSub = self.subsList[self.position + 1]
            else:
                print('[SubsEngine] setDelayToNextSubtitle - we are on last subtitle')
                return
            toSubDelay = (self.__pts - (toSub['start'] * self.subsFpsRatio)) / 90
            self.setSubsDelay(toSubDelay)

        self.stopTimers()
        self.getPlayPts(setDelay)

    def setSubsDelayToPrevSubtitle(self):
        def setDelay():
            if not self.renderer.subShown:
                print('[SubsEngine] setDelayToPrevSubtitle - skipping to start of current sub')
                # position is incremented right after subtitle is hidden so we have to go one back
                toSub = self.subsList[self.position - 1]
            elif self.renderer.subShown and self.position != 0:
                print('[SubsEngine] setDelayToPrevSubtitle - prev pos: %d of %d' % (self.position - 1, len(self.subsList)))
                toSub = self.subsList[self.position - 1]
            else:
                print('[SubsEngine] setDelayToPrevSubtitle - we are on first subtitle')
                return
            toSubDelay = (self.__pts - (toSub['start'] * self.subsFpsRatio)) / 90
            self.setSubsDelay(toSubDelay)

        self.stopTimers()
        self.getPlayPts(setDelay)

    def reset(self, position=True):
        self.stopTimers()
        self.hideSub()
        if position:
            self.position = 0
        self.__seek = None
        self.__pts = None
        self.__callbackPts = None
        self.sub = None
        self.subsDelay = 0
        self.subsFpsRatio = 1

    def refresh(self):
        self.stopTimers()
        self.hideSub()
        self.refreshTimer.start(self.refreshTimerDelay, True)

    def pause(self):
        self.stopTimers()
        self.hideSub()

    def play(self):
        self.stopTimers()
        self.hideSub()
        self.getPlayPts(self.prePlay)

    def sync(self):
        self._oldPts = None

        def checkPts():
            if self._oldPts is None:
                self._oldPts = self.__pts
                self.getPlayPts(checkPts, self.syncDelay)
            # video is frozen no progress made
            elif self._oldPts == self.__pts:
                self._oldPts = None
                self.getPlayPts(checkPts, self.syncDelay)
            # abnormal pts
            elif (self.__pts > self._oldPts + self.syncDelay * 90 + (200 * 90)) or (
                    self.__pts < self._oldPts + self.syncDelay * 90 - (200 * 90)):
                self._oldPts = None
                self.getPlayPts(checkPts, self.syncDelay)
                # normal playback
            else:
                del self._oldPts
                self.updateSubPosition()
                self.doPlay()
        self.stopTimers()
        self.hideSub()
        self.getPlayPts(checkPts, self.syncDelay)

    def prePlay(self):
        for f in self.preDoPlay:
            f()
        self.doPlay()

    def doPlay(self):
        if self.position == len(self.subsList):
            print('[SubsEngine] reached end of subtitle list')
            self.position = len(self.subsList) - 1
            self.stopTimers()
        else:
            self.sub = self.subsList[self.position]
            self.getPlayPts(self.doWait)

    def doWait(self):
        subStartPts = int(self.sub['start'] * self.subsFpsRatio) + self.subsDelay
        if self.__pts < subStartPts:
            diffPts = subStartPts - self.__pts
            diffMs = diffPts / 90
            if diffMs > 50:
                self.getPlayPts(self.doWait, diffMs)
            else:
                print('[SubsEngine] sub shown sooner by %dms' % diffMs)
                self.renderSub()
        else:
            subsEndPts = (self.sub['end'] * self.subsFpsRatio) + self.subsDelay
            if subsEndPts - self.__pts < 0:
                #print('[SubsEngine] sub should be already shown - %dms, skipping...'%((subsEndPts - self.__pts)/90))
                self.getPlayPts(self.skipSubs, 100)
            else:
                print('[SubsEngine] sub shown later by %dms' % ((self.__pts - subStartPts) / 90))
                self.renderSub()

    def skipSubs(self):
        if self.position == len(self.subsList) - 1:
            self.incSubPosition()
        else:
            self.updateSubPosition()
        self.doPlay()

    def renderSub(self):
        duration = int(self.sub['duration'] * self.subsFpsRatio)
        self.renderer.setSubtitle(self.sub)
        self.hideTimer.start(duration, True)

    def checkHideSub(self):
        if self.subsList[-1] == self.sub:
            self.hideSub()
        elif (self.subsList[self.position]['end'] * self.subsFpsRatio) + self.hideInterval < (self.subsList[self.position + 1]['start'] * self.subsFpsRatio):
            self.hideSub()

    def hideSub(self):
        self.renderer.hideSubtitle()

    def incSubPosition(self):
        self.position += 1

    def updateSubPosition(self):
        playPts = self.__pts
        print('[SubsEngine] pre-update sub position:', self.position)
        subStartPts = (self.subsList[self.position]['start'] * self.subsFpsRatio) + self.subsDelay
        subStartEndPts = (self.subsList[self.position]['end'] * self.subsFpsRatio) + self.subsDelay
        # seek backwards
        if subStartPts > playPts:
            subPrevEndPts = (self.subsList[self.position - 1]['end'] * self.subsFpsRatio) + self.subsDelay
            while self.position > 0 and subPrevEndPts > playPts:
                self.position -= 1
                subPrevEndPts = (self.subsList[self.position - 1]['end'] * self.subsFpsRatio) + self.subsDelay
        # seek forward
        elif subStartPts < playPts and subStartEndPts < playPts:
            while self.position < len(self.subsList) - 1 and subStartPts < playPts and subStartEndPts < playPts:
                self.position += 1
                subStartPts = (self.subsList[self.position]['start'] * self.subsFpsRatio) + self.subsDelay
                subStartEndPts = (self.subsList[self.position]['end'] * self.subsFpsRatio) + self.subsDelay
        print('[SubsEngine] post-update sub position:', self.position)

    def showDialog(self):
        self.renderer.show()

    def hideSubtitlesDialog(self):
        self.renderer.hide()

    def stopTimers(self):
        if self.refreshTimer is not None:
            self.refreshTimer.stop()
        if self.getPlayPtsTimer is not None:
            self.getPlayPtsTimer.stop()
        if self.hideTimer is not None:
            self.hideTimer.stop()

    def exit(self):
        del self.hideTimer_conn_array[:]
        del self.hideTimer
        del self.refreshTimer_conn
        del self.refreshTimer
        del self.getPlayPtsTimer_conn_array[:]
        del self.getPlayPtsTimer
        del self.onSubsDelayChanged[:]
        del self.onSubsFpsChanged[:]
        self.removeNotifiers()


class PanelList(MenuList):
    def __init__(self, list, height=30):
        MenuList.__init__(self, list, False, eListboxPythonMultiContent)
        self.l.setItemHeight(height)
        self.l.setFont(0, gFont("Regular", 20))
        self.l.setFont(1, gFont("Regular", 17))


def PanelListEntry(name, mode):
    res = [(name, mode)]
    res.append(MultiContentEntryText(pos=(5, 5), size=(330, 25), font=0, flags=RT_VALIGN_CENTER, text=name))
    return res


def PanelColorListEntry(name, value, colorName, colorValue, sizePanelX):
    res = [(name)]
    res.append(MultiContentEntryText(pos=(0, 5), size=(sizePanelX, 30), font=1, flags=RT_HALIGN_LEFT, text=name, color=colorName))
    res.append(MultiContentEntryText(pos=(0, 5), size=(sizePanelX, 30), font=1, flags=RT_HALIGN_RIGHT, text=value, color=colorValue))
    return res


class SubsMenu(Screen):
    if isFullHD():
        skin = """
            <screen position="center,center" size="750,600" zPosition="1" >
                <widget name="title_label" position="0,5" size="750,35" valign="center" halign="center" font="Regular;25" transparent="1" foregroundColor="white" />
                <widget name="subfile_label" position="0,50" size="750,50" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="#DAA520" />
                <widget name="subfile_list" position="center,100" size="400,30" transparent="1" />
                <eLabel position="5,202" size="735,1" backgroundColor="#999999" />
                <widget name="menu_list" position="0,210" size="750,352" transparent="1" scrollbarMode="showOnDemand" />
                <widget name="copyright" position="15,562" size="720,20" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="white" />
            </screen>"""
    else:
        skin = """
            <screen position="center,center" size="500,400" zPosition="1" >
                <widget name="title_label" position="0,5" size="500,35" valign="center" halign="center" font="Regular;25" transparent="1" foregroundColor="white" />
                <widget name="subfile_label" position="0,50" size="500,50" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="#DAA520" />
                <widget name="subfile_list" position="center,100" size="300,30" transparent="1" />
                <eLabel position="5,135" size="490,1" backgroundColor="#999999" />
                <widget name="menu_list" position="0,140" size="500,235" transparent="1" scrollbarMode="showOnDemand" />
                <widget name="copyright" position="10,375" size="480,20" valign="center" halign="center" font="Regular;15" transparent="1" foregroundColor="white" />
            </screen>"""

    def __init__(self, session, infobar, subfile=None, subdir=None, encoding=None, embeddedSupport=False, embeddedEnabled=False, searchSupport=False):
        Screen.__init__(self, session)
        self.infobar = infobar
        self.subfile = subfile
        self.subdir = subdir
        self.encoding = encoding
        self.embeddedSupport = embeddedSupport
        self.embeddedEnabled = embeddedEnabled
        self.searchSupport = searchSupport
        self.embeddedSubtitle = None
        self.newSelection = False
        self.changeEncoding = False
        self.changedEncodingGroup = False
        self.changedShadowType = False
        self.changedSettings = False
        self.reloadEmbeddedScreen = False
        self.turnOff = False
        self.forceReload = False

        self["title_label"] = Label(_("Currently choosed subtitles"))
        self["subfile_label"] = Label("")
        self["subfile_list"] = PanelList([], 25)
        self["menu_list"] = PanelList([], 28)
        self["copyright"] = Label("")
        # self["copyright"] = Label("created by %s <%s>"%(__author__,__email__))
        self["actions"] = ActionMap(["SetupActions"],
            {
                "ok": self.ok,
                "cancel": self.cancel,
            }, -2)

        self["menuactions"] = ActionMap(["NavigationActions"], {
			"top": self.top,
			"pageUp": self.pageUp,
			"up": self.up,
			"down": self.down,
			"pageDown": self.pageDown,
			"bottom": self.bottom
		}, -2)

        self.onLayoutFinish.append(self.initTitle)
        self.onLayoutFinish.append(self.initGUI)
        self.onLayoutFinish.append(self.disableSelection)

    def top(self):
        self["menu_list"].top()

    def pageUp(self):
        self["menu_list"].pageUp()

    def up(self):
        self["menu_list"].up()

    def down(self):
        self["menu_list"].down()

    def pageDown(self):
        self["menu_list"].pageDown()

    def bottom(self):
        self["menu_list"].bottom()

    def disableSelection(self):
        self["subfile_list"].selectionEnabled(False)

    def initTitle(self):
        self.setTitle("SubsSupport %s" % __version__)

    def initGUI(self):
        self.initSubInfo()
        self.initMenu()

    def initSubInfo(self):
        subInfo = []
        if self.embeddedEnabled or self.embeddedSubtitle:
            self["subfile_label"].setText(_("Embedded Subtitles"))
            self["subfile_label"].instance.setForegroundColor(parseColor("#ffff00"))
        elif self.subfile is not None:
            self["subfile_label"].setText(toString(os.path.split(self.subfile)[1]))
            self["subfile_label"].instance.setForegroundColor(parseColor("#DAA520"))

            if self.newSelection:
                pass
                # subInfo.append(PanelColorListEntry(_("State:"),_("not loaded"), 0xDAA520, 0xffff00, 300))
            elif self.encoding and not self.newSelection:
                # subInfo.append(PanelColorListEntry(_("State:"),_("loaded"), 0xDAA520, 0x00ff00, 300))
                subInfo.append(PanelColorListEntry(_("Encoding:"), self.encoding, 0xDAA520, 0xffffff, 300))
            elif not self.encoding and not self.newSelection:
                # subInfo.append(PanelColorListEntry(_("State:"),_("not loaded"), 0xDAA520, 0xffff00, 300))
                subInfo.append(PanelColorListEntry(_("Encoding:"), _("cannot decode"), 0xDAA520, 0xffffff, 300))
        else:
            self["subfile_label"].setText(_("None"))
            self["subfile_label"].instance.setForegroundColor(parseColor("#DAA520"))
        self["subfile_list"].setList(subInfo)

    def initMenu(self):
        self.menu = [(_('Choose subtitles'), 'choose')]
        if self.searchSupport:
            self.menu.append((_("Search subtitles"), 'search'))
        if not self.embeddedEnabled:
            if self.subfile is not None and not self.newSelection:
                self.menu.append((_('Change encoding'), 'encoding'))
            self.menu.append((_('Subtitles settings'), 'settings'))
        if self.embeddedEnabled and QuickSubtitlesConfigMenu:
            self.menu.append((_('Subtitles settings (embedded)'), 'settings_embedded_pli'))
        if self.embeddedEnabled and not QuickSubtitlesConfigMenu:
            self.menu.append((_('Subtitles settings (embedded)'), 'settings_embedded'))
        if self.subfile is not None or self.embeddedEnabled:
            self.menu.append((_('Turn off subtitles'), 'subsoff'))
        list = [PanelListEntry(x, y) for x, y in self.menu]
        self["menu_list"].setList(list)

    def ok(self):
        mode = self["menu_list"].getCurrent()[0][1]
        if mode == 'choose':
            self.session.openWithCallback(self.subsChooserCB, SubsChooser, self.infobar.subsSettings, self.subdir, self.embeddedSupport, False, True)
        elif mode == 'search':
            self.searchSubs()
        elif mode == 'settings':
            self.session.openWithCallback(self.subsSetupCB, SubsSetupMainMisc, self.infobar.subsSettings)
        elif mode == 'settings_embedded':
            self.session.openWithCallback(self.subsSetupEmbeddedCB, SubsSetupEmbedded, self.infobar.subsSettings.embedded)
        elif mode == 'settings_embedded_pli':
            self.session.open(QuickSubtitlesConfigMenu, self.infobar)
        elif mode == 'encoding':
            self.changeEncoding = True
            self.cancel()
        elif mode == 'subsoff':
            self.turnOff = True
            self.cancel()

    def getSearchTitleList(self, sName, sPath):
        searchTitles = []
        if sName:
            searchTitles.append(sName)
        if sPath:
            dirname = os.path.basename(os.path.dirname(sPath))
            dirnameFix = dirname.replace('.', ' ').replace('_', ' ').replace('-', ' ')
            filename = os.path.splitext(os.path.basename(sPath))[0]
            filenameFix = filename.replace('.', ' ').replace('_', ' ').replace('-', ' ')
            if filename not in searchTitles:
                searchTitles.append(filename)
            if filenameFix not in searchTitles:
                searchTitles.append(filenameFix)
            if dirname not in searchTitles:
                searchTitles.append(dirname)
            if dirnameFix not in searchTitles:
                searchTitles.append(dirnameFix)
        return searchTitles

    def searchSubs(self):
        def checkDownloadedSubsSelection(downloadedSubtitle=None):
            if downloadedSubtitle:
                self.subsChooserCB(downloadedSubtitle, False, True)

        def paramsDialogCB(callback=None):
            if callback:
                self.session.openWithCallback(checkDownloadedSubsSelection, SubsSearch, seeker, subsSettings.search, sPath, titleList, resetSearchParams=False)

        def showProvidersErrorCB(callback):
            if not callback:
                subsSettings.search.showProvidersErrorMessage.value = False
            if subsSettings.search.openParamsDialogOnSearch.value:
                self.session.openWithCallback(paramsDialogCB, SubsSearchParamsMenu, seeker, subsSettings.search, titleList, enabledList=False)
            else:
                self.session.openWithCallback(checkDownloadedSubsSelection, SubsSearch, seeker, subsSettings.search, sPath, titleList)

        if self.searchSupport:
            ref = self.session.nav.getCurrentlyPlayingServiceReference()
            try:
                sPath = ref.getPath()
            except Exception:
                sPath = None
            try:
                sName = ref.getName()
            except Exception:
                sName = None
            titleList = self.getSearchTitleList(sName, sPath)
            subsSettings = self.infobar.subsSettings
            seeker = E2SubsSeeker(self.session, subsSettings.search, debug=True)

            if seeker.providers_error and subsSettings.search.showProvidersErrorMessage.value:
                msg = _("Some subtitles providers are not working") + ".\n"
                msg += _("For more details please check search settings") + "."
                msg += "\n\n"
                msg += _("Do you want to show this message again?")
                self.session.openWithCallback(showProvidersErrorCB, MessageBox, msg, type=MessageBox.TYPE_YESNO)

            elif subsSettings.search.openParamsDialogOnSearch.value:
                self.session.openWithCallback(paramsDialogCB, SubsSearchParamsMenu, seeker, subsSettings.search, titleList, enabledList=False)
            else:
                self.session.openWithCallback(checkDownloadedSubsSelection, SubsSearch, seeker, subsSettings.search, sPath, titleList)

    def subsChooserCB(self, subfile=None, embeddedSubtitle=None, forceReload=False):
        if subfile is not None and self.subfile != subfile:
            self.subfile = subfile
            self.subdir = os.path.dirname(self.subfile)
            self.newSelection = True
            self.embeddedEnabled = False
            self.cancel()
        elif subfile is not None and self.subfile == subfile and forceReload:
            self.forceReload = True
            self.cancel()
        elif embeddedSubtitle and embeddedSubtitle != self.infobar.selected_subtitle:
            self.embeddedSubtitle = embeddedSubtitle
            self.cancel()
        # self.initGUI()

    def subsSetupCB(self, changedSettings=False, changedEncodingGroup=False,
                    changedShadowType=False):
        self.changedSettings = changedSettings
        self.changedEncodingGroup = changedEncodingGroup
        self.changedShadowType = changedShadowType

    def subsSetupEmbeddedCB(self, reloadEmbeddedScreen=False):
        self.reloadEmbeddedScreen = reloadEmbeddedScreen

    def cancel(self):
        self.close(self.subfile, self.embeddedSubtitle, self.changedSettings, self.changeEncoding,
                   self.changedEncodingGroup, self.changedShadowType, self.reloadEmbeddedScreen, self.turnOff, self.forceReload)

# rework


class SubsSetupExternal(BaseMenuScreen):

    @staticmethod
    def getConfigList(externalSettings):
        configList = []
        shadowType = externalSettings.shadow.type.getValue()
        shadowEnabled = externalSettings.shadow.enabled.getValue()
        backgroundType = externalSettings.background.type.getValue()
        backgroundEnabled = externalSettings.background.enabled.getValue()
        configList.append(getConfigListEntry(_("Font type (Regular)"), externalSettings.font.regular.type))
        configList.append(getConfigListEntry(_("Font color (Regular)"), externalSettings.font.regular.color))
        configList.append(getConfigListEntry(_("Font transparency (Regular)"), externalSettings.font.regular.alpha))
        configList.append(getConfigListEntry(_("Font type (Italic)"), externalSettings.font.italic.type))
        configList.append(getConfigListEntry(_("Font color (Italic"), externalSettings.font.italic.color))
        configList.append(getConfigListEntry(_("Font transparency (Italic)"), externalSettings.font.italic.alpha))
        configList.append(getConfigListEntry(_("Font type (Bold)"), externalSettings.font.bold.type))
        configList.append(getConfigListEntry(_("Font color (Bold)"), externalSettings.font.bold.color))
        configList.append(getConfigListEntry(_("Font transparency (Bold)"), externalSettings.font.bold.alpha))
        configList.append(getConfigListEntry(_("Font size"), externalSettings.font.size))
        configList.append(getConfigListEntry(_("Position"), externalSettings.position))
        configList.append(getConfigListEntry(_("Shadow"), externalSettings.shadow.enabled))
        if shadowEnabled:
            configList.append(getConfigListEntry(_("Shadow type"), externalSettings.shadow.type))
            if shadowType == 'offset':
                configList.append(getConfigListEntry(_("Shadow X-offset"), externalSettings.shadow.xOffset))
                configList.append(getConfigListEntry(_("Shadow Y-offset"), externalSettings.shadow.yOffset))
            else:
                configList.append(getConfigListEntry(_("Shadow size"), externalSettings.shadow.size))
            configList.append(getConfigListEntry(_("Shadow color"), externalSettings.shadow.color))
        configList.append(getConfigListEntry(_("Background"), externalSettings.background.enabled))
        if backgroundEnabled:
            configList.append(getConfigListEntry(_("Background type"), externalSettings.background.type))
            if backgroundType == 'dynamic':
                configList.append(getConfigListEntry(_("Background X-offset"), externalSettings.background.xOffset))
                configList.append(getConfigListEntry(_("Background Y-offset"), externalSettings.background.yOffset))
            configList.append(getConfigListEntry(_("Background color"), externalSettings.background.color))
            configList.append(getConfigListEntry(_("Background transparency"), externalSettings.background.alpha))
        return configList

    def __init__(self, session, externalSettings):
        BaseMenuScreen.__init__(self, session, _("External Subtitles settings"))
        self.externalSettings = externalSettings

    def buildMenu(self):
        self["config"].setList(self.getConfigList(self.externalSettings))

    def keySave(self):
        changedShadowType = self.externalSettings.shadow.type.isChanged()
        for x in self["config"].list:
            x[1].save()
        configfile.save()
        self.close(True, changedShadowType)

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        current = self["config"].getCurrent()[1]
        if current in [self.externalSettings.shadow.type,
                       self.externalSettings.shadow.enabled,
                       self.externalSettings.background.enabled,
                       self.externalSettings.background.type]:
            self.buildMenu()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        current = self["config"].getCurrent()[1]
        if current in [self.externalSettings.shadow.type,
                       self.externalSettings.shadow.enabled,
                       self.externalSettings.background.enabled,
                       self.externalSettings.background.type]:
            self.buildMenu()


class SubsSetupMainMisc(BaseMenuScreen):
    def __init__(self, session, subsSettings):
        BaseMenuScreen.__init__(self, session, _("Subtitles setting"))
        self.subsSettings = subsSettings
        self.showExpertSettings = ConfigYesNo(default=False)

    def buildMenu(self):
        configList = []
        configList.append(getConfigListEntry(_("Pause video on opening subtitles menu"), self.subsSettings.pauseVideoOnSubtitlesMenu))
        configList.append(getConfigListEntry("-" * 200, ConfigNothing()))
        configList.extend(SubsSetupExternal.getConfigList(self.subsSettings.external))
        configList.append(getConfigListEntry(_("Encoding"), self.subsSettings.encodingsGroup))
        configList.append(getConfigListEntry(_("Show expert settings"), self.showExpertSettings))
        if self.showExpertSettings.value:
            engineSettings = self.subsSettings.engine
            configList.append(getConfigListEntry(_("Hide delay"), engineSettings.expert.hideDelay))
            configList.append(getConfigListEntry(_("Sync delay"), engineSettings.expert.syncDelay))
            configList.append(getConfigListEntry(_("Player delay"), engineSettings.expert.playerDelay))
            configList.append(getConfigListEntry(_("Refresh delay"), engineSettings.expert.refreshDelay))
            configList.append(getConfigListEntry(_("PTS check delay"), engineSettings.expert.ptsDelayCheck))
        self["config"].setList(configList)

    def keySave(self):
        changedEncodingGroup = self.subsSettings.encodingsGroup.isChanged()
        changedShadowType = self.subsSettings.external.shadow.type.isChanged()
        for x in self["config"].list:
            x[1].save()
        configfile.save()
        self.close(True, changedEncodingGroup, changedShadowType)

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        current = self["config"].getCurrent()[1]
        if current in [self.subsSettings.external.shadow.type,
                       self.subsSettings.external.shadow.enabled,
                       self.showExpertSettings,
                       self.subsSettings.external.background.enabled,
                       self.subsSettings.external.background.type]:
            self.buildMenu()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        current = self["config"].getCurrent()[1]
        if current in [self.subsSettings.external.shadow.type,
                       self.subsSettings.external.shadow.enabled,
                       self.showExpertSettings,
                       self.subsSettings.external.background.enabled,
                       self.subsSettings.external.background.type]:
            self.buildMenu()


class SubsSetupEmbedded(BaseMenuScreen):

    @staticmethod
    def initConfig(configsubsection):
        configsubsection.position = ConfigSelection(default="94", choices=positionChoiceList)
        configsubsection.font = ConfigSubsection()
        configsubsection.font.regular = ConfigSubsection()
        configsubsection.font.regular.type = ConfigSelection(default=getDefaultFont("regular"), choices=fontChoiceList)
        configsubsection.font.italic = ConfigSubsection()
        configsubsection.font.italic.type = ConfigSelection(default=getDefaultFont("italic"), choices=fontChoiceList)
        configsubsection.font.bold = ConfigSubsection()
        configsubsection.font.bold.type = ConfigSelection(default=getDefaultFont("bold"), choices=fontChoiceList)
        configsubsection.font.size = ConfigSelection(default="34", choices=fontSizeChoiceList)
        configsubsection.color = ConfigSelection(default="ffffff", choices=colorChoiceList)
        configsubsection.shadow = ConfigSubsection()
        configsubsection.shadow.size = ConfigSelection(default="3", choices=shadowSizeChoiceList)
        configsubsection.shadow.color = ConfigSelection(default="000000", choices=colorChoiceList)
        configsubsection.shadow.xOffset = ConfigSelection(default="-3", choices=shadowOffsetChoiceList)
        configsubsection.shadow.yOffset = ConfigSelection(default="-3", choices=shadowOffsetChoiceList)

    @staticmethod
    def getConfigList(embeddedSettings):
        fontSizeCfg = getEmbeddedFontSizeCfg(embeddedSettings.font.size)
        configList = []
        configList.append(getConfigListEntry(_("Font type (Regular)"), embeddedSettings.font.regular.type))
        configList.append(getConfigListEntry(_("Font type (Italic)"), embeddedSettings.font.italic.type))
        configList.append(getConfigListEntry(_("Font type (Bold)"), embeddedSettings.font.bold.type))
        configList.append(getConfigListEntry(_("Font size"), fontSizeCfg))
        configList.append(getConfigListEntry(_("Position"), embeddedSettings.position))
        configList.append(getConfigListEntry(_("Color"), embeddedSettings.color))
        configList.append(getConfigListEntry(_("Shadow X-offset"), embeddedSettings.shadow.xOffset))
        configList.append(getConfigListEntry(_("Shadow Y-offset"), embeddedSettings.shadow.yOffset))
        return configList

    def __init__(self, session, embeddedSettings):
        BaseMenuScreen.__init__(self, session, _("Embedded subtitles settings"))
        self.embeddedSettings = embeddedSettings

    def buildMenu(self):
        self["config"].setList(self.getConfigList((self.embeddedSettings)))

    def keySave(self):
        reloadEmbeddedScreen = (self.embeddedSettings.position.isChanged() or
            getEmbeddedFontSizeCfg(self.embeddedSettings.font.size).isChanged())
        for x in self["config"].list:
            x[1].save()
        configfile.save()
        self.close(reloadEmbeddedScreen)


class SubsSetupGeneral(BaseMenuScreen):
    def __init__(self, session, generalSettings):
        BaseMenuScreen.__init__(self, session, _("General settings"))
        self.generalSettings = generalSettings

    def buildMenu(self):
        self["config"].setList([
            getConfigListEntry(_("Pause video on opening subtitles menu"), self.generalSettings.pauseVideoOnSubtitlesMenu),
            getConfigListEntry(_("Encoding"), self.generalSettings.encodingsGroup),
        ])


def FileEntryComponent(name, absolute=None, isDir=False):
    res = [(absolute, isDir)]
    if isFullHD():
        res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 770, 30, 1, RT_HALIGN_LEFT, toString(name)))
    else:
        res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 570, 30, 0, RT_HALIGN_LEFT, toString(name)))
    if isDir:
        png = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "extensions/directory.png"))
    else:
        png = LoadPixmap(os.path.join(os.path.dirname(__file__), 'img', 'subtitles.png'))
    if png is not None:
        res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 2, 20, 20, png))
    return res


# TODO rework so there is one general SubtitlesChooser, where we can quickly
# switch between different views(search, embedded, external, history..), i.e
# we can go directly from search screen -> embedded screen (if embedded subtitles are available)

class SubFileList(FileList):
    def __init__(self, defaultDir):
        extensions = []
        for parser in PARSERS:
            extensions += list(parser.parsing)
        FileList.__init__(self, defaultDir, matchingPattern="(?i)^.*\." + '(' + '|'.join(ext[1:] for ext in extensions) + ')', useServiceRef=False)
        self.l.setFont(0, gFont("Regular", 18))
        self.l.setFont(1, gFont("Regular", 27))
        if isFullHD():
            self.l.setItemHeight(35)
        else:
            self.l.setItemHeight(23)

    def changeDir(self, directory, select=None):
        self.list = []

        # if we are just entering from the list of mount points:
        if self.current_directory is None:
            if directory and self.showMountpoints:
                self.current_mountpoint = self.getMountpointLink(directory)
            else:
                self.current_mountpoint = None
        self.current_directory = directory
        directories = []
        files = []

        if directory is None and self.showMountpoints: # present available mountpoints
            for p in harddiskmanager.getMountedPartitions():
                path = os.path.join(p.mountpoint, "")
                if path not in self.inhibitMounts and not self.inParentDirs(path, self.inhibitDirs):
                    self.list.append(FileEntryComponent(name=p.description, absolute=path, isDir=True))
            files = []
            directories = []
        elif directory is None:
            files = []
            directories = []
        elif self.useServiceRef:
            # we should not use the 'eServiceReference(string)' constructor, because it doesn't allow ':' in the directoryname
            root = eServiceReference(2, 0, directory)
            if self.additional_extensions:
                root.setName(self.additional_extensions)
            serviceHandler = eServiceCenter.getInstance()
            list = serviceHandler.list(root)

            while True:
                s = list.getNext()
                if not s.valid():
                    del list
                    break
                if s.flags & s.mustDescent:
                    directories.append(s.getPath())
                else:
                    files.append(s)
            directories.sort()
            files.sort()
        else:
            if fileExists(directory):
                try:
                    files = os.listdir(directory)
                except:
                    files = []
                files.sort()
                tmpfiles = files[:]
                for x in tmpfiles:
                    if os.path.isdir(directory + x):
                        directories.append(directory + x + "/")
                        files.remove(x)

        if self.showDirectories:
            if directory:
                if self.showMountpoints and directory == self.current_mountpoint:
                    self.list.append(FileEntryComponent(name="<" + _("List of storage devices") + ">", absolute=None, isDir=True))
                elif (directory != self.topDirectory) and not (self.inhibitMounts and self.getMountpoint(directory) in self.inhibitMounts):
                    self.list.append(FileEntryComponent(name="<" + _("Parent directory") + ">", absolute='/'.join(directory.split('/')[:-2]) + '/', isDir=True))
            for x in directories:
                if not (self.inhibitMounts and self.getMountpoint(x) in self.inhibitMounts) and not self.inParentDirs(x, self.inhibitDirs):
                    name = x.split('/')[-2]
                    self.list.append(FileEntryComponent(name=name, absolute=x, isDir=True))

        if self.showFiles:
            for x in files:
                if self.useServiceRef:
                    path = x.getPath()
                    name = path.split('/')[-1]
                else:
                    path = directory + x
                    name = x

                if (self.matchingPattern is None) or self.matchingPattern.search(path):
                    self.list.append(FileEntryComponent(name=name, absolute=x, isDir=False))

        if self.showMountpoints and len(self.list) == 0:
            self.list.append(FileEntryComponent(name=_("nothing connected"), absolute=None, isDir=False))

        self.l.setList(self.list)

        if select is not None:
            i = 0
            self.moveToIndex(0)
            for x in self.list:
                p = x[0][0]

                if isinstance(p, eServiceReference):
                    p = p.getPath()

                if p == select:
                    self.moveToIndex(i)
                i += 1


class SubsChooserMenuList(MenuList):
    def __init__(self, embeddedAvailable=False, searchSupport=False, historySupport=False):
        MenuList.__init__(self, [], False, eListboxPythonMultiContent)
        self.l.setItemHeight(30)
        self.l.setFont(0, gFont("Regular", 21))
        menulist = []
        if embeddedAvailable:
            res = [('embedded')]
            res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(35, 25), png=loadPNG(os.path.join(os.path.dirname(__file__), 'img', 'key_red.png'))))
            res.append(MultiContentEntryText(pos=(60, 5), size=(350, 25), font=0, flags=RT_VALIGN_CENTER, text=_("Choose from embedded subtitles")))
            menulist.append(res)
        if historySupport:
            res = [('downloaded')]
            res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(35, 25), png=loadPNG(os.path.join(os.path.dirname(__file__), 'img', 'key_yellow.png'))))
            res.append(MultiContentEntryText(pos=(60, 5), size=(350, 25), font=0, flags=RT_VALIGN_CENTER, text=_("Choose from downloaded subtitles")))
            menulist.append(res)
        if searchSupport:
            res = [('search')]
            res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(35, 25), png=loadPNG(os.path.join(os.path.dirname(__file__), 'img', 'key_blue.png'))))
            res.append(MultiContentEntryText(pos=(60, 5), size=(350, 25), font=0, flags=RT_VALIGN_CENTER, text=_("Choose from web subtitles")))
            menulist.append(res)
        if embeddedAvailable or historySupport or searchSupport:
            self.l.setList(menulist)


class E2SubsSeeker(SubsSeeker):
    def __init__(self, session, searchSettings, debug=False):
        self.session = session
        self.download_thread = None
        self.search_settings = searchSettings
        download_path = searchSettings.downloadPath.value
        tmp_path = searchSettings.tmpPath.value

        class SubsSearchSettingsProvider(E2SettingsProvider):
            def __init__(self, providerName, defaults, configSubSection):
                E2SettingsProvider.__init__(self, providerName, configSubSection, defaults)

        SubsSeeker.__init__(self, download_path, tmp_path,
                            captcha_cb=self.captcha_cb,
                            delay_cb=self.delay_cb,
                            message_cb=messageCB,
                            settings_provider_cls=SubsSearchSettingsProvider,
                            settings_provider_args=searchSettings,
                            debug=debug)

        self.providers_error = False
        for p in self.seekers:
            if p.error is not None:
                self.providers_error = True

    def captcha_cb(self, image_path):
        assert self.download_thread is not None
        assert self.download_thread.is_alive()
        return self.download_thread.getCaptcha(image_path)

    def delay_cb(self, seconds):
        assert self.download_thread is not None
        assert self.download_thread.is_alive()
        message = _("Subtitles will be downloaded in") + " " + str(seconds) + " " + _("seconds")
        self.download_thread.getDelay(seconds, message)


class SubsChooser(Screen):
    if isFullHD():
        skin = """
            <screen position="center,center" size="915,690" zPosition="3" >
                <widget name="file_list" position="0,45" size="915,495" scrollbarMode="showOnDemand" />
                <eLabel position="7,555" size="900,1" backgroundColor="#999999" />
                <widget name="menu_list" position="0,570" size="915,120" scrollbarMode="showOnDemand" />
            </screen>
            """
    else:
        skin = """
            <screen position="center,center" size="610,460" zPosition="3" >
                <widget name="file_list" position="0,30" size="610,330" scrollbarMode="showOnDemand" />
                <eLabel position="5,370" size="600,1" backgroundColor="#999999" />
                <widget name="menu_list" position="0,380" size="610,80" scrollbarMode="showOnDemand" />
            </screen>
            """

    def __init__(self, session, subsSettings, subdir=None, embeddedSupport=False, searchSupport=False, historySupport=False, titleList=None):
        Screen.__init__(self, session)
        self.session = session
        self.subsSettings = subsSettings
        defaultDir = subdir
        if subdir is not None and not subdir.endswith('/'):
            defaultDir = subdir + '/'
        self.embeddedList = None
        self.embeddedSubtitle = None
        if embeddedSupport:
            service = self.session.nav.getCurrentService()
            subtitle = service and service.subtitle()
            self.embeddedList = subtitle and subtitle.getSubtitleList()
        self.searchSupport = searchSupport
        self.historySupport = historySupport
        self.titleList = titleList
        ref = self.session.nav.getCurrentlyPlayingServiceReference()
        videoPath = ref and ref.getPath()
        if videoPath and os.path.isfile(videoPath):
            self.videoPath = videoPath
        else:
            self.videoPath = None
        videoName = ref and os.path.split(ref.getPath())[1]
        self["filename"] = StaticText(videoName)
        self["file_list"] = SubFileList(defaultDir)
        self["menu_list"] = SubsChooserMenuList(self.embeddedList, searchSupport, historySupport)
        self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                "ok": self.ok,
                "cancel": self.close,

                "red": self.embeddedSubsSelection,
                "green": lambda: None,
                "yellow": self.downloadedSubsSelection,
                "blue": self.webSubsSelection,

                "up": self["file_list"].up,
                "upRepeated": self["file_list"].up,
                "upUp": lambda: None,
                "left": self["file_list"].pageUp,
                "leftRepeated": self["file_list"].pageUp,
                "leftUp": lambda: None,
                "down": self["file_list"].down,
                "downRepeated": self["file_list"].down,
                "downUp": lambda: None,
                "right": self["file_list"].pageDown,
                "rightRepeated": self["file_list"].pageDown,
                "rightUp": lambda: None,
            }, -2)

        self.onLayoutFinish.append(self.updateTitle)
        self.onLayoutFinish.append(self.disableMenuList)

    def updateTitle(self):
        self.setTitle(_("Choose Subtitles"))

    def disableMenuList(self):
        self["menu_list"].selectionEnabled(False)

    def ok(self):
        if self['file_list'].canDescent():
            self['file_list'].descent()
        else:
            filePath = os.path.join(self['file_list'].current_directory, self['file_list'].getFilename())
            self.close(filePath, False)

    def checkEmbeddedSubsSelection(self, embeddedSubtitle=None):
        if embeddedSubtitle:
            self.close(None, embeddedSubtitle)

    def embeddedSubsSelection(self):
        if self.embeddedList:
            self.session.openWithCallback(self.checkEmbeddedSubsSelection, SubsEmbeddedSelection)

    def webSubsSelection(self):
        def checkDownloadedSubsSelection(downloadedSubtitle=None):
            if downloadedSubtitle:
                self.close(downloadedSubtitle, False, True)

        def paramsDialogCB(callback=None):
            if callback:
                self.session.openWithCallback(checkDownloadedSubsSelection, SubsSearch, seeker, subsSettings.search, self.videoPath, self.titleList, resetSearchParams=False)

        def showProvidersErrorCB(callback):
            if not callback:
                subsSettings.search.showProvidersErrorMessage.value = False
            if subsSettings.search.openParamsDialogOnSearch.value:
                self.session.openWithCallback(paramsDialogCB, SubsSearchParamsMenu, seeker, subsSettings.search, self.titleList, enabledList=False)
            else:
                self.session.openWithCallback(checkDownloadedSubsSelection, SubsSearch, seeker, subsSettings.search, self.videoPath, self.titleList)
        subsSettings = self.subsSettings
        if not self.searchSupport:
            return
        seeker = E2SubsSeeker(self.session, subsSettings.search, debug=True)
        if seeker.providers_error and subsSettings.search.showProvidersErrorMessage.value:
            msg = _("Some subtitles providers are not working") + ".\n"
            msg += _("For more details please check search settings") + "."
            msg += "\n\n"
            msg += _("Do you want to show this message again?")
            self.session.openWithCallback(showProvidersErrorCB, MessageBox, msg, type=MessageBox.TYPE_YESNO)

        elif subsSettings.search.openParamsDialogOnSearch.value:
            self.session.openWithCallback(paramsDialogCB, SubsSearchParamsMenu, seeker, subsSettings.search, self.titleList, enabledList=False)
        else:
            self.session.openWithCallback(checkDownloadedSubsSelection, SubsSearch, seeker, subsSettings.search, self.videoPath, self.titleList)

    def downloadedSubsSelectionCB(self, subtitles, downloadedSubtitle=None):
        fpath = os.path.join(self.subsSettings.search.downloadHistory.path.value, 'hsubtitles.json')
        try:
            json.dump(subtitles, open(fpath, "w"))
        except Exception as e:
            print('[SubsFileChooser] downloadedSubsSelectionCB - %s' % str(e))
        if downloadedSubtitle:
            self.close(downloadedSubtitle, False, True)

    def downloadedSubsSelection(self):
        if not self.historySupport:
            return
        fpath = os.path.join(self.subsSettings.search.downloadHistory.path.value, 'hsubtitles.json')
        try:
            subtitles = json.load(open(fpath, "r"))
        except Exception as e:
            print('[SubsFileChooser] downloadedSubsSelection - %s' % str(e))
            subtitles = []
        self.session.openWithCallback(self.downloadedSubsSelectionCB, SubsDownloadedSelection, subtitles, self.subsSettings.search.downloadHistory)


class SubsDownloadedSelection(Screen):
    class InfoScreen(Screen):
        if isFullHD():
            skin = """
            <screen position = "center,center" size="975,300" zPosition="4" flags="wfNoBorder" backgroundColor="#333333">
                <widget source="path" render="Label" position="7,7" size="960,285" valign="center" halign="center" font="Regular;30"/>
            </screen>
            """
        else:
            skin = """
            <screen position = "center,center" size="650,200" zPosition="4" flags="wfNoBorder" backgroundColor="#333333">
                <widget source="path" render="Label" position="5,5" size="640,190" valign="center" halign="center" font="Regular;20"/>
            </screen>
            """

        def __init__(self, session, subtitle):
            Screen.__init__(self, session)
            self["path"] = StaticText(_(toString(subtitle['fpath'])))

    if isFullHD():
        skin = """
        <screen  position="center,center" size="1050,780" zPosition="3">
            <widget source="header_name" render="Label" position = "7,15" size="540,37" font="Regular;27" halign="left" foregroundColor="#0xcccccc" />
            <widget source="header_provider" render="Label" position = "570,15" size="247,37" font="Regular;27" halign="left" foregroundColor="#0xcccccc" />
            <widget source="header_date" render="Label" position = "787, 15" size="170,25" font="Regular;27" halign="left" foregroundColor="#0xcccccc" />
            <eLabel position="7,67" size="1035,1" backgroundColor="#999999" />
            <widget source="subtitles" render="Listbox" scrollbarMode="showOnDemand" position="7,82" size="1035,532" zPosition="3" transparent="1" >
                <convert type="TemplatedMultiContent">
                    {"templates":
                        {"default": (60, [
                            MultiContentEntryPixmapAlphaBlend(pos = (0, 18),   size = (29, 29), png=0), # key,
                            MultiContentEntryText(pos = (45, 0),   size = (487, 60),  font = 0, flags = RT_HALIGN_CENTER|RT_VALIGN_CENTER|RT_WRAP, text=1, color=0xFF000004), # name,
                            MultiContentEntryText(pos = (562, 0),  size = (247, 60),  font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER,  text = 2, color=0xFF000004), # provider,
                            MultiContentEntryText(pos = (780, 0), size = (255, 60), font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER,  text = 3, color=0xFF000004), # date,
                        ], True, "showOnDemand"),
                        },
                    "fonts": [gFont("Regular", 23)],
                    "itemHeight": 60
                    }
                </convert>
            </widget>
            <eLabel position="7,645" size="1035,1" backgroundColor="#999999" />
            <widget source="entries_sum" render="Label" position = "15, 660" size="450,37" font="Regular;27" halign="left" foregroundColor="white" />
            <eLabel position="7,705" size="1035,1" backgroundColor="#999999" />
            <ePixmap  pixmap="skin_default/buttons/key_info.png" position="15,727" size="35,25" transparent="1" alphatest="on" />
            <ePixmap  pixmap="skin_default/buttons/key_red.png" position="75,727" size="35,25" transparent="1" alphatest="on" />
            <widget source="key_red" render="Label" position = "135, 727" size="345,37" font="Regular;30" halign="left" foregroundColor="white" />
            <ePixmap pixmap="skin_default/buttons/key_blue.png" position="750,727" size="35,25" transparent="1" alphatest="on" />
            <widget source="key_blue" render="Label" position = "810, 727" size="195,37" font="Regular;30" halign="left" foregroundColor="white" />
        </screen> """
    else:
        skin = """
        <screen  position="center,center" size="700,520" zPosition="3">
            <widget source="header_name" render="Label" position = "5,10" size="360,25" font="Regular;18" halign="left" foregroundColor="#0xcccccc" />
            <widget source="header_provider" render="Label" position = "380,10" size="165,25" font="Regular;18" halign="left" foregroundColor="#0xcccccc" />
            <widget source="header_date" render="Label" position = "525, 10" size="170,25" font="Regular;18" halign="left" foregroundColor="#0xcccccc" />
            <eLabel position="5,45" size="690,1" backgroundColor="#999999" />
            <widget source="subtitles" render="Listbox" scrollbarMode="showOnDemand" position="5,55" size="690,355" zPosition="3" transparent="1" >
                <convert type="TemplatedMultiContent">
                    {"templates":
                        {"default": (50, [
                            MultiContentEntryPixmapAlphaBlend(pos = (0, 15),   size = (24, 24), png=0), # key,
                            MultiContentEntryText(pos = (30, 0),   size = (325, 50),  font = 0, flags = RT_HALIGN_CENTER|RT_VALIGN_CENTER|RT_WRAP, text=1, color=0xFF000004), # name,
                            MultiContentEntryText(pos = (375, 0),  size = (165, 50),  font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER,  text = 2, color=0xFF000004), # provider,
                            MultiContentEntryText(pos = (520, 0), size = (170, 50), font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER,  text = 3, color=0xFF000004), # date,
                        ], True, "showOnDemand"),
                        },
                    "fonts": [gFont("Regular", 19), gFont("Regular", 16)],
                    "itemHeight": 50
                    }
                </convert>
            </widget>
            <eLabel position="5,430" size="690,1" backgroundColor="#999999" />
            <widget source="entries_sum" render="Label" position = "10, 440" size="300,25" font="Regular;18" halign="left" foregroundColor="white" />
            <eLabel position="5,470" size="690,1" backgroundColor="#999999" />
            <ePixmap  pixmap="skin_default/buttons/key_info.png" position="10,485" size="35,25" transparent="1" alphatest="on" />
            <ePixmap  pixmap="skin_default/buttons/key_red.png" position="50,485" size="35,25" transparent="1" alphatest="on" />
            <widget source="key_red" render="Label" position = "90, 485" size="230,25" font="Regular;20" halign="left" foregroundColor="white" />
            <ePixmap pixmap="skin_default/buttons/key_blue.png" position="500,485" size="35,25" transparent="1" alphatest="on" />
            <widget source="key_blue" render="Label" position = "540, 485" size="130,25" font="Regular;20" halign="left" foregroundColor="white" />
        </screen> """

    def __init__(self, session, subtitles, historySettings, marked=None):
        Screen.__init__(self, session)
        self["header_name"] = StaticText(_("Name"))
        self["header_provider"] = StaticText(_("Provider"))
        self["header_date"] = StaticText(_("Download date"))
        self["subtitles"] = List()
        self["entries_sum"] = StaticText()
        self["key_red"] = StaticText(_("Remove (file)"))
        self["key_blue"] = StaticText(_("Settings"))
        self["actions"] = ActionMap(["ColorActions", "OkCancelActions", "InfoActions"],
        {
            "ok": self.ok,
            "cancel": self.cancel,
            "info": self.showInfo,
            "red": self.removeEntry,
            "blue": self.openSettings,
        }, -2)
        self["infoActions"] = ActionMap(["ColorActions", "OkCancelActions", "DirectionActions", "InfoActions"],
            {
             "ok": self.closeInfoDialog,
             "cancel": self.closeInfoDialog,
             "info": self.closeInfoDialog,
             "red": self.closeInfoDialog,
             "green": self.closeInfoDialog,
             "blue": self.closeInfoDialog,
             "up": self.closeInfoDialog,
             "upUp": self.closeInfoDialog,
             "down": self.closeInfoDialog,
             "downUp": self.closeInfoDialog,
             "right": self.closeInfoDialog,
             "rightUp": self.closeInfoDialog,
             "left": self.closeInfoDialog,
             "leftUp": self.closeInfoDialog,
        })
        self["infoActions"].setEnabled(False)
        self.subtitles = subtitles
        self.historySettings = historySettings
        self.marked = marked or []
        self.onLayoutFinish.append(self.updateWindowTitle)
        self.onLayoutFinish.append(self.updateSubsList)
        self.onLayoutFinish.append(self.updateEntriesSum)
        self.onLayoutFinish.append(self.updateRemoveAction)

    def updateWindowTitle(self):
        self.setTitle(_("Downloaded Subtitles"))

    def updateSubsList(self):
        imgDict = {'unk': loadPNG(os.path.join(os.path.dirname(__file__), 'img', 'countries', 'UNK.png'))}
        subtitleListGUI = []
        for sub in self.subtitles[:]:
            fpath = toString(sub['fpath'])
            if not os.path.isfile(fpath):
                self.subtitles.remove(sub)
                continue
            if sub.get('country', 'unk') not in imgDict:
                countryImgPath = os.path.join(os.path.dirname(__file__), 'img', 'countries', sub['country'] + '.png')
                if os.path.isfile(countryImgPath):
                    imgDict[sub['country']] = loadPNG(toString(countryImgPath))
                    countryPng = imgDict[sub['country']]
                else:
                    countryPng = imgDict['unk']
            if sub in self.marked:
                color = 0x00ff00
            else:
                color = 0xffffff
            date = datetime.fromtimestamp(os.path.getctime(fpath)).strftime("%d-%m-%Y %H:%M")
            name = os.path.splitext(os.path.basename(fpath))[0]
            subtitleListGUI.append((countryPng, toString(name), toString(sub['provider']), date, color),)
        imgDict = None
        self['subtitles'].list = subtitleListGUI

    def updateEntriesSum(self):
        limit = int(self.historySettings.limit.value)
        self["entries_sum"].text = _("Entries count:") + " " + str(len(self.subtitles)) + " / " + str(limit)

    def updateRemoveAction(self):
        if self.historySettings.removeAction.value == 'file':
            self["key_red"].text = _("Remove Entry (List+File)")
        else:
            self["key_red"].text = _("Remove Entry (List)")

    def removeEntry(self):
        def removeEntryCB(doRemove=False):
            if doRemove:
                if self.historySettings.removeAction.value == 'file':
                    try:
                        os.unlink(subtitle['fpath'])
                    except OSError as e:
                        print("[SubsDownloadedSelection] cannot remove - %s" % (str(e)))
                        self.session.open(MessageBox, _("There was an error while removing subtitle, please check log"), type=MessageBox.TYPE_ERROR)
                    else:
                        self.subtitles.remove(subtitle)
                        curridx = self['subtitles'].index
                        self.updateSubsList()
                        self['subtitles'].index = curridx - 1
                        self.updateEntriesSum()
                else:
                    self.subtitles.remove(subtitle)
                    curridx = self['subtitles'].index
                    self.updateSubsList()
                    self['subtitles'].index = curridx - 1
                    self.updateEntriesSum()

        if self["subtitles"].count() > 0:
            subtitle = self.subtitles[self["subtitles"].index]
            if self.historySettings.removeAction.value == 'file':
                if self.historySettings.removeActionAsk.value:
                    message = _("Subtitle") + " '" + toString(subtitle['name']) + "' " + _("will be removed from file system")
                    message += "\n\n" + _("Do you want to proceed?")
                    self.session.openWithCallback(removeEntryCB, MessageBox, message, type=MessageBox.TYPE_YESNO)
                else:
                    removeEntryCB(True)
            else:
                if self.historySettings.removeActionAsk.value:
                    message = _("Subtitle") + " '" + toString(subtitle['name']) + "' " + _("will be removed from list")
                    message += "\n\n" + _("Do you want to proceed?")
                    self.session.openWithCallback(removeEntryCB, MessageBox, message, type=MessageBox.TYPE_YESNO)
                else:
                    removeEntryCB(True)

    def openSettings(self):
        def menuCB(callback=None):
            self.updateEntriesSum()
            self.updateRemoveAction()
        self.session.openWithCallback(menuCB, SubsDownloadedSubtitlesMenu, self.historySettings)

    def showInfo(self):
        if self["subtitles"].count() > 0:
            subtitle = self.subtitles[self["subtitles"].index]
            self["actions"].setEnabled(False)
            self["infoActions"].setEnabled(True)
            self.__infoScreen = self.session.instantiateDialog(self.InfoScreen, subtitle)
            self.__infoScreen.show()

    def closeInfoDialog(self):
        self.session.deleteDialog(self.__infoScreen)
        self["infoActions"].setEnabled(False)
        self["actions"].setEnabled(True)

    def ok(self):
        if self["subtitles"].count() > 0:
            subtitle = self.subtitles[self["subtitles"].index]
            self.close(self.subtitles, subtitle['fpath'])
        self.close(self.subtitles, None)

    def cancel(self):
        self.close(self.subtitles, None)


class SubsDownloadedSubtitlesMenu(BaseMenuScreen):
    def __init__(self, session, historySettings):
        BaseMenuScreen.__init__(self, session, _("Downloaded Subtitles - Settings"))
        self.historySettings = historySettings

    def buildMenu(self):
        menuList = []
        menuList.append(getConfigListEntry(_("Max history entries"), self.historySettings.limit))
        menuList.append(getConfigListEntry(_("Remove action"), self.historySettings.removeAction))
        menuList.append(getConfigListEntry(_("Ask on remove action"), self.historySettings.removeActionAsk))
        self["config"].setList(menuList)

    def keyOK(self):
        if self["config"].getCurrent()[1] == self.historySettings.path:
            self.session.openWithCallback(self.changeDir, LocationBox,
                 _("Select Directory"), currDir=self.historySettings.path.value)

# source from openpli


class SubsEmbeddedSelection(Screen):
    if isFullHD():
        skin = """
        <screen name="SubsEmbeddedSelection" position="center,center" size="727,330">
            <widget source="streams" render="Listbox" scrollbarMode="showOnDemand" position="15,60" size="697,270" zPosition="3" transparent="1" >
                <convert type="TemplatedMultiContent">
                    {"templates":
                        {"default": (37, [
                            MultiContentEntryText(pos = (0, 0),   size = (52, 37),  font = 0, flags = RT_HALIGN_LEFT,  text = 1), # key,
                            MultiContentEntryText(pos = (60, 0),  size = (90, 37),  font = 0, flags = RT_HALIGN_LEFT,  text = 2), # number,
                            MultiContentEntryText(pos = (165, 0), size = (180, 37), font = 0, flags = RT_HALIGN_LEFT,  text = 3), # description,
                            MultiContentEntryText(pos = (360, 0), size = (300, 37), font = 0, flags = RT_HALIGN_LEFT,  text = 4), # language,
                        ], True, "showNever"),
                        },
                    "fonts": [gFont("Regular", 30)],
                    "itemHeight": 37
                    }
                </convert>
            </widget>
        </screen>"""
    else:
        skin = """
        <screen name="SubsEmbeddedSelection" position="center,center" size="485,220">
            <widget source="streams" render="Listbox" scrollbarMode="showOnDemand" position="10,40" size="465,180" zPosition="3" transparent="1" >
                <convert type="TemplatedMultiContent">
                    {"templates":
                        {"default": (25, [
                            MultiContentEntryText(pos = (0, 0),   size = (35, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 1), # key,
                            MultiContentEntryText(pos = (40, 0),  size = (60, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 2), # number,
                            MultiContentEntryText(pos = (110, 0), size = (120, 25), font = 0, flags = RT_HALIGN_LEFT,  text = 3), # description,
                            MultiContentEntryText(pos = (240, 0), size = (200, 25), font = 0, flags = RT_HALIGN_LEFT,  text = 4), # language,
                        ], True, "showNever"),
                        },
                    "fonts": [gFont("Regular", 20), gFont("Regular", 16)],
                    "itemHeight": 25
                    }
                </convert>
            </widget>
        </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self["streams"] = List([], enableWrapAround=True)
        self["actions"] = ActionMap(["SetupActions", "DirectionActions", "MenuActions"],
        {
            "ok": self.keyOk,
            "cancel": self.cancel,
        }, -2)
        self.onLayoutFinish.append(self.updateTitle)
        self.onLayoutFinish.append(self.fillList)

    def updateTitle(self):
        self.setTitle(_("Choose subtitles"))

    def fillList(self):
        idx = 0
        streams = []
        subtitlelist = self.getSubtitleList()
        for x in subtitlelist:
            number = str(x[1])
            description = "?"
            language = ""

            try:
                if x[4] != "und":
                    if x[4] in LanguageCodes:
                        language = LanguageCodes[x[4]][0]
                    else:
                        language = x[4]
            except:
                language = ""

            if x[0] == 0:
                description = "DVB"
                number = "%x" % (x[1])

            elif x[0] == 1:
                description = "teletext"
                number = "%x%02x" % (x[3] and x[3] or 8, x[2])

            elif x[0] == 2:
                types = ("unknown", "embedded", "SSA file", "ASS file",
                        "SRT file", "VOB file", "PGS file")
                try:
                    description = types[x[2]]
                except:
                    description = _("unknown") + ": %s" % x[2]
                number = str(int(number) + 1)
            print(x, number, description, language)
            streams.append((x, "", number, description, language))
            idx += 1
        self["streams"].list = streams

    def getSubtitleList(self):
        service = self.session.nav.getCurrentService()
        subtitle = service and service.subtitle()
        subtitlelist = subtitle and subtitle.getSubtitleList()
        embeddedlist = []
        for x in subtitlelist:
            if x[0] == 2:
                types = ("unknown", "embedded", "SSA file", "ASS file",
                            "SRT file", "VOB file", "PGS file")
                # filter embedded subtitles
                if x[2] not in [1, 2, 3, 4, 5, 6]:
                    continue
            embeddedlist.append(x)
        return embeddedlist

        self.selectedSubtitle = None
        return subtitlelist

    def cancel(self):
        self.close()

    def keyOk(self):
        cur = self["streams"].getCurrent()
        self.close(cur[0][:4])


class SubsSearchProcess(object):
    processes = []
    process_path = os.path.join(os.path.dirname(__file__), 'searchsubs.py')

    def __init__(self):
        self.log = SimpleLogger('SubsSearchProcess', SimpleLogger.LOG_INFO)
        self.toRead = None
        self.pPayload = None
        self.data = ""
        self.__stopping = False
        self.appContainer = eConsoleAppContainer()
        self.stdoutAvail_conn = eConnectCallback(self.appContainer.stdoutAvail, self.dataOutCB)
        self.stderrAvail_conn = eConnectCallback(self.appContainer.stderrAvail, self.dataErrCB)
        self.appContainer_conn = eConnectCallback(self.appContainer.appClosed, self.finishedCB)

    def recieveMessages(self, data):
        def getMessage(data):
            mSize = int(data[:7])
            mPayload = data[7:mSize]
            mPart = mSize > len(data)
            return mSize, mPayload, mPart

        def readMessage(payload):
            try:
                message = json.loads(payload)
            except EOFError:
                pass
            except Exception:
                self.log.debug('data is not in JSON format! - %s' % str(payload))
            else:
                self.log.debug('message successfully recieved')
                self.toRead = None
                self.pPayload = None
                self.handleMessage(message)

        def readStart(data):
            mSize, mPayload, mPart = getMessage(data)
            if not mPart:
                data = data[mSize:]
                readMessage(mPayload)
                if len(data) > 0:
                    readStart(data)
            else:
                self.toRead = mSize - len(data)
                self.pPayload = mPayload

        def readContinue(data):
            nextdata = data[:self.toRead]
            self.pPayload += nextdata
            data = data[len(nextdata):]
            self.toRead -= len(nextdata)
            if self.toRead == 0:
                readMessage(self.pPayload)
                if len(data) > 0:
                    readStart(data)

        if self.pPayload is not None:
            readContinue(data)
        else:
            readStart(data)

    def handleMessage(self, data):
        self.log.debug('handleMessage "%s"', data)
        if data['message'] == Messages.MESSAGE_UPDATE_CALLBACK:
            self.callbacks['updateCB'](data['value'])
        if data['message'] == Messages.MESSAGE_OVERWRITE_CALLBACK:
            self.callbacks['overwriteCB'](data['value'], self.write)
        if data['message'] == Messages.MESSAGE_CHOOSE_FILE_CALLBACK:
            self.callbacks['choosefileCB'](data['value'], self.write)
        if data['message'] == Messages.MESSAGE_CAPTCHA_CALLBACK:
            self.callbacks['captchaCB'](data['value'], self.write)
        if data['message'] == Messages.MESSAGE_DELAY_CALLBACK:
            self.callbacks['delayCB'](data['value'], self.write)
        if data['message'] == Messages.MESSAGE_FINISHED_SCRIPT:
            self.callbacks['successCB'](data['value'])
        if data['message'] == Messages.MESSAGE_CANCELLED_SCRIPT:
            print('script successfully cancelled')
        if data['message'] == Messages.MESSAGE_ERROR_SCRIPT:
            self.callbacks['errorCB'](data['value'])

    def start(self, params, callbacks):
        self.processes.append(self)
        self.callbacks = callbacks
        cmd = "python %s" % self.process_path
        self.log.debug("start - '%s'", cmd)
        self.appContainer.execute(cmd)
        self.write(params)

    def running(self):
        return self.appContainer.running()

    def stop(self):
        def check_stopped():
            if not self.appContainer.running():
                self.stopTimer.stop()
                del self.stopTimer_conn
                del self.stopTimer
                del self.__i
                return
            if self.__i == 0:
                self.__i += 1
                self.log.debug('2. sending SIGKILL')
                self.appContainer.kill()
            elif self.__i == 1:
                self.stopTimer.stop()
                del self.stopTimer_conn
                del self.stopTimer
                raise Exception("cannot kill process")

        if self.__stopping:
            self.log.debug('already stopping..')
            return
        self.__stopping = True
        self.log.debug('stopping process..')
        self.__i = 0

        if self.appContainer.running():
            self.log.debug('1. sending SIGINT')
            self.appContainer.sendCtrlC()
            self.stopTimer = eTimer()
            self.stopTimer_conn = eConnectCallback(self.stopTimer.timeout, check_stopped)
            self.stopTimer.start(2000, False)
        else:
            self.log.debug('process is already stopped')

    def write(self, data):
        dump = json.dumps(data)
        dump = "%07d%s" % (len(dump), dump)
        try:
            self.appContainer.write(dump)
        # DMM image
        except TypeError:
            self.appContainer.write(dump, len(dump))

    def dataErrCB(self, data):
        self.log.debug("dataErrCB: '%s'", data)
        self.error = data

    def dataOutCB(self, data):
        self.log.debug("dataOutCB: '%s", data)
        self.recieveMessages(data)

    def finishedCB(self, retval):
        self.processes.remove(self)
        self.log.debug('process finished, retval:%d', retval)


class Suggestions(object):
    def __init__(self):
        self._cancelled = False

    def __str__(self):
        return self.__class__.__name__

    def cancel(self):
        self._cancelled = True

    def getSuggestions(self, queryString, successCB, errorCB):
        if queryString is not None:
            d = self._getSuggestions(queryString)
            self.successCB = successCB
            self.errorCB = errorCB
            d.addCallbacks(self.getSuggestionsSuccess, self.getSuggestionsError)

    def getSuggestionsSuccess(self, data):
        if not self._cancelled:
            self.successCB(self._processResult(data))

    def getSuggestionsError(self, failure):
        if not self._cancelled:
            failure.printTraceback()
            self.errorCB(failure)

    def _getSuggestions(self):
        return Deferred()

    def _processResult(self, data):
        return data


class OpenSubtitlesSuggestions(Suggestions):
    def _getSuggestions(self, queryString):
        query = "http://www.opensubtitles.org/libs/suggest.php?format=json2&SubLanguageID=null&MovieName=" + quote(queryString)
        return client.getPage(six.ensure_binary(query), timeout=6)

    def _processResult(self, data):
        return json.loads(data)['result']


class HistorySuggestions(Suggestions):
    def __init__(self, historyCfg):
        Suggestions.__init__(self)
        self.historyCfg = historyCfg

    def _getSuggestions(self, queryString):
        def getHistory(queryString):
            historyList = self.historyCfg.value.split(',')
            historyList = [{'name': name, 'total': len(historyList) - idx} for idx, name in enumerate(historyList)]
            d.callback(historyList)
        d = Deferred()
        getHistory(queryString)
        return d


class BaseSuggestionsListScreen(Screen):
    def __init__(self, session, title, configTextWithSuggestions, positionX, titleColor):
        desktopSize = getDesktopSize()
        windowSize = (int(0.35 * desktopSize[0]), 0.25 * desktopSize[1])
        fontSize = 27 if isFullHD() else 18
        self.skin = """
            <screen position="%d, %d" size="%d,%d" backgroundColor="#33202020" flags="wfNoBorder" zPosition="6" >
                <widget source="suggestionstitle" render="Label" position = "0,0" size="%d, %d" font="Regular;%d" halign="center" valign="center" foregroundColor="%s" transparent="0" />
                <widget source="suggestionslist" render="Listbox" position="%d,%d" size="%d, %d" scrollbarMode="showOnDemand" transparent="1" >
                    <convert type="TemplatedMultiContent">
                         {"templates":
                            {"default": (%d, [
                                MultiContentEntryText(pos = (0, 0),   size = (%d, %d),  font = 0, flags = RT_HALIGN_LEFT,  text = 0), # title,
                            ], True, "showOnDemand"),
                            "notselected": (%d, [
                                MultiContentEntryText(pos = (0, 0),   size = (%d, %d),  font = 0, flags = RT_HALIGN_LEFT,  text = 0), # title,
                            ], False, "showOnDemand")
                            },
                        "fonts": [gFont("Regular", %d)],
                        "itemHeight": %d
                    }
                    </convert>
                </widget>
            </screen>""" % (
                    positionX, int(0.03 * desktopSize[1]), windowSize[0], windowSize[1],
                    windowSize[0], fontSize + 10, fontSize, titleColor,
                    int(0.05 * windowSize[0]), fontSize + 10 + 20, int(0.9 * windowSize[0]), windowSize[1] - (fontSize + 10 + 20 + int(0.05 * windowSize[1])),
                    fontSize + 5,
                    int(0.9 * windowSize[0]), fontSize + 10,
                    fontSize + 5,
                    int(0.9 * windowSize[0]), fontSize + 10,
                    fontSize,
                    fontSize + 5)
        Screen.__init__(self, session)
        self.list = []
        self["suggestionslist"] = List(self.list)
        self["suggestionstitle"] = StaticText(toString(title))
        self.configTextWithSuggestion = configTextWithSuggestions

    def update(self, suggestions):
        if suggestions:
            if not self.shown:
                self.show()
            suggestions.sort(key=lambda x: int(x['total']))
            suggestions.reverse()
            self.list = []
            for s in suggestions:
                self.list.append((toString(s['name']),))
            self["suggestionslist"].setList(self.list)
            self["suggestionslist"].setIndex(0)
            print(suggestions)
        else:
            self.hide()

    def getlistlenght(self):
        return len(self.list)

    def up(self):
        if self.list:
            self["suggestionslist"].selectPrevious()
            return self.getSelection()

    def down(self):
        if self.list:
            self["suggestionslist"].selectNext()
            return self.getSelection()

    def pageUp(self):
        if self.list:
            self["suggestionslist"].selectPrevious()
            return self.getSelection()

    def pageDown(self):
        if self.list:
            self["suggestionslist"].selectNext()
            return self.getSelection()

    def activate(self):
        self.enableSelection(True)
        return self.getSelection()

    def deactivate(self):
        self.enableSelection(False)
        return self.getSelection()

    def getSelection(self):
        if not self["suggestionslist"].getCurrent():
            return None
        return self["suggestionslist"].getCurrent()[0]

    def enableSelection(self, value):
        if value:
            self['suggestionslist'].style = 'default'
        else:
            self['suggestionslist'].style = 'notselected'


class SuggestionsListScreen(BaseSuggestionsListScreen):
    def __init__(self, session, configTextWithSuggestions):
        title = _("Suggestions") + " (" + _("press green") + ")"
        positionX = getDesktopSize()[0] * 0.6
        BaseSuggestionsListScreen.__init__(self, session, title, configTextWithSuggestions, positionX, 'green')


class HistoryListScreen(BaseSuggestionsListScreen):
    def __init__(self, session, configTextWithSuggestions):
        title = _("History") + " (" + _("press red") + ")"
        positionX = getDesktopSize()[0] * 0.05
        BaseSuggestionsListScreen.__init__(self, session, title, configTextWithSuggestions, positionX, 'red')


class ConfigTextWithSuggestionsAndHistory(ConfigText):
    def __init__(self, historyCfg, default="", fixed_size=True, visible_width=False):
        ConfigText.__init__(self, default, fixed_size, visible_width)
        self.historyCfg = historyCfg
        self.historyClass = HistorySuggestions
        self.historyWindow = None
        self.__history = None
        self.suggestionsClass = OpenSubtitlesSuggestions
        self.suggestionsWindow = None
        self.__suggestions = None
        self.currentWindow = None

    def handleKey(self, key, callback=None):
        ConfigText.handleKey(self, key, callback)
        if key in [KEY_DELETE, KEY_BACKSPACE, KEY_ASCII, KEY_TIMEOUT]:
            self.getSuggestions()

    def onSelect(self, session):
        ConfigText.onSelect(self, session)
        if session is not None:
            if self.suggestionsWindow is None:
                self.suggestionsWindow = session.instantiateDialog(SuggestionsListScreen, self)
            self.suggestionsWindow.deactivate()
            self.suggestionsWindow.show()
            if self.historyWindow is None:
                self.historyWindow = session.instantiateDialog(HistoryListScreen, self)
            self.historyWindow.deactivate()
            self.historyWindow.show()
        self.getSuggestions()
        self.getHistory()

    def onDeselect(self, session):
        self.cancelGetSuggestions()
        self.cancelGetHistory()
        ConfigText.onDeselect(self, session)
        if self.suggestionsWindow is not None:
            self.suggestionsWindow.hide()
        if self.historyWindow is not None:
            self.historyWindow.hide()

    def getCurrentSelection(self):
        if self.currentWindow.getlistlenght() > 0:
            return self.currentWindow.getSelection()

    def currentListUp(self):
        if self.currentWindow.getlistlenght() > 0:
            self.value = self.currentWindow.up()

    def currentListDown(self):
        if self.currentWindow.getlistlenght() > 0:
            self.value = self.currentWindow.down()

    def currentListPageDown(self):
        if self.currentWindow.getlistlenght() > 0:
            self.value = self.currentWindow.pageDown()

    def currentListPageUp(self):
        if self.currentWindow.getlistlenght() > 0:
            self.value = self.currentWindow.pageUp()

    def propagateSuggestions(self, suggestionsList):
        self.cancelGetSuggestions()
        if self.suggestionsWindow:
            self.suggestionsWindow.update(suggestionsList)

    def propagateHistory(self, historyList):
        self.cancelGetHistory()
        if self.historyWindow:
            self.historyWindow.update(historyList)

    def enableSuggestions(self, value):
        if value:
            if self.suggestionsWindow:
                self.tmpValue = self.value
                selection = self.suggestionsWindow.activate()
                if selection is None:
                    print('empty suggesstions list')
                    return False
                self.value = selection
                self.currentWindow = self.suggestionsWindow
                return True
            else:
                print('Error - suggestionsWindow no longer exists')
                return False
        else:
            self.cancelGetSuggestions()
            if self.suggestionsWindow:
                self.suggestionsWindow.deactivate()
                self.currentWindow = None
                self.getSuggestions()
                return True
            else:
                print('Error - suggestionsWindow no longer exists')
                return False

    def enableHistory(self, value):
        if value:
            if self.historyWindow:
                self.tmpValue = self.value
                selection = self.historyWindow.activate()
                if selection is None:
                    print("Error - empty history list")
                    return False
                self.value = selection
                self.currentWindow = self.historyWindow
                return True
            else:
                print('Error - historyWindow no longer exists')
                return False
        else:
            self.cancelGetHistory()
            if self.historyWindow:
                self.historyWindow.deactivate()
                self.currentWindow = None
                self.getHistory()
                return True
            else:
                print('Error - historyWindow no longer exists')
                return False

    def cancelGetSuggestions(self):
        if self.__suggestions is not None:
            self.__suggestions.cancel()

    def cancelGetHistory(self):
        if self.__history is not None:
            self.__history.cancel()

    def gotSuggestionsError(self, val):
        print("[ConfigTextWithSuggestions] gotSuggestionsError:", val)

    def gotHistoryError(self, val):
        print("[ConfigTextWithSuggestions] gotHistoryError:", val)

    def getSuggestions(self):
        self.__suggestions = self.suggestionsClass().getSuggestions(self.value, self.propagateSuggestions, self.gotSuggestionsError)

    def getHistory(self):
        self.__history = self.historyClass(self.historyCfg).getSuggestions(self.value, self.propagateHistory, self.gotHistoryError)

    def cancelSuggestions(self):
        self.value = self.tmpValue
        self.enableSuggestions(False)
        self.enableHistory(False)


class Message(object):
    def __init__(self, infowidget, errorwidget):
        self.infowidget = infowidget
        self.errorwidget = errorwidget
        self.timer = eTimer()
        self.timer_conn = eConnectCallback(self.timer.timeout, self.hide)

    def info(self, text, timeout=None):
        self.timer.stop()
        self.errorwidget.hide()
        self.infowidget.setText(text)
        self.infowidget.show()
        if timeout:
            self.timer.start(timeout, True)

    def error(self, text, timeout=None):
        self.timer.stop()
        self.infowidget.hide()
        self.errorwidget.setText(text)
        self.errorwidget.show()
        if timeout:
            self.timer.start(timeout, True)

    def hide(self):
        self.timer.stop()
        self.errorwidget.hide()
        self.infowidget.hide()

    def exit(self):
        self.hide()
        del self.timer_conn
        del self.timer


class SearchParamsHelper(object):
    def __init__(self, seeker, searchSettings):
        self.seeker = seeker
        self.searchSettings = searchSettings
        self.searchTitle = searchSettings.title
        self.searchType = searchSettings.type
        self.searchYear = searchSettings.year
        self.searchSeason = searchSettings.season
        self.searchEpisode = searchSettings.episode
        self.searchProvider = searchSettings.provider
        self.searchUseFilePath = searchSettings.useFilePath

    def resetSearchParams(self):
        self.searchType.value = self.searchType.default
        self.searchType.save()
        self.searchTitle.value = self.searchTitle.default
        self.searchTitle.save()
        self.searchSeason.value = self.searchSeason.default
        self.searchSeason.save()
        self.searchEpisode.value = self.searchEpisode.default
        self.searchEpisode.save()
        self.searchYear.value = self.searchYear.default
        self.searchYear.save()
        self.searchProvider.value = self.searchProvider.default
        self.searchProvider.save()
        self.searchUseFilePath.value = self.searchUseFilePath.default

    def detectSearchParams(self, searchExpression):
        self.resetSearchParams()
        params = detectSearchParams(searchExpression)
        if params[2]:
            self.searchType.value = "tv_show"
            self.searchTitle.value = params[2]
            self.searchSeason.value = params[3] and int(params[3]) or 0
            self.searchEpisode.value = params[4] and int(params[4]) or 0
        else:
            self.searchType.value = "movie"
            self.searchTitle.value = params[0]
            self.searchYear.value = params[1] and int(params[1]) or 0
        self.updateProviders()

    def getSearchParams(self):
        langs = [self.searchSettings.lang1.value,
                 self.searchSettings.lang2.value,
                 self.searchSettings.lang3.value]
        provider = self.searchProvider.value
        title = self.searchTitle.value
        tvshow = self.searchType.value == "tv_show" and title or ""
        year = self.searchYear.value and not tvshow and str(self.searchYear.value) or ""
        season = self.searchSeason.value and tvshow and str(self.searchSeason.value) or ""
        episode = self.searchEpisode.value and tvshow and str(self.searchEpisode.value) or ""
        return provider, langs, title, year, tvshow, season, episode

    def updateProviders(self):
        tvshow = self.searchType.value == "tv_show"
        providers = self.seeker.getProviders([self.searchSettings.lang1.value,
                 self.searchSettings.lang2.value,
                 self.searchSettings.lang3.value], not tvshow, tvshow)
        choiceList = []
        choiceList.append(("all", _("All")))
        choiceList.extend((p.id, p.provider_name) for p in providers)
        self.searchProvider.setChoices(choiceList)
        if self.searchProvider.value not in [p.id for p in providers]:
            if tvshow:
                self.searchProvider.value = self.searchSettings.tvshowProvider.value
            else:
                self.searchProvider.value = self.searchSettings.movieProvider.value
        tvshowProviders = self.seeker.getProviders(movie=False, tvshow=True)
        choiceList = []
        choiceList.append(("all", _("All")))
        choiceList.extend((p.id, p.provider_name) for p in tvshowProviders)
        self.searchSettings.tvshowProvider.setChoices(choiceList)
        movieProviders = self.seeker.getProviders(movie=True, tvshow=False)
        choiceList = []
        choiceList.append(("all", _("All")))
        choiceList.extend((p.id, p.provider_name) for p in movieProviders)
        self.searchSettings.movieProvider.setChoices(choiceList)


class SubsSearchDownloadOptions(Screen, ConfigListScreen):
    if isFullHD():
        skin = """
            <screen position="center,center" size="735,525" zPosition="5" >
                <widget name="config" position="15,15" size="705,165" font="Regular;27" itemHeight="37" zPosition="1" />
                <eLabel position="12,192" size="711,118" backgroundColor="#ff0000" />
                <widget source="fname" render="Label" position="15,195" size="705,112" valign="center" halign="center" font="Regular;28" foregroundColor="#ffffff" zPosition="1" />
                <eLabel position="12,330" size="711,118" backgroundColor="#00ff00" />
                <widget source="dpath" render="Label" position="15,333" size="705,112" valign="center" halign="center" font="Regular;28" foregroundColor="#ffffff" zPosition="1" />
                <eLabel position="7,457" size="720,1" backgroundColor="#999999" />
                <ePixmap  pixmap="skin_default/buttons/key_red.png" position="15,472" size="35,25" transparent="1" alphatest="on" />
                <widget source="key_red" render="Label" position = "75,472" size="165,37" font="Regular;30" halign="left" foregroundColor="white" />
                <ePixmap pixmap="skin_default/buttons/key_green.png" position="255,472" size="35,25" transparent="1" alphatest="on" />
                <widget source="key_green" render="Label" position = "315,472" size="165,37" font="Regular;30" halign="left" foregroundColor="white" />
                <ePixmap pixmap="skin_default/buttons/key_blue.png" position="495,472" size="35,25" transparent="1" alphatest="on" />
                <widget source="key_blue" render="Label" position = "555,472" size="720,37" font="Regular;30" halign="left" foregroundColor="white" />
            </screen>
        """
    else:
        skin = """
            <screen position="center,center" size="490,350" zPosition="5" >
                <widget name="config" position="10, 10" size="470,110" zPosition="1" />
                <eLabel position="8,128" size="474,79" backgroundColor="#ff0000" />
                <widget source="fname" render="Label" position="10,130" size="470,75" valign="center" halign="center" font="Regular;19" foregroundColor="#ffffff" zPosition="1" />
                <eLabel position="8,220" size="474,79" backgroundColor="#00ff00" />
                <widget source="dpath" render="Label" position="10,222" size="470,75" valign="center" halign="center" font="Regular;19" foregroundColor="#ffffff" zPosition="1" />
                <eLabel position="5,305" size="480,1" backgroundColor="#999999" />
                <ePixmap  pixmap="skin_default/buttons/key_red.png" position="10,315" size="35,25" transparent="1" alphatest="on" />
                <widget source="key_red" render="Label" position = "50, 315" size="110,25" font="Regular;20" halign="left" foregroundColor="white" />
                <ePixmap pixmap="skin_default/buttons/key_green.png" position="170,315" size="35,25" transparent="1" alphatest="on" />
                <widget source="key_green" render="Label" position = "210, 315" size="110,25" font="Regular;20" halign="left" foregroundColor="white" />
                <ePixmap pixmap="skin_default/buttons/key_blue.png" position="330,315" size="35,25" transparent="1" alphatest="on" />
                <widget source="key_blue" render="Label" position = "370, 315" size="480,25" font="Regular;20" halign="left" foregroundColor="white" />
            </screen>
        """

    def __init__(self, session, subtitle, saveAs, saveTo, addLang, dPath, vPath=None):
        Screen.__init__(self, session)
        saveAsOptions = []
        saveAsOptions.append(('version', _("Release")))
        if vPath is not None and os.path.isfile(vPath):
            saveAsOptions.append(('video', _("Video filename")))
        saveAsOptions.append(('custom', _("User defined")))
        saveToOptions = []
        saveToOptions.append(('custom', _('User defined')))
        if vPath is not None and os.path.isfile(vPath):
            saveToOptions.append(('video', _('Next to video')))
        if saveAs == 'default':
            # we don't know what the default filename will be
            saveAs = 'version'
        elif saveAs == 'video' and vPath is None:
            saveAs = 'version'
        if saveTo == 'video' and vPath is None:
            saveTo = 'custom'
        self.configSaveAs = ConfigSelection(default=saveAs, choices=saveAsOptions)
        self.configSaveTo = ConfigSelection(default=saveTo, choices=saveToOptions)
        self.configAddLang = ConfigYesNo(default=addLang)
        configList = [
            getConfigListEntry(_("Save to"), self.configSaveTo),
            getConfigListEntry(_("Save as"), self.configSaveAs),
            getConfigListEntry(_("Append language to filename"), self.configAddLang),
        ]
        ConfigListScreen.__init__(self, configList, session)
        self.subtitle = subtitle
        self.dPath = dPath
        self.vPath = vPath
        self["fname"] = StaticText()
        self["dpath"] = StaticText()
        self["key_red"] = StaticText(_("Filename"))
        self["key_green"] = StaticText(_("Path"))
        self["key_blue"] = StaticText(_("Reset"))
        self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions"],
        {
            "right": self.keyRight,
             "left": self.keyLeft,
             "ok": self.confirm,
             "cancel": self.cancel,
             "red": self.editFName,
             "green": self.editDPath,
             "blue": self.resetDefaults
        }, -2)
        self.onLayoutFinish.append(self.updateWindowTitle)
        self.onLayoutFinish.append(self.updateFName)
        self.onLayoutFinish.append(self.updateDPath)

    def buildMenu(self):
        configList = []
        configList.append(getConfigListEntry(_("Save to"), self.configSaveTo))
        configList.append(getConfigListEntry(_("Save as"), self.configSaveAs))
        if self.configSaveAs.value != "custom":
            configList.append(getConfigListEntry(_("Append language to filename"), self.configAddLang))
        self["config"].setList(configList)

    def updateWindowTitle(self):
        self.setTitle(_("Download options"))

    def updateFName(self):
        fname = None
        if self.configSaveAs.value == "video":
            fname = os.path.splitext(os.path.basename(self.vPath))[0]
        elif self.configSaveAs.value == "version":
            fname = os.path.splitext(self.subtitle['filename'])[0]
        if self.configAddLang.value and not self.configSaveAs.value == "custom":
            fname = "%s.%s" % (fname, languageTranslate(self.subtitle['language_name'], 0, 2))
        if fname:
            self["fname"].text = toString(fname)

    def updateDPath(self):
        dpath = None
        if self.configSaveTo.value == "video":
            dpath = os.path.dirname(self.vPath)
        elif self.configSaveTo.value == "custom":
            dpath = self.dPath
        if dpath:
            self["dpath"].text = toString(dpath)

    def resetDefaults(self):
        for x in self["config"].list:
            x[1].value = x[1].default
        self.buildMenu()
        self.updateFName()
        self.updateDPath()

    def editFName(self):
        def editFnameCB(callback=None):
            if callback is not None and len(callback):
                self["fname"].text = callback
                self.configSaveAs.value = "custom"
                self.buildMenu()
                self.updateFName()
        from Screens.VirtualKeyBoard import VirtualKeyBoard
        self.session.openWithCallback(editFnameCB, VirtualKeyBoard, _("Edit Filename"), text=toString(self["fname"].text.strip()))

    def editDPath(self):
        def editDPathCB(callback=None):
            if callback is not None and len(callback):
                self["dpath"].text = callback
                self.configSaveTo.value = "custom"
                self["config"].invalidate(self.configSaveTo)
        self.session.openWithCallback(editDPathCB, LocationBox, _("Edit download path"), currDir=toString(self["dpath"].text.strip()))

    def confirm(self):
        fname = self["fname"].text.strip()
        if len(fname) == "":
            self.session.open(MessageBox, _("Filename cannot be empty!"), type=MessageBox.TYPE_WARNING)
            return
        dpath = self["dpath"].text.strip()
        if not os.path.isdir(dpath):
            self.session.open(MessageBox, _("Path doesn't exist!"), type=MessageBox.TYPE_WARNING)
            return
        self.close(dpath, fname)

    def cancel(self):
        self.close(None, None)

    def keyRight(self):
        saveAsConfig = False
        if self['config'].getCurrent()[1] == self.configSaveAs:
            saveAsConfig = True
            currIdx = self.configSaveAs.choices.index(self.configSaveAs.value)
            if currIdx == len(self.configSaveAs.choices) - 1:
                nextChoice = self.configSaveAs.choices[0]
            else:
                nextChoice = self.configSaveAs.choices[currIdx + 1]
            if nextChoice == 'custom':
                self.configSaveAs.value = nextChoice
        ConfigListScreen.keyRight(self)
        if saveAsConfig:
            self.buildMenu()
        if self['config'].getCurrent()[1] in (self.configSaveAs, self.configAddLang):
            self.updateFName()
        elif self['config'].getCurrent()[1] in (self.configSaveTo,):
            self.updateDPath()

    def keyLeft(self):
        saveAsConfig = False
        if self['config'].getCurrent()[1] == self.configSaveAs:
            saveAsConfig = True
            currIdx = self.configSaveAs.choices.index(self.configSaveAs.value)
            if currIdx == 0:
                nextChoice = self.configSaveAs.choices[len(self.configSaveAs.choices) - 1]
            else:
                nextChoice = self.configSaveAs.choices[currIdx - 1]
            if nextChoice == 'custom':
                self.configSaveAs.value = nextChoice
        ConfigListScreen.keyLeft(self)
        if saveAsConfig:
            self.buildMenu()
        if self['config'].getCurrent()[1] in (self.configSaveAs, self.configAddLang):
            self.updateFName()
        elif self['config'].getCurrent()[1] in (self.configSaveTo,):
            self.updateDPath()


class SubsSearchContextMenu(Screen):
    if isFullHD():
        skin = """
            <screen position="center,center" size="600,525" zPosition="5" flags="wfNoBorder">
                <eLabel position="0,0" size="600,525" backgroundColor="#999999" zPosition="0" />
                <widget source="subtitle_release" render="Label" position="7,7" size="585,75" valign="center" halign="center" font="Regular;28" foregroundColor="#66BFFF" zPosition="1" />
                <widget source="context_menu" render="Listbox" position="7,90" size="585,427" scrollbarMode="showNever" zPosition="1">
                <convert type="TemplatedMultiContent">
                    {"templates":
                        {"default": (33, [
                            MultiContentEntryText(pos = (7,0),   size = (570,33),  font = 0, color = 0xffffff, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER,  text = 0), # langname,
                        ], True, "showOnDemand"),
                        },
                    "fonts": [gFont("Regular", 28)],
                    "itemHeight":33,
                    }
                </convert>
            </widget>
            </screen>
        """
    else:
        skin = """
            <screen position="center,center" size="400,350" zPosition="5" flags="wfNoBorder">
                <eLabel position="0,0" size="400,350" backgroundColor="#999999" zPosition="0" />
                <widget source="subtitle_release" render="Label" position="5,5" size="390,50" valign="center" halign="center" font="Regular;19" foregroundColor="#66BFFF" zPosition="1" />
                <widget source="context_menu" render="Listbox" position="5,60" size="390,285" scrollbarMode="showNever" zPosition="1">
                <convert type="TemplatedMultiContent">
                    {"templates":
                        {"default": (22, [
                            MultiContentEntryText(pos = (5, 0),   size = (380, 22),  font = 0, color = 0xffffff, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER,  text = 0), # langname,
                        ], True, "showOnDemand"),
                        },
                    "fonts": [gFont("Regular", 19)],
                    "itemHeight":22,
                    }
                </convert>
            </widget>
            </screen>
        """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.options = []
        self["subtitle_release"] = StaticText()
        self["context_menu"] = List()

    def up(self):
        self["context_menu"].selectNext()

    def down(self):
        self["context_menu"].selectPrevious()

    def right(self):
        self["context_menu"].selectNext()

    def left(self):
        self["context_menu"].selectPrevious()

    def updateGUI(self, subtitle, options):
        self["subtitle_release"].text = toString(subtitle['filename'])
        self["context_menu"].list = [(o[0],) for o in options]
        self.options = options

    def getSelection(self):
        return self.options[self["context_menu"].index][1]

class SubsSearch(Screen):
    if isFullHD():
        skin = """
        <screen name="SubsSearch" position="center,center" size="1350,780" zPosition="3" >
            <widget source="search_info" render="Listbox" position="15,15" size="1320,225" zPosition="3" scrollbarMode="showNever"  transparent="1" >
                <convert type="TemplatedMultiContent">
                    {"templates":
                        {"default": (33, [
                            MultiContentEntryText(pos = (0,0),   size = (300,33),  font = 0, color = 0xDAA520, flags = RT_HALIGN_LEFT,  text = 0), # langname,
                            MultiContentEntryText(pos = (307,0),   size = (600,33),  font = 0, flags = RT_HALIGN_LEFT,  text = 1)
                        ], False, "showNever"),
                        },
                    "fonts": [gFont("Regular", 27)],
                    "itemHeight":33,
                    }
                </convert>
            </widget>
            <widget source="header_country" render="Label" position = "7,262" size="180,37" font="Regular;27" halign="left" foregroundColor="#0xcccccc" />
            <widget source="header_release" render="Label" position = "217,262" size="802,37" font="Regular;27" halign="left" foregroundColor="#0xcccccc" />
            <widget source="header_provider" render="Label" position = "1057,262" size="202,37" font="Regular;27" halign="left" foregroundColor="#0xcccccc" />
            <widget source="header_sync" render="Label" position = "1275,262" size="30,37" font="Regular;27" halign="left" foregroundColor="#0xcccccc" />
            <eLabel position="7,307" size="1335,1" backgroundColor="#999999" />
            <widget name="loadmessage"  position="7,315" size="1335,390" valign="center" halign="center" font="Regular;28" foregroundColor="#ffffff" zPosition="4" />
            <widget name="errormessage" position="7,315" size="1335,390" valign="center" halign="center" font="Regular;28" foregroundColor="#ff0000" zPosition="5" />
            <widget source="subtitles" render="Listbox" scrollbarMode="showOnDemand" position="7,315" size="1335,390" zPosition="3" transparent="1" >
                <convert type="TemplatedMultiContent">
                    {"templates":
                        {"default": (34, [
                            MultiContentEntryPixmapAlphaBlend(pos = (0,0),   size = (36,36), png=0), # key,
                            MultiContentEntryText(pos = (45,0),   size = (150,37),  font = 0, flags = RT_HALIGN_LEFT,  text = 1), # language,
                            MultiContentEntryText(pos = (210,0),  size = (802,37),  font = 0, flags = RT_HALIGN_LEFT,  text = 2), # filename,
                            MultiContentEntryText(pos = (1050,0), size = (202,37), font = 0, flags = RT_HALIGN_LEFT,  text = 3), # size,
                            MultiContentEntryPixmapAlphaBlend(pos = (1267,0),   size = (36,36), png=4), # syncPng,
                        ], True, "showOnDemand"),
                        },
                    "fonts": [gFont("Regular", 27), gFont("Regular", 16)],
                    "itemHeight": 34
                    }
                </convert>
            </widget>
            <eLabel position="7,712" size="1335,1" backgroundColor="#999999" />
            <widget source="key_menu_img" render="Pixmap" pixmap="skin_default/buttons/key_menu.png" position="10,727" size="35,25" transparent="1" alphatest="on" >
                <convert type="ConditionalShowHide" />
            </widget>
            <eLabel position="1333,712" size="1335,1" backgroundColor="#999999" />
            <widget source="key_info_img" render="Pixmap" pixmap="skin_default/buttons/key_info.png" position="1300,727" size="35,25" transparent="1" alphatest="on" >
                <convert type="ConditionalShowHide" />
            </widget>
            <ePixmap  pixmap="skin_default/buttons/key_red.png" position="50,727" size="35,25" transparent="1" alphatest="on" />
            <widget source="key_red" render="Label" position = "93,727" size="268,37" font="Regular;30" halign="left" foregroundColor="white" />
            <ePixmap pixmap="skin_default/buttons/key_green.png" position="371,727" size="35,25" transparent="1" alphatest="on" />
            <widget source="key_green" render="Label" position = "414,727" size="268,37" font="Regular;30" halign="left" foregroundColor="white" />
            <ePixmap pixmap="skin_default/buttons/key_yellow.png" position="692,727" size="35,25" transparent="1" alphatest="on" />
            <widget source="key_yellow" render="Label" position = "735,727" size="268,37" font="Regular;30" halign="left" foregroundColor="white" />
            <ePixmap pixmap="skin_default/buttons/key_blue.png" position="985,727" size="35,25" transparent="1" alphatest="on" />
            <widget source="key_blue" render="Label" position = "1035,727" size="268,37" font="Regular;30" halign="left" foregroundColor="white" />
        </screen>
        """
    else:
        skin = """
        <screen name="SubsSearch" position="center,center" size="700,520" zPosition="3" >
            <widget source="search_info" render="Listbox" position="10,10" size="680,150" zPosition="3" scrollbarMode="showNever"  transparent="1" >
                <convert type="TemplatedMultiContent">
                    {"templates":
                        {"default": (22, [
                            MultiContentEntryText(pos = (0, 0),   size = (200, 22),  font = 0, color = 0xDAA520, flags = RT_HALIGN_LEFT,  text = 0), # langname,
                            MultiContentEntryText(pos = (205, 0),   size = (400, 22),  font = 0, flags = RT_HALIGN_LEFT,  text = 1)
                        ], False, "showNever"),
                        },
                    "fonts": [gFont("Regular", 18)],
                    "itemHeight":22,
                    }
                </convert>
            </widget>
            <widget source="header_country" render="Label" position = "5,175" size="120,25" font="Regular;18" halign="left" foregroundColor="#0xcccccc" />
            <widget source="header_release" render="Label" position = "145,175" size="335,25" font="Regular;18" halign="left" foregroundColor="#0xcccccc" />
            <widget source="header_provider" render="Label" position = "505, 175" size="135,25" font="Regular;18" halign="left" foregroundColor="#0xcccccc" />
            <widget source="header_sync" render="Label" position = "650, 175" size="20,25" font="Regular;18" halign="left" foregroundColor="#0xcccccc" />
            <eLabel position="5,205" size="690,1" backgroundColor="#999999" />
            <widget name="loadmessage"  position="5,210" size="690,260" valign="center" halign="center" font="Regular;19" foregroundColor="#ffffff" zPosition="4" />
            <widget name="errormessage" position="5,210" size="690,260" valign="center" halign="center" font="Regular;19" foregroundColor="#ff0000" zPosition="5" />
            <widget source="subtitles" render="Listbox" scrollbarMode="showOnDemand" position="5,210" size="690,260" zPosition="3" transparent="1" >
                <convert type="TemplatedMultiContent">
                    {"templates":
                        {"default": (23, [
                            MultiContentEntryPixmapAlphaBlend(pos = (0, 0),   size = (24, 24), png=0), # key,
                            MultiContentEntryText(pos = (30, 0),   size = (100, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 1), # language,
                            MultiContentEntryText(pos = (140, 0),  size = (335, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 2), # filename,
                            MultiContentEntryText(pos = (500, 0), size = (135, 25), font = 0, flags = RT_HALIGN_LEFT,  text = 3), # size,
                            MultiContentEntryPixmapAlphaBlend(pos = (645, 0),   size = (24, 24), png=4), # syncPng,
                        ], True, "showOnDemand"),
                        },
                    "fonts": [gFont("Regular", 18), gFont("Regular", 16)],
                    "itemHeight": 23
                    }
                </convert>
            </widget>
            <eLabel position="5,475" size="690,1" backgroundColor="#999999" />
            <widget source="key_menu_img" render="Pixmap" pixmap="skin_default/buttons/key_menu.png" position="3,485" size="35,25" transparent="1" alphatest="on" >
                <convert type="ConditionalShowHide" />
            </widget>
            <eLabel position="600,475" size="690,1" backgroundColor="#999999" />
            <widget source="key_info_img" render="Pixmap" pixmap="skin_default/buttons/key_info.png" position="667,485" size="35,25" transparent="1" alphatest="on" >
                <convert type="ConditionalShowHide" />
            </widget>
            <ePixmap  pixmap="skin_default/buttons/key_red.png" position="40,485" size="35,25" transparent="1" alphatest="on" />
            <widget source="key_red" render="Label" position = "80, 485" size="120,25" font="Regular;20" halign="left" foregroundColor="white" />
            <ePixmap pixmap="skin_default/buttons/key_green.png" position="205,485" size="35,25" transparent="1" alphatest="on" />
            <widget source="key_green" render="Label" position = "245, 485" size="110,25" font="Regular;20" halign="left" foregroundColor="white" />
            <ePixmap pixmap="skin_default/buttons/key_yellow.png" position="365,485" size="35,25" transparent="1" alphatest="on" />
            <widget source="key_yellow" render="Label" position = "405, 485" size="110,25" font="Regular;20" halign="left" foregroundColor="white" />
            <ePixmap pixmap="skin_default/buttons/key_blue.png" position="525,485" size="35,25" transparent="1" alphatest="on" />
            <widget source="key_blue" render="Label" position = "565, 485" size="100,25" font="Regular;20" halign="left" foregroundColor="white" />
        </screen> """

    def __init__(self, session, seeker, searchSettings, filepath=None, searchTitles=None, resetSearchParams=True, standAlone=False):
        Screen.__init__(self, session)
        self.searchSettings = searchSettings
        self.standAlone = standAlone
        searchTitles = searchTitles or [""]
        self.searchParamsHelper = SearchParamsHelper(seeker, searchSettings)
        self.seeker = seeker
        self.searchExpression = searchTitles[0]
        self.searchTitles = searchTitles
        self.filepath = filepath
        if self.filepath:                                         
            self.filepath = urllib.parse.unquote(self.filepath)
        self.isLocalFilepath = filepath and os.path.isfile(filepath) or False
        self.searchTitle = searchSettings.title
        self.searchType = searchSettings.type
        self.searchYear = searchSettings.year
        self.searchSeason = searchSettings.season
        self.searchEpisode = searchSettings.episode
        self.searchProvider = searchSettings.provider
        self.searchUseFilePath = searchSettings.useFilePath
        self.__downloadedSubtitles = []
        self.__downloading = False
        self.__searching = False
        self["loadmessage"] = Label("")
        self["errormessage"] = Label("")
        self["search_info"] = List([])
        self["header_country"] = StaticText(_("Language"))
        self["header_release"] = StaticText(_("Release"))
        self["header_provider"] = StaticText(_("Provider"))
        self["header_sync"] = StaticText(_("S"))
        self["subtitles"] = List([])
        self["key_info_img"] = Boolean() 
        self["key_menu_img"] = Boolean()
        self["key_red"] = StaticText(_("Update"))
        self["key_green"] = StaticText(_("Search"))
        self["key_yellow"] = StaticText(_("History"))    
        self["key_blue"] = StaticText(_("Settings"))      
        self["okCancelActions"] = ActionMap(["OkCancelActions"],
        {
            "ok": self.keyOk,
            "cancel": self.keyCancel,
        })
        self["menuActions"] = ActionMap(["ColorActions", "MenuActions", "MovieSelectionActions"],
        {
            "red": self.updateSearchParams,
            "green": self.searchSubs,
            "yellow": self.openDownloadHistory,
            "blue": self.openSettings,
            "menu": self.openContextMenu,
            "showEventInfo": self.eventinfo,
         })

        self["listActions"] = ActionMap(["DirectionActions"],
        {
            "up": self.keyUp,
            "upRepeated": self.keyUp,
            "upUp": lambda: None,
            "down": self.keyDown,
            "downRepeated": self.keyDown,
            "downUp": lambda: None,
            "right": self.keyRight,
            "rightRepeated": self.keyRight,
            "rightUp": lambda: None,
            "left": self.keyLeft,
            "leftRepeated": self.keyLeft,
            "leftUp": lambda: None,
        }, -2)

        self["searchActions"] = ActionMap(["OkCancelActions"],
        {
            "ok": self.cancelSearchSubs,
            "cancel": self.close,
        })
        self["searchActions"].setEnabled(False)
        self["downloadActions"] = ActionMap(["OkCancelActions"],
        {
            "ok": lambda: None,
            "cancel": self.cancelDownloadSubs
        })
        self["downloadActions"].setEnabled(False)

        self.__contextMenu = self.session.instantiateDialog(SubsSearchContextMenu)
        self["contextMenuActions"] = ActionMap(["DirectionActions", "OkCancelActions", "MenuActions"],
        {
            "up": self.__contextMenu.up,
            "upRepeated": self.__contextMenu.up,
            "upUp": lambda: None,
            "down": self.__contextMenu.down,
            "downRepeated": self.__contextMenu.down,
            "downUp": lambda: None,
            "right": self.__contextMenu.right,
            "rightRepeated": self.__contextMenu.right,
            "rightUp": lambda: None,
            "left": self.__contextMenu.left,
            "leftRepeated": self.__contextMenu.left,
            "leftUp": lambda: None,

            "ok": self.contextMenuOk,
            "cancel": self.contextMenuCancel,

            "menu": self.contextMenuCancel,
            "showEventInfo": self.contextMenuCancel,
         })
        self["contextMenuActions"].setEnabled(False)
        self.message = Message(self['loadmessage'], self['errormessage'])
        self.onLayoutFinish.append(self.updateTitle)
        self.onLayoutFinish.append(self.__getSubtitlesRenderer)
        if resetSearchParams:
            self.onLayoutFinish.append(self.detectSearchParams)
            self.onLayoutFinish.append(self.searchParamsHelper.updateProviders)
        self.onLayoutFinish.append(self.updateSearchInfoList)
        self.onLayoutFinish.append(self.updateBottomMenu)
        if not searchSettings.manualSearch.value and not self.standAlone:
            self.onLayoutFinish.append(self.searchSubs)
        else:
            self.onLayoutFinish.append(self.searchMessage)
        self.onClose.append(self.__contextMenu.hide)
        self.onClose.append(self.__contextMenu.doClose)
        self.onClose.append(self.message.exit)
        self.onClose.append(self.searchParamsHelper.resetSearchParams)
        self.onClose.append(self.stopSearchSubs)
        self.onClose.append(self.closeSeekers) 
        
    def eventinfo(self):         
        tmdb_file=resolveFilename(SCOPE_PLUGINS, "Extensions/tmdb")
        if os.path.exists(tmdb_file):
               from Plugins.Extensions.tmdb import tmdb
               reload_module(tmdb)
               s = self.session.nav.getCurrentService()
               info = s.info()
               event = info.getEvent(0) # 0 = now, 1 = next
               name = event and event.getEventName() or ''
               self.session.open(tmdb.tmdbScreen, name, 2)
        else:
               self.session.open(MessageBox, _('Sorry!\ntmdb is not installed on your image'), MessageBox.TYPE_ERROR, timeout=5)

    def __getSubtitlesRenderer(self):
        from Components.Sources.Source import Source
        from Components.Renderer.Listbox import Listbox
        for r in self.renderer:
            if isinstance(r, Listbox):
                s = r
                while not isinstance(s, Source):
                    s = s.source
                if s == self['subtitles']:
                    self.__listboxRenderer = r
                    break

    def updateTitle(self):
        self.title = _("Subtitles search")

    def updateSearchInfoList(self):
        searchInfoList = []
        lang1 = self.searchSettings.lang1.value
        lang2 = self.searchSettings.lang2.value
        lang3 = self.searchSettings.lang3.value
        lang1 = lang1 in LanguageCodes and LanguageCodes[lang1][0] or lang1
        lang2 = lang2 in LanguageCodes and LanguageCodes[lang2][0] or lang2
        lang3 = lang3 in LanguageCodes and LanguageCodes[lang3][0] or lang3
        langs = [lang1]
        if lang2 not in langs:
            langs.append(lang2)
        if lang3 not in langs:
            langs.append(lang3)
        languages = ", ".join(_(lang) for lang in langs)
        year = self.searchYear.value and str(self.searchYear.value) or ""
        season = self.searchSeason.value and str(self.searchSeason.value) or ""
        episode = self.searchEpisode.value and str(self.searchEpisode.value) or ""
        useFilePathStr = self.searchUseFilePath.value and _("yes") or _("no")
        searchInfoList.append((_("Title") + ":", self.searchTitle.value))
        searchInfoList.append((_("Type") + ":", self.searchType.getText()))
        if self.searchType.value == "movie":
            searchInfoList.append((_("Year") + ":", year))
        else:
            searchInfoList.append((_("Season") + ":", season))
            searchInfoList.append((_("Episode") + ":", episode))
        searchInfoList.append((_("Provider") + ":", self.searchProvider.getText()))
        searchInfoList.append((_("Preferred languages") + ":", languages))
        searchInfoList.append((_("Use File path") + ":", useFilePathStr))
        self['search_info'].list = searchInfoList

    def updateSubsList(self):
        imgDict = {
            'sync': loadPNG(os.path.join(os.path.dirname(__file__), 'img', 'check.png')),
            'unk': loadPNG(os.path.join(os.path.dirname(__file__), 'img', 'countries', 'UNK.png'))
        }
        subtitleListGUI = []
        for sub in self.subtitlesList:
            sync = 'sync' in sub and sub['sync'] or False
            if sub['country'] not in imgDict:
                countryImgPath = os.path.join(os.path.dirname(__file__), 'img', 'countries', sub['country'] + '.png')
                if os.path.isfile(countryImgPath):
                    countryPng = loadPNG(countryImgPath)
                    imgDict[sub['country']] = countryPng
                else:
                    countryPng = imgDict['unk']
            syncPng = sync and imgDict['sync'] or None
            subtitleListGUI.append((countryPng, _(toString(sub['language_name'])),
                toString(sub['filename']), toString(sub['provider']), syncPng),)
        imgDict = None
        self['subtitles'].list = subtitleListGUI

    def updateBottomMenu(self):
        if self.__searching:
            self["key_red"].text = ""
            self["key_green"].text = ""
            self["key_yellow"].text = ""
            self["key_blue"].text = ""
            self["key_menu_img"].boolean = False
            self["key_info_img"].boolean = False
        elif self.__downloading:
            self["key_red"].text = ""
            self["key_green"].text = ""
            self["key_yellow"].text = ""
            self["key_blue"].text = ""
            self["key_menu_img"].boolean = False
            self["key_info_img"].boolean = False
        else:
            self["key_red"].text = (_("Update"))
            self["key_green"].text = (_("Search"))
            self["key_yellow"].text = (_("History"))
            self["key_blue"].text = (_("Settings"))
            if self["subtitles"].count() > 0:
                self["key_menu_img"].boolean = True
                self["key_info_img"].boolean = True
                
    def updateActionMaps(self):
        if self.__searching:
            self["okCancelActions"].setEnabled(False)
            self["listActions"].setEnabled(False)
            self["menuActions"].setEnabled(False)
            self["searchActions"].setEnabled(True)
            self["downloadActions"].setEnabled(False)
            self["contextMenuActions"].setEnabled(False)
        elif self.__downloading:
            self["okCancelActions"].setEnabled(False)
            self["listActions"].setEnabled(False)
            self["menuActions"].setEnabled(False)
            self["searchActions"].setEnabled(False)
            self["downloadActions"].setEnabled(True)
            self["contextMenuActions"].setEnabled(False)
        elif self.__contextMenu.already_shown and self.__contextMenu.shown:
            self["okCancelActions"].setEnabled(False)
            self["listActions"].setEnabled(False)
            self["menuActions"].setEnabled(False)
            self["searchActions"].setEnabled(False)
            self["downloadActions"].setEnabled(False)
            self["contextMenuActions"].setEnabled(True)
        else:
            self["okCancelActions"].setEnabled(True)
            self["listActions"].setEnabled(True)
            self["menuActions"].setEnabled(True)
            self["searchActions"].setEnabled(False)
            self["downloadActions"].setEnabled(False)
            self["contextMenuActions"].setEnabled(False)

    def detectSearchParams(self):
        self.searchParamsHelper.detectSearchParams(self.searchExpression)

    def closeSeekers(self):
        for seeker in self.seeker.seekers:
            seeker.close()

    def keyOk(self):
        if self['subtitles'].count():
            self.downloadSubs(self.subtitlesList[self["subtitles"].index])

    def keyCancel(self):
        self.close()

    def keyUp(self):
        if self['subtitles'].count():
            self.message.hide()
            self['subtitles'].selectPrevious()

    def keyDown(self):
        if self['subtitles'].count():
            self.message.hide()
            self['subtitles'].selectNext()

    def keyRight(self):
        if self['subtitles'].count():
            self.message.hide()
            self.__listboxRenderer.move(self.__listboxRenderer.instance.pageDown)

    def keyLeft(self):
        if self['subtitles'].count():
            self.message.hide()
            self.__listboxRenderer.move(self.__listboxRenderer.instance.pageUp)

    def searchMessage(self):
        self.message.info(_("Update search parameters if not correct\n and press green button for search"))

    def searchSubs(self):
        def searchSubsUpdate(args):
            pfinished, status, value = args
            if status:
                self.__finished[pfinished] = value
            else:
                self.__finished[pfinished] = {'list': [], 'status': status, 'message': str(value)}
            progressMessage = "%s - %d%%" % (_("loading subtitles list"), int(len(self.__finished.keys()) / float(len(provider)) * 100))
            progressMessage += "\n" + _("subtitles found") + " (%d)" % (sum(len(self.__finished[p]['list']) for p in self.__finished.keys()))
            progressMessage += "\n\n" + _("Press OK to Stop")
            self.message.info(progressMessage)

        self.stopSearchSubs()
        self.subtitlesList = []
        self.subtitlesDict = {}
        self.__finished = {}
        p = self.searchParamsHelper.getSearchParams()
        langs, title, year, tvshow, season, episode = p[1], p[2], p[3], p[4], p[5], p[6]
        providers = self.seeker.getProviders(langs, not tvshow, tvshow)
        if self.searchProvider.value == "all":
            provider = providers
        else:
            provider = [p for p in providers if p.id == self.searchProvider.value]
        filepath = self.searchUseFilePath.value and self.filepath or None
        timeout = float(self.searchSettings.timeout.value)
        params = {
            'search': {
                'providers': [p.id for p in provider],
                'title': title,
                'filepath': filepath,
                'langs': langs,
                'year': year,
                'tvshow': tvshow,
                'season': season,
                'episode': episode,
                'timeout': timeout
            },
            'settings': dict((s.id, s.settings_provider.getSettingsDict()) for s in self.seeker.seekers)
        }
        callbacks = {
            'updateCB': searchSubsUpdate,
            'successCB': self.searchSubsSuccess,
            'errorCB': self.searchSubsError
        }
        progressMessage = "%s - %d%%" % (_("loading subtitles list"), 0)
        progressMessage += "\n" + _("subtitles found") + " (%d)" % 0
        progressMessage += "\n\n" + _("Press OK to Stop")
        self.message.info(progressMessage)
        self.__searching = True
        self.updateActionMaps()
        self.updateSubsList()
        self.updateBottomMenu()
        SubsSearchProcess().start(params, callbacks)

    def cancelSearchSubs(self):
        self.stopSearchSubs()
        self.searchSubsSuccess(self.__finished)

    def stopSearchSubs(self):
        for p in SubsSearchProcess.processes:
            p.stop()
        print(len(SubsSearchProcess.processes), 'processes still running')

    def searchSubsSuccess(self, subtitles):
        print('[SubsSearch] search success')
        self.message.hide()
        self.subtitlesDict = subtitles
        subtitlesList = self.seeker.getSubtitlesList(subtitles)
        subtitlesList = self.seeker.sortSubtitlesList(subtitlesList, sort_sync=True)
        langs = [self.searchSettings.lang1.value,
                    self.searchSettings.lang2.value,
                    self.searchSettings.lang3.value]
        if self.searchSettings.defaultSort.value == 'lang':
            subtitlesList = self.seeker.sortSubtitlesList(subtitlesList, langs, sort_langs=True)
        elif self.searchSettings.defaultSort.value == 'provider':
            subtitlesList = self.seeker.sortSubtitlesList(subtitlesList, langs, sort_provider=True)
        self.subtitlesList = subtitlesList
        if len(self.subtitlesList) == 0:
            noSubtitlesMessage = _("No subtitles found :(")
            noSubtitlesMessage += "\n" + _("Try update(simplify) search expression and try again..")
            self.message.info(noSubtitlesMessage)
        self.__searching = False
        self.updateSubsList()
        self.updateBottomMenu()
        self.updateActionMaps()

    def searchSubsError(self, error):
        print('[SubsSearch] search error', str(error))
        try:
            self.message.error(error.message, 4000)
        except:
            self.message.error("error", 4000)
        self.subtitlesList = []
        self.subtitlesDict = {}
        self.updateSubsList()
        self.__searching = False
        self.updateBottomMenu()
        self.updateActionMaps()

    def downloadSubs(self, subtitle, downloadDir=None, fName=None, saveAs=None,
        saveTo=None, langToFilename=None, askOverwrite=None, closeOnSuccess=None):

        if saveAs is None:
            saveAs = self.searchSettings.saveAs.value
        if saveAs == 'video' and not self.isLocalFilepath:
            saveAs = self.searchSettings.saveAsFallback.value
        if langToFilename is None:
            langToFilename = self.searchSettings.addLangToSubsFilename.value
        if askOverwrite is None:
            askOverwrite = self.searchSettings.askOverwriteExistingSubs.value
        if closeOnSuccess is None:
            closeOnSuccess = self.searchSettings.loadSubtitlesAfterDownload.value
        if downloadDir is None:
            if saveTo is None:
                saveTo = self.searchSettings.saveTo.value
            if saveTo == 'video' and self.isLocalFilepath:
                downloadDir = os.path.dirname(self.filepath)
            else:
                downloadDir = self.searchSettings.downloadPath.value
        self.__downloading = True
        self.__downloadingSubtitle = subtitle
        self.updateActionMaps()
        self.updateBottomMenu()
        self.message.info(_('downloading subtitles...'))
        self.__closeOnSuccess = closeOnSuccess

        settings = {
            "save_as": saveAs,
            "lang_to_filename": langToFilename,
            "ask_overwrite": askOverwrite
        }
        params = {
            'download': {
                'selected_subtitle': subtitle,
                'subtitles_dict': self.subtitlesDict,
                'path': downloadDir,
                'filename': fName,
                'settings': settings
            },
            'download_path': self.searchSettings.downloadPath.value,
            'tmp_path': self.searchSettings.tmpPath.value,

            'settings': dict((s.id, s.settings_provider.getSettingsDict()) for s in self.seeker.seekers)
        }

        def choosefileCB(subFiles, resultCB):
            choiceTitle = _("There are more subtitles in unpacked archive\n please select which one do you want to use")
            choiceList = [(os.path.basename(subfile), subfile) for subfile in subFiles]
            self.session.openWithCallback(resultCB, ChoiceBox, choiceTitle, choiceList)

        def overwriteCB(subfile, resultCB):
            overwriteText = _("Subtitles with this name already exist\nDo you want to overwrite them") + "?"
            self.session.openWithCallback(resultCB, MessageBox, overwriteText, MessageBox.TYPE_YESNO)

        def captchaCB(imagePath, resultCB):
            Captcha(self.session, resultCB, imagePath)

        def delayCB(seconds, resultCB):
            message = _("Subtitles will be downloaded in") + " " + str(seconds) + " " + _("seconds")
            self.session.openWithCallback(resultCB, DelayMessageBox, seconds, message)

        callbacks = {
            'choosefileCB': choosefileCB,
            'captchaCB': captchaCB,
            'overwriteCB': overwriteCB,
            'delayCB': delayCB,
            'successCB': self.downloadSubsSuccess,
            'errorCB': self.downloadSubsError,
        }
        SubsSearchProcess().start(params, callbacks)

    def downloadSubsSuccess(self, subFile):
        print('[SubsSearch] download success %s' % toString(subFile))
        dsubtitle = {
            "name": toUnicode(os.path.basename(subFile)),
            "country": toUnicode(self.__downloadingSubtitle['country']),
            "provider": toUnicode(self.__downloadingSubtitle['provider']),
            "fpath": toUnicode(subFile),
        }
        if self.searchSettings.downloadHistory.enabled.value:
            downloadHistoryDir = self.searchSettings.downloadHistory.path.value
            if not os.path.isdir(downloadHistoryDir):
                try:
                    os.makedirs(downloadHistoryDir)
                except:
                    pass
            fpath = os.path.join(downloadHistoryDir, 'hsubtitles.json')
            try:
                subtitles = json.load(open(fpath, "r"))
            except Exception as e:
                print('[SubsSearch] cannot load download history:', e)
                subtitles = []
            limit = int(self.searchSettings.downloadHistory.limit.value)
            if dsubtitle in subtitles:
                subtitles.remove(dsubtitle)
            if len(subtitles) >= limit:
                print('[SubsSearch] download history limit reached!, removing oldest entries')
                del subtitles[-(len(subtitles) - limit):]
            subtitles.insert(0, dsubtitle)
            try:
                json.dump(subtitles, open(fpath, 'w'))
            except Exception as e:
                print('[SubsSearch] cannot save download history:', e)
                self.session.open(MessageBox, _("Cannot save download history, for details look in log"),
                        MessageBox.TYPE_ERROR, timeout=3)
        self.__downloadedSubtitles.append(dsubtitle)
        self.afterDownloadSuccess(dsubtitle)
        self.message.hide()
        self.__downloading = False
        del self.__downloadingSubtitle
        self.updateBottomMenu()
        self.updateActionMaps()

    def downloadSubsError(self, e):
        print('[SubsSearch] download error', str(e))
        self.__downloading = False
        del self.__downloadingSubtitle
        self.updateBottomMenu()
        self.updateActionMaps()

        errorMessageFormat = "[{0}]: {1}"
        if e['error_code'] == SubtitlesErrors.CAPTCHA_RETYPE_ERROR:
            self.message.error(errorMessageFormat.format(e['provider'], _("captcha doesn't match, try again...")), 4000)
        elif e['error_code'] == SubtitlesErrors.INVALID_CREDENTIALS_ERROR:
            self.message.error(errorMessageFormat.format(e.provider, _("invalid credentials provided, correct them and try again")), 4000)
        elif e['error_code'] == SubtitlesErrors.NO_CREDENTIALS_ERROR:
            self.message.error(errorMessageFormat.format(e.provider, _("no credentials provided, set them and try again")), 4000)
        else:
            self.message.error(_("download error ocurred, for details see /tmp/subssearch.log"), 4000)

    def cancelDownloadSubs(self):
        print('[SubsSearch] download cancelled')
        self.__downloading = False
        del self.__downloadingSubtitle
        self.stopSearchSubs()
        self.updateBottomMenu()
        self.updateActionMaps()
        self.message.hide()

    def afterDownloadSuccess(self, subtitle):
        if not self.standAlone and self.__closeOnSuccess:
            self.close(subtitle['fpath'])
        self.__closeOnSuccess = None

    def openContextMenu(self):
        if not self["subtitles"].count() > 0:
            return
        downloadOptions = [
            (_("Download (user defined)"), "d_custom"),
            (_("Download (next to video)"), "d_video"),
            (_("Download (more...)"), "d_more"),
        ]
        downloadAndLoadOptions = [
            (_("Download and Load (user defined) "), "do_custom"),
            (_("Download and Load (next to video)"), "do_video"),
            (_("Download and Load (more...)"), "do_more"),
        ]
        if not self.isLocalFilepath or self.standAlone:
            downloadOptions.remove(downloadOptions[1])
            downloadAndLoadOptions.remove(downloadAndLoadOptions[1])
        if self.standAlone:
            del downloadAndLoadOptions[:]
        options = []
        if not self.searchSettings.loadSubtitlesAfterDownload.value or self.standAlone:
            if len(downloadOptions) > 0:
                if self.searchSettings.saveTo.value == "custom":
                    options.append(downloadOptions[0])
                elif self.searchSettings.saveTo.value == "video" and self.isLocalFilepath:
                    options.append(downloadOptions[1])
                elif self.searchSettings.saveTo.value == "more":
                    options.append(downloadOptions[-1])
                for o in downloadOptions:
                    if o not in options:
                        options.append(o)
                options.extend(downloadAndLoadOptions)
        else:
            if len(downloadAndLoadOptions) > 0:
                if self.searchSettings.saveTo.value == "custom":
                    options.append(downloadAndLoadOptions[0])
                elif self.searchSettings.saveTo.value == "video" and self.isLocalFilepath:
                    options.append(downloadAndLoadOptions[1])
                elif self.searchSettings.saveTo.value == "more":
                    options.append(downloadAndLoadOptions[-1])
                for o in downloadAndLoadOptions:
                    if o not in options:
                        options.append(o)
                options.extend(downloadOptions)

        subtitle = self.subtitlesList[self["subtitles"].index]
        self.__contextMenu.updateGUI(subtitle, options)
        self.__contextMenu.show()
        self.updateActionMaps()

    def contextMenuOk(self):
        def downloadMoreCB(dPath, fName):
            if dPath and fName:
                self.downloadSubs(subtitle, downloadDir=dPath, fName=fName, closeOnSuccess=closeOnSuccess)
        answer = self.__contextMenu.getSelection()
        self.__contextMenu.hide()
        self.updateActionMaps()
        subtitle = self.subtitlesList[self["subtitles"].index]
        if answer == "d_custom":
            self.downloadSubs(subtitle, saveTo='custom', closeOnSuccess=False)
        elif answer == 'd_video':
            self.downloadSubs(subtitle, saveTo='video', closeOnSuccess=False)
        elif answer == 'do_custom':
            self.downloadSubs(subtitle, saveTo='custom', closeOnSuccess=True)
        elif answer == 'do_video':
            self.downloadSubs(subtitle, saveTo='video', closeOnSuccess=True)
        elif answer == 'do_more':
            closeOnSuccess = True
        elif answer == 'd_more':
            closeOnSuccess = False
        if answer == 'd_more' or answer == 'do_more':
            saveAs = self.searchSettings.saveAs.value
            saveTo = self.searchSettings.saveTo.value
            addLang = self.searchSettings.addLangToSubsFilename.value
            dPath = self.searchSettings.downloadPath.value
            vPath = self.filepath
            self.session.openWithCallback(downloadMoreCB, SubsSearchDownloadOptions,
                subtitle, saveAs, saveTo, addLang, dPath, vPath)

    def contextMenuCancel(self):
        self.__contextMenu.hide()
        self.updateActionMaps()

    def updateSearchParams(self):
        def updateSearchParamsCB(callback=None):
            if callback:
                self.updateSearchInfoList()
                self.updateBottomMenu()
                if not self.searchSettings.manualSearch.value:
                    self.searchSubs()
        self.session.openWithCallback(updateSearchParamsCB, SubsSearchParamsMenu, self.seeker, self.searchSettings, self.searchTitles, False)

    def openDownloadHistory(self):
        def openDownloadHistoryCB(subtitles, subtitle=None):
            if len(subtitles) > 0:
                if not self.searchSettings.downloadHistory.enabled.value:
                    for i in self.__downloadedSubtitles:
                        if i in subtitles:
                            subtitles.remove(i)
                try:
                    json.dump(subtitles, open(fpath, "w"))
                except Exception as e:
                    print('[SubsSearch] save download history:', e)
            if subtitle is not None:
                if not self.standAlone:
                    self.close(subtitle)

        fpath = os.path.join(self.searchSettings.downloadHistory.path.value, 'hsubtitles.json')
        try:
            subtitles = json.load(open(fpath, "r"))
        except Exception as e:
            print('[SubsSearch] cannot load download history:', e)
            subtitles = []
        self.session.openWithCallback(openDownloadHistoryCB, SubsDownloadedSelection,
            subtitles, self.searchSettings.downloadHistory, self.__downloadedSubtitles)

    def openSettings(self):
        def openSettingsCB(langChanged=False):
            self.seeker.tmp_path = self.searchSettings.tmpPath.value
            self.seeker.download_path = self.searchSettings.downloadPath.value
            self.searchParamsHelper.updateProviders()
            self.updateSearchInfoList()
            self.updateBottomMenu()
            if langChanged and not self.searchSettings.manualSearch.value:
                self.searchSubs()

        self.session.openWithCallback(openSettingsCB, SubsSearchSettings, self.searchSettings, self.seeker, self.isLocalFilepath)


class SubsSearchSettings(Screen, ConfigListScreen):

    @staticmethod
    def getConfigList(searchSettings):
        configList = []
        configList.append(getConfigListEntry(_("Preferred subtitles language") + ' 1', searchSettings.lang1))
        configList.append(getConfigListEntry(_("Preferred subtitles language") + ' 2', searchSettings.lang2))
        configList.append(getConfigListEntry(_("Preferred subtitles language") + ' 3', searchSettings.lang3))
        configList.append(getConfigListEntry(_("Preferred Movie provider"), searchSettings.movieProvider))
        configList.append(getConfigListEntry(_("Preferred TV show provider"), searchSettings.tvshowProvider))
        configList.append(getConfigListEntry(_("Manual search"), searchSettings.manualSearch))
        configList.append(getConfigListEntry(_("Subtitles provider timeout"), searchSettings.timeout))
        configList.append(getConfigListEntry(_("Check search parameters before subtitles search"), searchSettings.openParamsDialogOnSearch))
        configList.append(getConfigListEntry(_("Sort subtitles list by"), searchSettings.defaultSort))
        configList.append(getConfigListEntry(_("Save subtitles as"), searchSettings.saveAs))
        configList.append(getConfigListEntry(_("Save subtitles as (fallback)"), searchSettings.saveAsFallback))
        configList.append(getConfigListEntry(_("Add subtitle's language to filename"), searchSettings.addLangToSubsFilename))
        configList.append(getConfigListEntry(_("Save subtitles to"), searchSettings.saveTo))
        configList.append(getConfigListEntry(_("Subtitles download path"), searchSettings.downloadPath))
        configList.append(getConfigListEntry(_("Subtitles temp path"), searchSettings.tmpPath))
        configList.append(getConfigListEntry(_("Always ask before overwriting existing subtitles"), searchSettings.askOverwriteExistingSubs))
        configList.append(getConfigListEntry(_("Load subtitles after download"), searchSettings.loadSubtitlesAfterDownload))
        historySettings = searchSettings.downloadHistory
        configList.append(getConfigListEntry(_("Save downloaded subtitles to history"), historySettings.enabled))
        if historySettings.enabled.value:
            configList.append(getConfigListEntry(_("Load/Save download history directory"), historySettings.path))
        return configList

    if isFullHD():
        skin = """
        <screen position="center,center" size="835,642" zPosition="3" >
            <widget name="key_red" position="12,6" zPosition="1" size="192,57" font="Regular;25" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_green" position="218,6" zPosition="1" size="192,57" font="Regular;25" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_yellow" position="424,6" zPosition="1" size="192,57" font="Regular;25" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_blue" position="629,6" zPosition="1" size="192,57" font="Regular;25" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
            <eLabel position="-1,83" size="835,1" backgroundColor="#999999" />
            <widget name="config" position="12,96" size="809,228" font="Regular;27" itemHeight="37" scrollbarMode="showOnDemand" />
            <widget source="header_name" render="Label" position = "12,340" size="257,32" font="Regular;23" halign="left" foregroundColor="#0xcccccc" />
            <widget source="header_lang" render="Label" position = "282,340" size="231,32" font="Regular;23" halign="left" foregroundColor="#0xcccccc" />
            <widget source="header_state" render="Label" position = "527,340" size="257,32" font="Regular;23" halign="right" foregroundColor="#0xcccccc" />
            <eLabel position="6,379" size="822,1" backgroundColor="#999999" />
            <widget source="providers" render="Listbox" scrollbarMode="showOnDemand" position="12,392" size="809,237" zPosition="3" transparent="1" >
                <convert type="TemplatedMultiContent">
                    {"templates":
                        {"default": (37, [
                            MultiContentEntryText(pos = (0,0),   size = (257,32),  font = 0, flags = RT_HALIGN_LEFT,  text = 0), # name,
                            MultiContentEntryText(pos = (269,0),  size = (231,32),  font = 0, flags = RT_HALIGN_LEFT,  text = 1), # lang,
                            MultiContentEntryText(pos = (514,0), size = (257,32), font = 0, flags = RT_HALIGN_RIGHT, text = 2, color=0xFF000003) # enabled,
                        ], True, "showOnDemand"),
                        "notselected": (37, [
                            MultiContentEntryText(pos = (0,0),   size = (257,32),  font = 0, flags = RT_HALIGN_LEFT,  text = 0), # name,
                            MultiContentEntryText(pos = (269,0),  size = (231,32),  font = 0, flags = RT_HALIGN_LEFT,  text = 1), # lang,
                            MultiContentEntryText(pos = (514,0), size = (257,32), font = 0, flags = RT_HALIGN_RIGHT,  text = 2, color=0xFF000003) # enabled,
                        ], False, "showOnDemand")
                        },
                    "fonts": [gFont("Regular", 27)],
                    "itemHeight": 37
                    }
                </convert>
            </widget>
        </screen>
        """
    else:
        skin = """
        <screen position="center,center" size="650,500" zPosition="3" >
            <widget name="key_red" position="10,5" zPosition="1" size="150,45" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_green" position="170,5" zPosition="1" size="150,45" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_yellow" position="330,5" zPosition="1" size="150,45" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" shadowOffset="-2,-2" shadowColor="black" />
            <widget name="key_blue" position="490,5" zPosition="1" size="150,45" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" shadowOffset="-2,-2" shadowColor="black" />
            <eLabel position="-1,55" size="650,1" backgroundColor="#999999" />
            <widget name="config" position="10,75" size="630,178" scrollbarMode="showOnDemand" />
            <!-- <eLabel position="5,245" size="640,1" backgroundColor="#999999" /> -->
            <widget source="header_name" render="Label" position = "10,265" size="200,25" font="Regular;18" halign="left" foregroundColor="#0xcccccc" />
            <widget source="header_lang" render="Label" position = "220,265" size="180,25" font="Regular;18" halign="left" foregroundColor="#0xcccccc" />
            <widget source="header_state" render="Label" position = "410, 265" size="200,25" font="Regular;18" halign="right" foregroundColor="#0xcccccc" />
            <eLabel position="5,295" size="640,1" backgroundColor="#999999" />
            <widget source="providers" render="Listbox" scrollbarMode="showOnDemand" position="10,305" size="630,185" zPosition="3" transparent="1" >
                <convert type="TemplatedMultiContent">
                    {"templates":
                        {"default": (23, [
                            MultiContentEntryText(pos = (0, 0),   size = (200, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 0), # name,
                            MultiContentEntryText(pos = (210, 0),  size = (180, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 1), # lang,
                            MultiContentEntryText(pos = (400, 0), size = (200, 25), font = 0, flags = RT_HALIGN_RIGHT, text = 2, color=0xFF000003) # enabled,
                        ], True, "showOnDemand"),
                        "notselected": (23, [
                            MultiContentEntryText(pos = (0, 0),   size = (200, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 0), # name,
                            MultiContentEntryText(pos = (210, 0),  size = (180, 25),  font = 0, flags = RT_HALIGN_LEFT,  text = 1), # lang,
                            MultiContentEntryText(pos = (400, 0), size = (200, 25), font = 0, flags = RT_HALIGN_RIGHT,  text = 2, color=0xFF000003) # enabled,
                        ], False, "showOnDemand")
                        },
                    "fonts": [gFont("Regular", 18), gFont("Regular", 16)],
                    "itemHeight": 23
                    }
                </convert>
            </widget>
        </screen> """

    FOCUS_CONFIG, FOCUS_PROVIDERS = range(2)

    def __init__(self, session, searchSettings, seeker, isLocalFilepath=True):
        Screen.__init__(self, session)
        ConfigListScreen.__init__(self, [], session=session)
        self.searchSettings = searchSettings
        self.searchParamsHelper = SearchParamsHelper(seeker, searchSettings)
        self.providers = seeker.seekers
        self.isLocalFilepath = isLocalFilepath
        self.focus = self.FOCUS_CONFIG
        self['providers'] = List([])
        self["header_name"] = StaticText(_("Provider name"))
        self["header_lang"] = StaticText(_("Supported languages"))
        self["header_state"] = StaticText(_("State"))
        self["key_green"] = Label(_("Save"))
        self["key_red"] = Label(_("Cancel"))
        self["key_blue"] = Label(_("Reset Defaults"))
        self["key_yellow"] = Label(_("Switch List"))
        self["actions"] = ActionMap(["DirectionActions", "SetupActions", "OkCancelActions", "ColorActions", "ListboxActions"],
        {
            "ok": self.keyOk,
            "cancel": self.keyCancel,
            "save": self.keySave,
            "up": self.keyUp,
            "down": self.keyDown,
            "right": self.keyRight,
            "left": self.keyLeft,
            "blue": self.resetDefaults,
            "yellow": self.switchList,
            "pageUp": self.switchList,
            "pageDown": self.switchList,
        }, -2)
        self.onLayoutFinish.append(self.setWindowTitle)
        self.onLayoutFinish.append(self.buildMenu)
        self.onLayoutFinish.append(self.updateProvidersList)
        self.onLayoutFinish.append(self.setConfigFocus)

    def setWindowTitle(self):
        self.setTitle(_("Subtitles search settings"))

    def buildMenu(self):
        self["config"].setList(self.getConfigList(self.searchSettings))

    def updateProvidersList(self):
        providerListGUI = []
        for provider in self.providers:
            providerName = provider.provider_name
            providerLangs = ','.join(provider.supported_langs)
            if provider.error is not None:
                providerState = _("error")
                providerStateColor = 0xff0000
            elif provider.settings_provider.getSetting('enabled'):
                providerState = _("enabled")
                providerStateColor = 0x00ff00
            else:
                providerState = _("disabled")
                providerStateColor = 0xffff00
            providerListGUI.append((toString(providerName), providerLangs, providerState, providerStateColor))
        self['providers'].list = providerListGUI

    def setConfigFocus(self):
        self.focus = self.FOCUS_CONFIG
        self['config'].instance.setSelectionEnable(True)
        self['providers'].style = 'notselected'

    def switchList(self):
        if self.focus == self.FOCUS_PROVIDERS:
            self.focus = self.FOCUS_CONFIG
            self['providers'].style = "notselected"
            self['config'].instance.setSelectionEnable(True)
        else:
            self.focus = self.FOCUS_PROVIDERS
            self['config'].instance.setSelectionEnable(False)
            self['providers'].style = 'default'

    def keyOk(self):
        if self.focus == self.FOCUS_PROVIDERS:
            provider = self.providers[self['providers'].index]
            if provider.error:
                self.showProviderError(provider)
            else:
                self.openProviderSettings(provider)
        else:
            current = self['config'].getCurrent()[1]
            if current == self.searchSettings.downloadPath:
                currentPath = self.searchSettings.downloadPath.value
                self.session.openWithCallback(self.setDownloadPath, LocationBox, "", "", currentPath)
            elif current == self.searchSettings.tmpPath:
                currentPath = self.searchSettings.tmpPath.value
                self.session.openWithCallback(self.setTmpPath, LocationBox, "", "", currentPath)
            elif current == self.searchSettings.downloadHistory.path:
                currentPath = self.searchSettings.downloadHistory.path.value
                self.session.openWithCallback(self.setHistoryPath, LocationBox, "", "", currentPath)
            elif current in [self.searchSettings.lang1,
                                                    self.searchSettings.lang2,
                                                    self.searchSettings.lang3]:
                self.session.openWithCallback(self.setLanguage, MyLanguageSelection, current.value)

    def setLanguage(self, language=None):
        if language:
            self['config'].getCurrent()[1].value = language
            self.buildMenu()

    def setDownloadPath(self, downloadPath=None):
        if downloadPath:
            self.searchSettings.downloadPath.value = downloadPath
            self.buildMenu()

    def setTmpPath(self, tmpPath=None):
        if tmpPath:
            self.searchSettings.tmpPath.value = tmpPath
            self.buildMenu()

    def setHistoryPath(self, historyPath=None):
        if historyPath:
            self.searchSettings.downloadHistory.path.value = historyPath
            self.buildMenu()

    def keySave(self):
        langChanged = (self.searchSettings.lang1.isChanged() or
                            self.searchSettings.lang2.isChanged() or
                            self.searchSettings.lang3.isChanged())
        for x in self["config"].list:
            x[1].save()
        self.close(langChanged)

    def keyCancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()

    def keyUp(self):
        if self.focus == self.FOCUS_CONFIG:
            self['config'].instance.moveSelection(self["config"].instance.moveUp)
        else:
            if self['providers'].index == 0:
                self['providers'].index = len(self['providers'].list) - 1
            else:
                self['providers'].selectPrevious()

    def keyDown(self):
        if self.focus == self.FOCUS_CONFIG:
            self['config'].instance.moveSelection(self["config"].instance.moveDown)
        else:
            if self['providers'].index == len(self['providers'].list) - 1:
                self['providers'].index = 0
            else:
                self['providers'].selectNext()

    def keyRight(self):
        if self.focus == self.FOCUS_CONFIG:
            ConfigListScreen.keyRight(self)
            if self['config'].getCurrent()[1] in [self.searchSettings.saveTo,
                self.searchSettings.downloadHistory.enabled]:
                self.buildMenu()

    def keyLeft(self):
        if self.focus == self.FOCUS_CONFIG:
            ConfigListScreen.keyLeft(self)
            if self['config'].getCurrent()[1] in [self.searchSettings.saveTo,
                self.searchSettings.downloadHistory.enabled]:
                self.buildMenu()

    def resetDefaults(self):
        for x in self["config"].list:
            x[1].value = x[1].default
        self.buildMenu()

    def showProviderError(self, provider):
        providerError = provider.error
        if isinstance(providerError, tuple):
            err_msg = providerError[1]
        else:
            err_msg = "unknown error"
            if isinstance(providerError, Exception):
                if isinstance(providerError, ImportError):
                    # No module named ...
                    err_msg = _("missing") + " python-%s " % (providerError.message.split()[-1]) + _("library")
                else:
                    err_msg = providerError.message
        msg = "%s: %s" % (provider.provider_name, err_msg)
        self.session.open(MessageBox, msg, MessageBox.TYPE_WARNING, timeout=5)

    def openProviderSettings(self, provider):
        self.session.openWithCallback(self.openProviderSettingsCB, SubsSearchProviderMenu, provider)

    def openProviderSettingsCB(self, changed=False):
        if changed:
            configIndex = self['config'].getCurrentIndex()
            providersIndex = self['providers'].index
            self.updateProvidersList()
            self.searchParamsHelper.updateProviders()
            self.buildMenu()
            self['config'].setCurrentIndex(configIndex)
            self['providers'].index = providersIndex


class SubsSearchParamsMenu(Screen, ConfigListScreen):
    LIST_CONFIG = 0
    LIST_SUGGESTIONS = 1
    LIST_HISTORY = 2

    def __init__(self, session, seeker, searchSettings, titleList=None, resetSearchParams=True, enabledList=True, windowTitle=None):
        ratio = 1.5 if isFullHD() else 1
        xOffset = 10
        desktopSize = getDesktopSize()
        windowSize = (desktopSize[0] / 2, desktopSize[1] * 2 / 5)
        xFullSize = (windowSize[0] - (2 * xOffset * ratio))
        sourceTitleInfoFont = 22 * ratio
        sourceTitleInfoSize = (xFullSize, sourceTitleInfoFont + 10)
        sourceTitleFont = 21 * ratio
        sourceTitleSize = (xFullSize, sourceTitleFont * 2 + 10)
        separatorSize = (xFullSize, 2 * ratio)
        configSize = (xFullSize, windowSize[1] - (2 * 10 * ratio))
        configFont = 21 * ratio
        configItemHeight = configFont + 10

        windowPos = (desktopSize[0] / 2 - windowSize[0] / 2, desktopSize[1] / 5 * 3 - windowSize[1] / 2)

        sourceTitleInfoPos = (xOffset * ratio, 10 * ratio)
        sourceTitlePos = (xOffset * ratio, sourceTitleInfoPos[1] + sourceTitleInfoSize[1] + 10 * ratio)
        separatorPos = (xOffset * ratio, sourceTitlePos[1] + sourceTitleSize[1] + 10 * ratio)
        configPos = (xOffset * ratio, separatorPos[1] + separatorSize[1] + 10 * ratio)

        self.skin = """
            <screen position="%d,%d" size="%d,%d" >
                <widget source="sourceTitleInfo" render="Label" position="%d,%d" size="%d,%d" halign="center" font="Regular;%d" foregroundColor="#66BFFF" />
                <widget source="sourceTitle" render="Label" position="%d,%d" size="%d,%d" halign="center" valign="center" font="Regular;%d" />
                <eLabel position="%d,%d" size="%d,%d" backgroundColor="#999999" />
                <widget name="config" position="%d,%d" size="%d,%d" font="Regular;%d" itemHeight="%d" scrollbarMode="showOnDemand" />
            </screen>""" % (
                    windowPos[0], windowPos[1], windowSize[0], windowSize[1],
                    sourceTitleInfoPos[0], sourceTitleInfoPos[1], sourceTitleInfoSize[0], sourceTitleInfoSize[1], sourceTitleInfoFont,
                    sourceTitlePos[0], sourceTitlePos[1], sourceTitleSize[0], sourceTitleSize[1], sourceTitleFont,
                    separatorPos[0], separatorPos[1], separatorSize[0], separatorSize[1],
                    configPos[0], configPos[1], configSize[0], configSize[1], configFont, configItemHeight
                    )
        Screen.__init__(self, session)
        ConfigListScreen.__init__(self, [], session=session)
        self["config"] = MyConfigList([], session, enabledList)
        if not self.handleInputHelpers in self["config"].onSelectionChanged:
            self["config"].onSelectionChanged.append(self.handleInputHelpers)
        self.searchParamsHelper = SearchParamsHelper(seeker, searchSettings)
        self.searchSettings = searchSettings
        if titleList is None:
            titleList = []
        self.sourceTitleList = titleList
        self.sourceTitle = titleList and titleList[0] or ""
        self.currentList = self.LIST_CONFIG
        self.windowTitle = windowTitle
        if len(self.sourceTitleList) == 0:
            self['sourceTitleInfo'] = StaticText(_("Source title not provided"))
        else:
            self['sourceTitleInfo'] = StaticText("%s [%d/%d]" % (_("Source title"), 1, len(self.sourceTitleList)))
        self['sourceTitle'] = StaticText(self.sourceTitle)
        self["suggestionActions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                 "ok": self.switchToConfigList,
                 "cancel": self.cancelToConfigList,

                 "red": self.cancelToHistoryList,
                 "green": self.cancelToSuggestionsList,
                 "yellow": lambda: None,
                 "blue": lambda: None,

                 "right": self.keyRight,
                 "rightRepeated": self.keyRight,
                 "rightUp": lambda: None,
                 "left": self.keyLeft,
                 "leftRepeated": self.keyLeft,
                 "leftUp": lambda: None,
                 "up": self.keyUp,
                 "upRepeated": self.keyUp,
                 "upUp": lambda: None,
                 "down": self.keyDown,
                 "downRepeated": self.keyDown,
                 "downUp": lambda: None,
             }, -2)

        self["configActions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                "ok": self.keyOK,
                "cancel": self.keyCancel,

                "red": self.switchToHistoryList,
                "green": self.switchToSuggestionsList,
                "yellow": lambda: None,
                "blue": self.toggleSourceTitle,

                "right": self.keyRight,
                "rightRepeated": self.keyRight,
                "rightUp": lambda: None,
                "left": self.keyLeft,
                "leftRepeated": self.keyLeft,
                "leftUp": lambda: None,
                "up": self.keyUp,
                "upRepeated": self.keyUp,
                "upUp": lambda: None,
                "down": self.keyDown,
                "downRepeated": self.keyDown,
                "downUp": lambda: None
            }, -2)

        self['suggestionActions'].setEnabled(False)
        if resetSearchParams and titleList is not None:
            self.onLayoutFinish.append(self.detectSearchParams)
        self.onLayoutFinish.append(self.buildMenu)
        self.onLayoutFinish.append(self.setWindowTitle)
        self.onLayoutFinish.append(self.saveAll)
        self.onClose.append(self.removeSuggestionWindows)

    def setWindowTitle(self):
        if self.windowTitle is not None:
            self.setTitle(self.windowTitle)
        else:
            self.setTitle(_("Update Search params"))

    def buildMenu(self):
        menuList = []
        menuList.append(getConfigListEntry(_("Title"), self.searchSettings.title))
        menuList.append(getConfigListEntry(_("Type"), self.searchSettings.type))
        if self.searchSettings.type.value == "movie":
            menuList.append(getConfigListEntry(_("Year"), self.searchSettings.year))
        else:
            menuList.append(getConfigListEntry(_("Season"), self.searchSettings.season))
            menuList.append(getConfigListEntry(_("Episode"), self.searchSettings.episode))
        menuList.append(getConfigListEntry(_("Provider"), self.searchSettings.provider))
        menuList.append(getConfigListEntry(_("Use File path"), self.searchSettings.useFilePath))
        self["config"].list = menuList
        self["config"].setList(menuList)

    def detectSearchParams(self):
        self.searchParamsHelper.detectSearchParams(self.sourceTitle)
        self.searchParamsHelper.updateProviders()

    def toggleSourceTitle(self):
        if len(self.sourceTitleList) == 0:
            return
        currIdx = self.sourceTitleList.index(self.sourceTitle)
        if self.sourceTitle == self.sourceTitleList[-1]:
            currIdx = 0
        else:
            currIdx += 1
        self.sourceTitle = self.sourceTitleList[currIdx]
        self['sourceTitle'].text = self.sourceTitle
        self['sourceTitleInfo'].text = "%s [%d/%d]" % (_("Source title"), currIdx + 1, len(self.sourceTitleList))
        self.detectSearchParams()
        self.buildMenu()

    def switchToSuggestionsList(self):
        if not self['config'].enabled:
            return

        if self["config"].getCurrent()[1] == self.searchSettings.title:
            self["configActions"].setEnabled(False)
            self["suggestionActions"].setEnabled(True)
            self["config"].invalidateCurrent()
            self["config"].getCurrent()[1].enableHistory(False)
            if self["config"].getCurrent()[1].enableSuggestions(True):
                self.currentList = self.LIST_SUGGESTIONS
            else:
                self.cancelToConfigList()

    def switchToHistoryList(self):
        if not self['config'].enabled:
            return

        if self["config"].getCurrent()[1] == self.searchSettings.title:
            self["configActions"].setEnabled(False)
            self["suggestionActions"].setEnabled(True)
            self["config"].invalidateCurrent()
            self["config"].getCurrent()[1].enableSuggestions(False)
            if self["config"].getCurrent()[1].enableHistory(True):
                self.currentList = self.LIST_HISTORY
            else:
                self.cancelToConfigList()

    def switchToConfigList(self):
        self["config"].getCurrent()[1].enableSuggestions(False)
        self["config"].getCurrent()[1].enableHistory(False)
        self["suggestionActions"].setEnabled(False)
        self["configActions"].setEnabled(True)
        self.currentList = self.LIST_CONFIG

    def cancelToHistoryList(self):
        self["config"].invalidateCurrent()
        self["config"].getCurrent()[1].cancelSuggestions()
        self.switchToHistoryList()

    def cancelToSuggestionsList(self):
        self["config"].invalidateCurrent()
        self["config"].getCurrent()[1].cancelSuggestions()
        self.switchToSuggestionsList()

    def cancelToConfigList(self):
        self["config"].invalidateCurrent()
        self["config"].getCurrent()[1].cancelSuggestions()
        self.switchToConfigList()

    def addToHistory(self):
        history = self.searchSettings.history.value.split(',')
        if history[0] == '':
            del history[0]
        if self.searchSettings.title.value in history:
            history.remove((self.searchSettings.title.value))
        history.insert(0, (self.searchSettings.title.value))
        if len(history) == 30:
            history.pop()
        self.searchSettings.history.value = ",".join(history)
        self.searchSettings.history.save()

    def keySave(self):
        for x in self["config"].list:
            x[1].save()
        self.close(True)

    def keyCancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()

    def keyOK(self):
        if self.currentList == self.LIST_CONFIG:
            self.addToHistory()
            self.saveAll()
            self.close(True)
        elif self.currentList in (self.LIST_SUGGESTIONS, self.LIST_HISTORY):
            self.switchToConfigList()

    def keyDown(self):
        if not self['config'].enabled:
            self['config'].enableList()
        elif self.currentList in (self.LIST_SUGGESTIONS, self.LIST_HISTORY):
            self["config"].getCurrent()[1].currentListDown()
            self["config"].invalidateCurrent()
        elif self.currentList == self.LIST_CONFIG:
            self['config'].instance.moveSelection(self["config"].instance.moveDown)

    def keyUp(self):
        if not self['config'].enabled:
            self['config'].enableList()
        elif self.currentList in (self.LIST_SUGGESTIONS, self.LIST_HISTORY):
            self["config"].getCurrent()[1].currentListUp()
            self["config"].invalidateCurrent()
        elif self.currentList == self.LIST_CONFIG:
            self['config'].instance.moveSelection(self["config"].instance.moveUp)

    def keyLeft(self):
        if not self['config'].enabled:
            self['config'].enableList()
        elif self.currentList in (self.LIST_SUGGESTIONS, self.LIST_HISTORY):
            self["config"].getCurrent()[1].currentListPageUp()
            self["config"].invalidateCurrent()
        elif self.currentList == self.LIST_CONFIG:
            ConfigListScreen.keyLeft(self)
            if self['config'].getCurrent()[1] == self.searchSettings.type:
                self.searchParamsHelper.updateProviders()
                self.buildMenu()

    def keyRight(self):
        if not self['config'].enabled:
            self['config'].enableList()
        elif self.currentList in (self.LIST_SUGGESTIONS, self.LIST_HISTORY):
            self["config"].getCurrent()[1].currentListPageDown()
            self["config"].invalidateCurrent()
        elif self.currentList == self.LIST_CONFIG:
            ConfigListScreen.keyRight(self)
            if self['config'].getCurrent()[1] == self.searchSettings.type:
                self.searchParamsHelper.updateProviders()
                self.buildMenu()

    def removeSuggestionWindows(self):
        if hasattr(self.searchSettings.title, 'suggestionsWindow'):
            suggestionsWindow = self.searchSettings.title.suggestionsWindow
            if suggestionsWindow is not None:
                self.session.deleteDialog(suggestionsWindow)
                self.searchSettings.title.suggestionsWindow = None
        if hasattr(self.searchSettings.title, 'historyWindow'):
            historyWindow = self.searchSettings.title.historyWindow
            if historyWindow is not None:
                self.session.deleteDialog(historyWindow)
                self.searchSettings.title.historyWindow = None


class SubsSearchProviderMenu(BaseMenuScreen):
    def __init__(self, session, provider):
        title = toString(provider.provider_name) + " " + _("settings")
        BaseMenuScreen.__init__(self, session, title)
        self.provider = provider

    def buildMenu(self):
        settingsProvider = self.provider.settings_provider
        self["config"].setList(settingsProvider.getE2Settings())
