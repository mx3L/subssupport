'''
Created on Sep 16, 2014

@author: marko
'''
from __future__ import absolute_import
from __future__ import print_function
import time
from . import _
from Components.ActionMap import HelpableActionMap
from Components.Label import Label
from Components.config import ConfigSubsection, getConfigListEntry
from Components.config import config, ConfigOnOff
from Screens.HelpMenu import HelpableScreen
from .compat import MessageBox, eConnectCallback
from Screens.MinuteInput import MinuteInput
from Screens.Screen import Screen

from .e2_utils import getFps, fps_float, BaseMenuScreen, isFullHD, getDesktopSize
from enigma import eTimer, getDesktop
from .parsers.baseparser import ParseError
from .process import LoadError, DecodeError, ParserNotFoundError
from skin import parseColor
from .subtitles import SubsChooser, initSubsSettings, SubsScreen, \
    SubsLoader, PARSERS, ALL_LANGUAGES_ENCODINGS, ENCODINGS, \
    warningMessage


config.plugins.subsSupport = ConfigSubsection()
config.plugins.subsSupport.dvb = ConfigSubsection()
config.plugins.subsSupport.dvb.autoSync = ConfigOnOff(default=True)


class SubsSetupDVBPlayer(BaseMenuScreen):
    def __init__(self, session, dvbSettings):
        BaseMenuScreen.__init__(self, session, _("DVB player settings"))
        self.dvbSettings = dvbSettings

    def buildMenu(self):
        self['config'].setList([getConfigListEntry(_("Auto sync to current event"), self.dvbSettings.autoSync)])


class SubsSupportDVB(object):
    def __init__(self, session):
        self.session = session
        self.subsSettings = initSubsSettings()
        session.openWithCallback(self.subsChooserCB, SubsChooser, self.subsSettings, searchSupport=True, historySupport=True, titleList=self.getTitleList())

    def getTitleList(self):
        eventList = []
        eventNow = self.session.screen["Event_Now"].getEvent()
        eventNext = self.session.screen["Event_Next"].getEvent()
        if eventNow:
            eventList.append(eventNow.getEventName())
        if eventNext:
            eventList.append(eventNext.getEventName())
        return eventList

    def subsChooserCB(self, subfile=None, embeddedSubtitle=None, forceReload=False):
        if subfile is not None:
            subsLoader = SubsLoader(PARSERS, ALL_LANGUAGES_ENCODINGS + ENCODINGS[self.subsSettings.encodingsGroup.getValue()])
            try:
                subsList, subsEnc = subsLoader.load(subfile, fps=getFps(self.session))
            except LoadError:
                warningMessage(self.session, _("Cannot load subtitles. Invalid path"))
            except DecodeError:
                warningMessage(self.session, _("Cannot decode subtitles. Try another encoding group"))
            except ParserNotFoundError:
                warningMessage(self.session, _("Cannot parse subtitles. Not supported subtitles format"))
            except ParseError:
                warningMessage(self.session, _("Cannot parse subtitles. Invalid subtitles format"))
            else:
                self.subsScreen = self.session.instantiateDialog(SubsScreen, self.subsSettings.external)
                subsEngine = SubsEngineDVB(self.session, self.subsSettings.engine, self.subsScreen)
                subsEngine.setSubsList(subsList)
                self.session.openWithCallback(self.subsControllerCB, SubsControllerDVB, subsEngine, config.plugins.subsSupport.dvb.autoSync.value)
        else:
            print('[SubsSupportDVB] no subtitles selected, exit')

    def subsControllerCB(self):
        self.session.deleteDialog(self.subsScreen)


class SubsControllerDVB(Screen, HelpableScreen):
    fpsChoices = ["23.976", "23.980", "24.000", "25.000", "29.970", "30.000"]

    def __init__(self, session, engine, autoSync=False, setSubtitlesFps=False, subtitlesFps=None):
        desktopSize = getDesktopSize()
        windowPosition = (int(0.03 * desktopSize[0]), int(0.05 * desktopSize[1]))
        windowSize = (int(0.9 * desktopSize[0]), int(0.4 * desktopSize[1]))
        fontSize = 33 if isFullHD() else 22
        leftWidget = (int(0.4 * windowSize[0]), fontSize + 10, fontSize)
        rightWidget = (int(0.4 * windowSize[0]), fontSize + 10, fontSize)
        xpos = (int(0.6 * windowSize[0]), )
        self.skin = """
            <screen position="%d,%d" size="%d,%d" zPosition="2" backgroundColor="transparent" flags="wfNoBorder">
                <widget name="subtitle" position="0,0" size="%d,%d" valign="center" halign="left" font="Regular;%d" transparent="1" foregroundColor="#ffffff" shadowColor="#40101010" shadowOffset="2,2" />
                <widget name="subtitlesTime" position="0,%d" size="%d,%d" valign="center" halign="left" font="Regular;%d" transparent="1" foregroundColor="#ffffff" shadowColor="#40101010" shadowOffset="2,2" />
                <widget name="subtitlesPosition" position="0,%d" size="%d,%d" valign="center" halign="left" font="Regular;%d" transparent="1" foregroundColor="#ffffff" shadowColor="#40101010" shadowOffset="2,2" />
                <widget name="subtitlesFps" position="0,%d" size="%d,%d" valign="center" halign="left" font="Regular;%d" transparent="1" foregroundColor="#6F9EF5" shadowColor="#40101010" shadowOffset="2,2" />
                <widget name="eventName" position="%d,%d" size="%d,%d" valign="center" halign="left" font="Regular;%d" transparent="1" foregroundColor="#ffffff" shadowColor="#40101010" shadowOffset="2,2" />
                <widget name="eventTime" position="%d,%d" size="%d,%d" valign="center" halign="left" font="Regular;%d" transparent="1" foregroundColor="#ffffff" shadowColor="#40101010" shadowOffset="2,2" />
                <widget name="eventDuration" position="%d,%d" size="%d,%d" valign="center" halign="left" font="Regular;%d" transparent="1" foregroundColor="#ffffff" shadowColor="#40101010" shadowOffset="2,2" />
            </screen>""" % (windowPosition + windowSize +
                leftWidget +
                (leftWidget[1] + 10,) + leftWidget +
                ((leftWidget[1] + 10) * 2,) + leftWidget +
                ((leftWidget[1] + 10) * 3,) + leftWidget +
                xpos + (0,) + rightWidget +
                xpos + ((rightWidget[1] + 10) * 1,) + rightWidget +
                xpos + ((rightWidget[1] + 10) * 2,) + rightWidget)

        Screen.__init__(self, session)
        HelpableScreen.__init__(self)
        self.engine = engine
        self.engine.onRenderSub.append(self.onRenderSub)
        self.engine.onHideSub.append(self.onHideSub)
        self.engine.onPositionUpdate.append(self.onUpdateSubPosition)
        subtitlesFps = subtitlesFps and fps_float(subtitlesFps)
        if subtitlesFps and str(subtitlesFps) in self.fpsChoices:
            self.providedSubtitlesFps = subtitlesFps
        else:
            self.providedSubtitlesFps = None
        self.hideTimer = eTimer()
        self.hideTimer_conn = eConnectCallback(self.hideTimer.timeout, self.hideStatus)
        self.hideTimerDelay = 5000
        self.eventTimer = eTimer()
        self.eventTimer_conn = eConnectCallback(self.eventTimer.timeout, self.updateEventStatus)
        self.subtitlesTimer = eTimer()
        self.subtitlesTimer_conn = eConnectCallback(self.subtitlesTimer.timeout, self.updateSubtitlesTime)
        self.subtitlesTimerStep = 500
        self._baseTime = 0
        self._accTime = 0
        self.statusLocked = False
        self['subtitle'] = Label()
        self['subtitlesPosition'] = Label(_("Subtitles Position") + ":")
        self['subtitlesTime'] = Label(_("Subtitles Time") + ":")
        self['subtitlesFps'] = Label(_("Subtitles FPS") + ":")
        self["eventName"] = Label(_("Event Name") + ":")
        self["eventTime"] = Label(_("Event Time") + ":")
        self["eventDuration"] = Label(_("Event Duration") + ":")
        self['actions'] = HelpableActionMap(self, "SubtitlesDVBActions",
        {
            "closePlugin": (self.close, _("close plugin")),
            "showHideStatus": (self.showHideStatus, _("show/hide subtitles status")),
            "playPauseSub": (self.playPause, _("play/pause subtitles playback")),
            "pauseSub": (self.pause, _("pause subtitles playback")),
            "resumeSub": (self.resume, _("resumes subtitles playback")),
            "restartSub": (self.restart, _("restarts current subtitle")),
            "nextSub": (self.nextSkip, _("skip to next subtitle")),
            "nextSubMinute": (self.nextMinuteSkip, _("skip to next subtitle (minute jump)")),
            "nextSubManual": (self.nextManual, _("skip to next subtitle by setting time in minutes")),
            "prevSub": (self.previousSkip, _("skip to previous subtitle")),
            "prevSubMinute": (self.previousMinuteSkip, _("skip to previous subtitle (minute jump)")),
            "prevSubManual": (self.previousManual, _("skip previous subtitle by setting time in minutes")),
            "eventSync": (self.eventSync, _("skip subtitle to current event position")),
            "changeFps": (self.changeFps, _("change subtitles fps")),
        }, 0)
        try:
            from Screens.InfoBar import InfoBar
            InfoBar.instance.subtitle_window.hide()
        except:
            pass
        self.onLayoutFinish.append(self.hideStatus)
        self.onLayoutFinish.append(self.engine.start)
        self.onLayoutFinish.append(self.startEventTimer)
        self.onLayoutFinish.append(self.startSubtitlesTimer)
        self.onLayoutFinish.append(self.showStatusWithTimer)
        if setSubtitlesFps and self.providedSubtitlesFps:
            self.onFirstExecBegin.append(self.setProvidedSubtitlesFps)
        if autoSync:
            self.onFirstExecBegin.append(self.eventSync)
        self.onClose.append(self.engine.close)
        self.onClose.append(self.delTimers)

    def startEventTimer(self):
        self.eventTimer.start(500)

    def startSubtitlesTimer(self):
        self.subtitlesTimer.start(self.subtitlesTimerStep)

    def setProvidedSubtitlesFps(self):
        self.engine.setSubsFps(self.providedSubtitlesFps)
        self.updateSubtitlesFps()

    def onUpdateSubPosition(self, position):
        self.updateSubtitlesPosition(position)

    def onRenderSub(self, sub):
        if self['subtitle'].visible:
            self.updateSubtitle(sub, True)
        if self['subtitlesTime'].visible:
            self.updateSubtitlesTime(sub)

    def onHideSub(self, sub):
        if sub == self.engine.subsList[-1]:
            self.subtitlesTimer.stop()
        if self['subtitle'].visible:
            nextSubIdx = self.engine.subsList.index(sub) + 1
            if nextSubIdx >= len(self.engine.subsList) - 1:
                nextSub = None
            else:
                nextSub = self.engine.subsList[nextSubIdx]
            self.updateSubtitle(nextSub, active=False)

    def showStatusWithTimer(self):
        self.showStatus(True)

    def showStatus(self, withTimer=False):
        sub = self.engine.getCurrentSub()
        active = self.engine.renderer.subShown
        self.updateSubtitle(sub, active)
        self.updateSubtitlesFps()
        self.updateSubtitlesPosition()
        self.updateEventStatus()
        self['subtitle'].visible = True
        self['subtitlesPosition'].visible = True
        self['subtitlesTime'].visible = True
        self['subtitlesFps'].visible = True
        self['eventName'].visible = True
        self['eventTime'].visible = True
        self['eventDuration'].visible = True
        if withTimer and not self.statusLocked:
            self.hideTimer.start(self.hideTimerDelay, True)

    def hideStatus(self):
        self['subtitle'].visible = False
        self['subtitlesPosition'].visible = False
        self['subtitlesTime'].visible = False
        self['subtitlesFps'].visible = False
        self['eventName'].visible = False
        self['eventTime'].visible = False
        self['eventDuration'].visible = False

    def updateSubtitle(self, sub, active):
        if sub is None:
            self['subtitle'].setText("")
            return
        st = sub['start'] * self.engine.fpsRatio / 90000
        et = sub['end'] * self.engine.fpsRatio / 90000
        stStr = "%d:%02d:%02d" % ((st / 3600, st % 3600 / 60, st % 60))
        etStr = "%d:%02d:%02d" % ((et / 3600, et % 3600 / 60, et % 60))
        if active:
            self['subtitle'].instance.setForegroundColor(parseColor("#F7A900"))
            self['subtitle'].setText("%s ----> %s" % (stStr, etStr))
        else:
            self['subtitle'].instance.setForegroundColor(parseColor("#aaaaaa"))
            self['subtitle'].setText("%s ----> %s" % (stStr, etStr))

    def updateSubtitlesPosition(self, position=None):
        if position is None:
            position = self.engine.subsList.index(self.engine.getCurrentSub())
        self['subtitlesPosition'].setText("%s: %d / %d" % (_("Subtitles Position"), position, len(self.engine.subsList) - 1))

    def updateSubtitlesTime(self, sub=None):
        if sub:
            self._baseTime = sub['start'] * self.engine.fpsRatio / 90
            self._accTime = 0
            if not self.engine.isPaused():
                self.startSubtitlesTimer()
        else:
            self._accTime += self.subtitlesTimerStep
        self._subtitlesTime = self._baseTime + self._accTime
        if self['subtitlesTime'].visible:
            st = self._subtitlesTime / 1000
            time = "%d:%02d:%02d" % (st / 3600, st % 3600 / 60, st % 60)
            self['subtitlesTime'].setText("%s: %s" % (_("Subtitles Time"), time))

    def updateSubtitlesFps(self):
        subsFps = self.engine.getSubsFps()
        videoFps = getFps(self.session, True)
        if subsFps is None or videoFps is None:
            self['subtitlesFps'].setText("%s: %s" % (_("Subtitles FPS"), _("unknown")))
            return
        if subsFps == videoFps:
            if self.providedSubtitlesFps is not None:
                if self.providedSubtitlesFps == videoFps:
                    self['subtitlesFps'].setText("%s: %s (%s)" % (_("Subtitles FPS"), _("original"), _("original")))
                else:
                    self['subtitlesFps'].setText("%s: %s (%s)" % (_("Subtitles FPS"), _("original"), str(self.providedSubtitlesFps)))
            else:
                self['subtitlesFps'].setText("%s: %s" % (_("Subtitles FPS"), _("original")))
        else:
            if self.providedSubtitlesFps is not None:
                if self.providedSubtitlesFps == videoFps:
                    self['subtitlesFps'].setText("%s: %s (%s)" % (_("Subtitles FPS"), str(subsFps), _("original")))
                else:
                    self['subtitlesFps'].setText("%s: %s (%s)" % (_("Subtitles FPS"), str(subsFps), str(self.providedSubtitlesFps)))
            else:
                self['subtitlesFps'].setText("%s: %s" % (_("Subtitles FPS"), str(subsFps)))

    def updateEventStatus(self):
        event = self.session.screen["Event_Now"].getEvent()
        if event is not None:
            eventName = event.getEventName()
            if eventName:
                if self["eventName"].getText() != eventName:
                    self["eventName"].setText("%s" % eventName)
            else:
                self["eventName"].setText("%s" % (_("unknown")))
            eventStartTime = event.getBeginTime()
            if eventStartTime:
                ep = int(time.time()) - eventStartTime
                self["eventTime"].setText("%s: %d:%02d:%02d" % (_("Time"), ep / 3600, ep % 3600 / 60, ep % 60))
            else:
                self["eventTime"].setText("%s: %s" % (_("Event Time"), "0:00:00"))
            eventDuration = event.getDuration()
            if eventDuration:
                if eventStartTime:
                    eventProgress = int(time.time()) - eventStartTime
                    if eventProgress > eventDuration:
                        ed = 0
                    else:
                        ed = eventDuration
                else:
                    ed = eventDuration
                self["eventDuration"].setText("%s: %d:%02d:%02d" % (_("Duration"), ed / 3600, ed % 3600 / 60, ed % 60))
            else:
                self["eventTime"].setText("%s: %s" % (_("Event Duration"), "0:00:00"))
        else:
            self["eventName"].setText("")
            self["eventTime"].setText("")
            self["eventDuration"].setText("")

    def changeFps(self):
        subsFps = self.engine.getSubsFps()
        if subsFps is None:
            return
        currIdx = self.fpsChoices.index(str(subsFps))
        if currIdx == len(self.fpsChoices) - 1:
            nextIdx = 0
        else:
            nextIdx = currIdx + 1
        self.engine.setSubsFps(fps_float(self.fpsChoices[nextIdx]))
        self.updateSubtitlesFps()
        sub = self.engine.getCurrentSub()
        active = self.engine.renderer.subShown
        self.updateSubtitle(sub, active)
        self.updateSubtitlesPosition()
        self.showStatus(True)

    def showHideStatus(self):
        if self['subtitle'].visible:
            self.statusLocked = False
            self.hideStatus()
        else:
            self.statusLocked = True
            self.showStatus()

    def eventSync(self):
        event = self.session.screen["Event_Now"].getEvent()
        if event is not None:
            progress = (int(time.time()) - event.getBeginTime()) * 1000
            self.engine.seekTo(progress)
        else:
            self.session.open(MessageBox, _("cannot sync to event, event is not available"), MessageBox.TYPE_INFO, simple=True, timeout=3)

    def playPause(self):
        if self.engine.isPaused():
            self.resume()
        else:
            self.pause()

    def pause(self):
        self.engine.pause()
        self.subtitlesTimer.stop()
        self.showStatus()

    def resume(self):
        self.engine.resume()
        self.startSubtitlesTimer()
        self.showStatus(True)

    def restart(self):
        self.engine.pause()
        self.engine.resume()
        self.showStatus(True)

    def nextSkip(self):
        self.engine.toNextSub()
        self.showStatus(True)

    def nextMinuteSkip(self):
        self.engine.seekRelative(60 * 1000)
        self.showStatus(True)

    def nextManual(self):
        def nextManualCB(minutes):
            if minutes > 0:
                self.engine.seekRelative(minutes * 60 * 1000)
                self.showStatus(True)
        self.session.openWithCallback(nextManualCB, MinuteInput)

    def previousSkip(self):
        self.engine.toPrevSub()
        self.showStatus(True)

    def previousMinuteSkip(self):
        self.engine.seekRelative(-60 * 1000)
        self.showStatus(True)

    def previousManual(self):
        def previousManualCB(minutes):
            if minutes > 0:
                self.engine.seekRelative(-minutes * 60 * 1000)
                self.showStatus(True)
        self.session.openWithCallback(previousManualCB, MinuteInput)

    def delTimers(self):
        self.hideTimer.stop()
        del self.hideTimer_conn
        del self.hideTimer
        self.eventTimer.stop()
        del self.eventTimer_conn
        del self.eventTimer
        self.subtitlesTimer.stop()
        del self.subtitlesTimer_conn
        del self.subtitlesTimer


class SubsEngineDVB(object):
    def __init__(self, session, engineSettings, renderer):
        self.session = session
        self.renderer = renderer
        self.delay = 0
        self.__position = 0
        self.fpsRatio = 1
        self.subsList = None
        self.paused = True
        self.waitTimer = eTimer()
        self.waitTimer_conn = eConnectCallback(self.waitTimer.timeout, self.doWait)
        self.hideTimer = eTimer()
        self.hideTimer_conn = eConnectCallback(self.hideTimer.timeout, self.hideTimerCallback)
        self.onRenderSub = []
        self.onHideSub = []
        self.onPositionUpdate = []

    def setSubsList(self, subsList):
        self.subsList = subsList

    def setSubsFps(self, subsFps):
        print("[SubsEngineDVB] setSubsFps - setting fps to %s" % str(subsFps))
        videoFps = getFps(self.session, True)
        if videoFps is None:
            print("[SubsEngineDVB] setSubsFps - cannot get video fps!")
        else:
            self.waitTimer.stop()
            self.hideTimer.stop()
            self.fpsRatio = subsFps / float(videoFps)
            self.renderSub()
            if not self.paused:
                self.setRefTime()
                self.startHideTimer()

    def setPosition(self, position):
        if position > len(self.subsList) - 1:
            return
        self.__position = position
        for f in self.onPositionUpdate:
            f(self.__position)

    def getPosition(self):
        return self.__position

    position = property(getPosition, setPosition)

    def getSubsFps(self):
        videoFps = getFps(self.session, True)
        if videoFps is None:
            return None
        return fps_float(self.fpsRatio * videoFps)

    def getCurrentSub(self):
        return self.subsList[self.position]

    def setRefTime(self):
        self.reftime = time.time() * 1000
        self.refposition = self.position
        self.delay = 0

    def isPaused(self):
        return self.paused

    def start(self):
        self.renderer.show()
        self.resume()

    def pause(self):
        self.waitTimer.stop()
        self.hideTimer.stop()
        self.paused = True

    def resume(self):
        self.waitTimer.stop()
        self.hideTimer.stop()
        self.setRefTime()
        self.renderSub()
        self.paused = False
        self.startHideTimer()

    def renderSub(self):
        for f in self.onRenderSub:
            f(self.subsList[self.position])
        self.renderer.setSubtitle(self.subsList[self.position])

    def hideSub(self):
        for f in self.onHideSub:
            f(self.subsList[self.position])
        self.renderer.hideSubtitle()

    def startHideTimer(self):
        self.hideTimer.start(int(self.subsList[self.position]['duration'] * self.fpsRatio), True)

    def hideTimerCallback(self):
        self.hideTimer.stop()
        self.waitTimer.stop()
        if self.position == len(self.subsList) - 1:
            self.hideSub()
        elif self.subsList[self.position]['end'] * self.fpsRatio + (200 * 90) < self.subsList[self.position + 1]['start'] * self.fpsRatio:
            self.hideSub()

        if self.position < len(self.subsList) - 1:
            self.position += 1
            self.toTime = self.reftime + ((self.subsList[self.position]['start'] - self.subsList[self.refposition]['start']) / 90 * self.fpsRatio)
            timeout = ((self.subsList[self.position]['start'] - self.subsList[self.position - 1]['end']) / 90 * self.fpsRatio) + self.delay
            self.waitTimer.start(int(timeout), True)

    def doWait(self):
        timeNow = time.time() * 1000
        delay = int(self.toTime - timeNow)
        if delay > 50:
            self.waitTimer.start(delay, True)
        elif delay <= 50 and delay >= 0:
            print("[SubsEngineDVB] sub shown sooner by %s ms" % (delay))
            self.delay = 0
            self.waitTimer.stop()
            self.renderSub()
            self.startHideTimer()
        else:
            print("[SubsEngineDVB] sub shown later by %s ms" % (abs(delay)))
            self.delay = delay
            self.waitTimer.stop()
            self.renderSub()
            self.startHideTimer()

    def seekTo(self, time):
        self.waitTimer.stop()
        self.hideTimer.stop()
        print("[SubsEngineDVB] seekTo, position before seek: %d" % self.position)
        firstSub = self.subsList[0]
        lastSub = self.subsList[-1]
        position = self.position
        if time > lastSub['start'] / 90 * self.fpsRatio:
            position = self.subsList.index(lastSub)
        elif time < firstSub['start'] / 90 * self.fpsRatio:
            position = 0
        elif abs(time - (firstSub['start'] / 90 * self.fpsRatio)) < abs(time - (lastSub['start'] / 90 * self.fpsRatio)):
            position = 0
            subStartTime = firstSub['start'] / 90 * self.fpsRatio
            while time > subStartTime:
                position += 1
                subStartTime = self.subsList[position]['start'] / 90 * self.fpsRatio
        else:
            position = self.subsList.index(lastSub)
            subStartTime = lastSub['start'] / 90 * self.fpsRatio
            while time < subStartTime:
                position -= 1
                subStartTime = self.subsList[position]['start'] / 90 * self.fpsRatio
        self.position = position
        print("[SubsEngineDVB] seekTo, position after seek: %d" % (self.position))
        self.renderSub()
        if not self.paused:
            self.setRefTime()
            self.startHideTimer()

    def seekRelative(self, time):
        self.waitTimer.stop()
        self.hideTimer.stop()
        print("[SubsEngine] seekRelative, position before seek: %d" % self.position)
        startSubTime = self.subsList[self.position]['start'] / 90 * self.fpsRatio
        position = self.position
        if time > 0:
            nextStartSubTime = 0
            while position != len(self.subsList) - 1 and time > nextStartSubTime:
                position += 1
                nextStartSubTime = ((self.subsList[position]['start']) / 90 * self.fpsRatio) - startSubTime
        else:
            prevEndSubTime = 0
            while position != 0 and time < prevEndSubTime:
                position -= 1
                prevEndSubTime = (self.subsList[position]['end'] / 90 * self.fpsRatio) - startSubTime
        self.position = position
        print("[SubsEngine] seekRelative, position after seek: %d" % self.position)
        self.renderSub()
        if not self.paused:
            self.setRefTime()
            self.startHideTimer()

    def toNextSub(self):
        self.waitTimer.stop()
        self.hideTimer.stop()
        if self.renderer.subShown and self.position < len(self.subsList) - 1:
            self.position += 1
        self.renderSub()
        if not self.paused:
            self.setRefTime()
            self.startHideTimer()

    def toPrevSub(self):
        self.waitTimer.stop()
        self.hideTimer.stop()
        if self.position > 0:
            self.position -= 1
        self.renderSub()
        if not self.paused:
            self.setRefTime()
            self.startHideTimer()

    def close(self):
        self.waitTimer.stop()
        del self.waitTimer_conn
        del self.waitTimer
        self.hideTimer.stop()
        del self.hideTimer_conn
        del self.hideTimer
