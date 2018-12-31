DOMAIN=SubsSupport
installdir = ${libdir}/enigma2/python/Plugins/Extensions/$(DOMAIN)

MSGFMT = msgfmt

LANGS = ar bg cs es et fr it lt pl pt ru sk uk
LANGPO = $(LANGS:=.po)
LANGMO = $(LANGS:=.mo)

all:
	for lang in $(LANGS); do \
	    msgfmt -o $$lang.mo $$lang.po; \
	done

CLEANFILES = $(LANGS:=.mo)

clean-local:
	$(RM) -r $(LANGS)

install-data-am:
	for lang in $(LANGS) ; do \
		mkdir -p $(DESTDIR)$(installdir)/locale/$$lang/LC_MESSAGES; \
		cp $$lang.mo $(DESTDIR)$(installdir)/locale/$$lang/LC_MESSAGES/$(DOMAIN).mo; \
		cp $$lang.po $(DESTDIR)$(installdir)/locale/$$lang/LC_MESSAGES/$$lang.po; \
	done
