--- compat.py   2021-10-30 14:52:00.000000000 +0200
+++ compat1.py  2021-04-18 09:59:50.000000000 +0200
@@ -17,16 +17,6 @@
 
 from . import _
 
-def isDMMImage():
-    try:
-        from enigma import eTimer
-        eTimer().timeout.connect
-    except Exception as e:
-        return False
-    return True
-
-DMM_IMAGE = isDMMImage()
-
 # taken from IPTVPlayer
