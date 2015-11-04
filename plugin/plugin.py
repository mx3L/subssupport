from . import _
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.PluginComponent import PluginDescriptor
from Components.config import config
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from subtitles import E2SubsSeeker, SubsSearch, initSubsSettings, \
    SubsSetupGeneral, SubsSearchSettings, SubsSetupExternal, SubsSetupEmbedded
from subtitlesdvb import SubsSupportDVB, SubsSetupDVBPlayer


def openSubtitlesSearch(session, **kwargs):
    settings = initSubsSettings().search
    eventList = []
    eventNow = session.screen["Event_Now"].getEvent()
    eventNext = session.screen["Event_Next"].getEvent()
    if eventNow:
        eventList.append(eventNow.getEventName())
    if eventNext:
        eventList.append(eventNext.getEventName())
    session.open(SubsSearch, E2SubsSeeker(session, settings), settings, searchTitles=eventList, standAlone=True)
    
def openSubtitlesPlayer(session, **kwargs):
    SubsSupportDVB(session)
    
def openSubsSupportSettings(session, **kwargs):
    settings = initSubsSettings()
    session.open(SubsSupportSettings, settings, settings.search, settings.external, settings.embedded, config.plugins.subsSupport.dvb)

class SubsSupportSettings(Screen):
    skin = """
        <screen position="center,center" size="370,200">
            <widget name="menuList" position="10,10" size="340,180"/>
        </screen>
        """
    def __init__(self, session, generalSettings, searchSettings, externalSettings, embeddedSettings, dvbSettings):
        Screen.__init__(self, session)
        self.generalSettings = generalSettings
        self.searchSettings = searchSettings
        self.externalSettings = externalSettings
        self.embeddedSettings = embeddedSettings
        self.dvbSettings = dvbSettings
        self["menuList"] = MenuList([
            (_("General settings"), "general"),
            (_("External subtitles settings"), "external"),
            (_("Embedded subtitles settings"), "embedded"),
            (_("Search settings"), "search"),
            (_("DVB player settings"), "dvb")
        ])
        self["actionmap"] = ActionMap(["OkCancelActions", "DirectionActions"], 
        {
            "up": self["menuList"].up,
            "down": self["menuList"].down,
            "ok": self.confirmSelection,
            "cancel": self.close,
        })
        self.onLayoutFinish.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setup_title = _("SubsSupport settings")
        self.setTitle(self.setup_title)

    def confirmSelection(self):
        selection  = self["menuList"].getCurrent()[1]
        if selection == "general":
            self.openGeneralSettings()
        elif selection == "external":
            self.openExternalSettings()
        elif selection == "embedded":
            self.openEmbeddedSettings()
        elif selection == "search":
            self.openSearchSettings()
        elif selection == "dvb":
            self.openDVBPlayerSettings()
        
    def openGeneralSettings(self):
        self.session.open(SubsSetupGeneral, self.generalSettings)
        
    def openSearchSettings(self):
        seeker = E2SubsSeeker(self.session, self.searchSettings, True)
        self.session.open(SubsSearchSettings, self.searchSettings, seeker, True)
        
    def openExternalSettings(self):
        self.session.open(SubsSetupExternal, self.externalSettings)
        
    def openEmbeddedSettings(self):
        try:
            from Screens.AudioSelection import QuickSubtitlesConfigMenu
        except ImportError:
            self.session.open(SubsSetupEmbedded, self.embeddedSettings)
        else:
            self.session.open(MessageBox, _("You have OpenPli-based image, please change embedded subtitles settings in Settings / System / Subtitles settings"), MessageBox.TYPE_INFO)
        
    def openDVBPlayerSettings(self):
        self.session.open(SubsSetupDVBPlayer, self.dvbSettings)


def Plugins(**kwargs):
    return [
        PluginDescriptor(_("SubsSupport settings"), PluginDescriptor.WHERE_PLUGINMENU, _("Change subssupport settings"), fnc=openSubsSupportSettings),
        PluginDescriptor(_("SubsSupport downloader"), PluginDescriptor.WHERE_PLUGINMENU, _("Download subtitles for your videos"), fnc=openSubtitlesSearch),
        PluginDescriptor(_("SubsSupport downloader"), PluginDescriptor.WHERE_EXTENSIONSMENU, _("Download subtitles for your videos"), fnc=openSubtitlesSearch),
        PluginDescriptor(_("SubsSupport DVB player"), PluginDescriptor.WHERE_PLUGINMENU, _("watch DVB broadcast with subtitles"), fnc=openSubtitlesPlayer),
        PluginDescriptor(_("SubsSupport DVB player"), PluginDescriptor.WHERE_EXTENSIONSMENU, _("watch DVB broadcast with subtitles"), fnc=openSubtitlesPlayer)
    ]
    