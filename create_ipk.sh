#!/bin/bash
# script taken from openwebif project
set -e

D=$(pushd $(dirname $0) &> /dev/null; pwd; popd &> /dev/null)
S=${D}/ipkg.src$$
P=${D}/ipkg.tmp.$$
B=${D}/ipkg.build.$$
DP=${D}/ipkg.deps

P26="http://www.python.org/ftp/python/2.6/Python-2.6.tgz"
P27="http://www.python.org/ftp/python/2.7.5/Python-2.7.5.tgz"

pushd ${D} &> /dev/null

PVER=$(cat plugin/__init__.py|grep __version__|sed s/__version__\ =\ //|sed s/\"//g|tr -d '[[:space:]]')
GITVER=$(git log -1 --format="%ci" | awk -F" " '{ print $1 }' | tr -d "-")
VER=$PVER-$GITVER

PKG=${D}/enigma2-plugin-extensions-subssupport_${VER}_all
PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/SubsSupport
popd &> /dev/null

rm -rf ${D}/ipkg.src*
rm -rf ${D}/ipkg.tmp*
rm -rf ${D}/ipkg.build*

mkdir -p ${P}/CONTROL
mkdir -p ${B}
mkdir -p ${DP}
mkdir -p ${S}
git archive --format=tar HEAD | (cd ${S} && tar xf -)

if [ -d ${DP}/Python-2.6 ] && [ -d ${DP}/Python-2.7 ]; then
	echo "python packages are already downloaded"
else
	echo "downloading neccesary python packages..."
	wget -O ${DP}/Python-2.6.tgz $P26
	wget -O ${DP}/Python-2.7.5.tgz $P27
	tar -C ${DP} -xzf ${DP}/Python-2.6.tgz
	tar -C ${DP} -xzf ${DP}/Python-2.7.5.tgz
	mv ${DP}/Python-2.7.5 ${DP}/Python-2.7
fi

cat > ${P}/CONTROL/control << EOF
Package: enigma2-plugin-extensions-subssupport
Version: ${VER}
Architecture: all
Section: extra
Priority: optional
Maintainer: mxfitsat@gmail.com
Recommends: python-xmlrpc, unrar, python-compression, python-codecs, python-zlib, python-difflib
Homepage: https://code.google.com/p/mediaplayer2-for-sh4/
Description: Enigma2 subtitles support library  $VER"
EOF

cat > ${P}/CONTROL/postrm << EOF
#!/bin/sh
rm -rf /usr/lib/enigma2/python/Plugins/Extensions/SubsSupport 2> /dev/null
exit 0
EOF

cat > ${P}/CONTROL/postinst << EOF
#!/bin/sh
if [ -d /usr/lib/python2.6 ]
 then
	echo "found python2.6"
	[ ! -e /usr/lib/python2.6/encodings/utf_8.py ] && cp /tmp/subssupport/python2.6/utf_8.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/utf_16.py ] && cp /tmp/subssupport/python2.6/utf_16.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/cp1250.py ] && cp /tmp/subssupport/python2.6/cp1250.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/cp1251.py ] && cp /tmp/subssupport/python2.6/cp1251.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/cp1252.py ] && cp /tmp/subssupport/python2.6/cp1252.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/cp1253.py ] && cp /tmp/subssupport/python2.6/cp1253.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/cp1254.py ] && cp /tmp/subssupport/python2.6/cp1254.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/cp1256.py ] && cp /tmp/subssupport/python2.6/cp1256.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/iso8859_2.py ] && cp /tmp/subssupport/python2.6/iso8859_2.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/iso8859_6.py ] && cp /tmp/subssupport/python2.6/iso8859_6.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/iso8859_7.py ] && cp /tmp/subssupport/python2.6/iso8859_7.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/iso8859_9.py ] && cp /tmp/subssupport/python2.6/iso8859_9.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/iso8859_15.py ] && cp /tmp/subssupport/python2.6/iso8859_15.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/koi8_r.py ] && cp /tmp/subssupport/python2.6/koi8_r.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/mac_cyrillic.py ] && cp /tmp/subssupport/python2.6/mac_cyrillic.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/mac_greek.py ] && cp /tmp/subssupport/python2.6/mac_greek.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/mac_latin2.py ] && cp /tmp/subssupport/python2.6/mac_latin2.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/mac_roman.py ] && cp /tmp/subssupport/python2.6/mac_roman.py /usr/lib/python2.6/encodings/
	[ ! -e /usr/lib/python2.6/encodings/mac_turkish.py ] && cp /tmp/subssupport/python2.6/mac_turkish.py /usr/lib/python2.6/encodings/
fi

if [ -d /usr/lib/python2.7 ]
 then
	echo "found python2.7"
	[ ! -e /usr/lib/python2.7/encodings/utf_8.py ] && cp /tmp/subssupport/python2.7/utf_8.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/utf_16.py ] && cp /tmp/subssupport/python2.7/utf_16.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/cp1250.py ] && cp /tmp/subssupport/python2.7/cp1250.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/cp1251.py ] && cp /tmp/subssupport/python2.7/cp1251.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/cp1252.py ] && cp /tmp/subssupport/python2.7/cp1252.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/cp1253.py ] && cp /tmp/subssupport/python2.7/cp1253.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/cp1254.py ] && cp /tmp/subssupport/python2.7/cp1254.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/cp1256.py ] && cp /tmp/subssupport/python2.7/cp1256.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/iso8859_2.py ] && cp /tmp/subssupport/python2.7/iso8859_2.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/iso8859_6.py ] && cp /tmp/subssupport/python2.7/iso8859_6.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/iso8859_7.py ] && cp /tmp/subssupport/python2.7/iso8859_7.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/iso8859_9.py ] && cp /tmp/subssupport/python2.7/iso8859_9.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/iso8859_15.py ] && cp /tmp/subssupport/python2.7/iso8859_15.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/koi8_r.py ] && cp /tmp/subssupport/python2.7/koi8_r.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/mac_cyrillic.py ] && cp /tmp/subssupport/python2.7/mac_cyrillic.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/mac_greek.py ] && cp /tmp/subssupport/python2.7/mac_greek.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/mac_latin2.py ] && cp /tmp/subssupport/python2.7/mac_latin2.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/mac_roman.py ] && cp /tmp/subssupport/python2.7/mac_roman.py /usr/lib/python2.7/encodings/
	[ ! -e /usr/lib/python2.7/encodings/mac_turkish.py ] && cp /tmp/subssupport/python2.7/mac_turkish.py /usr/lib/python2.7/encodings/
fi
rm -rf /tmp/subssupport
exit 0
EOF

chmod 755 ${P}/CONTROL/postinst
chmod 755 ${P}/CONTROL/postrm

mkdir -p ${P}${PLUGINPATH}
cp -rp ${S}/plugin/* ${P}${PLUGINPATH}

for lang in cs sk pl ru pt; do \
    mkdir -p ${P}${PLUGINPATH}/locale/${lang}/LC_MESSAGES; \
    msgfmt ${D}/locale/${lang}.po -o ${P}${PLUGINPATH}/locale/${lang}/LC_MESSAGES/SubsSupport.mo; \
    cp -rp ${D}/locale/${lang}.po ${P}${PLUGINPATH}/locale/${lang}/LC_MESSAGES/;
done

python -O -m compileall ${P} > /dev/null
#find ${P} -name "*.po" -exec rm {} \;
find ${P} -name "Makefile.am" -exec rm {} \;

mkdir -p ${P}/tmp/subssupport
mkdir -p ${P}/tmp/subssupport/python2.6/
mkdir -p ${P}/tmp/subssupport/python2.7/

cp -p ${DP}/Python-2.6/Lib/encodings/utf_8.py ${P}/tmp/subssupport/python2.6/utf_8.py
cp -p ${DP}/Python-2.6/Lib/encodings/utf_16.py ${P}/tmp/subssupport/python2.6/utf_16.py
cp -p ${DP}/Python-2.6/Lib/encodings/cp1250.py ${P}/tmp/subssupport/python2.6/cp1250.py
cp -p ${DP}/Python-2.6/Lib/encodings/cp1251.py ${P}/tmp/subssupport/python2.6/cp1251.py
cp -p ${DP}/Python-2.6/Lib/encodings/cp1252.py ${P}/tmp/subssupport/python2.6/cp1252.py
cp -p ${DP}/Python-2.6/Lib/encodings/cp1253.py ${P}/tmp/subssupport/python2.6/cp1253.py
cp -p ${DP}/Python-2.6/Lib/encodings/cp1254.py ${P}/tmp/subssupport/python2.6/cp1254.py
cp -p ${DP}/Python-2.6/Lib/encodings/cp1256.py ${P}/tmp/subssupport/python2.6/cp1256.py
cp -p ${DP}/Python-2.6/Lib/encodings/iso8859_2.py ${P}/tmp/subssupport/python2.6/iso8859_2.py
cp -p ${DP}/Python-2.6/Lib/encodings/iso8859_6.py ${P}/tmp/subssupport/python2.6/iso8859_6.py
cp -p ${DP}/Python-2.6/Lib/encodings/iso8859_7.py ${P}/tmp/subssupport/python2.6/iso8859_7.py
cp -p ${DP}/Python-2.6/Lib/encodings/iso8859_9.py ${P}/tmp/subssupport/python2.6/iso8859_9.py
cp -p ${DP}/Python-2.6/Lib/encodings/iso8859_15.py ${P}/tmp/subssupport/python2.6/iso8859_15.py
cp -p ${DP}/Python-2.6/Lib/encodings/koi8_r.py ${P}/tmp/subssupport/python2.6/koi8_r.py
cp -p ${DP}/Python-2.6/Lib/encodings/mac_latin2.py ${P}/tmp/subssupport/python2.6/mac_latin2.py
cp -p ${DP}/Python-2.6/Lib/encodings/mac_cyrillic.py ${P}/tmp/subssupport/python2.6/mac_cyrillic.py
cp -p ${DP}/Python-2.6/Lib/encodings/mac_greek.py ${P}/tmp/subssupport/python2.6/mac_greek.py
cp -p ${DP}/Python-2.6/Lib/encodings/mac_roman.py ${P}/tmp/subssupport/python2.6/mac_roman.py
cp -p ${DP}/Python-2.6/Lib/encodings/mac_turkish.py ${P}/tmp/subssupport/python2.6/mac_turkish.py

cp -p ${DP}/Python-2.7/Lib/encodings/utf_8.py ${P}/tmp/subssupport/python2.7/utf_8.py
cp -p ${DP}/Python-2.7/Lib/encodings/utf_16.py ${P}/tmp/subssupport/python2.7/utf_16.py
cp -p ${DP}/Python-2.7/Lib/encodings/cp1250.py ${P}/tmp/subssupport/python2.7/cp1250.py
cp -p ${DP}/Python-2.7/Lib/encodings/cp1251.py ${P}/tmp/subssupport/python2.7/cp1251.py
cp -p ${DP}/Python-2.7/Lib/encodings/cp1252.py ${P}/tmp/subssupport/python2.7/cp1252.py
cp -p ${DP}/Python-2.7/Lib/encodings/cp1253.py ${P}/tmp/subssupport/python2.7/cp1253.py
cp -p ${DP}/Python-2.7/Lib/encodings/cp1254.py ${P}/tmp/subssupport/python2.7/cp1254.py
cp -p ${DP}/Python-2.7/Lib/encodings/cp1256.py ${P}/tmp/subssupport/python2.7/cp1256.py
cp -p ${DP}/Python-2.7/Lib/encodings/iso8859_2.py ${P}/tmp/subssupport/python2.7/iso8859_2.py
cp -p ${DP}/Python-2.7/Lib/encodings/iso8859_6.py ${P}/tmp/subssupport/python2.7/iso8859_6.py
cp -p ${DP}/Python-2.7/Lib/encodings/iso8859_7.py ${P}/tmp/subssupport/python2.7/iso8859_7.py
cp -p ${DP}/Python-2.7/Lib/encodings/iso8859_9.py ${P}/tmp/subssupport/python2.7/iso8859_9.py
cp -p ${DP}/Python-2.7/Lib/encodings/iso8859_15.py ${P}/tmp/subssupport/python2.7/iso8859_15.py
cp -p ${DP}/Python-2.7/Lib/encodings/koi8_r.py ${P}/tmp/subssupport/python2.7/koi8_r.py
cp -p ${DP}/Python-2.7/Lib/encodings/mac_latin2.py ${P}/tmp/subssupport/python2.7/mac_latin2.py
cp -p ${DP}/Python-2.7/Lib/encodings/mac_cyrillic.py ${P}/tmp/subssupport/python2.7/mac_cyrillic.py
cp -p ${DP}/Python-2.7/Lib/encodings/mac_greek.py ${P}/tmp/subssupport/python2.7/mac_greek.py
cp -p ${DP}/Python-2.7/Lib/encodings/mac_roman.py ${P}/tmp/subssupport/python2.7/mac_roman.py
cp -p ${DP}/Python-2.7/Lib/encodings/mac_turkish.py ${P}/tmp/subssupport/python2.7/mac_turkish.py

tar -C ${P} -czf ${B}/data.tar.gz . --exclude=CONTROL
tar -C ${P}/CONTROL -czf ${B}/control.tar.gz .

echo "2.0" > ${B}/debian-binary

cd ${B}
ls -la
ar -r ${PKG}.ipk ./debian-binary ./control.tar.gz ./data.tar.gz
ar -r ${PKG}.deb ./debian-binary ./control.tar.gz ./data.tar.gz

rm -rf ${P}
rm -rf ${B}
rm -rf ${S}

