Thievery
--------

Written for Ludum Dare 25 by Schnerble, a.k.a. Chris Bevan.

You should be able to just launch the executable and hopefully all will be fine
- but there are a couple of notes below in case it isn't.

Thanks for playing! :)


1.    Post-Compo Version Edits
2.1.  Platform Notes: Windows
2.2.  Platform Notes: Linux
2.3.  Platform Notes: Source
3.    Credits


1.  Post-Compo Version Edits
----------------------------

I made a few *minor* edits when adding this readme file, after the compo.
These were:

- Added a warning screen for when AVBin isn't found
- Fixed an incorrect position of a house on level 3 that got a guard stuck
- Raised the alert distance slightly (from 70 to 100)
  (this is the range in which the guards notice something happening nearby
   that isn't in front of them, and go over to look at it)

Other than those, this post-compo version is identical to the original.


2.1.  Platform Notes: Windows
-----------------------------

The build is 32-bit, although I built on a 64-bit machine.  AVBin has worked
correctly on every machine I've tested it on, but some users are reporting
errors.  If you have problems, please let me know on the comments page - but
I'm struggling to track down what the problem is :(  Here's the original page
for AVBin, in case it's useful:

http://code.google.com/p/avbin/

Note though that only the version on this page will work, because unfortunately
the newer versions on the "new home" page do not work correctly with Pyglet.


2.2.  Platform Notes: Linux
---------------------------

The build is 64-bit, and I built it on Kubuntu 12.04.  If you have a Linux
flavour that's at least that recent, it should be fine.  If not, try the
source version; as long as you can get Python and Pyglet installed, and
ideally AVBin as well, it should work without problems.

The package names, at least on (K)ubuntu, are "python", "python-pyglet",
and "libavbin0".


2.3.  Platform Notes: Source
----------------------------

If you install Python, Pyglet and AVBin, then all should work fine by just
moving to the source directory and typing:

"python thievery.py".

Python:   http://www.python.org/download/       (tested with version 2.7.3;
                                                 requires at least 2.6)
Pyglet:   http://www.pyglet.org/download.html   (tested with version 1.1.4)
AVBin:    http://code.google.com/p/avbin/       (tested with version 5)


3.  Tools
---------

Music:            Autotracker
SFX:              BFXR
Programmer Art:   Gimp
Code Language:    Python
Libraries:        Pyglet, AVBin
Packager:         Pyinstaller
Editors:          Kate (Linux), Programmer's Notepad (Windows)
